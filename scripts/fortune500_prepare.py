#!/usr/bin/env python3
"""Prepare the Fortune 500 identity and external-classification research corpus."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
WORD = re.compile(r"[a-z0-9]+")
SUFFIXES = {"co","company","companies","corp","corporation","inc","incorporated","group","holdings","holding","limited","ltd","llc","lp","plc","the","de","nv","sa","na"}


@dataclass(frozen=True)
class Entity:
    cik: str
    name: str
    ticker: str
    sic: str
    sic_description: str
    entity_type: str
    exchanges: str


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def decode_csv(raw: bytes) -> list[dict[str, str]]:
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return [dict(row) for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="replace")))]


def normalize(value: str) -> str:
    tokens = WORD.findall(value.lower().replace("&", " and ").replace(".com", " com "))
    while tokens and tokens[-1] in SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def compact(value: str) -> str:
    return normalize(value).replace(" ", "")


def acronym(value: str) -> str:
    tokens = [t for t in normalize(value).split() if t not in {"and","of","for"}]
    return "".join(t[0] for t in tokens if t).upper()


def parse_first(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    try:
        parsed = json.loads(value.replace("'", '"'))
        if isinstance(parsed, list) and parsed:
            return str(parsed[0])
    except json.JSONDecodeError:
        pass
    return value.strip("[]'\"").split(",")[0].strip()


def load_entities(rows: list[dict[str, str]]) -> dict[str, Entity]:
    result: dict[str, Entity] = {}
    for row in rows:
        cik = str(row.get("cik", "")).strip().replace(".0", "").zfill(10)
        name = (row.get("name") or "").strip()
        if not cik.strip("0") or not name:
            continue
        result[cik] = Entity(
            cik=cik,
            name=name,
            ticker=parse_first(row.get("tickers", "")),
            sic=(row.get("sic") or "").strip().replace(".0", ""),
            sic_description=(row.get("sicDescription") or "").strip(),
            entity_type=(row.get("entityType") or "").strip(),
            exchanges=(row.get("exchanges") or "").strip(),
        )
    return result


def add_index(index: dict[str, set[str]], key: str, cik: str) -> None:
    if key:
        index[key].add(cik)


def build_indexes(entities: dict[str, Entity], former_rows: list[dict[str, str]]) -> dict[str, dict[str, set[str]]]:
    idx: dict[str, dict[str, set[str]]] = {
        "current": defaultdict(set), "compact": defaultdict(set), "acronym": defaultdict(set),
        "former": defaultdict(set), "former_compact": defaultdict(set), "first": defaultdict(set),
    }
    for entity in entities.values():
        add_index(idx["current"], normalize(entity.name), entity.cik)
        add_index(idx["compact"], compact(entity.name), entity.cik)
        ac = acronym(entity.name)
        if 2 <= len(ac) <= 8:
            add_index(idx["acronym"], ac, entity.cik)
        first = normalize(entity.name).split()[:1]
        if first:
            add_index(idx["first"], first[0], entity.cik)
    for row in former_rows:
        cik = str(row.get("cik", "")).strip().replace(".0", "").zfill(10)
        name = (row.get("name") or "").strip()
        if cik in entities and name:
            add_index(idx["former"], normalize(name), cik)
            add_index(idx["former_compact"], compact(name), cik)
    return idx


def result_for(entity: Entity, status: str, basis: str, score: float, rationale: str) -> dict[str, Any]:
    return {
        "status": status, "match_basis": basis, "score": round(score, 6),
        "resolved_name": entity.name, "cik": entity.cik, "ticker": entity.ticker,
        "sic": entity.sic, "sic_description": entity.sic_description,
        "entity_type": entity.entity_type, "exchanges": entity.exchanges, "rationale": rationale,
    }


def resolve(company: str, entities: dict[str, Entity], idx: dict[str, dict[str, set[str]]], overrides: dict[str, Any], automatic: float, candidate: float) -> dict[str, Any]:
    override = overrides.get(company)
    if override:
        entity = entities.get(str(override["cik"]).zfill(10))
        if entity:
            return result_for(entity, "resolved", "controlled_override", 1.0, override["reason"])

    keys = [("exact_name", idx["current"].get(normalize(company), set())), ("compact_name", idx["compact"].get(compact(company), set()))]
    if company.isupper() and 2 <= len(company) <= 8:
        keys.append(("acronym", idx["acronym"].get(company, set())))
    keys.extend([("former_name", idx["former"].get(normalize(company), set())), ("former_name", idx["former_compact"].get(compact(company), set()))])
    for basis, ciks in keys:
        if len(ciks) == 1:
            return result_for(entities[next(iter(ciks))], "resolved", basis, 1.0, "Unique normalized identity match in the pinned SEC-derived filer metadata.")
        if len(ciks) > 1:
            return {"status": "ambiguous", "match_basis": basis, "score": 1.0, "candidates": sorted(ciks), "rationale": "More than one filer shares this normalized identity key."}

    norm = normalize(company)
    first = norm.split()[:1]
    pool = set(idx["first"].get(first[0], set())) if first else set()
    if not pool:
        pool = set(entities)
    scored: list[tuple[float, Entity]] = []
    for cik in pool:
        entity = entities[cik]
        score = SequenceMatcher(None, compact(company), compact(entity.name)).ratio()
        if score >= candidate:
            scored.append((score, entity))
    scored.sort(key=lambda x: (-x[0], x[1].cik))
    if scored:
        top_score, top = scored[0]
        second = scored[1][0] if len(scored) > 1 else 0.0
        if top_score >= automatic and top_score - second >= 0.03:
            return result_for(top, "resolved", "fuzzy_name", top_score, "High-similarity name match with a conservative separation from the next candidate.")
        return {
            "status": "candidate" if len(scored) == 1 else "ambiguous", "match_basis": "fuzzy_name",
            "score": round(top_score, 6),
            "candidates": [{"cik": e.cik, "name": e.name, "score": round(s, 6)} for s, e in scored[:5]],
            "rationale": "Name similarity requires analyst confirmation before identity is treated as resolved.",
        }
    return {"status": "unresolved", "match_basis": "no_match", "score": 0.0, "candidates": [], "rationale": "No sufficiently similar listed filer was found; the organization may be private, mutual, cooperative, foreign, governmental, or differently named."}


def validate_records(records: list[dict[str, Any]], schema_name: str) -> None:
    schema = read_json(ROOT / "schemas" / schema_name)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors: list[str] = []
    for i, record in enumerate(records, 1):
        for error in validator.iter_errors(record):
            errors.append(f"record {i} {'.'.join(map(str, error.path)) or '<record>'}: {error.message}")
    if errors:
        raise ValueError("schema validation failed:\n  " + "\n  ".join(errors[:50]))


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in records), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-file", required=True)
    parser.add_argument("--listed-metadata-file", required=True)
    parser.add_argument("--listed-names-file", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    manifest = read_json(ROOT / "research/fortune-500-2026/manifest.json")
    parent = read_json(ROOT / manifest["parent_corpus_manifest"])
    roster_raw = Path(args.source_file).read_bytes()
    roster_sha = hashlib.sha256(roster_raw).hexdigest()
    if roster_sha != parent["machine_readable_roster"]["expected_sha256"]:
        raise ValueError(f"Fortune roster source drift: expected {parent['machine_readable_roster']['expected_sha256']}, found {roster_sha}")
    rows = json.loads(roster_raw)[parent["machine_readable_roster"]["data_path"]]
    rows = sorted((r for r in rows if int(r["rank"]) <= 500), key=lambda r: int(r["rank"]))
    if [int(r["rank"]) for r in rows] != list(range(1, 501)):
        raise ValueError("Fortune 500 cohort must contain exactly ranks 1 through 500")

    metadata_raw = Path(args.listed_metadata_file).read_bytes()
    names_raw = Path(args.listed_names_file).read_bytes()
    metadata_sha = hashlib.sha256(metadata_raw).hexdigest()
    names_sha = hashlib.sha256(names_raw).hexdigest()
    entities = load_entities(decode_csv(metadata_raw))
    indexes = build_indexes(entities, decode_csv(names_raw))
    overrides = read_json(ROOT / manifest["entity_overrides"])["overrides"]
    activity_map = {e["source_label"]: e for e in read_json(ROOT / manifest["primary_activity_map"])["entries"]}

    observed_at = manifest["observed_at"]
    ranking_source = {
        "source_type": "external_classification", "title": "2026 Fortune 1000 machine-readable roster and primary activity classification",
        "url": parent["machine_readable_roster"]["page_url"], "publisher": parent["machine_readable_roster"]["publisher"],
        "accessed_at": parent["machine_readable_roster"]["retrieved_at"], "content_sha256": roster_sha,
    }
    mirror = manifest["regulatory_metadata_mirror"]
    mirror_source = {
        "source_type": "regulatory_metadata_mirror", "title": "SEC-derived listed filer metadata",
        "url": mirror["listed_metadata_url"], "publisher": "Datamule Data", "accessed_at": observed_at,
        "evidence_locator": f"Pinned mirror commit {mirror['commit']}", "content_sha256": metadata_sha,
    }

    cohort: list[dict[str, Any]] = []
    identities: list[dict[str, Any]] = []
    crosswalks: dict[tuple[str, str], dict[str, Any]] = {}
    resolution_counts: Counter[str] = Counter()

    for row in rows:
        rank = int(row["rank"])
        company = row["company"]
        resolution = resolve(company, entities, indexes, overrides, manifest["minimum_automatic_match_score"], manifest["minimum_candidate_match_score"])
        resolution_counts[resolution["status"]] += 1
        activity = activity_map[row["industry"]]
        concept_ids = list(activity["candidate_concept_ids"])
        compound = bool(re.search(r"(?:,|/|\band\b|\bother\b|\bdiversified\b|\bmiscellaneous\b)", row["industry"], re.I)) or len(concept_ids) > 1
        identity_id = f"AMACS-ORGID-CAND-F500-2026-{rank:03d}"
        cohort.append({
            "position": rank, "company": company, "industry": row["industry"],
            "headquarters": {"city": row.get("city", ""), "region": row.get("state", ""), "country": "US"},
            "identity_id": identity_id, "identity_resolution": resolution,
            "primary_candidate_concept_ids": concept_ids, "compound_or_catch_all": compound,
        })

        names = [{"name_type": "ranking_display_name", "value": company, "source_reference": "fortune-500-2026"}]
        identifiers = [{"scheme": "fortune_rank_2026", "value": str(rank), "issuing_authority": "US500", "status": "current"}]
        sources = [ranking_source]
        preferred = company
        org_type = "unknown"
        if resolution["status"] == "resolved":
            preferred = resolution["resolved_name"]
            org_type = "reporting_entity"
            names.append({"name_type": "regulatory_name", "value": resolution["resolved_name"], "source_reference": "pinned-sec-derived-mirror"})
            identifiers.append({"scheme": "sec_cik", "value": resolution["cik"], "issuing_authority": "U.S. Securities and Exchange Commission", "status": "current"})
            if resolution.get("ticker"):
                identifiers.append({"scheme": "ticker", "value": resolution["ticker"], "issuing_authority": "SEC-derived listed filer metadata", "status": "current"})
            if resolution.get("sic"):
                identifiers.append({"scheme": "sec_sic", "value": resolution["sic"], "issuing_authority": "U.S. Securities and Exchange Commission", "status": "current"})
            sources.append(mirror_source)
        identities.append({
            "identity_id": identity_id, "preferred_name": preferred, "organization_type": org_type,
            "names": names, "external_identifiers": identifiers, "relationships": [],
            "verification_status": "research_candidate", "sources": sources,
            "status": "draft", "version_introduced": "0.3.0", "profile_import_status": "prohibited",
        })

        for concept_id in concept_ids:
            key = (row["industry"], concept_id)
            if key not in crosswalks:
                crosswalks[key] = {
                    "crosswalk_id": "AMACS-XWALK-F500-" + hashlib.sha256(f"{row['industry']}|{concept_id}".encode()).hexdigest()[:16].upper(),
                    "source_scheme": {"scheme_id": "us500-fortune-1000-primary-activity-2026", "title": "2026 Fortune 1000 machine-readable primary activity classification", "edition": "2026", "publisher": parent["machine_readable_roster"]["publisher"], "source_field": "industry"},
                    "source_entry": {"label": row["industry"]}, "target_concept_id": concept_id,
                    "mapping_relation": "broad_match" if compound else "close_match", "mapping_status": "candidate", "confidence": "low",
                    "rationale": "The external activity category is a taxonomy crosswalk candidate only and requires semantic review before approval.",
                    "provenance": [ranking_source], "status": "draft", "version_introduced": "0.3.0", "not_for_alias_import": True,
                }

    crosswalk_records = sorted(crosswalks.values(), key=lambda r: r["crosswalk_id"])
    validate_records(identities, "organization-identity.schema.json")
    validate_records(crosswalk_records, "external-classification-crosswalk.schema.json")

    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    write_jsonl(out / "cohort-records.jsonl", cohort)
    write_jsonl(out / "organization-identity-candidates.jsonl", identities)
    write_jsonl(out / "external-classification-crosswalk-candidates.jsonl", crosswalk_records)
    summary = {
        "corpus_id": manifest["corpus_id"], "organization_count": len(cohort),
        "identity_resolution_counts": dict(sorted(resolution_counts.items())),
        "crosswalk_candidate_count": len(crosswalk_records), "identity_candidate_count": len(identities),
        "roster_sha256": roster_sha, "regulatory_metadata_sha256": metadata_sha, "regulatory_names_sha256": names_sha,
        "profile_assertions_created": 0, "external_aliases_created": 0,
    }
    (out / "prepare-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Fortune 500 preparation failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
