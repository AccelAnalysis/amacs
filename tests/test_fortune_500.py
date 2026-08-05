import gzip
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
        self.entities = {
            "0001018724": MODULE.SecEntity("0001018724", "AMAZON COM INC", "AMZN", "5961", "RETAIL-CATALOG & MAIL-ORDER HOUSES", "operating", "Nasdaq"),
            "0000034088": MODULE.SecEntity("0000034088", "EXXON MOBIL CORP", "XOM", "2911", "PETROLEUM REFINING", "operating", "NYSE"),
            "0000000001": MODULE.SecEntity("0000000001", "EXAMPLE INDUSTRIES INC", "EXM"),
        }
        self.names = MODULE.build_name_index(self.entities, [
            {"cik": "1018724", "name": "Amazon.com, Inc."},
            {"cik": "34088", "name": "Exxon Corporation"},
        ])

    def test_decodes_gzip_csv(self):
        raw = gzip.compress(b"name,cik,tickers\nExample Inc,1,['EXM']\n")
        rows = MODULE.decode_csv(raw)
        self.assertEqual(rows[0]["name"], "Example Inc")

    def test_normalized_and_compact_name_matching(self):
        self.assertEqual(MODULE.normalize_name("Example Industries, Inc."), "example industries")
        self.assertEqual(MODULE.compact_name("ExxonMobil Holdings"), "exxonmobil")
        self.assertEqual(MODULE.compact_name("Exxon Mobil Corp."), "exxonmobil")

    def test_controlled_override_resolves_nonidentical_name(self):
        result = MODULE.resolve_entity(
            "Amazon", self.entities, self.names,
            {"Amazon": {"cik": "0001018724", "sec_name": "AMAZON COM INC", "reason": "controlled"}},
            0.94, 0.86,
        )
        self.assertEqual(result["status"], "resolved_override")
        self.assertEqual(result["cik"], "0001018724")

    def test_former_name_can_resolve(self):
        result = MODULE.resolve_entity("Amazon.com", self.entities, self.names, {}, 0.94, 0.86)
        self.assertEqual(result["status"], "resolved_automatic")
        self.assertEqual(result["cik"], "0001018724")

    def test_low_similarity_is_not_forced(self):
        result = MODULE.resolve_entity("Private Mutual Association", self.entities, self.names, {}, 0.94, 0.86)
        self.assertEqual(result["status"], "unresolved")

    def test_sic_description_mapping_is_low_confidence(self):
        concepts = [{
            "concept_id": "AMACS-CAP-000001",
            "label": "Petroleum refining",
            "definition": "Refine crude petroleum.",
            "parent_id": "AMACS-FAM-000001",
            "terms": ["Petroleum refining"],
        }]
        mappings = MODULE.lexical_mappings("PETROLEUM REFINING", concepts)
        self.assertEqual(mappings[0]["concept_id"], "AMACS-CAP-000001")
        self.assertEqual(mappings[0]["confidence"], "low")

    def test_no_profile_assertion_path(self):
        source = (ROOT / "scripts" / "analyze_fortune_500.py").read_text(encoding="utf-8")
        self.assertIn('"not_for_profile_import": True', source)
        self.assertIn('"profile_assertions_created": 0', source)


if __name__ == "__main__":
    unittest.main()
