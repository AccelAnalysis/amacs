"""Shared AMACS source loading and deterministic seed expansion."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]

DATASET_PATHS: dict[str, str] = {
    "relationships": "source/relationships.jsonl",
    "properties": "source/properties.jsonl",
    "property_values": "source/property-values.jsonl",
    "concept_properties": "source/concept-properties/**/*.jsonl",
    "credentials": "source/credentials.jsonl",
    "units": "source/units.jsonl",
    "requirement_types": "source/requirement-types.jsonl",
    "requirement_bundles": "source/requirement-bundles/**/*.jsonl",
    "governance_profiles": "source/governance-profiles.jsonl",
    "readiness_rules": "source/readiness-rules/**/*.jsonl",
    "request_families": "source/request-families.jsonl",
    "response_sections": "source/response-sections.jsonl",
    "response_templates": "source/response-templates.jsonl",
    "decision_factors": "source/decision-factors.jsonl",
    "decision_templates": "source/decision-templates.jsonl",
}

DATASET_ORDER = [
    "concepts", "relationships", "aliases", "properties", "property_values",
    "concept_properties", "credentials", "units", "requirement_types",
    "requirement_bundles", "governance_profiles", "readiness_rules",
    "request_families", "response_sections", "response_templates",
    "decision_factors", "decision_templates",
]

DATASET_FILENAMES = {
    "concepts": "concepts.jsonl",
    "relationships": "relationships.jsonl",
    "aliases": "aliases.jsonl",
    "properties": "properties.jsonl",
    "property_values": "property-values.jsonl",
    "concept_properties": "concept-properties.jsonl",
    "credentials": "credentials.jsonl",
    "units": "units.jsonl",
    "requirement_types": "requirement-types.jsonl",
    "requirement_bundles": "requirement-bundles.jsonl",
    "governance_profiles": "governance-profiles.jsonl",
    "readiness_rules": "readiness-rules.jsonl",
    "request_families": "request-families.jsonl",
    "response_sections": "response-sections.jsonl",
    "response_templates": "response-templates.jsonl",
    "decision_factors": "decision-factors.jsonl",
    "decision_templates": "decision-templates.jsonl",
}


def _clean(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if not key.startswith("__")}


def read_jsonl(paths: Iterable[Path], root: Path = ROOT) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
            record["__source_file"] = str(path.relative_to(root))
            record["__source_line"] = line_number
            records.append(record)
    return records


def expand_domain_seed(seed: dict[str, Any], source_file: str) -> list[dict[str, Any]]:
    version = seed.get("version_introduced", "0.1.0")
    origin = seed.get("source_origin", "original_amacs")
    records: list[dict[str, Any]] = [{
        "concept_id": seed["domain_id"],
        "concept_type": "domain",
        "preferred_label": seed["label"],
        "definition": seed["definition"],
        "status": seed.get("status", "active"),
        "matchable": False,
        "editorial_maturity": seed.get("editorial_maturity", "reviewed"),
        "version_introduced": version,
        "primary_parent_id": None,
        "source_origin": origin,
        "__source_file": source_file,
        "__source_line": 1,
    }]
    for family in seed["families"]:
        family_label = family["label"]
        records.append({
            "concept_id": family["family_id"],
            "concept_type": "family",
            "preferred_label": family_label,
            "definition": family.get("definition") or f"A grouping of market capabilities associated with {family_label.lower()}.",
            "status": family.get("status", "active"),
            "matchable": False,
            "editorial_maturity": family.get("editorial_maturity", "reviewed"),
            "version_introduced": version,
            "primary_parent_id": seed["domain_id"],
            "source_origin": origin,
            "__source_file": source_file,
            "__source_line": 1,
        })
        for raw_capability in family["capabilities"]:
            capability = ({"capability_id": raw_capability[0], "label": raw_capability[1]}
                          if isinstance(raw_capability, list) else raw_capability)
            label = capability["label"]
            records.append({
                "concept_id": capability["capability_id"],
                "concept_type": "capability",
                "preferred_label": label,
                "definition": capability.get("definition") or (
                    f"The organizational ability to provide or perform {label.lower()} in a commercial, "
                    "institutional, public, or community context, as applicable."
                ),
                "status": capability.get("status", "active"),
                "matchable": True,
                "editorial_maturity": capability.get("editorial_maturity", "draft"),
                "version_introduced": version,
                "primary_parent_id": family["family_id"],
                "source_origin": origin,
                "__source_file": source_file,
                "__source_line": 1,
            })
    return records


def expand_domain_extension(extension: dict[str, Any], source_file: str) -> list[dict[str, Any]]:
    """Expand additive families without restating or mutating an existing domain seed."""
    version = extension["version_introduced"]
    origin = extension.get("source_origin", "original_amacs")
    records: list[dict[str, Any]] = []
    for family in extension["families"]:
        family_label = family["label"]
        records.append({
            "concept_id": family["family_id"],
            "concept_type": "family",
            "preferred_label": family_label,
            "definition": family["definition"],
            "status": family.get("status", "active"),
            "matchable": False,
            "editorial_maturity": family.get("editorial_maturity", "draft"),
            "version_introduced": version,
            "primary_parent_id": extension["domain_id"],
            "source_origin": origin,
            "__source_file": source_file,
            "__source_line": 1,
        })
        for capability in family["capabilities"]:
            records.append({
                "concept_id": capability["capability_id"],
                "concept_type": "capability",
                "preferred_label": capability["label"],
                "definition": capability["definition"],
                "status": capability.get("status", "active"),
                "matchable": True,
                "editorial_maturity": capability.get("editorial_maturity", "draft"),
                "version_introduced": version,
                "primary_parent_id": family["family_id"],
                "source_origin": origin,
                "__source_file": source_file,
                "__source_line": 1,
            })
    return records


def load_concepts(root: Path = ROOT) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(root.glob("source/domain-seeds/*.json")):
        seed = json.loads(path.read_text(encoding="utf-8"))
        records.extend(expand_domain_seed(seed, str(path.relative_to(root))))
    for path in sorted(root.glob("source/domain-extensions/**/*.json")):
        extension = json.loads(path.read_text(encoding="utf-8"))
        records.extend(expand_domain_extension(extension, str(path.relative_to(root))))
    return records


def load_aliases(root: Path = ROOT) -> list[dict[str, Any]]:
    path = root / "source/alias-seed.json"
    seed = json.loads(path.read_text(encoding="utf-8"))
    version = seed["version_introduced"]
    records: list[dict[str, Any]] = []
    for concept_id, entries in seed["aliases"]:
        for alias_id, alias, alias_type, language, region in entries:
            records.append({
                "alias_id": alias_id,
                "concept_id": concept_id,
                "alias": alias,
                "alias_type": alias_type,
                "language": language,
                "region": region,
                "status": "active",
                "version_introduced": version,
                "__source_file": "source/alias-seed.json",
                "__source_line": 1,
            })
    return records


def load_dataset(name: str, root: Path = ROOT, with_metadata: bool = False) -> list[dict[str, Any]]:
    if name == "concepts":
        records = load_concepts(root)
    elif name == "aliases":
        records = load_aliases(root)
    else:
        records = read_jsonl(sorted(root.glob(DATASET_PATHS[name])), root)
    return records if with_metadata else [_clean(record) for record in records]


def all_datasets(root: Path = ROOT, with_metadata: bool = False) -> dict[str, list[dict[str, Any]]]:
    return {name: load_dataset(name, root, with_metadata) for name in DATASET_ORDER}


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(_clean(record), ensure_ascii=False, separators=(",", ":")) + "\n")
