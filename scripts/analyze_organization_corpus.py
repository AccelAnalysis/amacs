#!/usr/bin/env python3
"""Generate research-only AMACS observations from an external organization corpus."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.request
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from amacs_io import ROOT, load_dataset


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_source(manifest: dict[str, Any], source_file: Path | None) -> tuple[bytes, str]:
    source = manifest["machine_readable_roster"]
    if source_file is not None:
        return source_file.read_bytes(), str(source_file)

    request = urllib.request.Request(
        source["data_url"],
        headers={"User-Agent": "AMACS taxonomy coverage research/0.3"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read(), source["data_url"]


def select_data(document: Any, data_path: str) -> Any:
    value = document
    for key in data_path.split("."):
        if key:
            value = value[key]
    return value


def validate_roster(rows: list[dict[str, Any]], manifest: dict[str, Any]) -> None:
    expected_count = manifest["expected_organization_count"]
    if len(rows) != expected_count:
        raise ValueError(f"expected {expected_count} organizations, found {len(rows)}")

    positions = [row["rank"] for row in rows]
    if len(set(positions)) != len(positions):
        raise ValueError("roster contains duplicate positions")
    expected_positions = set(range(
        manifest["expected_position_min"],
        manifest["expected_position_max"] + 1,
    ))
    if set(positions) != expected_positions:
        missing = sorted(expected_positions - set(positions))
        extra = sorted(set(positions) - expected_positions)
        raise ValueError(f"roster position mismatch; missing={missing}, extra={extra}")

    required_fields = {"rank", "company", "industry", "city", "state"}
    for row in rows:
        missing_fields = required_fields - set(row)
        if missing_fields:
            raise ValueError(f"rank {row.get('rank')} is missing fields {sorted(missing_fields)}")


def load_activity_map(path: Path, capability_ids: set[str]) -> dict[str, dict[str, Any]]:
    document = read_json(path)
    entries: dict[str, dict[str, Any]] = {}
    for entry in document["entries"]:
        label = entry["source_label"]
        if label in entries:
            raise ValueError(f"duplicate activity-map label: {label}")
        if entry["baseline_status"] not in {"direct", "partial", "gap"}:
            raise ValueError(f"invalid baseline status for {label}")
        missing_ids = set(entry["candidate_concept_ids"]) - capability_ids
        if missing_ids:
            raise ValueError(f"{label} references missing capabilities {sorted(missing_ids)}")
        entries[label] = entry
    return entries


def cohort_memberships(position: int) -> list[str]:
    memberships = ["fortune_1000"]
    if position <= 500:
        memberships.append("fortune_500")
    if position <= 100:
        memberships.append("fortune_100")
    return memberships


def build_observation(
    row: dict[str, Any],
    manifest: dict[str, Any],
    source_sha256: str,
    activity_map: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    position = int(row["rank"])
    activity = activity_map[row["industry"]]
    allowed_organizations = activity.get("organization_names")
    if allowed_organizations is not None and row["company"] not in allowed_organizations:
        raise ValueError(
            f"activity mapping for {row['industry']} is restricted to {allowed_organizations}; "
            f"found {row['company']} at position {position}"
        )
    default_rationale = (
        "The external primary-activity label identifies this AMACS concept as a taxonomy-coverage "
        "candidate only; first-party evidence and entity-scope review are required before any "
        "organization capability assertion."
    )
    evidence = [{
        "source_type": "ranking_profile",
        "title": "Full List of Fortune 1000 Companies (2026)",
        "url": manifest["machine_readable_roster"]["page_url"],
        "publisher": manifest["machine_readable_roster"]["publisher"],
        "accessed_at": manifest["machine_readable_roster"]["retrieved_at"],
        "evidence_locator": f"Position {position}; primary activity field",
        "content_sha256": source_sha256,
    }]
    evidence.extend(activity.get("supplemental_evidence", []))
    activity_observation = activity.get("activity_observation", {
        "source_label": row["industry"],
        "method": "industry_proxy",
    })
    return {
        "observation_id": f"fortune-1000-2026-rank-{position:04d}",
        "organization": {
            "name": row["company"],
            "entity_scope": "reporting_entity",
            "headquarters": {
                "city": row["city"],
                "region": row["state"],
                "country": "US",
            },
        },
        "corpus": {
            "corpus_id": manifest["corpus_id"],
            "edition": manifest["edition"],
            "memberships": cohort_memberships(position),
            "position": position,
        },
        "observed_at": manifest["machine_readable_roster"]["retrieved_at"],
        "activity_observation": activity_observation,
        "evidence": evidence,
        "candidate_mappings": [
            {
                "concept_id": concept_id,
                "mapping_status": activity.get("mapping_status", "candidate"),
                "confidence": activity.get("confidence", "low"),
                "entity_relationship": activity.get("entity_relationship", "unknown"),
                "rationale": activity.get("rationale", default_rationale),
            }
            for concept_id in activity["candidate_concept_ids"]
        ],
        "gap_disposition": activity.get("gap_disposition", "insufficient_evidence"),
        "review_status": activity.get("review_status", "machine_triage"),
        "not_for_profile_import": True,
    }


def validate_observations(observations: list[dict[str, Any]]) -> None:
    schema = read_json(ROOT / "schemas" / "organization-taxonomy-observation.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for observation in observations:
        for error in validator.iter_errors(observation):
            location = ".".join(str(part) for part in error.path) or "<record>"
            errors.append(f"{observation['observation_id']} {location}: {error.message}")
    if errors:
        raise ValueError("generated observations failed schema validation:\n  " + "\n  ".join(errors))


def build_summary(
    rows: list[dict[str, Any]],
    observations: list[dict[str, Any]],
    activity_map: dict[str, dict[str, Any]],
    manifest: dict[str, Any],
    source_sha256: str,
) -> dict[str, Any]:
    organization_baseline = Counter(activity_map[row["industry"]]["baseline_status"] for row in rows)
    label_baseline = Counter(entry["baseline_status"] for entry in activity_map.values())
    used_concepts = sorted({
        mapping["concept_id"]
        for observation in observations
        for mapping in observation["candidate_mappings"]
    })
    review_counts = Counter(observation["review_status"] for observation in observations)
    mapping_status_counts = Counter(
        mapping["mapping_status"]
        for observation in observations
        for mapping in observation["candidate_mappings"]
    )
    first_party_count = sum(
        any(evidence["source_type"] in {"company_website", "regulatory_filing", "annual_report"}
            for evidence in observation["evidence"])
        for observation in observations
    )
    return {
        "corpus_id": manifest["corpus_id"],
        "edition": manifest["edition"],
        "source_sha256": source_sha256,
        "organization_count": len(rows),
        "cohort_counts": {
            "fortune_1000": len(rows),
            "fortune_500": sum(row["rank"] <= 500 for row in rows),
            "fortune_100": sum(row["rank"] <= 100 for row in rows),
        },
        "primary_activity_label_count": len({row["industry"] for row in rows}),
        "baseline_release": manifest["baseline_amacs_release"],
        "baseline_organization_coverage": dict(sorted(organization_baseline.items())),
        "baseline_label_coverage": dict(sorted(label_baseline.items())),
        "candidate_release": manifest["candidate_amacs_release"],
        "organizations_with_candidate_concept_coverage": len(observations),
        "observation_review_counts": dict(sorted(review_counts.items())),
        "mapping_status_counts": dict(sorted(mapping_status_counts.items())),
        "observations_with_first_party_evidence": first_party_count,
        "candidate_concept_ids_used": used_concepts,
        "profile_assertions_created": 0,
        "generated_observation_semantics": "taxonomy_research_only",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate non-assertive AMACS taxonomy observations for an organization corpus.",
    )
    parser.add_argument(
        "--manifest",
        default="research/fortune-1000-2026/manifest.json",
        help="Corpus manifest path relative to the repository root.",
    )
    parser.add_argument("--source-file", help="Optional local roster JSON used instead of retrieval.")
    parser.add_argument("--output", required=True, help="Output directory for observations and summary.")
    parser.add_argument(
        "--allow-source-drift",
        action="store_true",
        help="Allow the external source hash to differ from the reviewed manifest snapshot.",
    )
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    manifest = read_json(manifest_path)

    source_file = Path(args.source_file) if args.source_file else None
    raw, source_description = read_source(manifest, source_file)
    source_sha256 = hashlib.sha256(raw).hexdigest()
    expected_sha256 = manifest["machine_readable_roster"]["expected_sha256"]
    if source_sha256 != expected_sha256 and not args.allow_source_drift:
        raise ValueError(
            f"source drift detected for {source_description}: expected {expected_sha256}, "
            f"found {source_sha256}; review the roster before using --allow-source-drift"
        )

    document = json.loads(raw)
    rows = select_data(document, manifest["machine_readable_roster"]["data_path"])
    validate_roster(rows, manifest)

    concepts = load_dataset("concepts", ROOT)
    capability_ids = {
        concept["concept_id"]
        for concept in concepts
        if concept["concept_type"] == "capability"
    }
    activity_map_path = ROOT / manifest["activity_map"]
    activity_map = load_activity_map(activity_map_path, capability_ids)
    roster_labels = {row["industry"] for row in rows}
    unmapped_labels = sorted(roster_labels - set(activity_map))
    unused_labels = sorted(set(activity_map) - roster_labels)
    if unmapped_labels or unused_labels:
        raise ValueError(
            f"activity-map mismatch; unmapped roster labels={unmapped_labels}, "
            f"unused map labels={unused_labels}"
        )

    observations = [
        build_observation(row, manifest, source_sha256, activity_map)
        for row in sorted(rows, key=lambda item: item["rank"])
    ]
    validate_observations(observations)
    summary = build_summary(rows, observations, activity_map, manifest, source_sha256)

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    observations_path = output / "organization-observations.jsonl"
    observations_path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in observations),
        encoding="utf-8",
    )
    summary_path = output / "coverage-summary.json"
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(observations_path)
    print(summary_path)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"organization corpus analysis failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
