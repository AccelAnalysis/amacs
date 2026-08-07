#!/usr/bin/env python3
"""Aggregate Fortune 500 evidence batches and enforce terminal completion."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
TERMINAL = {
    "annual_report_reviewed",
    "annual_report_found_no_extractable_activity",
    "annual_report_unavailable",
    "identity_unresolved",
    "evidence_error",
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in records), encoding="utf-8")


def validate_records(records: list[dict[str, Any]]) -> None:
    schema = read_json(ROOT / "schemas/organization-evidence-review.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for record in records:
        for error in validator.iter_errors(record):
            location = ".".join(map(str, error.path)) or "<record>"
            errors.append(f"{record.get('review_id', '<unknown>')} {location}: {error.message}")
    if errors:
        raise ValueError("evidence review schema failures:\n  " + "\n  ".join(errors[:100]))


def aggregate(records: list[dict[str, Any]], expected_count: int = 500) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validate_records(records)
    positions = [int(r["organization"]["position"]) for r in records]
    counts = Counter(positions)
    duplicate_positions = sorted(p for p, n in counts.items() if n != 1)
    expected = set(range(1, expected_count + 1))
    missing = sorted(expected - set(positions))
    extra = sorted(set(positions) - expected)
    if len(records) != expected_count or missing or extra or duplicate_positions:
        raise ValueError(
            f"Fortune 500 completion requires one review per rank; records={len(records)} "
            f"missing={missing} extra={extra} duplicate={duplicate_positions}"
        )
    nonterminal = sorted({r["evidence_disposition"] for r in records if r["evidence_disposition"] not in TERMINAL})
    if nonterminal:
        raise ValueError(f"nonterminal evidence dispositions found: {nonterminal}")

    disposition_counts = Counter(r["evidence_disposition"] for r in records)
    resolution_counts = Counter(r["identity_resolution_status"] for r in records)
    gap_counts: Counter[str] = Counter()
    for r in records:
        gap_counts.update(r["gap_candidates"])
    reports = [r for r in records if r["evidence"]]
    with_activities = [r for r in records if r["observed_activity_statements"]]
    with_segments = [r for r in records if r["observed_segments"]]
    with_mappings = [r for r in records if r["candidate_mappings"]]
    all_segments = sum(len(r["observed_segments"]) for r in records)
    all_activities = sum(len(r["observed_activity_statements"]) for r in records)
    all_mappings = sum(len(r["candidate_mappings"]) for r in records)

    batches: list[dict[str, Any]] = []
    for start in range(1, expected_count + 1, 50):
        cohort = [r for r in records if start <= r["organization"]["position"] <= start + 49]
        batches.append({
            "rank_start": start,
            "rank_end": min(start + 49, expected_count),
            "organization_count": len(cohort),
            "annual_reports_reviewed": sum(bool(r["evidence"]) for r in cohort),
            "organizations_with_activity_statements": sum(bool(r["observed_activity_statements"]) for r in cohort),
            "organizations_with_segments": sum(bool(r["observed_segments"]) for r in cohort),
            "organizations_with_candidate_mappings": sum(bool(r["candidate_mappings"]) for r in cohort),
            "terminal_dispositions": dict(sorted(Counter(r["evidence_disposition"] for r in cohort).items())),
        })

    refinements: list[dict[str, Any]] = [
        {
            "refinement_key": "external_classification_crosswalk",
            "status": "implemented",
            "finding": "External industry and regulatory categories require governed crosswalks rather than AMACS aliases.",
            "affected_organizations": expected_count,
        },
        {
            "refinement_key": "organization_identity",
            "status": "implemented",
            "finding": "Organization identity must distinguish display, regulatory, legal, former, trade, brand, subsidiary, and segment identities independently from capability assertions.",
            "affected_organizations": expected_count,
        },
        {
            "refinement_key": "evidence_author_host_separation",
            "status": "implemented",
            "finding": "Mirrored first-party documents require separate authoring-organization and document-host provenance so evidence authority is not confused with hosting location.",
            "affected_organizations": len(reports),
        },
        {
            "refinement_key": "operating_segment_representation",
            "status": "implemented_research_model",
            "finding": "Operating segments require explicit entity relationship representation rather than attribution directly to the parent reporting entity.",
            "affected_organizations": len(with_segments),
            "observed_segment_count": all_segments,
        },
    ]
    if gap_counts["capability_granularity"]:
        refinements.append({
            "refinement_key": "capability_granularity_review",
            "status": "candidate",
            "finding": "First-party activity statements were found without a sufficiently specific lexical AMACS mapping and require semantic capability review.",
            "affected_organizations": gap_counts["capability_granularity"],
        })
    if gap_counts["crosswalk_conflict"]:
        refinements.append({
            "refinement_key": "crosswalk_conflict_review",
            "status": "candidate",
            "finding": "First-party annual-report mappings diverged from the external primary-activity proxy and require crosswalk or organization-scope review.",
            "affected_organizations": gap_counts["crosswalk_conflict"],
        })
    if gap_counts["evidence_model"]:
        refinements.append({
            "refinement_key": "document_extraction_review",
            "status": "candidate",
            "finding": "Some documents could not be safely attributed or parsed and should remain evidence-model exceptions rather than inferred capabilities.",
            "affected_organizations": gap_counts["evidence_model"],
        })

    summary = {
        "corpus_id": "fortune-500-2026",
        "completion_status": "complete",
        "organization_count": expected_count,
        "rank_coverage": {"minimum": 1, "maximum": expected_count, "missing": [], "duplicates": []},
        "identity_resolution_counts": dict(sorted(resolution_counts.items())),
        "evidence_disposition_counts": dict(sorted(disposition_counts.items())),
        "annual_reports_reviewed": len(reports),
        "organizations_with_activity_statements": len(with_activities),
        "activity_statement_count": all_activities,
        "organizations_with_operating_segments": len(with_segments),
        "operating_segment_count": all_segments,
        "organizations_with_candidate_mappings": len(with_mappings),
        "candidate_mapping_count": all_mappings,
        "gap_candidate_counts": dict(sorted(gap_counts.items())),
        "rank_batches": batches,
        "profile_assertions_created": 0,
        "external_aliases_created": 0,
        "completion_semantics": "Every organization has a terminal governed evidence disposition; evidence unavailable or unresolved is a completed review outcome, not evidence of capability.",
    }
    return summary, refinements


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    input_dir = Path(args.input_dir)
    files = sorted(input_dir.glob("evidence-batch-*.jsonl"))
    if not files:
        raise ValueError(f"no evidence batch files found under {input_dir}")
    records: list[dict[str, Any]] = []
    for path in files:
        records.extend(read_jsonl(path))
    records.sort(key=lambda r: int(r["organization"]["position"]))
    summary, refinements = aggregate(records)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "organization-evidence-reviews.jsonl", records)
    (out / "fortune-500-completion-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    (out / "fortune-500-refinement-candidates.json").write_text(json.dumps(refinements, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Fortune 500 aggregation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
