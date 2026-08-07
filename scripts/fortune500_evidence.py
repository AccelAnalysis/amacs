#!/usr/bin/env python3
"""Review first-party annual-report evidence for a bounded Fortune 500 batch."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import sys
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
WORD = re.compile(r"[a-z0-9]+")
GENERIC = {"and","the","company","companies","corporation","corp","inc","incorporated","group","holdings","holding","business","businesses","service","services","product","products","operations","operation","market","markets","global","international","com"}
ACTIVITY = re.compile(r"\b(?:we|our company|the company|our business|our businesses)\s+(?:is|are|provides?|offers?|manufactures?|sells?|distributes?|operates?|develops?|owns?|manages?|underwrites?|generates?|transports?|produces?|retails?|markets?|delivers?|designs?|builds?|finances?|insures?|licenses?)\b", re.I)
SEGMENT = re.compile(r"\b(?:reportable|operating|business) segments?\b", re.I)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in records), encoding="utf-8")


def tokens(value: str) -> set[str]:
    return {t for t in WORD.findall(value.lower()) if len(t) >= 3 and t not in GENERIC}


def load_concepts() -> list[dict[str, Any]]:
    sys.path.insert(0, str(ROOT / "scripts"))
    from amacs_io import load_dataset  # type: ignore
    concepts = load_dataset("concepts", ROOT)
    aliases = load_dataset("aliases", ROOT)
    alias_map: dict[str, list[str]] = defaultdict(list)
    for alias in aliases:
        alias_map[alias["concept_id"]].append(alias["alias"])
    return [{
        "concept_id": c["concept_id"], "label": c["preferred_label"],
        "terms": [c["preferred_label"], *alias_map.get(c["concept_id"], [])],
    } for c in concepts if c["concept_type"] == "capability"]


def exchange_codes(raw: str) -> list[str]:
    upper = (raw or "").upper()
    result: list[str] = []
    if "NASDAQ" in upper:
        result.append("NASDAQ")
    if "NYSE" in upper or "NEW YORK STOCK EXCHANGE" in upper:
        result.append("NYSE")
    if "AMEX" in upper or "NYSE AMERICAN" in upper:
        result.append("AMEX")
    return list(dict.fromkeys(result))


def report_urls(ticker: str, exchanges: str, years: list[int], base_url: str) -> list[tuple[int, str]]:
    ticker = ticker.upper().replace("/", "-")
    result: list[tuple[int, str]] = []
    for year in years:
        for exchange in exchange_codes(exchanges):
            result.append((year, f"{base_url}/HostedData/AnnualReports/PDF/{exchange}_{ticker}_{year}.pdf"))
            result.append((year, f"{base_url}/HostedData/AnnualReportArchive/{ticker[:1].lower()}/{exchange}_{ticker}_{year}.pdf"))
    return result


def fetch_pdf(url: str, user_agent: str, max_bytes: int) -> bytes | None:
    request = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "application/pdf,*/*;q=0.8"})
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > max_bytes:
                return None
            data = response.read(max_bytes + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return None
    if len(data) > max_bytes or not data.startswith(b"%PDF"):
        return None
    return data


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or " ").strip()


def organization_identified(text: str, company: str, resolved_name: str, ticker: str) -> bool:
    head = text[:60000].lower()
    company_tokens = tokens(company) | tokens(resolved_name)
    if company_tokens:
        hits = sum(1 for token in company_tokens if token in head)
        if hits >= min(2, len(company_tokens)):
            return True
    return bool(ticker and re.search(rf"\b{re.escape(ticker.lower())}\b", head))


def sentence_candidates(page_text: str) -> list[str]:
    normalized = clean_text(page_text)
    pieces = re.split(r"(?<=[.!?])\s+|\s*[•●▪]\s*", normalized)
    return [p.strip() for p in pieces if 35 <= len(p.strip()) <= 500]


def extract_evidence(reader: PdfReader, max_pages: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str, int]:
    activities: list[dict[str, Any]] = []
    segments: list[dict[str, Any]] = []
    seen_activity: set[str] = set()
    seen_segment: set[str] = set()
    identity_text_parts: list[str] = []
    pages_reviewed = min(len(reader.pages), max_pages)
    for page_index in range(pages_reviewed):
        try:
            text = reader.pages[page_index].extract_text() or ""
        except Exception:
            continue
        if page_index < 12:
            identity_text_parts.append(text)
        sentences = sentence_candidates(text)
        for sentence in sentences:
            if ACTIVITY.search(sentence) and sentence.casefold() not in seen_activity and len(activities) < 24:
                seen_activity.add(sentence.casefold())
                activities.append({
                    "statement": sentence, "method": "first_party_document_extract",
                    "entity_relationship": "direct", "evidence_locator": f"annual report page {page_index + 1}",
                })
            if SEGMENT.search(sentence):
                match = re.search(r"segments?\s*(?::|are|include|consist of|comprised of)\s*(.+)", sentence, re.I)
                if match:
                    tail = re.split(r"[.;]", match.group(1), maxsplit=1)[0]
                    for raw_name in re.split(r",|\band\b|;", tail):
                        name = clean_text(raw_name).strip(" :-–—()")
                        if 2 <= len(name) <= 100 and len(name.split()) <= 10 and name.casefold() not in seen_segment:
                            seen_segment.add(name.casefold())
                            segments.append({"name": name, "entity_relationship": "operating_segment", "confidence": "medium", "evidence_locator": f"annual report page {page_index + 1}"})
                            if len(segments) >= 20:
                                break
    return activities, segments, "\n".join(identity_text_parts), pages_reviewed


def lexical_mappings(activities: list[dict[str, Any]], concepts: list[dict[str, Any]], primary_ids: set[str]) -> list[dict[str, Any]]:
    evidence = " ".join(a["statement"] for a in activities)
    evidence_tokens = tokens(evidence)
    if not evidence_tokens:
        return []
    ranked: list[tuple[float, dict[str, Any]]] = []
    for concept in concepts:
        best = 0.0
        for term in concept["terms"]:
            term_tokens = tokens(term)
            if not term_tokens:
                continue
            overlap = evidence_tokens & term_tokens
            if not overlap:
                continue
            score = len(overlap) / len(term_tokens)
            if len(overlap) >= 2:
                score += 0.15
            best = max(best, min(score, 1.0))
        if best < 0.65:
            continue
        in_primary = concept["concept_id"] in primary_ids
        ranked.append((best + (0.1 if in_primary else 0.0), {
            "concept_id": concept["concept_id"], "mapping_status": "candidate",
            "confidence": "medium" if best >= 0.9 and in_primary else "low",
            "entity_relationship": "direct", "mapping_basis": "first_party_activity_statement",
            "rationale": "Company-authored annual-report activity language overlaps the governed AMACS concept label or aliases; the mapping remains a research candidate pending semantic review.",
        }))
    ranked.sort(key=lambda x: (-x[0], x[1]["concept_id"]))
    return [record for _, record in ranked[:12]]


def validate(record: dict[str, Any]) -> None:
    schema = read_json(ROOT / "schemas/organization-evidence-review.schema.json")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = list(validator.iter_errors(record))
    if errors:
        raise ValueError("; ".join(f"{'.'.join(map(str, e.path)) or '<record>'}: {e.message}" for e in errors[:10]))


def review_record(row: dict[str, Any], manifest: dict[str, Any], concepts: list[dict[str, Any]]) -> dict[str, Any]:
    rank = int(row["position"])
    resolution = row["identity_resolution"]
    memberships = ["fortune_1000", "fortune_500"] + (["fortune_100"] if rank <= 100 else [])
    base = {
        "review_id": f"AMACS-EVID-F500-2026-{rank:03d}",
        "organization": {"name": row["company"], "position": rank, "identity_id": row["identity_id"]},
        "corpus": {"corpus_id": manifest["corpus_id"], "edition": manifest["edition"], "memberships": memberships},
        "identity_resolution_status": resolution["status"], "evidence_disposition": "identity_unresolved",
        "evidence": [], "observed_segments": [], "observed_activity_statements": [], "candidate_mappings": [],
        "gap_candidates": ["identity_resolution"], "review_status": "machine_reviewed", "not_for_profile_import": True,
    }
    if resolution["status"] != "resolved":
        validate(base)
        return base

    base["organization"]["resolved_name"] = resolution["resolved_name"]
    base["organization"]["external_identifiers"] = {k: v for k, v in {"sec_cik": resolution.get("cik", ""), "ticker": resolution.get("ticker", ""), "sec_sic": resolution.get("sic", "")}.items() if v}
    evidence_cfg = manifest["annual_report_evidence"]
    pdf: bytes | None = None
    report_year: int | None = None
    report_url: str | None = None
    for year, url in report_urls(resolution.get("ticker", ""), resolution.get("exchanges", ""), evidence_cfg["candidate_report_years"], evidence_cfg["base_url"]):
        pdf = fetch_pdf(url, evidence_cfg["user_agent"], evidence_cfg["maximum_pdf_bytes"])
        if pdf:
            report_year, report_url = year, url
            break
    if not pdf or report_year is None or report_url is None:
        base["evidence_disposition"] = "annual_report_unavailable"
        base["gap_candidates"] = ["evidence_unavailable"]
        validate(base)
        return base

    try:
        reader = PdfReader(io.BytesIO(pdf), strict=False)
        activities, segments, identity_text, pages_reviewed = extract_evidence(reader, evidence_cfg["maximum_pages_reviewed"])
    except Exception:
        base["evidence_disposition"] = "evidence_error"
        base["gap_candidates"] = ["evidence_model"]
        validate(base)
        return base

    if not organization_identified(identity_text, row["company"], resolution["resolved_name"], resolution.get("ticker", "")):
        base["evidence_disposition"] = "evidence_error"
        base["gap_candidates"] = ["evidence_model"]
        validate(base)
        return base

    base["evidence"] = [{
        "source_type": "annual_report_mirror", "title": f"{resolution['resolved_name']} annual report {report_year}",
        "url": report_url, "authoring_organization": resolution["resolved_name"], "host": evidence_cfg["host"],
        "report_year": report_year, "accessed_at": manifest["observed_at"], "content_sha256": hashlib.sha256(pdf).hexdigest(),
        "pages_reviewed": pages_reviewed, "evidence_locator": "Company-authored annual report mirrored by AnnualReports.com; activity and segment locators are page-specific.",
    }]
    base["observed_activity_statements"] = activities
    base["observed_segments"] = segments
    mappings = lexical_mappings(activities, concepts, set(row["primary_candidate_concept_ids"]))
    base["candidate_mappings"] = mappings
    base["evidence_disposition"] = "annual_report_reviewed" if activities or segments else "annual_report_found_no_extractable_activity"
    gaps: list[str] = []
    mapped_ids = {m["concept_id"] for m in mappings}
    primary_ids = set(row["primary_candidate_concept_ids"])
    if activities and not mappings:
        gaps.append("capability_granularity")
    if mapped_ids and primary_ids and mapped_ids.isdisjoint(primary_ids):
        gaps.append("crosswalk_conflict")
    if not gaps:
        gaps.append("none")
    base["gap_candidates"] = gaps
    validate(base)
    return base


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--batch-index", type=int, required=True)
    parser.add_argument("--batch-count", type=int, default=10)
    args = parser.parse_args()
    if not (0 <= args.batch_index < args.batch_count):
        raise ValueError("batch index must be between zero and batch-count minus one")

    manifest = read_json(ROOT / "research/fortune-500-2026/manifest.json")
    concepts = load_concepts()
    rows = [r for r in read_jsonl(Path(args.input)) if (int(r["position"]) - 1) % args.batch_count == args.batch_index]
    reviews = [review_record(row, manifest, concepts) for row in rows]
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(output, reviews)
    counts: dict[str, int] = defaultdict(int)
    for review in reviews:
        counts[review["evidence_disposition"]] += 1
    print(json.dumps({"batch": args.batch_index, "records": len(reviews), "dispositions": dict(sorted(counts.items()))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"Fortune 500 evidence review failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
