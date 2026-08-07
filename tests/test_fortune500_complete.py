import importlib.util
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


PREP = load_module("fortune500_prepare_test", "scripts/fortune500_prepare.py")
EVID = load_module("fortune500_evidence_test", "scripts/fortune500_evidence.py")
AGG = load_module("fortune500_aggregate_test", "scripts/fortune500_aggregate.py")


class Fortune500CompleteTests(unittest.TestCase):
    def test_acronym_index_can_resolve_company_display_name(self):
        entity = PREP.Entity("0000051143", "INTERNATIONAL BUSINESS MACHINES CORP", "IBM", "", "", "", "NYSE")
        entities = {entity.cik: entity}
        indexes = PREP.build_indexes(entities, [])
        result = PREP.resolve("IBM", entities, indexes, {}, 0.94, 0.86)
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["match_basis"], "acronym")
        self.assertEqual(result["ticker"], "IBM")

    def test_annual_report_candidates_include_exchange_and_year(self):
        urls = EVID.report_urls("WMT", "['NYSE']", [2025], "https://www.annualreports.com")
        self.assertTrue(any("NYSE_WMT_2025.pdf" in url for _, url in urls))

    def test_terminal_unresolved_review_validates(self):
        record = {
            "review_id": "AMACS-EVID-F500-2026-001",
            "organization": {"name": "Example", "position": 1, "identity_id": "AMACS-ORGID-CAND-F500-2026-001"},
            "corpus": {"corpus_id": "fortune-500-2026", "edition": "2026", "memberships": ["fortune_1000", "fortune_500", "fortune_100"]},
            "identity_resolution_status": "unresolved",
            "evidence_disposition": "identity_unresolved",
            "evidence": [], "observed_segments": [], "observed_activity_statements": [], "candidate_mappings": [],
            "gap_candidates": ["identity_resolution"], "review_status": "machine_reviewed", "not_for_profile_import": True,
        }
        EVID.validate(record)

    def test_crosswalk_and_identity_examples_validate(self):
        pairs = [
            ("examples/external-classification-crosswalk.example.json", "schemas/external-classification-crosswalk.schema.json"),
            ("examples/organization-identity.example.json", "schemas/organization-identity.schema.json"),
        ]
        for example_path, schema_path in pairs:
            example = json.loads((ROOT / example_path).read_text(encoding="utf-8"))
            schema = json.loads((ROOT / schema_path).read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(example))
            self.assertEqual(errors, [], f"{example_path}: {errors}")

    def test_aggregate_refuses_incomplete_cohort(self):
        with self.assertRaises(ValueError):
            AGG.aggregate([], expected_count=500)

    def test_no_profile_assertion_path(self):
        combined = "\n".join(
            (ROOT / path).read_text(encoding="utf-8")
            for path in ["scripts/fortune500_prepare.py", "scripts/fortune500_evidence.py", "scripts/fortune500_aggregate.py"]
        )
        self.assertIn('"not_for_profile_import": True', combined)
        self.assertIn('"profile_assertions_created": 0', combined)
        self.assertIn('"external_aliases_created": 0', combined)


if __name__ == "__main__":
    unittest.main()
