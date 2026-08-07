import importlib.util
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from amacs_io import DATASET_ORDER, load_dataset  # noqa: E402


def validate_example(example_path: str, schema_path: str):
    example = json.loads((ROOT / example_path).read_text(encoding="utf-8"))
    schema = json.loads((ROOT / schema_path).read_text(encoding="utf-8"))
    return list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(example))


class Fortune100ArchitectureTests(unittest.TestCase):
    def test_market_role_registry_is_governed_and_unique(self):
        roles = load_dataset("market_roles", ROOT)
        self.assertEqual(len(roles), 18)
        self.assertEqual(len({r["market_role_id"] for r in roles}), 18)
        self.assertEqual(len({r["code"] for r in roles}), 18)
        self.assertIn("market_roles", DATASET_ORDER)

    def test_outcome_registry_is_governed_and_unique(self):
        outcomes = load_dataset("outcome_types", ROOT)
        self.assertEqual(len(outcomes), 12)
        self.assertEqual(len({r["outcome_type_id"] for r in outcomes}), 12)
        self.assertEqual(len({r["code"] for r in outcomes}), 12)
        self.assertIn("outcome_types", DATASET_ORDER)

    def test_existing_organization_capability_example_remains_valid(self):
        errors = validate_example("examples/organization-capability.example.json", "schemas/organization-capability.schema.json")
        self.assertEqual(errors, [], errors)

    def test_capability_evidence_example_validates(self):
        errors = validate_example("examples/capability-evidence.example.json", "schemas/capability-evidence.schema.json")
        self.assertEqual(errors, [], errors)

    def test_outcome_observation_example_validates(self):
        errors = validate_example("examples/outcome-observation.example.json", "schemas/outcome-observation.schema.json")
        self.assertEqual(errors, [], errors)

    def test_capability_assertion_supports_scope_role_and_evidence(self):
        schema = json.loads((ROOT / "schemas/organization-capability.schema.json").read_text(encoding="utf-8"))
        props = schema["properties"]
        self.assertIn("organization_identity_id", props)
        self.assertIn("entity_scope", props)
        self.assertIn("market_role_ids", props)
        self.assertIn("evidence_ids", props)

    def test_outcome_learning_is_explicitly_gated(self):
        schema = json.loads((ROOT / "schemas/outcome-observation.schema.json").read_text(encoding="utf-8"))
        values = schema["properties"]["learning_status"]["enum"]
        self.assertIn("eligible_for_review", values)
        self.assertIn("approved_for_aggregate_learning", values)
        self.assertNotIn("automatic", values)


if __name__ == "__main__":
    unittest.main()
