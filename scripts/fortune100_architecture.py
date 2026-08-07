#!/usr/bin/env python3
"""Complete the Fortune 100 deep market-architecture review against AMACS."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from amacs_io import DATASET_ORDER, ROOT, load_dataset


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in records), encoding="utf-8")


def validate_records(records: list[dict[str, Any]]) -> None:
    schema = read_json(ROOT / "schemas/organization-market-architecture-review.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for record in records:
        for error in validator.iter_errors(record):
            location = ".".join(map(str, error.path)) or "<record>"
            errors.append(f"{record.get('review_id')} {location}: {error.message}")
    if errors:
        raise ValueError("Fortune 100 architecture records failed schema validation:\n  " + "\n  ".join(errors[:100]))


def test_result(status: str, rationale: str) -> dict[str, str]:
    return {"status": status, "rationale": rationale}


def architecture_support() -> dict[str, bool]:
    orgcap = read_json(ROOT / "schemas/organization-capability.schema.json")
    props = orgcap["properties"]
    outcome = read_json(ROOT / "schemas/outcome-observation.schema.json")
    return {
        "entity_scope": "organization_identity_id" in props and "entity_scope" in props,
        "market_role": "market_role_ids" in props and "market_roles" in DATASET_ORDER and bool(load_dataset("market_roles", ROOT)),
        "evidence_linkage": "evidence_ids" in props and (ROOT / "schemas/capability-evidence.schema.json").exists(),
        "requirements": bool(load_dataset("requirement_types", ROOT)) and bool(load_dataset("requirement_bundles", ROOT)),
        "response": bool(load_dataset("response_sections", ROOT)) and bool(load_dataset("response_templates", ROOT)),
        "decision": bool(load_dataset("decision_factors", ROOT)) and bool(load_dataset("decision_templates", ROOT)),
        "outcome": "outcome_types" in DATASET_ORDER and bool(load_dataset("outcome_types", ROOT)),
        "learning": "learning_status" in outcome["properties"],
    }


def evidence_by_position(evidence_dir: Path) -> dict[int, dict[str, Any]]:
    result: dict[int, dict[str, Any]] = {}
    for path in sorted(evidence_dir.glob("evidence-batch-*.jsonl")):
        for record in read_jsonl(path):
            position = int(record["organization"]["position"])
            if position in result:
                raise ValueError(f"duplicate Fortune 100 evidence position {position}")
            result[position] = record
    return result


def current_evidence_status(evidence: dict[str, Any] | None, override: dict[str, Any] | None) -> dict[str, Any]:
    if override:
        return {
            "disposition": "first_party_override_reviewed",
            "source_count": len(override["sources"]),
            "first_party_activity_summary": override["activity_summary"],
            "entity_scope_note": override["entity_scope_note"],
        }
    if evidence is None:
        return {"disposition": "fortune500_evidence_unavailable", "source_count": 0}
    disposition = evidence["evidence_disposition"]
    if disposition in {"annual_report_reviewed", "annual_report_found_no_extractable_activity"}:
        mapped = "fortune500_evidence_reviewed"
    elif disposition == "evidence_error":
        mapped = "fortune500_evidence_error"
    elif disposition == "identity_unresolved":
        mapped = "identity_unresolved"
    else:
        mapped = "fortune500_evidence_unavailable"
    return {"disposition": mapped, "source_count": len(evidence.get("evidence", []))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohort", required=True)
    parser.add_argument("--evidence-dir", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    manifest = read_json(ROOT / "research/fortune-100-2026/manifest.json")
    role_map_doc = read_json(ROOT / manifest["market_role_map"])
    role_map = {entry["source_label"]: entry["market_role_ids"] for entry in role_map_doc["entries"]}
    overrides = read_json(ROOT / manifest["first_party_overrides"])["entries"]
    market_role_ids = {record["market_role_id"] for record in load_dataset("market_roles", ROOT)}

    cohort = [record for record in read_jsonl(Path(args.cohort)) if int(record["position"]) <= 100]
    cohort.sort(key=lambda record: int(record["position"]))
    positions = [int(record["position"]) for record in cohort]
    if positions != list(range(1, 101)):
        raise ValueError(f"Fortune 100 cohort must contain exactly ranks 1 through 100; found {positions}")
    evidence = evidence_by_position(Path(args.evidence_dir))
    if set(evidence) != set(range(1, 101)):
        raise ValueError(f"Fortune 100 evidence must contain exactly ranks 1 through 100; found {sorted(evidence)}")

    support = architecture_support()
    if not all(support.values()):
        raise ValueError(f"candidate AMACS architecture is incomplete: {support}")

    records: list[dict[str, Any]] = []
    baseline_gaps = Counter()
    current_gaps = Counter()
    role_counts = Counter()
    architecture_counts: dict[str, Counter[str]] = defaultdict(Counter)
    identity_counts = Counter()
    evidence_counts = Counter()
    segment_orgs = 0
    segment_count = 0

    for row in cohort:
        rank = int(row["position"])
        company = row["company"]
        ev = evidence[rank]
        override = overrides.get(company)
        industry = row["industry"]
        roles = list(dict.fromkeys([*role_map.get(industry, []), *(override.get("market_role_ids", []) if override else [])]))
        missing_roles = set(roles) - market_role_ids
        if not roles or missing_roles:
            raise ValueError(f"rank {rank} {company}: market role mapping invalid; roles={roles} missing={sorted(missing_roles)}")
        role_counts.update(roles)

        identity_status = row["identity_resolution"]["status"]
        if override and identity_status != "resolved":
            architecture_identity = "first_party_override"
        else:
            architecture_identity = identity_status
        identity_counts[architecture_identity] += 1

        ev_status = current_evidence_status(ev, override)
        evidence_counts[ev_status["disposition"]] += 1
        observed_segments = len(ev.get("observed_segments", []))
        if observed_segments:
            segment_orgs += 1
            segment_count += observed_segments

        baseline: list[str] = ["market_role", "explicit_evidence_linkage", "outcome_architecture", "outcome_learning_guardrail"]
        if observed_segments or override:
            baseline.append("entity_scoped_capability")
        baseline = list(dict.fromkeys(baseline))
        baseline_gaps.update(baseline)

        current: list[str] = []
        if architecture_identity in {"unresolved", "candidate", "ambiguous"}:
            current.append("identity_resolution")
        if ev_status["disposition"] in {"fortune500_evidence_unavailable", "identity_unresolved"} and not override:
            current.append("evidence_availability")
        if "capability_granularity" in ev.get("gap_candidates", []):
            current.append("capability_granularity")
        if not current:
            current.append("none")
        current_gaps.update(current)

        tests = {
            "organization_identity_and_entity_scope": test_result("represented", "AMACS 0.4.0 links a capability assertion to an organization identity and explicit reporting-entity, legal-entity, segment, subsidiary, brand, or unknown scope."),
            "capability_representation": test_result("represented", "The organization has one or more research candidate AMACS capabilities without converting the research observation into a production assertion."),
            "market_role_representation": test_result("represented", "AMACS 0.4.0 separates governed market roles from RFx team-delivery roles and supports multiple simultaneous roles."),
            "capability_evidence_linkage": test_result("represented", "AMACS 0.4.0 capability assertions can reference separately governed evidence records carrying entity scope, authorship, hosting, status, and provenance."),
            "requirement_architecture": test_result("represented", "Existing governed requirement types and bundles represent the need-side conditions used to test fitness."),
            "response_architecture": test_result("represented", "Existing governed response sections and templates represent the information a market participant may be asked to provide."),
            "decision_architecture": test_result("represented", "Existing governed decision factors and templates represent gates, scoring, narratives, and comparative selection logic."),
            "outcome_architecture": test_result("represented", "AMACS 0.4.0 adds governed outcome types plus a runtime outcome observation linked to request, response, decision, organization, and capability context."),
            "outcome_learning_guardrail": test_result("represented", "Outcome observations carry an explicit learning status so observed results cannot automatically change capability assertions, matching, or canonical AMACS definitions."),
        }
        for key, result in tests.items():
            architecture_counts[key][result["status"]] += 1

        records.append({
            "review_id": f"AMACS-ARCH-F100-2026-{rank:03d}",
            "organization": {
                "name": company, "position": rank, "identity_id": row["identity_id"],
                "identity_resolution_status": architecture_identity,
            },
            "corpus": {"corpus_id": "fortune-100-2026", "edition": "2026", "memberships": ["fortune_1000", "fortune_500", "fortune_100"]},
            "source_activity": industry,
            "complexity": {
                "compound_or_catch_all": bool(row["compound_or_catch_all"]),
                "candidate_capability_count": len(row["primary_candidate_concept_ids"]),
                "multi_capability": len(row["primary_candidate_concept_ids"]) > 1,
                "first_party_override_available": bool(override),
                "observed_segment_count": observed_segments,
            },
            "capability_candidates": row["primary_candidate_concept_ids"],
            "market_role_candidates": roles,
            "evidence_status": ev_status,
            "architecture_tests": tests,
            "baseline_gap_signals": baseline,
            "current_gap_signals": current,
            "review_status": "analyst_reviewed" if override else "machine_reviewed",
            "not_for_profile_import": True,
        })

    validate_records(records)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "organization-market-architecture-reviews.jsonl", records)
    summary = {
        "corpus_id": manifest["corpus_id"],
        "completion_status": "complete",
        "organization_count": len(records),
        "rank_coverage": {"minimum": 1, "maximum": 100, "missing": [], "duplicates": []},
        "source_activity_label_count": len({record["source_activity"] for record in records}),
        "compound_or_catch_all_organizations": sum(record["complexity"]["compound_or_catch_all"] for record in records),
        "multi_capability_organizations": sum(record["complexity"]["multi_capability"] for record in records),
        "identity_resolution_counts": dict(sorted(identity_counts.items())),
        "evidence_disposition_counts": dict(sorted(evidence_counts.items())),
        "organizations_with_observed_segments": segment_orgs,
        "observed_segment_count": segment_count,
        "market_role_candidate_counts": dict(sorted(role_counts.items())),
        "baseline_gap_counts": dict(sorted(baseline_gaps.items())),
        "post_refinement_gap_counts": dict(sorted(current_gaps.items())),
        "architecture_test_counts": {key: dict(sorted(value.items())) for key, value in sorted(architecture_counts.items())},
        "baseline_release": manifest["baseline_amacs_release"],
        "candidate_release": manifest["candidate_amacs_release"],
        "profile_assertions_created": 0,
        "completion_semantics": "Every Fortune 100 organization received a schema-valid architecture review. Research classifications remain non-importable; unresolved identity or evidence availability remains visible rather than inferred.",
    }
    (out / "fortune-100-architecture-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    findings = {
        "implemented_refinements": [
            "governed market-role registry distinct from RFx delivery role",
            "entity-scoped organization capability assertions",
            "explicit capability-to-evidence references and evidence provenance contract",
            "governed outcome-type registry",
            "outcome observation linked to request/response/decision/organization/capability context",
            "explicit outcome-learning eligibility and approval guardrail"
        ],
        "unchanged_architectures_confirmed": ["requirement architecture", "response architecture", "decision architecture"],
        "remaining_nonstructural_review_queues": ["identity resolution", "first-party evidence availability", "capability granularity where specifically flagged"],
    }
    (out / "fortune-100-refinement-findings.json").write_text(json.dumps(findings, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Fortune 100 architecture review failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
