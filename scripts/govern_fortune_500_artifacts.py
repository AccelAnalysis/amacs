#!/usr/bin/env python3
"""Convert Fortune 500 analyzer outputs into governed AMACS research artifacts."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
WORD = re.compile(r"[a-z0-9]+")


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, records: Iterable[dict[str, Any]]) -> None:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in records),
        encoding="utf-8",
    )


def normalize_name(value: str) -> str:
    suffixes = {
        "co", "company", "companies", "corp", "corporation", "inc", "incorporated",
        "group", "holdings", "holding", "limited", "ltd", "llc", "lp", "plc", "the",
    }
    tokens = WORD.findall(value.lower().replace("&", " and ").replace(".com", " com "))
    while tokens and tokens[-1] in suffixes:
        tokens.pop()
    return " ".join(tokens)


def nonempty_dict(value: dict[str, Any]) -> dict[str, str]:
    return {str(key): str(item) for key, item in value.items() if item not in (None, "")}


def ranking_evidence(manifest: dict[str, Any], parent: dict[str, Any], summary: dict[str, Any], rank: int) -> dict[str, Any]:
    roster = parent["machine_readable_roster"]
    return {
        "source_type": "external_classification",
        "title": "2026 Fortune 1000 machine-readable roster and primary activity classification",
        "url": roster["page_url"],
        "publisher": roster["publisher"],
        "accessed_at": roster["retrieved_at"],
        "evidence_locator": f"Position {rank}; primary activity field",
        "content_sha256": summary["roster_source_sha256"],
    }


def mirror_evidence(manifest: dict[str, Any], summary: dict[str, Any], names: bool = False) -> dict[str, Any]:
    mirror = manifest["regulatory_metadata_mirror"]
    source = summary["regulatory_metadata_source"]
    return {
        "source_type": "regulatory_metadata_mirror",
        "title": "SEC-derived listed filer name history" if names else "SEC-derived listed filer metadata",
        "url": mirror["listed_names_url"] if names else mirror["listed_metadata_url"],
        "publisher": "Datamule Data",
        "accessed_at": manifest["observed_at"],
        "evidence_locator": f"Pinned mirror commit {mirror['commit']}",
        "content_sha256": source["listed_names_sha256"] if names else source["listed_metadata_sha256"],
    }


def identity_match_basis(ranking_name: str, resolution: dict[str, Any]) -> str:
    status = resolution.get("status", "unresolved")
    if status == "resolved_override":
        return "controlled_override"
    if status == "unresolved":
        return "no_match"
    matched_type = resolution.get("matched_name_type", "")
    if matched_type == "former_or_alternate_sec_name":
        return "former_name"
    matched_name = resolution.get("matched_name", "")
    if matched_name and normalize_name(ranking_name) == normalize_name(matched_name):
        return "exact_name"
    if matched_name and normalize_name(ranking_name).replace(" ", "") == normalize_name(matched_name).replace(" ", ""):
        return "compact_name"
    return "fuzzy_name"


def governed_resolution(raw: dict[str, Any], ranking_name: str) -> dict[str, Any]:
    source_status = raw.get("status", "unresolved")
    status = (
        "resolved" if source_status.startswith("resolved")
        else source_status if source_status in {"candidate", "ambiguous", "unresolved"}
        else "unresolved"
    )
    result: dict[str, Any] = {
        "status": status,
        "match_basis": identity_match_basis(ranking_name, raw),
        "source_status": source_status,
        "score": float(raw.get("score", 0.0)),
        "rationale": raw.get("reason") or "The reporting entity requires analyst resolution.",
    }
    if status == "resolved":
        identifiers = nonempty_dict({"cik": raw.get("cik"), "ticker": raw.get("ticker")})
        result["resolved_identity"] = {
            "preferred_name": raw.get("sec_name") or ranking_name,
            "organization_type": "reporting_entity",
            "external_identifiers": identifiers,
        }
    candidates = []
    for candidate in raw.get("candidates", []):
        candidate_basis = "former_name" if candidate.get("matched_name_type") == "former_or_alternate_sec_name" else "fuzzy_name"
        candidates.append({
            "preferred_name": candidate.get("sec_name") or candidate.get("matched_name") or ranking_name,
            "score": float(candidate.get("score", 0.0)),
            "match_basis": candidate_basis,
            "external_identifiers": nonempty_dict({"cik": candidate.get("cik"), "ticker": candidate.get("ticker")}),
        })
    if candidates:
        result["candidates"] = candidates
    return result


def mapping_relation(primary: dict[str, Any], ranking_mapping_count: int, basis: str) -> str:
    if basis == "regulatory_sic_description":
        return "related_match"
    if primary.get("compound_or_catch_all") or ranking_mapping_count > 1:
        return "broad_match"
    return "close_match"


def governed_mappings(raw: dict[str, Any]) -> list[dict[str, Any]]:
    primary = raw["primary_activity"]
    ranking_count = sum(item.get("basis") == "ranking_primary_activity" for item in raw["candidate_mappings"])
    mappings = []
    for item in raw["candidate_mappings"]:
        original_basis = item.get("basis", "ranking_primary_activity")
        basis = "external_classification" if original_basis == "ranking_primary_activity" else "regulatory_sic_description"
        rationale = item.get("rationale")
        if not rationale:
            rationale = (
                "The SEC-derived SIC description produced a lexical AMACS candidate. Semantic review is required "
                "because SIC wording is not evidence of direct organizational capability and may create false positives."
            )
        status = item.get("mapping_status", "candidate")
        if status not in {"exact", "candidate", "partial", "none"}:
            status = "candidate"
        mappings.append({
            "concept_id": item["concept_id"],
            "mapping_status": status,
            "confidence": item.get("confidence", "low"),
            "entity_relationship": "unknown",
            "mapping_basis": basis,
            "mapping_relation": mapping_relation(primary, ranking_count, original_basis),
            "rationale": rationale,
        })
    return mappings


def gap_disposition(raw: dict[str, Any]) -> str:
    status = raw["entity_resolution"].get("status", "unresolved")
    if status in {"candidate", "ambiguous", "unresolved"}:
        return "organization_identity_candidate"
    primary = raw["primary_activity"]
    ranking_count = sum(item.get("basis") == "ranking_primary_activity" for item in raw["candidate_mappings"])
    if primary.get("compound_or_catch_all") or ranking_count > 1 or not primary.get("exact_source_alias_present"):
        return "crosswalk_candidate"
    return "insufficient_evidence"


def transform_observation(
    raw: dict[str, Any], manifest: dict[str, Any], parent: dict[str, Any], summary: dict[str, Any]
) -> dict[str, Any]:
    rank = int(raw["corpus"]["position"])
    ranking_name = raw["organization"]["ranking_name"]
    regulatory = raw.get("regulatory_metadata") or {}
    external_identifiers = nonempty_dict({"cik": regulatory.get("cik"), "ticker": regulatory.get("ticker")})
    memberships = ["fortune_1000", "fortune_500"]
    if rank <= 100:
        memberships.append("fortune_100")
    primary = raw["primary_activity"]
    description = (
        f"The external classification assigns the primary activity label '{primary['source_label']}'. "
        f"Baseline AMACS coverage was {primary['baseline_status']}."
    )
    if primary.get("compound_or_catch_all"):
        description += " The source label is compound or catch-all and must be represented through a crosswalk rather than imported as an AMACS alias."
    if regulatory.get("sic_description"):
        description += f" The resolved reporting entity carries the SEC-derived SIC description '{regulatory['sic_description']}'."
    evidence = [ranking_evidence(manifest, parent, summary, rank)]
    if regulatory:
        evidence.append(mirror_evidence(manifest, summary))
        if raw["entity_resolution"].get("matched_name_type") == "former_or_alternate_sec_name":
            evidence.append(mirror_evidence(manifest, summary, names=True))
    return {
        "observation_id": raw["observation_id"],
        "organization": {
            "name": ranking_name,
            "entity_scope": "reporting_entity" if raw["entity_resolution"].get("status", "").startswith("resolved") else "unknown",
            **({"external_identifiers": external_identifiers} if external_identifiers else {}),
            "headquarters": raw["organization"]["headquarters"],
        },
        "corpus": {
            "corpus_id": raw["corpus"]["corpus_id"],
            "edition": raw["corpus"]["edition"],
            "memberships": memberships,
            "position": rank,
        },
        "observed_at": manifest["observed_at"],
        "activity_observation": {
            "source_label": primary["source_label"],
            "description": description,
            "method": "industry_proxy",
            "source_scheme_id": "us500-fortune-1000-primary-activity-2026",
            "compound_or_catch_all": bool(primary.get("compound_or_catch_all")),
        },
        "identity_resolution": governed_resolution(raw["entity_resolution"], ranking_name),
        "evidence": evidence,
        "candidate_mappings": governed_mappings(raw),
        "gap_disposition": gap_disposition(raw),
        "review_status": raw.get("review_status", "machine_triage"),
        "not_for_profile_import": True,
    }


def crosswalk_candidates(
    refinement: dict[str, Any], manifest: dict[str, Any], parent: dict[str, Any], summary: dict[str, Any]
) -> list[dict[str, Any]]:
    roster = parent["machine_readable_roster"]
    records = []
    for label_review in refinement["label_review"]:
        label = label_review["source_label"]
        relation = "broad_match" if label_review["compound_or_catch_all"] or label_review["candidate_concept_count"] > 1 else "close_match"
        for concept_id in label_review["candidate_concept_ids"]:
            digest = hashlib.sha256(f"2026|{label}|{concept_id}".encode("utf-8")).hexdigest()[:16].upper()
            rationale = (
                f"The external primary-activity category '{label}' is a candidate {relation.replace('_', ' ')} "
                f"to {concept_id}. The category covers {label_review['organization_count']} Fortune 500 organizations "
                f"and maps to {label_review['candidate_concept_count']} AMACS capability concept(s)."
            )
            records.append({
                "crosswalk_id": f"AMACS-XWALK-F500-{digest}",
                "source_scheme": {
                    "scheme_id": "us500-fortune-1000-primary-activity-2026",
                    "title": "2026 Fortune 1000 machine-readable primary activity classification",
                    "edition": manifest["edition"],
                    "publisher": roster["publisher"],
                    "source_field": "industry",
                },
                "source_entry": {"label": label},
                "target_concept_id": concept_id,
                "mapping_relation": relation,
                "mapping_status": "candidate",
                "confidence": "low",
                "rationale": rationale,
                "provenance": [{
                    "source_type": "external_classification",
                    "title": "2026 Fortune 1000 machine-readable roster and primary activity classification",
                    "url": roster["page_url"],
                    "publisher": roster["publisher"],
                    "accessed_at": roster["retrieved_at"],
                    "content_sha256": summary["roster_source_sha256"],
                }],
                "status": "draft",
                "version_introduced": manifest["baseline_amacs_release"],
                "not_for_alias_import": True,
            })
    return records


def identity_candidates(
    raw_records: list[dict[str, Any]], manifest: dict[str, Any], parent: dict[str, Any], summary: dict[str, Any]
) -> list[dict[str, Any]]:
    records = []
    for raw in raw_records:
        rank = int(raw["corpus"]["position"])
        ranking_name = raw["organization"]["ranking_name"]
        resolution = raw["entity_resolution"]
        regulatory = raw.get("regulatory_metadata") or {}
        names = [{"name_type": "ranking_display_name", "value": ranking_name, "source_reference": "fortune-500-2026"}]
        sec_name = regulatory.get("sec_name") or resolution.get("sec_name")
        if sec_name and sec_name.casefold() != ranking_name.casefold():
            names.append({"name_type": "regulatory_name", "value": sec_name, "source_reference": "pinned-sec-derived-mirror"})
        matched_name = resolution.get("matched_name")
        if matched_name and resolution.get("matched_name_type") == "former_or_alternate_sec_name" and matched_name.casefold() not in {item["value"].casefold() for item in names}:
            names.append({"name_type": "former_name", "value": matched_name, "source_reference": "pinned-sec-derived-name-history"})
        identifiers = [{
            "scheme": "fortune_rank_2026", "value": str(rank), "issuing_authority": "US500", "status": "current"
        }]
        for scheme, value, authority in (
            ("sec_cik", regulatory.get("cik"), "U.S. Securities and Exchange Commission"),
            ("ticker", regulatory.get("ticker"), "SEC-derived listed filer metadata"),
            ("sic", regulatory.get("sic"), "U.S. Securities and Exchange Commission"),
        ):
            if value:
                identifiers.append({"scheme": scheme, "value": str(value), "issuing_authority": authority, "status": "current"})
        sources = [ranking_evidence(manifest, parent, summary, rank)]
        if regulatory:
            sources.append(mirror_evidence(manifest, summary))
            if any(item["name_type"] == "former_name" for item in names):
                sources.append(mirror_evidence(manifest, summary, names=True))
        records.append({
            "identity_id": f"AMACS-ORGID-CAND-F500-2026-{rank:03d}",
            "preferred_name": sec_name or ranking_name,
            "organization_type": "reporting_entity" if resolution.get("status", "").startswith("resolved") else "unknown",
            "names": names,
            "external_identifiers": identifiers,
            "relationships": [],
            "verification_status": "research_candidate",
            "sources": sources,
            "status": "draft",
            "version_introduced": manifest["baseline_amacs_release"],
            "profile_import_status": "prohibited",
        })
    return records


def validate_records(records: list[dict[str, Any]], schema_path: Path, label: str) -> None:
    validator = Draft202012Validator(read_json(schema_path), format_checker=FormatChecker())
    errors = []
    for index, record in enumerate(records, 1):
        for error in validator.iter_errors(record):
            location = ".".join(str(part) for part in error.path) or "<record>"
            errors.append(f"{label} record {index} {location}: {error.message}")
            if len(errors) >= 25:
                break
        if len(errors) >= 25:
            break
    if errors:
        raise ValueError("\n".join(errors))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="research/fortune-500-2026/manifest.json")
    parser.add_argument("--input-dir", required=True)
    parser.add_argument("--schema-dir", default="schemas")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    schema_dir = Path(args.schema_dir)
    if not schema_dir.is_absolute():
        schema_dir = ROOT / schema_dir
    input_dir = Path(args.input_dir)
    manifest = read_json(manifest_path)
    parent = read_json(ROOT / manifest["parent_corpus_manifest"])
    summary = read_json(input_dir / "cohort-depth-summary.json")
    refinement = read_json(input_dir / "refinement-candidates.json")
    raw_records = read_jsonl(input_dir / "organization-taxonomy-observations.jsonl")

    if len(raw_records) != manifest["expected_organization_count"]:
        raise ValueError(f"expected {manifest['expected_organization_count']} observations, found {len(raw_records)}")
    observations = [transform_observation(record, manifest, parent, summary) for record in raw_records]
    crosswalks = crosswalk_candidates(refinement, manifest, parent, summary)
    identities = identity_candidates(raw_records, manifest, parent, summary)

    validate_records(observations, schema_dir / "organization-taxonomy-observation.schema.json", "observation")
    validate_records(crosswalks, schema_dir / "external-classification-crosswalk.schema.json", "crosswalk")
    validate_records(identities, schema_dir / "organization-identity.schema.json", "identity")

    if any(not record["not_for_profile_import"] for record in observations):
        raise ValueError("all Fortune 500 observations must prohibit profile import")
    if any(not record["not_for_alias_import"] for record in crosswalks):
        raise ValueError("all external crosswalk candidates must prohibit alias import")
    if any(record["profile_import_status"] != "prohibited" for record in identities):
        raise ValueError("all research identity candidates must prohibit profile import")

    write_jsonl(input_dir / "organization-taxonomy-observations.jsonl", observations)
    write_jsonl(input_dir / "external-classification-crosswalk-candidates.jsonl", crosswalks)
    write_jsonl(input_dir / "organization-identity-candidates.jsonl", identities)
    governance_summary = {
        "corpus_id": manifest["corpus_id"],
        "schema_validation": "passed",
        "validated_observation_count": len(observations),
        "validated_crosswalk_candidate_count": len(crosswalks),
        "validated_identity_candidate_count": len(identities),
        "observation_gap_dispositions": {
            value: sum(record["gap_disposition"] == value for record in observations)
            for value in sorted({record["gap_disposition"] for record in observations})
        },
        "crosswalks_imported_as_aliases": 0,
        "organization_profiles_created": 0,
        "organization_capability_assertions_created": 0,
    }
    write_json(input_dir / "governance-summary.json", governance_summary)
    print(json.dumps(governance_summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Fortune 500 artifact governance failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
