#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from amacs_io import DATASET_ORDER, all_datasets

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_FILES = {
    'concepts': 'concept.schema.json',
    'relationships': 'relationship.schema.json',
    'aliases': 'alias.schema.json',
    'properties': 'property.schema.json',
    'property_values': 'property-value.schema.json',
    'concept_properties': 'concept-property.schema.json',
    'credentials': 'credential.schema.json',
    'units': 'unit.schema.json',
    'requirement_types': 'requirement-type.schema.json',
    'requirement_bundles': 'requirement-bundle.schema.json',
    'governance_profiles': 'governance-profile.schema.json',
    'readiness_rules': 'readiness-rule.schema.json',
    'request_families': 'request-family.schema.json',
    'response_sections': 'response-section.schema.json',
    'response_templates': 'response-template.schema.json',
    'decision_factors': 'decision-factor.schema.json',
    'decision_templates': 'decision-template.schema.json',
    'market_roles': 'market-role.schema.json',
    'outcome_types': 'outcome-type.schema.json',
}

ID_FIELDS = {
    'concepts': 'concept_id', 'relationships': 'relationship_id', 'aliases': 'alias_id',
    'properties': 'property_id', 'property_values': 'property_value_id',
    'concept_properties': 'concept_property_id', 'credentials': 'credential_id',
    'units': 'unit_id', 'requirement_types': 'requirement_type_id',
    'requirement_bundles': 'requirement_bundle_id', 'governance_profiles': 'governance_profile_id',
    'readiness_rules': 'readiness_rule_id', 'request_families': 'request_family_id',
    'response_sections': 'response_section_id', 'response_templates': 'response_template_id',
    'decision_factors': 'decision_factor_id', 'decision_templates': 'decision_template_id',
    'market_roles': 'market_role_id', 'outcome_types': 'outcome_type_id',
}


def load_schema(filename: str) -> dict[str, Any]:
    return json.loads((ROOT / 'schemas' / filename).read_text(encoding='utf-8'))


def validate_record_set(name: str, records: list[dict[str, Any]], errors: list[str]) -> None:
    validator = Draft202012Validator(load_schema(SCHEMA_FILES[name]), format_checker=FormatChecker())
    for index, record in enumerate(records, start=1):
        for error in sorted(validator.iter_errors(record), key=lambda item: list(item.path)):
            location = '.'.join(str(part) for part in error.path) or '<record>'
            errors.append(f'{name} record {index} {location}: {error.message}')


def validate_seed_sources(errors: list[str]) -> None:
    domain_validator = Draft202012Validator(load_schema('domain-seed.schema.json'), format_checker=FormatChecker())
    domain_paths = sorted((ROOT / 'source' / 'domain-seeds').glob('*.json'))
    if not domain_paths:
        errors.append('no AMACS domain seed files found')
    for path in domain_paths:
        instance = json.loads(path.read_text(encoding='utf-8'))
        for error in sorted(domain_validator.iter_errors(instance), key=lambda item: list(item.path)):
            location = '.'.join(str(part) for part in error.path) or '<seed>'
            errors.append(f'{path.relative_to(ROOT)} {location}: {error.message}')

    extension_validator = Draft202012Validator(
        load_schema('domain-extension.schema.json'),
        format_checker=FormatChecker(),
    )
    base_domain_ids = {
        json.loads(path.read_text(encoding='utf-8'))['domain_id']
        for path in domain_paths
    }
    for path in sorted((ROOT / 'source' / 'domain-extensions').glob('**/*.json')):
        instance = json.loads(path.read_text(encoding='utf-8'))
        for error in sorted(extension_validator.iter_errors(instance), key=lambda item: list(item.path)):
            location = '.'.join(str(part) for part in error.path) or '<extension>'
            errors.append(f'{path.relative_to(ROOT)} {location}: {error.message}')
        if instance.get('domain_id') not in base_domain_ids:
            errors.append(
                f"{path.relative_to(ROOT)} references unknown base domain {instance.get('domain_id')}"
            )

    alias_path = ROOT / 'source' / 'alias-seed.json'
    if not alias_path.exists():
        errors.append('source/alias-seed.json is missing')
    else:
        alias_validator = Draft202012Validator(load_schema('alias-seed.schema.json'), format_checker=FormatChecker())
        instance = json.loads(alias_path.read_text(encoding='utf-8'))
        for error in sorted(alias_validator.iter_errors(instance), key=lambda item: list(item.path)):
            location = '.'.join(str(part) for part in error.path) or '<seed>'
            errors.append(f'source/alias-seed.json {location}: {error.message}')


def check_unique_ids(data: dict[str, list[dict[str, Any]]], errors: list[str]) -> None:
    all_ids: list[str] = []
    for name in DATASET_ORDER:
        field = ID_FIELDS[name]
        ids = [record[field] for record in data[name]]
        duplicates = [value for value, count in Counter(ids).items() if count > 1]
        if duplicates:
            errors.append(f'{name}: duplicate IDs: {duplicates}')
        all_ids.extend(ids)
    duplicates = [value for value, count in Counter(all_ids).items() if count > 1]
    if duplicates:
        errors.append(f'global duplicate IDs: {duplicates}')


def check_references(data: dict[str, list[dict[str, Any]]], errors: list[str]) -> None:
    concepts = {record['concept_id']: record for record in data['concepts']}
    properties = {record['property_id'] for record in data['properties']}
    credentials = {record['credential_id'] for record in data['credentials']}
    units = {record['unit_id'] for record in data['units']}
    requirement_types = {record['requirement_type_id']: record for record in data['requirement_types']}
    requirement_bundles = {record['requirement_bundle_id'] for record in data['requirement_bundles']}
    governance_profiles = {record['governance_profile_id'] for record in data['governance_profiles']}
    request_families = {record['request_family_id'] for record in data['request_families']}
    response_sections = {record['response_section_id'] for record in data['response_sections']}
    response_templates = {record['response_template_id'] for record in data['response_templates']}
    decision_factors = {record['decision_factor_id'] for record in data['decision_factors']}
    decision_templates = {record['decision_template_id'] for record in data['decision_templates']}

    for record in data['concepts']:
        parent = record['primary_parent_id']
        if parent is not None and parent not in concepts:
            errors.append(f"{record['concept_id']}: missing parent {parent}")
        if parent == record['concept_id']:
            errors.append(f"{record['concept_id']}: self-parent is forbidden")
        if record['concept_type'] == 'domain' and parent is not None:
            errors.append(f"{record['concept_id']}: domain must not have a parent")
        if record['concept_type'] != 'domain' and parent is None:
            errors.append(f"{record['concept_id']}: non-domain requires a parent")
        if record['matchable'] != (record['concept_type'] == 'capability'):
            errors.append(f"{record['concept_id']}: matchable must be true only for capabilities")

    for record in data['relationships']:
        if record['source_concept_id'] not in concepts:
            errors.append(f"{record['relationship_id']}: missing source concept")
        if record['target_concept_id'] not in concepts:
            errors.append(f"{record['relationship_id']}: missing target concept")
        if record['source_concept_id'] == record['target_concept_id']:
            errors.append(f"{record['relationship_id']}: self-relationship is forbidden")

    for record in data['aliases']:
        if record['concept_id'] not in concepts:
            errors.append(f"{record['alias_id']}: missing concept {record['concept_id']}")

    for record in data['property_values']:
        if record['property_id'] not in properties:
            errors.append(f"{record['property_value_id']}: missing property {record['property_id']}")

    for record in data['properties']:
        missing = sorted(set(record['allowed_unit_ids']) - units)
        if missing:
            errors.append(f"{record['property_id']}: missing allowed units {missing}")

    for record in data['units']:
        base = record['base_unit_id']
        factor = record['conversion_factor_to_base']
        if base is not None and base not in units:
            errors.append(f"{record['unit_id']}: missing base unit {base}")
        if base == record['unit_id']:
            errors.append(f"{record['unit_id']}: unit cannot be its own base")
        if (base is None) != (factor is None):
            errors.append(f"{record['unit_id']}: base unit and conversion factor must be supplied together")

    for record in data['concept_properties']:
        if record['concept_id'] not in concepts:
            errors.append(f"{record['concept_property_id']}: missing concept")
        if record['property_id'] not in properties:
            errors.append(f"{record['concept_property_id']}: missing property")

    for record in data['response_templates']:
        missing = sorted(set(record['section_ids']) - response_sections)
        if missing:
            errors.append(f"{record['response_template_id']}: missing sections {missing}")

    for record in data['decision_templates']:
        missing = sorted(set(record['factor_ids']) - decision_factors)
        if missing:
            errors.append(f"{record['decision_template_id']}: missing factors {missing}")

    for record in data['requirement_bundles']:
        bundle_id = record['requirement_bundle_id']
        missing_requests = sorted(set(record['applicable_request_family_ids']) - request_families)
        if missing_requests:
            errors.append(f'{bundle_id}: missing request families {missing_requests}')
        item_keys = [item['item_key'] for item in record['items']]
        duplicates = [value for value, count in Counter(item_keys).items() if count > 1]
        if duplicates:
            errors.append(f'{bundle_id}: duplicate item keys {duplicates}')
        for item in record['items']:
            item_ref = f"{bundle_id}/{item['item_key']}"
            requirement_type = requirement_types.get(item['requirement_type_id'])
            if requirement_type is None:
                errors.append(f'{item_ref}: missing requirement type')
            else:
                if item['decision_treatment'] not in requirement_type['allowed_decision_treatments']:
                    errors.append(
                        f"{item_ref}: decision treatment {item['decision_treatment']} is not allowed "
                        f"for requirement type {requirement_type['requirement_type_id']}"
                    )
                if item['default_team_coverage_allowed'] and not requirement_type['team_coverage_allowed']:
                    errors.append(
                        f"{item_ref}: team coverage is not allowed for requirement type "
                        f"{requirement_type['requirement_type_id']}"
                    )
            if item['property_id'] is not None and item['property_id'] not in properties:
                errors.append(f'{item_ref}: missing property')
            if item['credential_id'] is not None and item['credential_id'] not in credentials:
                errors.append(f'{item_ref}: missing credential')
            if item['requirement_level'] == 'informational' and item['decision_treatment'] != 'informational_only':
                errors.append(f'{item_ref}: informational item must be informational only')
            if item['decision_treatment'] == 'gate_only' and item['requirement_level'] != 'required':
                errors.append(f'{item_ref}: gate-only item must be required')
            missing_sections = sorted(set(item['linked_response_section_ids']) - response_sections)
            if missing_sections:
                errors.append(f'{item_ref}: missing response sections {missing_sections}')
            missing_factors = sorted(set(item['linked_decision_factor_ids']) - decision_factors)
            if missing_factors:
                errors.append(f'{item_ref}: missing decision factors {missing_factors}')

    for record in data['request_families']:
        request_id = record['request_family_id']
        if record['default_response_template_id'] not in response_templates:
            errors.append(f'{request_id}: missing response template')
        if record['default_decision_template_id'] not in decision_templates:
            errors.append(f'{request_id}: missing decision template')
        if record['default_governance_profile_id'] not in governance_profiles:
            errors.append(f'{request_id}: missing default governance profile')
        missing_governance = sorted(set(record['allowed_governance_profile_ids']) - governance_profiles)
        if missing_governance:
            errors.append(f'{request_id}: missing governance profiles {missing_governance}')
        if record['default_governance_profile_id'] not in record['allowed_governance_profile_ids']:
            errors.append(f'{request_id}: default governance profile is not allowed')
        missing_bundles = sorted(set(record['recommended_requirement_bundle_ids']) - requirement_bundles)
        if missing_bundles:
            errors.append(f'{request_id}: missing requirement bundles {missing_bundles}')

    for record in data['readiness_rules']:
        rule_id = record['readiness_rule_id']
        missing_requests = sorted(set(record['applies_to_request_family_ids']) - request_families)
        if missing_requests:
            errors.append(f'{rule_id}: missing request families {missing_requests}')
        missing_governance = sorted(set(record['applies_to_governance_profile_ids']) - governance_profiles)
        if missing_governance:
            errors.append(f'{rule_id}: missing governance profiles {missing_governance}')
        if record['severity'] == 'blocking' and not record['blocking']:
            errors.append(f'{rule_id}: blocking severity must block publication')
        if record['blocking'] and record['acknowledgment_allowed']:
            errors.append(f'{rule_id}: blocking rule cannot allow acknowledgment')


def check_cycles(data: dict[str, list[dict[str, Any]]], errors: list[str]) -> None:
    parent_of = {record['concept_id']: record['primary_parent_id'] for record in data['concepts']}
    for concept_id in parent_of:
        seen: set[str] = set()
        current: str | None = concept_id
        while current is not None:
            if current in seen:
                errors.append(f'hierarchy cycle detected from {concept_id} at {current}')
                break
            seen.add(current)
            current = parent_of.get(current)


def check_labels_and_codes(data: dict[str, list[dict[str, Any]]], errors: list[str]) -> None:
    labels = Counter(record['preferred_label'].casefold() for record in data['concepts'] if record['status'] == 'active')
    duplicates = sorted(value for value, count in labels.items() if count > 1)
    if duplicates:
        errors.append(f'duplicate active concept labels: {duplicates}')

    aliases = Counter((record['concept_id'], record['alias'].casefold(), record['language'])
                      for record in data['aliases'] if record['status'] == 'active')
    duplicates = sorted(value for value, count in aliases.items() if count > 1)
    if duplicates:
        errors.append(f'duplicate aliases: {duplicates}')

    for dataset, field in [
        ('request_families', 'code'), ('requirement_types', 'code'),
        ('requirement_bundles', 'code'), ('governance_profiles', 'code'),
        ('readiness_rules', 'code'), ('units', 'code'),
        ('market_roles', 'code'), ('outcome_types', 'code'),
    ]:
        values = Counter(record[field] for record in data[dataset] if record['status'] == 'active')
        duplicates = sorted(value for value, count in values.items() if count > 1)
        if duplicates:
            errors.append(f'{dataset}: duplicate active codes: {duplicates}')


def main() -> int:
    errors: list[str] = []
    validate_seed_sources(errors)
    try:
        data = all_datasets(ROOT)
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f'AMACS source loading failed: {exc}', file=sys.stderr)
        return 1

    for name in DATASET_ORDER:
        validate_record_set(name, data[name], errors)
    check_unique_ids(data, errors)
    check_references(data, errors)
    check_cycles(data, errors)
    check_labels_and_codes(data, errors)

    if errors:
        print('AMACS validation failed:', file=sys.stderr)
        for error in errors:
            print(f'  - {error}', file=sys.stderr)
        return 1

    print('AMACS validation passed.')
    for name in DATASET_ORDER:
        print(f'  {name}: {len(data[name])}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
