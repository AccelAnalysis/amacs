#!/usr/bin/env python3
"""Execute the Fortune 500 analyzer with indexed regulatory-name resolution."""
from __future__ import annotations

from collections import defaultdict
from typing import Any

import analyze_fortune_500 as base


def build_name_index(entities: dict[str, base.SecEntity], name_rows: list[dict[str, str]]) -> dict[str, Any]:
    rows: list[tuple[str, str, str]] = []
    seen: set[tuple[str, str]] = set()
    for entity in entities.values():
        key = (entity.cik, base.normalize_name(entity.name))
        if key[1] and key not in seen:
            seen.add(key)
            rows.append((entity.name, entity.cik, "current_sec_name"))
    for row in name_rows:
        cik = str(row.get("cik", "")).strip().replace(".0", "").zfill(10)
        name = (row.get("name") or "").strip()
        key = (cik, base.normalize_name(name))
        if cik in entities and key[1] and key not in seen:
            seen.add(key)
            rows.append((name, cik, "former_or_alternate_sec_name"))

    exact: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    compact: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    prefixes: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    first_tokens: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for item in rows:
        normalized = base.normalize_name(item[0])
        compacted = normalized.replace(" ", "")
        exact[normalized].append(item)
        compact[compacted].append(item)
        if compacted:
            prefixes[compacted[:4]].append(item)
        if normalized:
            first_tokens[normalized.split()[0]].append(item)
    return {"rows": rows, "exact": exact, "compact": compact, "prefixes": prefixes, "first_tokens": first_tokens}


def resolve_entity(
    company: str,
    entities: dict[str, base.SecEntity],
    name_index: dict[str, Any],
    overrides: dict[str, Any],
    automatic_threshold: float,
    candidate_threshold: float,
) -> dict[str, Any]:
    override = overrides.get(company)
    if override:
        cik = str(override["cik"]).zfill(10)
        entity = entities.get(cik)
        return {
            "status": "resolved_override", "score": 1.0, "cik": cik,
            "sec_name": override.get("sec_name") or (entity.name if entity else ""),
            "ticker": entity.ticker if entity else "", "matched_name": override.get("sec_name", ""),
            "matched_name_type": "controlled_override", "reason": override["reason"],
        }

    normalized = base.normalize_name(company)
    compacted = normalized.replace(" ", "")
    exact_rows = [*name_index["exact"].get(normalized, []), *name_index["compact"].get(compacted, [])]
    exact_by_cik = {row[1]: row for row in exact_rows}
    if len(exact_by_cik) == 1:
        matched_name, cik, name_type = next(iter(exact_by_cik.values()))
        entity = entities[cik]
        return {
            "status": "resolved_automatic", "score": 1.0, "cik": cik,
            "sec_name": entity.name, "ticker": entity.ticker, "matched_name": matched_name,
            "matched_name_type": name_type,
            "reason": "Exact normalized or compact-name match against current and historical SEC filer names.",
        }
    if len(exact_by_cik) > 1:
        return {
            "status": "ambiguous", "score": 1.0,
            "candidates": [{
                "cik": cik, "sec_name": entities[cik].name, "ticker": entities[cik].ticker,
                "matched_name": row[0], "matched_name_type": row[2], "score": 1.0,
            } for cik, row in sorted(exact_by_cik.items())],
            "reason": "The ranking name exactly matches more than one SEC filer and requires analyst confirmation.",
        }

    pool: dict[tuple[str, str], tuple[str, str, str]] = {}
    for row in name_index["prefixes"].get(compacted[:4], []):
        pool[(row[1], base.normalize_name(row[0]))] = row
    first_token = normalized.split()[0] if normalized else ""
    for row in name_index["first_tokens"].get(first_token, []):
        pool[(row[1], base.normalize_name(row[0]))] = row
    if not pool:
        return {
            "status": "unresolved", "score": 0.0, "candidates": [],
            "reason": "No plausible current or historical SEC filer name shared the normalized prefix or first token.",
        }

    ranked = sorted(
        ((base.score_name(company, name), name, cik, name_type) for name, cik, name_type in pool.values()),
        key=lambda item: (-item[0], item[2], item[1]),
    )[:5]
    top_score, top_name, top_cik, top_type = ranked[0]
    second_score = next((score for score, _, cik, _ in ranked[1:] if cik != top_cik), 0.0)
    candidates = []
    seen: set[str] = set()
    for score, matched_name, cik, name_type in ranked:
        if score < candidate_threshold or cik in seen:
            continue
        seen.add(cik)
        entity = entities[cik]
        candidates.append({
            "cik": cik, "sec_name": entity.name, "ticker": entity.ticker,
            "matched_name": matched_name, "matched_name_type": name_type, "score": score,
        })
    entity = entities[top_cik]
    if top_score >= automatic_threshold and top_score - second_score >= 0.02:
        return {
            "status": "resolved_automatic", "score": top_score, "cik": top_cik,
            "sec_name": entity.name, "ticker": entity.ticker, "matched_name": top_name,
            "matched_name_type": top_type,
            "reason": "Conservative indexed fuzzy match against current and historical SEC filer names.",
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


base.build_name_index = build_name_index
base.resolve_entity = resolve_entity

if __name__ == "__main__":
    raise SystemExit(base.main())
