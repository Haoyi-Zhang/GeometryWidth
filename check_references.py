"""Validate the retained scholarly reference audit without network access.

This checks completeness and internal consistency of the archived audit. It does
not replace reading the linked primary or persistent records.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
MINIMUM_REFERENCES = 55
EXPECTED_REFERENCES = 55
RECENT_KEYS = {
    "benhamza2026identifiable",
    "cai2026vlm3",
    "cruickshank2026hypergraph",
    "nelson2026statistical",
}
ALLOWED_DOMAINS = {
    "arxiv.org",
    "doi.org",
    "ieeexplore.ieee.org",
    "jmlr.org",
    "link.springer.com",
    "proceedings.mlr.press",
    "proceedings.neurips.cc",
}
ALLOWED_ENTRY_TYPES = {"article", "book", "inproceedings"}
ALLOWED_STATUSES = {
    "primary_publisher_record_reverified_2026-09-21",
    "primary_proceedings_record_reverified_2026-09-21",
    "primary_preprint_record_reverified_2026-09-21",
    "persistent_identifier_record_reverified_2026-09-21",
    "current_primary_record_verified_2026-09-21",
}


class ReferenceAuditError(ValueError):
    """Raised when the retained reference audit is malformed or incomplete."""


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ReferenceAuditError(message)


def validate(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        required = {
            "bib_key", "entry_type", "title", "authors", "year", "venue",
            "primary_record", "record_type", "metadata_status",
            "manuscript_citation", "manuscript_role", "last_verified",
            "redistribution", "notes",
        }
        require(reader.fieldnames is not None, "missing CSV header")
        require(set(reader.fieldnames) == required, "unexpected reference-audit columns")
    require(len(rows) >= MINIMUM_REFERENCES, "fewer than 55 scholarly references")
    require(len(rows) == EXPECTED_REFERENCES, "retained audit must contain exactly 55 rows")
    keys = [row["bib_key"] for row in rows]
    require(len(set(keys)) == len(keys), "duplicate BibTeX key in reference audit")
    for index, row in enumerate(rows, start=2):
        prefix = f"row {index} ({row.get('bib_key', '<missing>')})"
        require(all(row[field].strip() for field in required), f"{prefix}: blank required field")
        require(row["entry_type"] in ALLOWED_ENTRY_TYPES, f"{prefix}: unsupported entry type")
        require(row["record_type"] == "scholarly publication", f"{prefix}: non-scholarly record")
        require(row["metadata_status"] in ALLOWED_STATUSES, f"{prefix}: unsupported status")
        require(row["last_verified"] == "2026-09-21", f"{prefix}: stale verification date")
        require(row["year"].isdigit() and 1900 <= int(row["year"]) <= 2026,
                f"{prefix}: invalid publication year")
        parsed = urlparse(row["primary_record"])
        require(parsed.scheme == "https" and bool(parsed.netloc), f"{prefix}: invalid HTTPS record")
        require(parsed.netloc.lower() in ALLOWED_DOMAINS,
                f"{prefix}: record is not on a retained scholarly/persistent domain")
        require(row["manuscript_citation"].startswith("main.tex:"),
                f"{prefix}: missing manuscript citation location")
        require(len(row["manuscript_role"].split()) >= 8,
                f"{prefix}: manuscript role is too vague")
    records = [row["primary_record"] for row in rows]
    require(len(set(records)) == len(records), "duplicate primary scholarly record")
    require(RECENT_KEYS <= set(keys), "missing one or more current 2026 neighboring works")
    for row in rows:
        if row["bib_key"] in RECENT_KEYS:
            require(row["metadata_status"] == "current_primary_record_verified_2026-09-21",
                    f"current work {row['bib_key']} lacks current primary-record status")
    status_counts = Counter(row["metadata_status"] for row in rows)
    domain_counts = Counter(urlparse(row["primary_record"]).netloc for row in rows)
    year_counts = Counter(row["year"] for row in rows)
    return {
        "accepted": True,
        "reference_count": len(rows),
        "minimum_required": MINIMUM_REFERENCES,
        "unique_bib_keys": len(set(keys)),
        "all_records_https": True,
        "all_records_scholarly": True,
        "all_records_on_retained_scholarly_domains": True,
        "unique_primary_records": len(set(records)),
        "all_rows_have_manuscript_roles": True,
        "current_2026_primary_records": sorted(RECENT_KEYS),
        "metadata_status_counts": dict(sorted(status_counts.items())),
        "record_domain_counts": dict(sorted(domain_counts.items())),
        "publication_year_counts": dict(sorted(year_counts.items())),
        "scope": "archived metadata and citation-use audit; not an online availability guarantee or exhaustive novelty review",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", nargs="?", type=Path, default=ROOT / "reference_audit.csv")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.audit)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
