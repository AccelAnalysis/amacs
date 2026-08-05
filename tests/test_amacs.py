from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from amacs_io import all_datasets, load_dataset  # noqa: E402

VALID_TEST_COMMIT = 'a' * 40


class AmacsFoundationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = all_datasets(ROOT)

    def test_validator_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / 'scripts' / 'validate.py')],
            cwd=ROOT, capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)

    def test_seed_has_broad_market_coverage(self):
        concepts = self.data['concepts']
        self.assertEqual(sum(record['concept_type'] == 'domain' for record in concepts), 16)
        self.assertGreaterEqual(sum(record['concept_type'] == 'family' for record in concepts), 75)
        self.assertGreaterEqual(sum(record['concept_type'] == 'capability' for record in concepts), 350)

    def test_domain_seed_expansion_is_deterministic(self):
        first = load_dataset('concepts', ROOT)
        second = load_dataset('concepts', ROOT)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 611)

    def test_capabilities_are_matchable_only(self):
        for concept in self.data['concepts']:
            self.assertEqual(concept['matchable'], concept['concept_type'] == 'capability')

    def test_search_alias_seed_is_substantive(self):
        capability_ids = {record['concept_id'] for record in self.data['concepts']}
        aliases = self.data['aliases']
        self.assertGreaterEqual(len(aliases), 150)
        self.assertTrue(all(alias['concept_id'] in capability_ids for alias in aliases))

    def test_standards_market_architecture_capabilities_are_explicit(self):
        concepts = {record['concept_id']: record for record in self.data['concepts']}
        domain = concepts['AMACS-DOM-000016']
        self.assertEqual(domain['preferred_label'], 'Standards, Taxonomy and Market Architecture')
        self.assertEqual(domain['concept_type'], 'domain')
        self.assertEqual(domain['version_introduced'], '0.2.0')

        expected = {
            'AMACS-CAP-000586': ('Taxonomy development', 'AMACS-FAM-000585'),
            'AMACS-CAP-000587': ('Standards governance', 'AMACS-FAM-000585'),
            'AMACS-CAP-000588': ('Capability mapping', 'AMACS-FAM-000585'),
            'AMACS-CAP-000590': ('Evidence architecture', 'AMACS-FAM-000589'),
            'AMACS-CAP-000591': ('Response architecture', 'AMACS-FAM-000589'),
            'AMACS-CAP-000592': ('Decision architecture', 'AMACS-FAM-000589'),
            'AMACS-CAP-000594': ('Controlled taxonomy licensing', 'AMACS-FAM-000593'),
            'AMACS-CAP-000595': ('Taxonomy API delivery', 'AMACS-FAM-000593'),
        }
        for concept_id, (label, parent_id) in expected.items():
            concept = concepts[concept_id]
            self.assertEqual(concept['preferred_label'], label)
            self.assertEqual(concept['primary_parent_id'], parent_id)
            self.assertEqual(concept['concept_type'], 'capability')
            self.assertTrue(concept['matchable'])
            self.assertEqual(concept['version_introduced'], '0.2.0')
            self.assertEqual(concept['editorial_maturity'], 'reviewed')
            self.assertGreaterEqual(len(concept['definition']), 80)

        self.assertEqual(concepts['AMACS-CAP-000145']['version_introduced'], '0.1.0')

        relationship_pairs = {
            (
                record['source_concept_id'],
                record['relationship_type'],
                record['target_concept_id'],
                record['version_introduced'],
            )
            for record in self.data['relationships']
        }
        self.assertIn(
            ('AMACS-CAP-000586', 'commonly_combined_with', 'AMACS-CAP-000587', '0.2.0'),
            relationship_pairs,
        )
        self.assertIn(
            ('AMACS-CAP-000591', 'commonly_combined_with', 'AMACS-CAP-000592', '0.2.0'),
            relationship_pairs,
        )
        self.assertIn(
            ('AMACS-CAP-000594', 'commonly_combined_with', 'AMACS-CAP-000595', '0.2.0'),
            relationship_pairs,
        )

    def test_request_families_reference_architectures(self):
        response_templates = {record['response_template_id'] for record in self.data['response_templates']}
        decision_templates = {record['decision_template_id'] for record in self.data['decision_templates']}
        for request in self.data['request_families']:
            self.assertIn(request['default_response_template_id'], response_templates)
            self.assertIn(request['default_decision_template_id'], decision_templates)

    def test_requirement_bundles_connect_request_response_and_decision(self):
        request_ids = {record['request_family_id'] for record in self.data['request_families']}
        requirement_type_ids = {record['requirement_type_id'] for record in self.data['requirement_types']}
        section_ids = {record['response_section_id'] for record in self.data['response_sections']}
        factor_ids = {record['decision_factor_id'] for record in self.data['decision_factors']}
        capability_fit_seen = False
        self.assertGreaterEqual(len(self.data['requirement_bundles']), 8)
        for bundle in self.data['requirement_bundles']:
            self.assertTrue(set(bundle['applicable_request_family_ids']).issubset(request_ids))
            for item in bundle['items']:
                self.assertIn(item['requirement_type_id'], requirement_type_ids)
                self.assertTrue(set(item['linked_response_section_ids']).issubset(section_ids))
                self.assertTrue(set(item['linked_decision_factor_ids']).issubset(factor_ids))
                if item['decision_treatment'] == 'gate_and_scored_depth':
                    capability_fit_seen = capability_fit_seen or 'AMACS-DEC-000005' in item['linked_decision_factor_ids']
        self.assertTrue(capability_fit_seen)

    def test_requirement_bundle_team_coverage_respects_requirement_type(self):
        requirement_types = {
            record['requirement_type_id']: record for record in self.data['requirement_types']
        }
        for bundle in self.data['requirement_bundles']:
            for item in bundle['items']:
                requirement_type = requirement_types[item['requirement_type_id']]
                if item['default_team_coverage_allowed']:
                    self.assertTrue(
                        requirement_type['team_coverage_allowed'],
                        msg=(
                            f"{bundle['requirement_bundle_id']}/{item['item_key']} allows team coverage "
                            f"but {requirement_type['requirement_type_id']} forbids it"
                        ),
                    )

    def test_request_families_reference_governance_and_bundles(self):
        governance_ids = {record['governance_profile_id'] for record in self.data['governance_profiles']}
        bundle_ids = {record['requirement_bundle_id'] for record in self.data['requirement_bundles']}
        for request in self.data['request_families']:
            self.assertIn(request['default_governance_profile_id'], governance_ids)
            self.assertIn(request['default_governance_profile_id'], request['allowed_governance_profile_ids'])
            self.assertTrue(set(request['allowed_governance_profile_ids']).issubset(governance_ids))
            self.assertTrue(set(request['recommended_requirement_bundle_ids']).issubset(bundle_ids))

    def test_readiness_rules_have_actionable_deep_links(self):
        rules = self.data['readiness_rules']
        self.assertGreaterEqual(len(rules), 25)
        for rule in rules:
            target = rule['fix_target']
            self.assertTrue(target['builder_stage'])
            self.assertTrue(target['section_key'])
            self.assertTrue(target['field_key'])
            if rule['blocking']:
                self.assertFalse(rule['acknowledgment_allowed'])
        capability_rule = {record['code']: record for record in rules}['CAPABILITY_FIT_FACTOR_LINKED']
        self.assertEqual(capability_rule['fix_target']['builder_stage'], 'decision_architecture')

    def test_controlled_units_are_linked_to_numeric_properties(self):
        units = {record['unit_id'] for record in self.data['units']}
        properties = {record['property_id']: record for record in self.data['properties']}
        self.assertGreaterEqual(len(units), 20)
        for prop in properties.values():
            self.assertTrue(set(prop['allowed_unit_ids']).issubset(units))
        self.assertTrue(properties['AMACS-PROP-000003']['allowed_unit_ids'])
        self.assertTrue(properties['AMACS-PROP-000027']['allowed_unit_ids'])
        self.assertTrue(properties['AMACS-PROP-000030']['allowed_unit_ids'])

    def test_runtime_examples_validate_against_schemas(self):
        pairs = [
            ('examples/organization-capability.example.json', 'schemas/organization-capability.schema.json'),
            ('examples/rfx-requirement.example.json', 'schemas/rfx-requirement.schema.json'),
            ('examples/taxonomy-proposal.example.json', 'schemas/proposal.schema.json'),
        ]
        for example_path, schema_path in pairs:
            instance = json.loads((ROOT / example_path).read_text(encoding='utf-8'))
            schema = json.loads((ROOT / schema_path).read_text(encoding='utf-8'))
            errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda error: list(error.path))
            self.assertEqual(errors, [], msg=f'{example_path}: ' + '; '.join(error.message for error in errors))

    def test_information_only_request_families_do_not_claim_award(self):
        requests = {record['code']: record for record in self.data['request_families']}
        for code in ['RFI', 'SOURCES_SOUGHT', 'RFQUAL_SOQ', 'TEAMING_PARTNER', 'SITE_SELECTION_RFI']:
            self.assertFalse(requests[code]['supports_award'])

    def test_site_selection_is_structured_and_confidential(self):
        requests = {record['code']: record for record in self.data['request_families']}
        sections = {record['preferred_label'] for record in self.data['response_sections']}
        profiles = {record['code']: record for record in self.data['governance_profiles']}
        self.assertIn('SITE_SELECTION_RFI', requests)
        self.assertFalse(requests['SITE_SELECTION_RFI']['supports_award'])
        self.assertIn('Site or building proposal', sections)
        self.assertIn('Utilities response', sections)
        self.assertIn('Operating cost model', sections)
        profile = profiles['CONFIDENTIAL_SITE_SELECTION']
        self.assertIn('confidential_project', profile['confidentiality_modes'])
        self.assertTrue(profile['requires_evaluation_lock'])

    def test_release_builder_materializes_expanded_datasets(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / 'scripts' / 'build_release.py'),
                    '--output',
                    temporary,
                    '--source-commit',
                    VALID_TEST_COMMIT,
                ],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            release = Path(temporary) / '0.2.0'
            concepts = (release / 'source' / 'concepts.jsonl').read_text(encoding='utf-8').splitlines()
            aliases = (release / 'source' / 'aliases.jsonl').read_text(encoding='utf-8').splitlines()
            manifest = json.loads((release / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(len(concepts), 611)
            self.assertEqual(len(aliases), 185)
            self.assertEqual(manifest['source_commit'], VALID_TEST_COMMIT)
            self.assertTrue((release / 'SHA256SUMS').exists())

    def test_release_builder_rejects_existing_version_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            command = [
                sys.executable,
                str(ROOT / 'scripts' / 'build_release.py'),
                '--output',
                temporary,
                '--source-commit',
                VALID_TEST_COMMIT,
            ]
            first = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertEqual(first.returncode, 0, msg=first.stdout + first.stderr)
            release = Path(temporary) / '0.2.0'
            checksums_before = (release / 'SHA256SUMS').read_text(encoding='utf-8')

            second = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=False)
            self.assertNotEqual(second.returncode, 0)
            self.assertIn('already exists and is immutable', second.stderr)
            self.assertEqual(
                (release / 'SHA256SUMS').read_text(encoding='utf-8'),
                checksums_before,
            )

    def test_release_builder_derives_git_source_commit(self):
        expected = subprocess.run(
            ['git', 'rev-parse', '--verify', 'HEAD'],
            cwd=ROOT, capture_output=True, text=True, check=True,
        ).stdout.strip().lower()
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run(
                [sys.executable, str(ROOT / 'scripts' / 'build_release.py'), '--output', temporary],
                cwd=ROOT, capture_output=True, text=True, check=False,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
            release = Path(temporary) / '0.2.0'
            manifest = json.loads((release / 'manifest.json').read_text(encoding='utf-8'))
            self.assertEqual(manifest['source_commit'], expected)
            self.assertRegex(manifest['source_commit'], r'^[0-9a-f]{40}$')


if __name__ == '__main__':
    unittest.main()
