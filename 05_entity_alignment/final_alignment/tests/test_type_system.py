from pathlib import Path
from tempfile import TemporaryDirectory
import sys
import unittest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from type_system import (  # noqa: E402
    TaxonomyClassifier,
    compatibility_state,
    semopenalex_type,
)


TAXONOMY = """\
@prefix yago: <http://yago-knowledge.org/resource/> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
schema:Person rdfs:subClassOf schema:Thing .
schema:CreativeWork rdfs:subClassOf schema:Thing .
schema:Organization rdfs:subClassOf schema:Thing .
yago:Researcher rdfs:subClassOf schema:Person .
yago:Clinical_trial rdfs:subClassOf yago:Review .
yago:Review rdfs:subClassOf schema:CreativeWork .
yago:University rdfs:subClassOf schema:Organization .
yago:University rdfs:subClassOf schema:Place .
"""


class Stage05TypeSystemTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = TemporaryDirectory()
        path = Path(self.tempdir.name) / "taxonomy.ttl"
        path.write_text(TAXONOMY, encoding="utf-8")
        self.classifier = TaxonomyClassifier(path)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_explicit_person_is_resolved(self) -> None:
        result = self.classifier.classify(
            {"http://yago-knowledge.org/resource/Researcher"},
            set(),
        )
        self.assertEqual(result["yago_profile_types"], "person_like")
        self.assertEqual(result["yago_type_evidence"], "taxonomy")

    def test_transitive_creative_work_is_resolved(self) -> None:
        result = self.classifier.classify(
            {"http://yago-knowledge.org/resource/Clinical_trial"},
            set(),
        )
        self.assertEqual(result["yago_profile_types"], "creative_work_like")

    def test_multiple_inheritance_is_preserved(self) -> None:
        result = self.classifier.classify(
            {"http://yago-knowledge.org/resource/University"},
            set(),
        )
        self.assertEqual(
            result["yago_profile_types"],
            "organization_like|place_like",
        )

    def test_predicate_fallback_is_explicitly_weaker(self) -> None:
        result = self.classifier.classify(set(), {"about"})
        self.assertEqual(result["yago_profile_type"], "creative_work_like")
        self.assertEqual(result["yago_type_evidence"], "predicate_fallback")
        self.assertEqual(result["yago_type_confidence"], "0.5")

    def test_unmapped_and_untyped_are_not_called_unknown(self) -> None:
        unmapped = self.classifier.classify(
            {"http://example.org/UnmappedClass"},
            set(),
        )
        untyped = self.classifier.classify(set(), set())
        self.assertEqual(unmapped["yago_profile_type"], "other_typed")
        self.assertEqual(untyped["yago_profile_type"], "untyped")
        self.assertNotIn("unknown", unmapped["yago_profile_types"])
        self.assertNotIn("unknown", untyped["yago_profile_types"])

    def test_compatibility_has_three_states(self) -> None:
        self.assertEqual(
            compatibility_state("person_like", "resolved", "author"),
            "compatible",
        )
        self.assertEqual(
            compatibility_state("creative_work_like", "resolved", "author"),
            "incompatible",
        )
        self.assertEqual(
            compatibility_state("untyped", "untyped", "author"),
            "unresolved",
        )

    def test_semopenalex_uri_type(self) -> None:
        self.assertEqual(
            semopenalex_type("<https://semopenalex.org/work/W1>"),
            "work",
        )
        self.assertEqual(
            semopenalex_type("<https://example.org/entity/1>"),
            "unrecognized_uri_type",
        )


if __name__ == "__main__":
    unittest.main()
