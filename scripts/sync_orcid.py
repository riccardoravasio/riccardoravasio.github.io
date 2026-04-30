#!/usr/bin/env python3
"""Append new publications from ORCID to _data/publications.yml.

Detects works on the configured ORCID profile that aren't already in the
YAML (matched by normalised title) and appends them at the bottom under a
review marker. Existing entries are preserved verbatim — featured flags,
descriptions, tags, manual edits — never touched.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

import requests

ORCID_ID = os.environ.get("ORCID_ID", "0000-0003-1100-4683")
DATA_FILE = Path(__file__).resolve().parent.parent / "_data" / "publications.yml"
HEADERS = {"Accept": "application/json"}
TIMEOUT = 30


def fetch_works(orcid_id: str) -> dict:
    r = requests.get(
        f"https://pub.orcid.org/v3.0/{orcid_id}/works",
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def fetch_work_detail(orcid_id: str, put_code: int) -> dict:
    r = requests.get(
        f"https://pub.orcid.org/v3.0/{orcid_id}/work/{put_code}",
        headers=HEADERS,
        timeout=TIMEOUT,
    )
    r.raise_for_status()
    return r.json()


def normalize_title(t: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (t or "").lower())


def yaml_quote(s: str) -> str:
    if s is None:
        return '""'
    s = str(s).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"'


def parse_existing_titles(content: str) -> set[str]:
    titles: set[str] = set()
    for line in content.splitlines():
        m = re.match(r'^\s*title:\s*"?(.+?)"?\s*$', line)
        if m:
            titles.add(normalize_title(m.group(1)))
    return titles


def parse_work(detail: dict) -> dict:
    title = ((detail.get("title") or {}).get("title") or {}).get("value") or ""

    year = None
    pub_date = detail.get("publication-date") or {}
    y = (pub_date.get("year") or {}) if pub_date else {}
    if y.get("value"):
        try:
            year = int(y["value"])
        except (TypeError, ValueError):
            pass

    venue = (detail.get("journal-title") or {}).get("value") or ""

    doi_url = "#"
    for ext in ((detail.get("external-ids") or {}).get("external-id") or []):
        if ext.get("external-id-type") == "doi":
            v = (ext.get("external-id-url") or {}).get("value")
            doi_url = v or f"https://doi.org/{ext.get('external-id-value', '')}"
            break

    authors: list[str] = []
    for c in ((detail.get("contributors") or {}).get("contributor") or []):
        name = (c.get("credit-name") or {}).get("value")
        if name:
            authors.append(name)

    return {
        "year": year,
        "authors": ", ".join(authors),
        "title": title.strip(),
        "venue": venue,
        "url": doi_url,
    }


def format_entry(work: dict) -> str:
    lines = [
        f"- year: {work['year']}" if work.get("year") else "- year: ",
        f"  authors: {yaml_quote(work.get('authors', ''))}",
        f"  title: {yaml_quote(work.get('title', ''))}",
        f"  venue: {yaml_quote(work.get('venue', ''))}",
        f"  url: {yaml_quote(work.get('url') or '#')}",
        "  tags: []",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    if not DATA_FILE.exists():
        print(f"Data file not found: {DATA_FILE}", file=sys.stderr)
        return 1

    content = DATA_FILE.read_text()
    existing = parse_existing_titles(content)

    print(f"Fetching ORCID works for {ORCID_ID}...")
    works = fetch_works(ORCID_ID)

    new_pubs: list[dict] = []
    for group in (works.get("group") or []):
        summaries = group.get("work-summary") or []
        if not summaries:
            continue
        summary = summaries[0]
        put_code = summary.get("put-code")
        title = ((summary.get("title") or {}).get("title") or {}).get("value") or ""
        if not title or normalize_title(title) in existing:
            continue
        try:
            detail = fetch_work_detail(ORCID_ID, put_code)
        except requests.RequestException as e:
            print(f"Skipping put-code {put_code}: {e}", file=sys.stderr)
            continue
        parsed = parse_work(detail)
        if parsed["title"] and normalize_title(parsed["title"]) not in existing:
            new_pubs.append(parsed)
            existing.add(normalize_title(parsed["title"]))

    if not new_pubs:
        print("No new publications.")
        return 0

    new_pubs.sort(key=lambda p: p.get("year") or 0, reverse=True)

    addition = "\n# --- Added by ORCID sync (review and tag/sort/edit as needed) ---\n"
    addition += "\n".join(format_entry(p) for p in new_pubs)

    if not content.endswith("\n"):
        content += "\n"
    DATA_FILE.write_text(content + addition)

    print(f"Added {len(new_pubs)} new publications:")
    for p in new_pubs:
        print(f"  - {p.get('year')}: {p.get('title')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
