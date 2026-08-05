#!/usr/bin/env python3
"""Run the Fortune 500 reporting-entity and first-party evidence-depth pass."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from difflib import SequenceMatcher
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
COMMON_SUFFIXES = {
    "co", "company", "companies", "corp", "corporation", "inc", "incorporated",
    "group", "holdings", "holding", "limited", "ltd", "llc", "lp", "plc",
    "the", "de", "nv", "sa", "na",
}
GENERIC_ACTIVITY_TOKENS = {
    "and", "business", "businesses", "company", "companies", "customer", "customers",
    "including", "market", "markets", "operation", "operations", "product", "products",
    "provide", "provides", "service", "services", "segment", "segments", "solutions",
    "through", "with", "worldwide", "global", "primarily", "also", "our", "its",
}
ACTIVITY_SIGNAL = re.compile(
    r"\b(reportable segments?|operating segments?|business segments?|we operate|our businesses?|"
    r"we provide|we offer|we manufacture|we distribute|we sell|we underwrite|we generate|"
    r"we develop|we own|we manage|we transport|principal activities?|principal products?)\b",
    re.IGNORECASE,
)
SEGMENT_SIGNAL = re.compile(
    r"\b(?:reportable|operating|business) segments?\b.{0,80}?(?::|\b(?:are|include|consist of|comprised of)\b).{0,420}",
    re.IGNORECASE | re.DOTALL,
)
WORD = re.compile(r"[a-z0-9]+")
ANNUAL_FORMS_DEFAULT = ("10-K", "10-K/A", "20-F", "20-F/A", "40-F", "40-F/A")


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"}:
            self.skip_depth += 1
        elif tag.lower() in {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg"} and self.skip_depth:
            self.skip_depth -= 1
        elif tag.lower() in {"p", "div", "li", "tr", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def text(self) -> str:
        value = html.unescape(" ".join(self.parts))
        value = re.sub(r"[\t\r ]+", " ", value)
        value = re.sub(r"\n\s*\n+", "\n", value)
        return value.strip()


@dataclass(frozen=True)
class SecEntity:
    cik: str
    name: str
    ticker: str


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def request_bytes(url: str, user_agent: str, timeout: int = 60) -> bytes:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent, "Accept-Encoding": "identity"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def normalize_name(value: str) -> str:
    value = value.lower().replace("&", " and ")
    value = value.replace(".com", " com ")
    tokens = WORD.findall(value)
    while tokens and tokens[-1] in COMMON_SUFFIXES:
        tokens.pop()
    return " ".join(tokens)


def compact_name(value: str) -> str:
    return normalize_name(value).replace(" ", "")


def sec_entities(document: dict[str, Any]) -> list[SecEntity]:
    entities: list[SecEntity] = []
    for item in document.values():
        cik = str(item["cik_str"]).zfill(10)
        entities.append(SecEntity(cik=cik, name=item["title"], ticker=item.get("ticker", "")))
    return entities


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


def resolve_entity(
    company: str,
    entities: list[SecEntity],
    overrides: dict[str, Any],
    automatic_threshold: float,
    candidate_threshold: float,
) -> dict[str, Any]:
    override = overrides.get(company)
    if override:
        return {
            "status": "resolved_override",
            "score": 1.0,
            "cik": str(override["cik"]).zfill(10),
            "sec_name": override["sec_name"],
            "ticker": next((entity.ticker for entity in entities if entity.cik == str(override["cik"]).zfill(10)), ""),
            "reason": override["reason"],
        }

    ranked = sorted(
        ((score_name(company, entity.name), entity) for entity in entities),
        key=lambda item: (-item[0], item[1].cik),
    )[:3]
    top_score, top = ranked[0]
    second_score = ranked[1][0] if len(ranked) > 1 else 0.0
    candidates = [
        {"cik": entity.cik, "sec_name": entity.name, "ticker": entity.ticker, "score": score}
        for score, entity in ranked
        if score >= candidate_threshold
    ]
    if top_score >= automatic_threshold and top_score - second_score >= 0.02:
        return {
            "status": "resolved_automatic",
            "score": top_score,
            "cik": top.cik,
            "sec_name": top.name,
            "ticker": top.ticker,
            "reason": "Conservative normalized-name match to the SEC company-ticker registry.",
        }
    if candidates:
        return {
            "status": "candidate" if len(candidates) == 1 else "ambiguous",
            "score": top_score,
            "candidates": candidates,
            "reason": "The name similarity requires analyst confirmation before resolving the reporting entity.",
        }
    return {
        "status": "unresolved",
        "score": top_score,
        "candidates": [],
        "reason": "No sufficiently similar SEC registrant was found; the organization may be private, mutual, cooperative, foreign, or differently named.",
    }


def latest_annual_filing(submissions: dict[str, Any], accepted_forms: Iterable[str]) -> dict[str, Any] | None:
    accepted = set(accepted_forms)
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    for index, form in enumerate(forms):
        if form in accepted:
            return {
                "form": form,
                "filing_date": recent["filingDate"][index],
                "report_date": recent.get("reportDate", [""] * len(forms))[index],
                "accession_number": recent["accessionNumber"][index],
                "primary_document": recent["primaryDocument"][index],
            }
    return None


def filing_url(template: str, cik: str, filing: dict[str, Any]) -> str:
    return template.format(
        cik_int=int(cik),
        accession_compact=filing["accession_number"].replace("-", ""),
        primary_document=filing["primary_document"],
    )


def html_to_text(raw: bytes) -> str:
    parser = TextExtractor()
    parser.feed(raw.decode("utf-8", errors="replace"))
    return parser.text()


def business_section(text: str) -> str:
    lower = text.lower()
    starts = [position for marker in ("item 1. business", "item 1 — business", "item 1 - business") if (position := lower.find(marker)) >= 0]
    if not starts:
        return text[:250_000]
    start = min(starts)
    end_candidates = [
        position for marker in ("item 1a. risk factors", "item 1a — risk factors", "item 1a - risk factors")
        if (position := lower.find(marker, start + 1000)) >= 0
    ]
    end = min(end_candidates) if end_candidates else min(start + 300_000, len(text))
    return text[start:end]


def sentences(text: str) -> list[str]:
    chunks = re.split(r"(?<=[.!?])\s+|\n+", text)
    cleaned = []
    for chunk in chunks:
        value = re.sub(r"\s+", " ", chunk).strip(" -•\t")
        if 60 <= len(value) <= 900:
            cleaned.append(value)
    return cleaned


def extract_statements(text: str, limit: int = 14) -> tuple[list[str], list[str]]:
    section = business_section(text)
    selected: list[str] = []
    seen: set[str] = set()
    for sentence in sentences(section):
        if ACTIVITY_SIGNAL.search(sentence):
            key = sentence.lower()
            if key not in seen:
                seen.add(key)
                selected.append(sentence[:900])
        if len(selected) >= limit:
            break
    segment_statements = []
    for match in SEGMENT_SIGNAL.finditer(section):
        value = re.sub(r"\s+", " ", match.group(0)).strip()
        if value and value.lower() not in {item.lower() for item in segment_statements}:
            segment_statements.append(value[:700])
        if len(segment_statements) >= 5:
            break
    return selected, segment_statements


def concept_index() -> list[dict[str, Any]]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from amacs_io import load_dataset  # type: ignore

    concepts = [item for item in load_dataset("concepts", ROOT) if item["concept_type"] == "capability"]
    aliases = load_dataset("aliases", ROOT)
    by_concept: dict[str, list[str]] = {}
    for alias in aliases:
        by_concept.setdefault(alias["concept_id"], []).append(alias["alias"])
    return [
        {
            "concept_id": concept["concept_id"],
            "label": concept["preferred_label"],
            "terms": [concept["preferred_label"], *by_concept.get(concept["concept_id"], [])],
        }
        for concept in concepts
    ]


def term_tokens(value: str) -> set[str]:
    return {token for token in WORD.findall(value.lower()) if len(token) >= 4 and token not in GENERIC_ACTIVITY_TOKENS}


def map_statement(statement: str, concepts: list[dict[str, Any]], limit: int = 5) -> list[dict[str, Any]]:
    statement_tokens = term_tokens(statement)
    scored: list[tuple[float, dict[str, Any]]] = []
    for concept in concepts:
        best = 0.0
        matched: set[str] = set()
        for term in concept["terms"]:
            tokens = term_tokens(term)
            overlap = statement_tokens & tokens
            if not overlap:
                continue
            score = len(overlap) / max(len(tokens), 1)
            if len(overlap) >= 2:
                score += 0.15
            if score > best:
                best = score
                matched = overlap
        if best >= 0.65:
            scored.append((best, {
                "concept_id": concept["concept_id"],
                "label": concept["label"],
                "score": round(min(best, 1.0), 4),
                "confidence": "low",
                "matched_terms": sorted(matched),
            }))
    scored.sort(key=lambda item: (-item[0], item[1]["concept_id"]))
    return [item for _, item in scored[:limit]]


def recurring_phrases(statements: list[str], concepts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    concept_tokens = set().union(*(term_tokens(term) for concept in concepts for term in concept["terms"]))
    counts: Counter[str] = Counter()
    organizations: dict[str, set[int]] = {}
    for packed in statements:
        rank_text, statement = packed.split("\t", 1)
        rank = int(rank_text)
        tokens = [token for token in WORD.findall(statement.lower()) if len(token) >= 5 and token not in GENERIC_ACTIVITY_TOKENS]
        for size in (2, 3):
            for index in range(len(tokens) - size + 1):
                phrase_tokens = tokens[index:index + size]
                if all(token in concept_tokens for token in phrase_tokens):
                    continue
                phrase = " ".join(phrase_tokens)
                counts[phrase] += 1
                organizations.setdefault(phrase, set()).add(rank)
    return [
        {"phrase": phrase, "occurrences": count, "organization_count": len(organizations[phrase])}
        for phrase, count in counts.most_common(100)
        if len(organizations[phrase]) >= 3
    ][:50]


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", default="research/fortune-500-2026/manifest.json")
    parser.add_argument("--source-file", help="Optional local Fortune roster JSON.")
    parser.add_argument("--sec-tickers-file", help="Optional local SEC company-ticker JSON.")
    parser.add_argument("--sec-fixture-dir", help="Optional directory containing CIK##########.json and filing HTML fixtures.")
    parser.add_argument("--output", required=True)
    parser.add_argument("--fetch-filings", action="store_true")
    parser.add_argument("--max-filings", type=int, default=500)
    parser.add_argument("--request-delay", type=float, default=0.12)
    parser.add_argument("--allow-source-drift", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.is_absolute():
        manifest_path = ROOT / manifest_path
    manifest = read_json(manifest_path)
    parent_manifest = read_json(ROOT / manifest["parent_corpus_manifest"])
    user_agent = manifest["sec"]["user_agent"]

    if args.source_file:
        roster_raw = Path(args.source_file).read_bytes()
    else:
        roster_raw = request_bytes(parent_manifest["machine_readable_roster"]["data_url"], user_agent)
    roster_sha = hashlib.sha256(roster_raw).hexdigest()
    expected_sha = parent_manifest["machine_readable_roster"]["expected_sha256"]
    if roster_sha != expected_sha and not args.allow_source_drift:
        raise ValueError(f"Fortune roster source drift: expected {expected_sha}, found {roster_sha}")
    roster_document = json.loads(roster_raw)
    rows = [row for row in roster_document[parent_manifest["machine_readable_roster"]["data_path"]] if int(row["rank"]) <= manifest["expected_position_max"]]
    rows.sort(key=lambda row: int(row["rank"]))
    expected_positions = list(range(manifest["expected_position_min"], manifest["expected_position_max"] + 1))
    if len(rows) != manifest["expected_organization_count"] or [int(row["rank"]) for row in rows] != expected_positions:
        raise ValueError("Fortune 500 cohort must contain exactly one record for each rank 1 through 500")

    if args.sec_tickers_file:
        ticker_raw = Path(args.sec_tickers_file).read_bytes()
    else:
        ticker_raw = request_bytes(manifest["sec"]["company_tickers_url"], user_agent)
    ticker_sha = hashlib.sha256(ticker_raw).hexdigest()
    entities = sec_entities(json.loads(ticker_raw))
    overrides = read_json(ROOT / manifest["entity_overrides"])["overrides"]
    concepts = concept_index()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    fixture_dir = Path(args.sec_fixture_dir) if args.sec_fixture_dir else None

    records: list[dict[str, Any]] = []
    filing_fetch_count = 0
    packed_statements: list[str] = []
    status_counts: Counter[str] = Counter()
    filing_status_counts: Counter[str] = Counter()
    error_counts: Counter[str] = Counter()

    for row in rows:
        rank = int(row["rank"])
        resolution = resolve_entity(
            row["company"], entities, overrides,
            manifest["minimum_automatic_match_score"], manifest["minimum_candidate_match_score"],
        )
        status_counts[resolution["status"]] += 1
        record: dict[str, Any] = {
            "observation_id": f"fortune-500-2026-rank-{rank:03d}",
            "organization": {
                "ranking_name": row["company"],
                "headquarters": {"city": row["city"], "region": row["state"], "country": "US"},
            },
            "corpus": {"corpus_id": manifest["corpus_id"], "edition": manifest["edition"], "position": rank},
            "primary_activity_label": row["industry"],
            "entity_resolution": resolution,
            "first_party_evidence": [],
            "activity_statements": [],
            "segment_statements": [],
            "candidate_mappings": [],
            "review_status": "machine_triage",
            "not_for_profile_import": True,
        }
        if resolution["status"].startswith("resolved"):
            cik = resolution["cik"]
            try:
                if fixture_dir:
                    submissions_raw = (fixture_dir / f"CIK{cik}.json").read_bytes()
                else:
                    submissions_url = manifest["sec"]["submissions_url_template"].format(cik=cik)
                    submissions_raw = request_bytes(submissions_url, user_agent)
                    time.sleep(args.request_delay)
                submissions = json.loads(submissions_raw)
                record["organization"]["sec_reporting_entity"] = {
                    "name": submissions.get("name", resolution["sec_name"]),
                    "cik": cik,
                    "ticker": resolution.get("ticker", ""),
                    "sic": submissions.get("sic", ""),
                    "sic_description": submissions.get("sicDescription", ""),
                    "entity_type": submissions.get("entityType", ""),
                }
                annual = latest_annual_filing(submissions, manifest["sec"].get("accepted_annual_forms", ANNUAL_FORMS_DEFAULT))
                if annual:
                    annual["url"] = filing_url(manifest["sec"]["archive_url_template"], cik, annual)
                    record["latest_annual_filing"] = annual
                    filing_status_counts["located"] += 1
                    if args.fetch_filings and filing_fetch_count < args.max_filings:
                        try:
                            if fixture_dir:
                                filing_raw = (fixture_dir / annual["primary_document"]).read_bytes()
                            else:
                                filing_raw = request_bytes(annual["url"], user_agent, timeout=90)
                                time.sleep(args.request_delay)
                            filing_fetch_count += 1
                            filing_sha = hashlib.sha256(filing_raw).hexdigest()
                            statements, segment_statements = extract_statements(html_to_text(filing_raw))
                            record["first_party_evidence"].append({
                                "source_type": "regulatory_filing",
                                "title": f"{annual['form']} filed {annual['filing_date']}",
                                "url": annual["url"],
                                "publisher": record["organization"]["sec_reporting_entity"]["name"],
                                "content_sha256": filing_sha,
                            })
                            record["activity_statements"] = statements
                            record["segment_statements"] = segment_statements
                            mapping_by_id: dict[str, dict[str, Any]] = {}
                            for statement in [*segment_statements, *statements]:
                                for mapping in map_statement(statement, concepts):
                                    current = mapping_by_id.get(mapping["concept_id"])
                                    if current is None or mapping["score"] > current["score"]:
                                        mapping_by_id[mapping["concept_id"]] = mapping
                                packed_statements.append(f"{rank}\t{statement}")
                            record["candidate_mappings"] = sorted(mapping_by_id.values(), key=lambda item: (-item["score"], item["concept_id"]))[:20]
                            filing_status_counts["fetched"] += 1
                        except (OSError, ValueError, urllib.error.URLError) as exc:
                            filing_status_counts["fetch_error"] += 1
                            error_counts[type(exc).__name__] += 1
                            record["filing_error"] = str(exc)[:500]
                else:
                    filing_status_counts["not_located"] += 1
            except (OSError, ValueError, KeyError, urllib.error.URLError) as exc:
                error_counts[type(exc).__name__] += 1
                record["submissions_error"] = str(exc)[:500]
        records.append(record)

    resolved = sum(count for status, count in status_counts.items() if status.startswith("resolved"))
    resolution_rate = resolved / len(rows)
    if resolution_rate < manifest["minimum_sec_resolution_rate"]:
        raise ValueError(f"SEC resolution rate {resolution_rate:.3f} is below the governed minimum {manifest['minimum_sec_resolution_rate']:.3f}")

    records_path = output / "organization-evidence-observations.jsonl"
    records_path.write_text("".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in records), encoding="utf-8")
    gaps = recurring_phrases(packed_statements, concepts)
    write_json(output / "recurring-unmapped-language.json", {"phrases": gaps})
    summary = {
        "corpus_id": manifest["corpus_id"],
        "edition": manifest["edition"],
        "organization_count": len(rows),
        "rank_min": rows[0]["rank"],
        "rank_max": rows[-1]["rank"],
        "roster_source_sha256": roster_sha,
        "sec_ticker_source_sha256": ticker_sha,
        "entity_resolution_counts": dict(sorted(status_counts.items())),
        "sec_resolution_rate": round(resolution_rate, 4),
        "annual_filing_counts": dict(sorted(filing_status_counts.items())),
        "organizations_with_first_party_evidence": sum(bool(record["first_party_evidence"]) for record in records),
        "organizations_with_activity_statements": sum(bool(record["activity_statements"]) for record in records),
        "organizations_with_segment_statements": sum(bool(record["segment_statements"]) for record in records),
        "organizations_with_candidate_mappings": sum(bool(record["candidate_mappings"]) for record in records),
        "candidate_concept_ids_used": sorted({mapping["concept_id"] for record in records for mapping in record["candidate_mappings"]}),
        "recurring_unmapped_phrase_count": len(gaps),
        "error_counts": dict(sorted(error_counts.items())),
        "profile_assertions_created": 0,
        "generated_observation_semantics": "taxonomy_research_only",
    }
    write_json(output / "evidence-depth-summary.json", summary)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Fortune 500 evidence-depth analysis failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
