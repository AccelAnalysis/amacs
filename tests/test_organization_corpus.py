from __future__ import annotations

import json
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from amacs_io import load_dataset  # noqa: E402
from analyze_organization_corpus import (  # noqa: E402
    build_observation,
    load_activity_map,
    validate_observations,
)


class OrganizationCorpusTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.manifest = json.loads(
            (ROOT / 'research' / 'fortune-1000-2026' / 'manifest.json').read_text(encoding='utf-8')
        )
        cls.summary = json.loads(
            (ROOT / 'research' / 'fortune-1000-2026' / 'reviewed-coverage-summary.json').read_text(
                encoding='utf-8'
            )
        )
        concepts = load_dataset('concepts', ROOT)
        cls.capability_ids = {
            record['concept_id']
            for record in concepts
            if record['concept_type'] == 'capability'
        }
        cls.activity_map = load_activity_map(
            ROOT / cls.manifest['activity_map'],
            cls.capability_ids,
        )

    def test_primary_activity_map_is_complete_and_governed(self):
        self.assertEqual(len(self.activity_map), 74)
        statuses = Counter(entry['baseline_status'] for entry in self.activity_map.values())
        self.assertEqual(statuses, {'direct': 13, 'partial': 35, 'gap': 26})
        self.assertTrue(all(entry['candidate_concept_ids'] for entry in self.activity_map.values()))
        self.assertTrue(all(
            set(entry['candidate_concept_ids']).issubset(self.capability_ids)
            for entry in self.activity_map.values()
        ))

    def test_reviewed_summary_reconciles(self):
        self.assertEqual(self.summary['organization_count'], 1000)
        self.assertEqual(sum(self.summary['baseline_organization_coverage'].values()), 1000)
        self.assertEqual(sum(self.summary['baseline_label_coverage'].values()), 74)
        self.assertEqual(self.summary['cohort_counts'], {
            'fortune_1000': 1000,
            'fortune_500': 500,
            'fortune_100': 100,
        })
        self.assertEqual(self.summary['profile_assertions_created'], 0)
        self.assertEqual(self.summary['observation_review_counts'], {
            'analyst_reviewed': 1,
            'machine_triage': 999,
        })
        self.assertEqual(self.summary['observations_with_first_party_evidence'], 1)

    def test_generated_boundary_observations_are_non_assertive(self):
        rows = [
            {
                'rank': 1,
                'company': 'Example One',
                'industry': 'Internet Services and Retailing',
                'city': 'Seattle',
                'state': 'Washington',
            },
            {
                'rank': 100,
                'company': 'Example One Hundred',
                'industry': 'Insurance: Life, Health (Mutual)',
                'city': 'Springfield',
                'state': 'Massachusetts',
            },
            {
                'rank': 500,
                'company': 'Example Five Hundred',
                'industry': 'Building Materials, Glass',
                'city': 'Scottsdale',
                'state': 'Arizona',
            },
            {
                'rank': 501,
                'company': 'Example Five Hundred One',
                'industry': 'Trucking, Truck Leasing',
                'city': 'Phoenix',
                'state': 'Arizona',
            },
            {
                'rank': 1000,
                'company': 'Example One Thousand',
                'industry': 'Building Materials, Glass',
                'city': 'Nashville',
                'state': 'Tennessee',
            },
        ]
        observations = [
            build_observation(row, self.manifest, 'a' * 64, self.activity_map)
            for row in rows
        ]
        validate_observations(observations)

        memberships = {record['corpus']['position']: record['corpus']['memberships'] for record in observations}
        self.assertEqual(memberships[1], ['fortune_1000', 'fortune_500', 'fortune_100'])
        self.assertEqual(memberships[100], ['fortune_1000', 'fortune_500', 'fortune_100'])
        self.assertEqual(memberships[500], ['fortune_1000', 'fortune_500'])
        self.assertEqual(memberships[501], ['fortune_1000'])
        self.assertEqual(memberships[1000], ['fortune_1000'])
        for observation in observations:
            self.assertTrue(observation['not_for_profile_import'])
            self.assertEqual(observation['review_status'], 'machine_triage')
            self.assertEqual(observation['gap_disposition'], 'insufficient_evidence')
            self.assertTrue(all(
                mapping['mapping_status'] == 'candidate'
                and mapping['confidence'] == 'low'
                for mapping in observation['candidate_mappings']
            ))

    def test_catch_all_mapping_is_bound_to_reviewed_organization(self):
        row = {
            'rank': 749,
            'company': 'Different Organization',
            'industry': 'Miscellaneous',
            'city': 'Example City',
            'state': 'Example State',
        }
        with self.assertRaisesRegex(ValueError, 'restricted to'):
            build_observation(row, self.manifest, 'a' * 64, self.activity_map)

    def test_reviewed_catch_all_uses_first_party_evidence(self):
        row = {
            'rank': 749,
            'company': 'Service Corp. International',
            'industry': 'Miscellaneous',
            'city': 'Houston',
            'state': 'Texas',
        }
        observation = build_observation(row, self.manifest, 'a' * 64, self.activity_map)
        validate_observations([observation])
        self.assertEqual(observation['activity_observation']['method'], 'explicit_statement')
        self.assertEqual(observation['review_status'], 'analyst_reviewed')
        self.assertEqual(observation['gap_disposition'], 'none')
        self.assertEqual(len(observation['evidence']), 2)
        self.assertTrue(all(
            mapping['mapping_status'] == 'exact'
            and mapping['confidence'] == 'high'
            and mapping['entity_relationship'] == 'direct'
            for mapping in observation['candidate_mappings']
        ))


if __name__ == '__main__':
    unittest.main()
