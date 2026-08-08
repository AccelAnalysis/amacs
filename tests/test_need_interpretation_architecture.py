from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
VALID_TEST_COMMIT = "b" * 40

SCHEMA_BY_EXAMPLE_KEY = {
    "market_need": "schemas/market-need.schema.json",
    "interpretation_record": "schemas/interpretation-record.schema.json",
    "interpretation_candidate": "schemas/interpretation-candidate.schema.json",
    "concept_interpretation_guidance": "schemas/concept-interpretation-guidance.schema.json",
}


class NeedAndInterpretationArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.examples = json.loads(
            (ROOT / "examples" / "need-and-interpretation.examples.json").read_text(encoding="utf-8")
        )

    def load(self, path: str) -> dict:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))

    def test_release_is_0_5_0(self):
        self.assertEqual((ROOT / "VERSION").read_text(encoding="utf-8").strip(), "0.5.0")
        self.assertEqual((ROOT / "RELEASE_DATE").read_text(encoding="utf-8").strip(), "2026-08-08")

    def test_runtime_examples_validate(self):
        self.assertEqual(set(self.examples), set(SCHEMA_BY_EXAMPLE_KEY))
        for example_key, schema_path in SCHEMA_BY_EXAMPLE_KEY.items():
            example = self.examples[example_key]
            schema = self.load(schema_path)
            Draft202012Validator.check_schema(schema)
            errors = sorted(
                Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(example),
                key=lambda error: list(error.path),
            )
            self.assertEqual(
                errors,
                [],
                msg=f"{example_key}: " + "; ".join(error.message for error in errors),
            )

    def test_market_need_separates_target_from_observed_outcome(self):
        need = self.examples["market_need"]
        self.assertEqual(need["solution_posture"], "open")
        self.assertTrue(need["observed_condition"])
        self.assertTrue(need["desired_outcome"])
        self.assertTrue(need["unresolved_questions"])
        self.assertNotIn("outcome_observation_id", need)
        self.assertEqual(need["confirmed_requirement_ids"], [])

    def test_interpretation_is_non_authoritative_and_requires_confirmation(self):
        record = self.examples["interpretation_record"]
        candidate = self.examples["interpretation_candidate"]
        self.assertTrue(record["human_confirmation_required"])
        self.assertEqual(record["authoritative_effect"], "none")
        self.assertEqual(candidate["authoritative_effect"], "none")
        self.assertEqual(candidate["disposition"], "suggested")
        self.assertEqual(candidate["target_kind"], "organization_capability_assertion")
        self.assertNotIn("assertion_status", candidate)

    def test_interpretation_contract_is_provider_neutral(self):
        record_schema = self.load("schemas/interpretation-record.schema.json")
        serialized = json.dumps(record_schema).casefold()
        for provider_term in ["openai", "anthropic", "gemini", "gpt-", "claude"]:
            self.assertNotIn(provider_term, serialized)
        self.assertIn("assisted", record_schema["properties"]["mapping_method"]["enum"])
        self.assertIn("human", record_schema["properties"]["mapping_method"]["enum"])

    def test_guidance_explains_boundaries_without_asserting_capability(self):
        guidance = self.examples["concept_interpretation_guidance"]
        self.assertTrue(guidance["inclusion_notes"])
        self.assertTrue(guidance["exclusion_notes"])
        self.assertTrue(guidance["clarification_questions"])
        self.assertEqual(guidance["concept_id"], "AMACS-CAP-000006")
        self.assertNotIn("organization_id", guidance)
        self.assertNotIn("assertion_status", guidance)

    def test_release_builder_includes_interpretation_schemas(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "build_release.py"),
                    "--output",
                    temporary,
                    "--source-commit",
                    VALID_TEST_COMMIT,
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            schema_dir = Path(temporary) / "0.5.0" / "schemas"
            for schema_path in SCHEMA_BY_EXAMPLE_KEY.values():
                self.assertTrue((schema_dir / Path(schema_path).name).exists())


if __name__ == "__main__":
    unittest.main()
