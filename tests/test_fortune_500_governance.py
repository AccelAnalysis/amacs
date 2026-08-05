import importlib.util
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "fortune500governance", ROOT / "scripts" / "govern_fortune_500_artifacts.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Fortune500GovernanceTests(unittest.TestCase):
    def test_compound_external_category_is_broad_crosswalk(self):
        primary = {"compound_or_catch_all": True}
        self.assertEqual(MODULE.mapping_relation(primary, 1, "ranking_primary_activity"), "broad_match")
        self.assertEqual(MODULE.mapping_relation(primary, 1, "regulatory_sic_description"), "related_match")

    def test_unresolved_entity_becomes_identity_candidate(self):
        raw = {
            "entity_resolution": {"status": "unresolved"},
            "primary_activity": {"compound_or_catch_all": False, "exact_source_alias_present": True},
            "candidate_mappings": [{"basis": "ranking_primary_activity"}],
        }
        self.assertEqual(MODULE.gap_disposition(raw), "organization_identity_candidate")

    def test_crosswalk_candidates_are_not_aliases(self):
        source = (ROOT / "scripts" / "govern_fortune_500_artifacts.py").read_text(encoding="utf-8")
        self.assertIn('"not_for_alias_import": True', source)
        self.assertIn('"profile_import_status": "prohibited"', source)
        self.assertIn('"not_for_profile_import": True', source)

    def test_controlled_override_stays_explicit(self):
        resolution = {
            "status": "resolved_override",
            "score": 1.0,
            "cik": "0001018724",
            "sec_name": "AMAZON COM INC",
            "ticker": "AMZN",
            "reason": "controlled override",
        }
        governed = MODULE.governed_resolution(resolution, "Amazon")
        self.assertEqual(governed["status"], "resolved")
        self.assertEqual(governed["match_basis"], "controlled_override")
        self.assertEqual(governed["resolved_identity"]["external_identifiers"]["cik"], "0001018724")

    def test_crosswalk_example_validates(self):
        schema = json.loads((ROOT / "schemas" / "external-classification-crosswalk.schema.json").read_text(encoding="utf-8"))
        example = json.loads((ROOT / "examples" / "external-classification-crosswalk.example.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(example))
        self.assertEqual(errors, [])

    def test_identity_example_validates(self):
        schema = json.loads((ROOT / "schemas" / "organization-identity.schema.json").read_text(encoding="utf-8"))
        example = json.loads((ROOT / "examples" / "organization-identity.example.json").read_text(encoding="utf-8"))
        errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(example))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
