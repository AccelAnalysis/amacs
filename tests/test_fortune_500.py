import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("fortune500", ROOT / "scripts" / "analyze_fortune_500.py")
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class Fortune500AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.entities = [
            MODULE.SecEntity("0001018724", "AMAZON COM INC", "AMZN"),
            MODULE.SecEntity("0000034088", "EXXON MOBIL CORP", "XOM"),
            MODULE.SecEntity("0000000001", "EXAMPLE INDUSTRIES INC", "EXM"),
        ]

    def test_normalized_and_compact_name_matching(self):
        self.assertEqual(MODULE.normalize_name("Example Industries, Inc."), "example industries")
        self.assertEqual(MODULE.compact_name("ExxonMobil Holdings"), "exxonmobil")
        self.assertEqual(MODULE.compact_name("Exxon Mobil Corp."), "exxonmobil")

    def test_controlled_override_resolves_nonidentical_name(self):
        result = MODULE.resolve_entity(
            "Amazon",
            self.entities,
            {"Amazon": {"cik": "0001018724", "sec_name": "AMAZON COM INC", "reason": "controlled"}},
            0.94,
            0.86,
        )
        self.assertEqual(result["status"], "resolved_override")
        self.assertEqual(result["cik"], "0001018724")

    def test_low_similarity_is_not_forced(self):
        result = MODULE.resolve_entity("Private Mutual Association", self.entities, {}, 0.94, 0.86)
        self.assertEqual(result["status"], "unresolved")

    def test_latest_annual_filing(self):
        submissions = {
            "filings": {"recent": {
                "form": ["10-Q", "10-K"],
                "filingDate": ["2026-05-01", "2026-02-15"],
                "reportDate": ["2026-03-31", "2025-12-31"],
                "accessionNumber": ["0001-26-000002", "0001-26-000001"],
                "primaryDocument": ["q1.htm", "annual.htm"],
            }}
        }
        filing = MODULE.latest_annual_filing(submissions, ["10-K"])
        self.assertIsNotNone(filing)
        self.assertEqual(filing["primary_document"], "annual.htm")

    def test_extracts_activity_and_segment_statements(self):
        text = """
        Item 1. Business
        We operate through three reportable segments: Cloud Services, Retail Stores, and Logistics Operations.
        We provide cloud infrastructure and distribute consumer products through physical and online stores.
        Item 1A. Risk Factors
        Risks are described here.
        """
        statements, segments = MODULE.extract_statements(text)
        self.assertTrue(statements)
        self.assertTrue(segments)
        self.assertNotIn("Risks are described", " ".join(statements))

    def test_no_profile_assertion_path(self):
        source = (ROOT / "scripts" / "analyze_fortune_500.py").read_text(encoding="utf-8")
        self.assertIn('"not_for_profile_import": True', source)
        self.assertIn('"profile_assertions_created": 0', source)


if __name__ == "__main__":
    unittest.main()
