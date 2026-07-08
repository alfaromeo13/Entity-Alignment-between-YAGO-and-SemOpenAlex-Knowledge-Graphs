import csv
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "scripts" / "build_yago_type_profiles.py"


class Stage05ProfileBuilderTest(unittest.TestCase):
    def test_rdf_type_object_is_retained_and_untyped_is_explicit(self) -> None:
        with TemporaryDirectory() as temporary:
            base = Path(temporary)
            graph = base / "graph"
            graph.mkdir()
            person = "<http://yago-knowledge.org/resource/Test_person>"
            untyped = "<http://yago-knowledge.org/resource/Test_untyped>"
            rdf_type = (
                "<http://www.w3.org/1999/02/22-rdf-syntax-ns#type>"
            )
            same_as = "<http://www.w3.org/2002/07/owl#sameAs>"

            entities = base / "entities.tsv"
            entities.write_text(
                "yago_entity\tsemopenalex_entity\n"
                f"{person}\t<https://semopenalex.org/author/A1>\n"
                f"{untyped}\t<https://semopenalex.org/work/W1>\n",
                encoding="utf-8",
            )
            (graph / "train.tsv").write_text(
                f"{person}\t{rdf_type}\t<http://schema.org/Person>\n"
                f"{untyped}\t{same_as}\t<http://example.org/id>\n",
                encoding="utf-8",
            )
            (graph / "valid.tsv").write_text("", encoding="utf-8")
            (graph / "test.tsv").write_text("", encoding="utf-8")
            taxonomy = base / "taxonomy.ttl"
            taxonomy.write_text(
                "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .\n"
                "@prefix schema: <http://schema.org/> .\n"
                "schema:Person rdfs:subClassOf schema:Thing .\n",
                encoding="utf-8",
            )
            output = base / "profiles.tsv"
            audit = base / "audit.json"

            subprocess.run(
                [
                    sys.executable,
                    str(BUILDER),
                    "--entities",
                    str(entities),
                    "--graph-dir",
                    str(graph),
                    "--taxonomy",
                    str(taxonomy),
                    "--output",
                    str(output),
                    "--audit-output",
                    str(audit),
                    "--progress-every",
                    "0",
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            with output.open(encoding="utf-8", newline="") as handle:
                rows = {
                    row["yago_entity"]: row
                    for row in csv.DictReader(handle, delimiter="\t")
                }
            self.assertEqual(
                rows[person]["yago_profile_type"],
                "person_like",
            )
            self.assertEqual(
                rows[person]["yago_rdf_types"],
                "http://schema.org/Person",
            )
            self.assertEqual(
                rows[untyped]["yago_profile_type"],
                "untyped",
            )
            self.assertEqual(
                rows[untyped]["yago_type_evidence"],
                "no_rdf_type",
            )
            report = json.loads(audit.read_text(encoding="utf-8"))
            self.assertEqual(report["literal_unknown_count"], 0)
            self.assertEqual(report["entities_with_rdf_type"], 1)


if __name__ == "__main__":
    unittest.main()
