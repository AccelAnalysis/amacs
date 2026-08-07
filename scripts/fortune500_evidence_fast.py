#!/usr/bin/env python3
"""Run the Fortune 500 evidence reviewer with bounded canonical report retrieval."""
from __future__ import annotations

import sys
import urllib.error
import urllib.request

import fortune500_evidence as evidence


def canonical_report_urls(ticker: str, exchanges: str, years: list[int], base_url: str):
    ticker = ticker.upper().replace("/", "-")
    result = []
    for year in years:
        for exchange in evidence.exchange_codes(exchanges):
            result.append((year, f"{base_url}/HostedData/AnnualReports/PDF/{exchange}_{ticker}_{year}.pdf"))
    return result


def bounded_fetch_pdf(url: str, user_agent: str, max_bytes: int):
    request = urllib.request.Request(
        url,
        headers={"User-Agent": user_agent, "Accept": "application/pdf,*/*;q=0.8"},
    )
    try:
        with urllib.request.urlopen(request, timeout=7) as response:
            length = response.headers.get("Content-Length")
            if length and int(length) > max_bytes:
                return None
            data = response.read(max_bytes + 1)
    except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, ValueError):
        return None
    if len(data) > max_bytes or not data.startswith(b"%PDF"):
        return None
    return data


evidence.report_urls = canonical_report_urls
evidence.fetch_pdf = bounded_fetch_pdf

if __name__ == "__main__":
    raise SystemExit(evidence.main())
