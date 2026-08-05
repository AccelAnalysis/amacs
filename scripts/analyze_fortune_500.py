#!/usr/bin/env python3
"""Run the Fortune 500 entity-resolution and AMACS taxonomy-depth pass."""
from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import io
import json
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORD = re.compile(r"[a-z0-9]+")
COMMON_SUFFIXES = {
    "co", "company", "companies", "corp", "corporation", "inc", "incorporated",
    "group", "holdings", "holding", "limited", "ltd", "llc", "lp", "plc",
    "the", "de", "nv", "sa", "na", "new",
}
GENERIC_TOKENS = {
    "and", "business", "businesses", "company", "companies", "consumer", "consumers",
    "commercial", "industry", "industries", "market", "markets", "operation", "operations",
    "product", "products", "service", "services", "other", "general", "diversified",
}
COMPOUND_MARKERS = re.compile(r"(?:,|/|\band\b|\bother\b|\bdiversified\b|\bmiscellaneous\b)", re.I)


@dataclass(frozen=True)
class SecEntity:
    cik: str
    name: str
    ticker: str = ""
    sic: str = ""
    sic_description: str = ""
    entity_type: str = ""
    exchanges: str = ""


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def fetch_bytes(url: str, user_agent: str = "AMACS taxonomy research/0.3") -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept-Encoding": "identity"})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read()


def read_source(path: str | None, url: str) -> bytes:
    return Path(path).read_bytes() if path else fetch_bytes(url)


def decode_csv(raw: bytes) -> list[dict[str, str]]:
    if raw[:2] == b"\x1f\x8b":
        raw = gzip.decompress(raw)
    return [dict(row) for row in csv.DictReader(io.StringIO(raw.decode("utf-8-sig", errors="replace")))]


def normalize_name(value: str) -> str:
    value = value.lower().replace("&", " and ").replace(".com", " com ")
    tokens = WORD.findall(value)
    while tokens and tokens[-1] in COMMON_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def compact_name(value: str) -> str:
    return normalize_name(value).replace(" ", "")


def score_name(left: str, right: str) -> float:
    left_normal = normalize_name(left)
    right_normal = normalize_name(right)
    if left_normal == right_normal or compact_name(left) == compact_name(right):
        return 1.0
    left_tokens = set(left_normal.split())
    right_tokens = set(right_normal.split())
    token_score = len(left_tokens & right_tokens) / max(len(left_tokens | right_tokens), 1)
    sequence_score = SequenceMatcher(None, compact_name(left), compact_name(right)).ratio()
    return round(max(sequence_score, (sequence_score + token_score) / 2), 6)


def parse_ticker(value: str) -> str:
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


def load_sec_entities(metadata_rows: list[dict[str, str]]) -> dict[str, SecEntity]:
    entities: dict[str, SecEntity] = {}
    for row in metadata_rows:
        cik = str(row.get("cik", "")).strip().replace(".0", "").zfill(10)
        name = (row.get("name") or "").strip()
        if not cik.strip("0") or not name:
            continue
        entities[cik] = SecEntity(
            cik=cik,
            name=name,
            ticker=parse_ticker(row.get("tickers", "")),
            sic=(row.get("sic") or "").strip().replace(".0", ""),
            sic_description=(row.get("sicDescription") or "").strip(),
            entity_type=(row.get("entityType") or "").strip(),
            exchanges=(row.get("exchanges") or "").strip(),
        )
    return entities


def build_name_index(entities: dict[str, SecEntity], name_rows: list[dict[str, str]]) -> list[tuple[str, str, str]]:
    index: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for entity in entities.values():
        key = (entity.cik, normalize_name(entity.name))
        if key[1] and key not in seen:
            seen.add(key)
            index.append((entity.name, entity.cik, "current_sec_name"))
    for row in name_rows:
        cik = str(row.get("cik", "")).strip().replace(".0", "").zfill(10)
        name = (row.get("name") or "").strip()
        key = (cik, normalize_name(name))
        if cik in entities and key[1] and key not in seen:
            seen.add(key)
            index.append((name, cik, "former_or_alternate_sec_name"))
    return index


def resolve_entity(
    company: str,
    entities: dict[str, SecEntity] | list[SecEntity],
    name_index_or_overrides: list[tuple[str, str, str]] | dict[str, Any],
    overrides_or_automatic: dict[str, Any] | float,
    automatic_or_candidate: float,
    candidate_threshold: float | None = None,
) -> dict[str, Any]:
    """Resolve a ranking name conservatively; supports the prior five-argument tests."""
    if isinstance(entities, list):
        entity_map = {entity.cik: entity for entity in entities}
        name_index = [(entity.name, entity.cik, "current_sec_name") for entity in entities]
        overrides = name_index_or_overrides if isinstance(name_index_or_overrides, dict) else {}
        automatic_threshold = float(overrides_or_automatic)
        candidate = float(automatic_or_candidate)
    else:
        entity_map = entities
        name_index = name_index_or_overrides if isinstance(name_index_or_overrides, list) else []
        overrides = overrides_or_automatic if isinstance(overrides_or_automatic, dict) else {}
        automatic_threshold = float(automatic_or_candidate)
        candidate = float(candidate_threshold if candidate_threshold is not None else 0.86)

    override = overrides.get(company)
    if override:
        cik = str(override["cik"]).zfill(10)
        entity = entity_map.get(cik)
        return {
            "status": "resolved_override", "score": 1.0, "cik": cik,
            "sec_name": override.get("sec_name") or (entity.name if entity else ""),
            "ticker": entity.ticker if entity else "", "matched_name": override.get("sec_name", ""),
            "matched_name_type": "controlled_override", "reason": override["reason"],
        }

    ranked = sorted(
        ((score_name(company, indexed_name), indexed_name, cik, name_type)
         for indexed_name, cik, name_type in name_index),
        key=lambda item: (-item[0], item[2], item[1]),
    )[:5]
    if not ranked:
        return {"status": "unresolved", "score": 0.0, "candidates": [], "reason": "The regulatory entity index is empty."}
    top_score, top_name, top_cik, top_type = ranked[0]
    second_score = next((score for score, _, cik, _ in ranked[1:] if cik != top_cik), 0.0)
    candidates = []
    seen_ciks: set[str] = set()
    for score, matched_name, cik, name_type in ranked:
        if score < candidate or cik in seen_ciks:
            continue
        seen_ciks.add(cik)
        entity = entity_map[cik]
        candidates.append({
            "cik": cik, "sec_name": entity.name, "ticker": entity.ticker,
            "matched_name": matched_name, "matched_name_type": name_type, "score": score,
        })
    entity = entity_map[top_cik]
    if top_score >= automatic_threshold and top_score - second_score >= 0.02:
        return {
            "status": "resolved_automatic", "score": top_score, "cik": top_cik,
            "sec_name": entity.name, "ticker": entity.ticker, "matched_name": top_name,
            "matched_name_type": top_type,
            "reason": "Conservative normalized-name match against current and historical SEC filer names.",
        }
    if candidates:
        return {
            "status": "candidate" if len(candidates) == 1 else "ambiguous",
            "score": top_score, "candidates": candidates,
            "reason": "The regulatory name similarity requires analyst confirmation.",
        }
    return {
        "status": "unresolved", "score": top_score, "candidates": [],
        "reason": "No sufficiently similar listed SEC filer was found; the organization may be private, mutual, cooperative, governmental, or differently named.",
    }


def load_amacs() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from amacs_io import load_dataset  # type: ignore
    return load_dataset("concepts", ROOT), load_dataset("aliases", ROOT)


def tokens(value: str) -> set[str]:
    return {token for token in WORD.findall(value.lower()) if len(token) >= 4 and token not in GENERIC_TOKENS}


def build_concept_index(concepts: list[dict[str, Any]], aliases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    alias_map: dict[str, list[str]] = defaultdict(list)
    for alias in aliases:
        alias_map[alias["concept_id"]].append(alias["alias"])
    return [{
        "concept_id": concept["concept_id"], "label": concept["preferred_label"],
        "definition": concept["definition"], "parent_id": concept.get("primary_parent_id"),
        "terms": [concept["preferred_label"], *alias_map.get(concept["concept_id"], [])],
    } for concept in concepts if concept["concept_type"] == "capability"]


def lexical_mappings(description: str, concept_index: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    source_tokens = tokens(description)
    if not source_tokens:
        return []
    scored: list[tuple[float, dict[str, Any]]] = []
    for concept in concept_index:
        best = 0.0
        matched: set[str] = set()
        for term in concept["terms"]:
            term_tokens = tokens(term)
            overlap = source_tokens & term_tokens
            if not overlap:
                continue
            score = len(overlap) / max(len(term_tokens), 1)
            if len(overlap) >= 2:
                score += 0.15
            if score > best:
                best, matched = score, overlap
        if best >= 0.65:
            scored.append((best, {
                "concept_id": concept["concept_id"], "label": concept["label"],
                "mapping_status": "candidate", "confidence": "low",
                "basis": "regulatory_sic_description", "score": round(min(best, 1.0), 4),
                "matched_terms": sorted(matched),
            }))
    scored.sort(key=lambda item: (-item[0], item[1]["concept_id"]))
    return [value for _, value in scored[:limit]]


def load_activity_map(path: Path, capability_ids: set[str]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for entry in read_json(path)["entries"]:
        missing = set(entry["candidate_concept_ids"]) - capability_ids
        if missing:
            raise ValueError(f"{entry['source_label']} references missing capabilities {sorted(missing)}")
        result[entry["source_label"]] = entry
    return result


def source_alias_present(label: str, mapped_ids: list[str], concept_index: list[dict[str, Any]]) -> bool:
    normalized = normalize_name(label)
    return any(
        concept["concept_id"] in mapped_ids
        and any(normalize_name(term) == normalized for term in concept["terms"])
        for concept in concept_index
    )


def validate_roster(rows: list[dict[str, Any]], expected_count: int) -> None:
    positions = sorted(int(row["rank"]) for row in rows)
    if len(rows) != expected_count or positions != list(range(1, expected_count + 1)):
        raise ValueError(f"cohort must contain exactly one organization at each rank 1 through {expected_count}")


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="research/fortune-500-2026/manifest.json")
    parser.add_argument("--source-file")
    parser.add_argument("--listed-metadata-file")
    parser.add_argument("--listed-names-file")
    parser.add_argument("--output", required=True)
    parser.add_argument("--allow-source-drift", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    manifest = read_json(manifest_path)
    parent = read_json(ROOT / manifest["parent_corpus_manifest"])

    roster_raw = read_source(args.source_file, parent["machine_readable_roster"]["data_url"])
    roster_sha = hashlib.sha256(roster_raw).hexdigest()
    expected_roster_sha = parent["machine_readable_roster"]["expected_sha256"]
    if roster_sha != expected_roster_sha and not args.allow_source_drift:
        raise ValueError(f"Fortune roster source drift: expected {expected_roster_sha}, found {roster_sha}")
    roster_doc = json.loads(roster_raw)
    rows = [row for row in roster_doc[parent["machine_readable_roster"]["data_path"]] if int(row["rank"]) <= manifest["expected_position_max"]]
    rows.sort(key=lambda row: int(row["rank"]))
    validate_roster(rows, manifest["expected_organization_count"])

    mirror = manifest["regulatory_metadata_mirror"]
    metadata_raw = read_source(args.listed_metadata_file, mirror["listed_metadata_url"])
    names_raw = read_source(args.listed_names_file, mirror["listed_names_url"])
    metadata_sha = hashlib.sha256(metadata_raw).hexdigest()
    names_sha = hashlib.sha256(names_raw).hexdigest()
    entities = load_sec_entities(decode_csv(metadata_raw))
    name_index = build_name_index(entities, decode_csv(names_raw))
    overrides = read_json(ROOT / manifest["entity_overrides"])["overrides"]

    concepts, aliases = load_amacs()
    concept_index = build_concept_index(concepts, aliases)
    activity_map = load_activity_map(ROOT / manifest["primary_activity_map"], {concept["concept_id"] for concept in concept_index})

    records: list[dict[str, Any]] = []
    resolution_counts: Counter[str] = Counter()
    label_counts: Counter[str] = Counter(row["industry"] for row in rows)
    concept_counts: Counter[str] = Counter()
    label_to_concepts: dict[str, set[str]] = defaultdict(set)
    unresolved: list[dict[str, Any]] = []

    for row in rows:
        rank = int(row["rank"])
        label = row["industry"]
        activity = activity_map[label]
        resolution = resolve_entity(
            row["company"], entities, name_index, overrides,
            manifest["minimum_automatic_match_score"], manifest["minimum_candidate_match_score"],
        )
        resolution_counts[resolution["status"]] += 1
        if resolution["status"] in {"candidate", "ambiguous", "unresolved"}:
            unresolved.append({"rank": rank, "organization": row["company"], "resolution": resolution})

        mappings: dict[tuple[str, str], dict[str, Any]] = {}
        for concept_id in activity["candidate_concept_ids"]:
            mapping = {
                "concept_id": concept_id,
                "mapping_status": activity.get("mapping_status", "candidate"),
                "confidence": activity.get("confidence", "low"),
                "basis": "ranking_primary_activity",
                "rationale": activity.get("rationale", "The ranking activity label identifies a taxonomy candidate, not an organization capability assertion."),
            }
            mappings[(concept_id, mapping["basis"])] = mapping
            concept_counts[concept_id] += 1
            label_to_concepts[label].add(concept_id)

        regulatory = None
        if resolution["status"].startswith("resolved"):
            entity = entities.get(resolution["cik"])
            if entity:
                regulatory = {
                    "cik": entity.cik, "sec_name": entity.name, "ticker": entity.ticker,
                    "sic": entity.sic, "sic_description": entity.sic_description,
                    "entity_type": entity.entity_type, "exchanges": entity.exchanges,
                    "source_chain": "SEC submissions bulk archive -> pinned Datamule metadata mirror",
                }
                for mapping in lexical_mappings(entity.sic_description, concept_index):
                    mappings[(mapping["concept_id"], mapping["basis"])] = mapping

        mapped_ids = activity["candidate_concept_ids"]
        records.append({
            "observation_id": f"fortune-500-2026-rank-{rank:03d}",
            "organization": {
                "ranking_name": row["company"],
                "headquarters": {"city": row["city"], "region": row["state"], "country": "US"},
            },
            "corpus": {"corpus_id": manifest["corpus_id"], "edition": manifest["edition"], "position": rank},
            "primary_activity": {
                "source_label": label, "baseline_status": activity["baseline_status"],
                "compound_or_catch_all": bool(COMPOUND_MARKERS.search(label)),
                "exact_source_alias_present": source_alias_present(label, mapped_ids, concept_index),
            },
            "entity_resolution": resolution,
            "regulatory_metadata": regulatory,
            "candidate_mappings": sorted(mappings.values(), key=lambda item: (item["basis"], item["concept_id"])),
            "review_status": "machine_triage",
            "not_for_profile_import": True,
        })

    resolved = sum(count for status, count in resolution_counts.items() if status.startswith("resolved"))
    resolution_rate = resolved / len(records)
    if resolution_rate < manifest["minimum_regulatory_resolution_rate"]:
        raise ValueError(
            f"regulatory resolution rate {resolution_rate:.3f} is below the governed minimum "
            f"{manifest['minimum_regulatory_resolution_rate']:.3f}"
        )

    label_reviews = []
    for label, count in sorted(label_counts.items(), key=lambda item: (-item[1], item[0])):
        ids = sorted(label_to_concepts[label])
        entry = activity_map[label]
        alias_present = source_alias_present(label, ids, concept_index)
        compound = bool(COMPOUND_MARKERS.search(label))
        label_reviews.append({
            "source_label": label, "organization_count": count,
            "baseline_status": entry["baseline_status"], "candidate_concept_ids": ids,
            "candidate_concept_count": len(ids), "compound_or_catch_all": compound,
            "exact_source_alias_present": alias_present,
            "review_reasons": [
                reason for condition, reason in (
                    (len(ids) > 1, "one source label maps to multiple capabilities"),
                    (compound, "source label is compound or catch-all"),
                    (not alias_present, "source label is not an exact governed alias"),
                    (entry["baseline_status"] != "direct", "baseline AMACS coverage was partial or absent"),
                ) if condition
            ],
        })

    concept_label_use: dict[str, set[str]] = defaultdict(set)
    for label, ids in label_to_concepts.items():
        for concept_id in ids:
            concept_label_use[concept_id].add(label)
    overbreadth = [{
        "concept_id": concept_id, "organization_count": concept_counts[concept_id],
        "source_labels": sorted(labels), "source_label_count": len(labels),
    } for concept_id, labels in concept_label_use.items() if len(labels) >= 3]
    overbreadth.sort(key=lambda item: (-item["source_label_count"], -item["organization_count"], item["concept_id"]))

    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    (output / "organization-taxonomy-observations.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in records),
        encoding="utf-8",
    )
    write_json(output / "entity-review-queue.json", {"organizations": unresolved})
    write_json(output / "refinement-candidates.json", {
        "label_review": label_reviews,
        "potential_concept_overbreadth": overbreadth,
        "promotion_rule": "Frequency prioritizes review; it does not by itself authorize an AMACS change.",
    })
    summary = {
        "corpus_id": manifest["corpus_id"], "edition": manifest["edition"],
        "organization_count": len(records), "roster_source_sha256": roster_sha,
        "regulatory_metadata_source": {
            "repository": mirror["repository"], "commit": mirror["commit"],
            "listed_metadata_sha256": metadata_sha, "listed_names_sha256": names_sha,
        },
        "entity_resolution_counts": dict(sorted(resolution_counts.items())),
        "regulatory_resolution_rate": round(resolution_rate, 4),
        "organizations_with_regulatory_metadata": sum(record["regulatory_metadata"] is not None for record in records),
        "organizations_with_sic_description": sum(bool((record["regulatory_metadata"] or {}).get("sic_description")) for record in records),
        "primary_activity_label_count": len(label_counts),
        "compound_or_catch_all_label_count": sum(item["compound_or_catch_all"] for item in label_reviews),
        "labels_without_exact_governed_alias": sum(not item["exact_source_alias_present"] for item in label_reviews),
        "labels_mapping_to_multiple_capabilities": sum(item["candidate_concept_count"] > 1 for item in label_reviews),
        "candidate_concept_ids_used": sorted(concept_counts),
        "profile_assertions_created": 0,
        "generated_observation_semantics": "taxonomy_research_only",
        "annual_filing_text_layer_status": "not_executed_in_ci_due_to_live_sec_edge_denial; governed follow-on evidence batches required",
    }
    write_json(output / "cohort-depth-summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Fortune 500 taxonomy-depth analysis failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
