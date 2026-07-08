import csv
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
AB_SCRIPTS = ROOT / "type_text_enrichment/scripts"
C_SCRIPTS = ROOT / "graph_neighbor_only/scripts"
STAGE05_SCRIPTS = ROOT.parent / "05_entity_alignment/final_alignment/scripts"

PROFILE_HEADER = [
    "yago_entity",
    "yago_profile_type",
    "yago_profile_types",
    "yago_type_status",
    "yago_type_evidence",
    "yago_type_confidence",
    "yago_rdf_type_count",
    "yago_rdf_types",
    "yago_predicate_count",
    "yago_top_predicates",
]


def write_tsv(path: Path, header: list, rows: list) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, delimiter="\t")
        writer.writerow(header)
        writer.writerows(rows)


def read_tsv(path: Path) -> list:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


class PipelineCliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.y1 = "<http://yago-knowledge.org/resource/Person_1>"
        self.y2 = "<http://yago-knowledge.org/resource/Work_1>"
        self.y3 = "<http://yago-knowledge.org/resource/Untyped_1>"
        self.a1 = "<https://semopenalex.org/author/A1>"
        self.a2 = "<https://semopenalex.org/author/A2>"
        self.w3 = "<https://semopenalex.org/work/W3>"
        self.profiles = self.base / "profiles.tsv"
        write_tsv(
            self.profiles,
            PROFILE_HEADER,
            [
                [
                    self.y1,
                    "person_like",
                    "person_like",
                    "resolved",
                    "taxonomy",
                    "1.0",
                    "1",
                    "http://schema.org/Person",
                    "1",
                    "type",
                ],
                [
                    self.y2,
                    "creative_work_like",
                    "creative_work_like",
                    "resolved",
                    "taxonomy",
                    "1.0",
                    "1",
                    "http://schema.org/CreativeWork",
                    "1",
                    "type",
                ],
                [
                    self.y3,
                    "untyped",
                    "untyped",
                    "untyped",
                    "no_rdf_type",
                    "0.0",
                    "0",
                    "",
                    "1",
                    "sameas",
                ],
            ],
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_script(self, script: Path, *arguments: str) -> None:
        subprocess.run(
            [sys.executable, str(script), *arguments],
            check=True,
            capture_output=True,
            text=True,
        )

    def test_stage05_policy_difference(self) -> None:
        alignments = self.base / "stage05.tsv"
        write_tsv(
            alignments,
            [
                "yago_entity",
                "semopenalex_entity",
                "semopenalex_type",
                "embedding_cosine",
            ],
            [
                [self.y1, self.a1, "author", "0.8"],
                [self.y2, self.a2, "author", "0.8"],
                [self.y3, self.a2, "author", "0.8"],
            ],
        )
        counts = {}
        for policy in ("keep", "reject"):
            accepted = self.base / f"{policy}_accepted.tsv"
            rejected = self.base / f"{policy}_rejected.tsv"
            summary = self.base / f"{policy}_summary.json"
            self.run_script(
                STAGE05_SCRIPTS / "apply_stage05_type_filter.py",
                "--input",
                str(alignments),
                "--profiles",
                str(self.profiles),
                "--accepted",
                str(accepted),
                "--rejected",
                str(rejected),
                "--summary",
                str(summary),
                "--unresolved-policy",
                policy,
            )
            counts[policy] = (
                len(read_tsv(accepted)),
                len(read_tsv(rejected)),
            )
            self.assertEqual(
                json.loads(summary.read_text())["literal_unknown_rows"],
                0,
            )
        self.assertEqual(counts["keep"], (2, 1))
        self.assertEqual(counts["reject"], (1, 2))

    def test_ab_rerank_and_proxy_priority(self) -> None:
        candidates = self.base / "candidates.tsv"
        scores = self.base / "scores.tsv"
        candidate_header = [
            "yago_entity",
            "semopenalex_entity",
            "embedding_cosine",
        ]
        write_tsv(
            candidates,
            candidate_header,
            [
                [self.y1, self.a1, "0.8"],
                [self.y2, self.a2, "0.9"],
                [self.y3, self.w3, "0.7"],
            ],
        )
        write_tsv(
            scores,
            [
                "yago_entity",
                "semopenalex_entity",
                "profile_tfidf_score",
            ],
            [
                [self.y1, self.a1, "0.5"],
                [self.y2, self.a2, "0.5"],
                [self.y3, self.w3, "0.5"],
            ],
        )
        permissive_all = self.base / "permissive_all.tsv"
        permissive_top1 = self.base / "permissive_top1.tsv"
        strict_all = self.base / "strict_all.tsv"
        strict_top1 = self.base / "strict_top1.tsv"
        summary = self.base / "rerank_summary.json"
        self.run_script(
            AB_SCRIPTS / "rerank_type_text_candidates.py",
            "--candidates",
            str(candidates),
            "--profile-scores",
            str(scores),
            "--yago-profiles",
            str(self.profiles),
            "--permissive-all",
            str(permissive_all),
            "--permissive-top1",
            str(permissive_top1),
            "--strict-all",
            str(strict_all),
            "--strict-top1",
            str(strict_top1),
            "--summary",
            str(summary),
        )
        self.assertEqual(len(read_tsv(permissive_top1)), 2)
        self.assertEqual(len(read_tsv(strict_top1)), 1)

        proxy_yago = "<http://yago-knowledge.org/resource/Proxy_1>"
        proxy = self.base / "proxy.tsv"
        write_tsv(
            proxy,
            ["yago_entity", "semopenalex_entity"],
            [[proxy_yago, self.a1]],
        )
        merged = self.base / "merged.tsv"
        rejected_proxy = self.base / "rejected_proxy.tsv"
        merge_summary = self.base / "merge_summary.json"
        self.run_script(
            AB_SCRIPTS / "merge_proxy_gold.py",
            "--proxy-gold",
            str(proxy),
            "--top1",
            str(permissive_top1),
            "--yago-profiles",
            str(self.profiles),
            "--unresolved-policy",
            "keep",
            "--output",
            str(merged),
            "--rejected-proxy",
            str(rejected_proxy),
            "--summary",
            str(merge_summary),
        )
        rows = read_tsv(merged)
        pairs = {
            (row["yago_entity"], row["semopenalex_entity"]) for row in rows
        }
        self.assertIn((proxy_yago, self.a1), pairs)
        self.assertNotIn((self.y1, self.a1), pairs)
        self.assertIn((self.y3, self.w3), pairs)
        self.assertEqual(len(pairs), 2)

        strict_merged = self.base / "strict_merged.tsv"
        strict_rejected_proxy = self.base / "strict_rejected_proxy.tsv"
        self.run_script(
            AB_SCRIPTS / "merge_proxy_gold.py",
            "--proxy-gold",
            str(proxy),
            "--top1",
            str(strict_top1),
            "--yago-profiles",
            str(self.profiles),
            "--unresolved-policy",
            "reject",
            "--output",
            str(strict_merged),
            "--rejected-proxy",
            str(strict_rejected_proxy),
            "--summary",
            str(self.base / "strict_merge_summary.json"),
        )
        strict_pairs = {
            (row["yago_entity"], row["semopenalex_entity"])
            for row in read_tsv(strict_merged)
        }
        self.assertNotIn((proxy_yago, self.a1), strict_pairs)
        self.assertIn((self.y1, self.a1), strict_pairs)
        self.assertEqual(len(read_tsv(strict_rejected_proxy)), 1)

    def test_c_only_rerank_and_source_metadata(self) -> None:
        scores = self.base / "neighbor_scores.tsv"
        write_tsv(
            scores,
            [
                "yago_entity",
                "semopenalex_entity",
                "embedding_cosine",
                "neighbor_tfidf_score",
            ],
            [
                [self.y1, self.a1, "0.8", "0.3"],
                [self.y2, self.a2, "0.9", "0.4"],
                [self.y3, self.w3, "0.7", "0.2"],
            ],
        )
        permissive_all = self.base / "c_permissive_all.tsv"
        permissive_top1 = self.base / "c_permissive_top1.tsv"
        strict_all = self.base / "c_strict_all.tsv"
        strict_top1 = self.base / "c_strict_top1.tsv"
        self.run_script(
            C_SCRIPTS / "rerank_graph_neighbor_candidates.py",
            "--scores",
            str(scores),
            "--yago-profiles",
            str(self.profiles),
            "--permissive-all",
            str(permissive_all),
            "--permissive-top1",
            str(permissive_top1),
            "--strict-all",
            str(strict_all),
            "--strict-top1",
            str(strict_top1),
            "--summary",
            str(self.base / "c_rerank_summary.json"),
        )
        self.assertEqual(len(read_tsv(permissive_top1)), 2)
        self.assertEqual(len(read_tsv(strict_top1)), 1)

        proxy_yago = "<http://yago-knowledge.org/resource/Proxy_2>"
        proxy = self.base / "c_proxy.tsv"
        write_tsv(
            proxy,
            ["yago_entity", "semopenalex_entity"],
            [[proxy_yago, self.a1]],
        )
        merged = self.base / "c_merged.tsv"
        self.run_script(
            C_SCRIPTS / "merge_proxy_gold.py",
            "--proxy-gold",
            str(proxy),
            "--top1",
            str(permissive_top1),
            "--yago-profiles",
            str(self.profiles),
            "--unresolved-policy",
            "keep",
            "--ranked-source",
            "embedding_graph_neighbor_top1_v2",
            "--proxy-evidence-column",
            "neighbor_tfidf_score",
            "--output",
            str(merged),
            "--rejected-proxy",
            str(self.base / "c_rejected_proxy.tsv"),
            "--summary",
            str(self.base / "c_merge_summary.json"),
        )
        rows = read_tsv(merged)
        proxy_row = next(row for row in rows if row["source"] == "strict_proxy_gold")
        ranked_row = next(
            row
            for row in rows
            if row["source"] == "embedding_graph_neighbor_top1_v2"
        )
        self.assertEqual(proxy_row["neighbor_tfidf_score"], "1.00000000")
        self.assertEqual(ranked_row["yago_entity"], self.y3)


if __name__ == "__main__":
    unittest.main()
