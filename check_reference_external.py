"""Validate the retained live-record reference audit produced during blind review.

The file records which primary or persistent record was resolved and how each
citation is used. This offline check validates the retained audit structure; it
does not make live network requests or establish priority.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXPECTED = 55
ALLOWED_PUBLICATION_STATUS = {
    "peer_reviewed_journal",
    "peer_reviewed_conference",
    "scholarly_book",
    "preprint_only",
}
ALLOWED_USE = {"contextual_boundary_citation", "direct_background_citation"}


class ExternalReferenceAuditError(ValueError):
    pass


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ExternalReferenceAuditError(message)


def validate(path: Path) -> dict:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        expected_fields = {
            "bib_key", "primary_record", "live_check_date", "record_status",
            "publication_status", "metadata_match_after_correction",
            "citation_use_assessment", "changes_made", "scope_note",
        }
        need(reader.fieldnames is not None and set(reader.fieldnames) == expected_fields,
             "unexpected external-reference audit columns")
    need(len(rows) == EXPECTED, "external-reference audit must contain 55 rows")
    keys = [row["bib_key"] for row in rows]
    need(len(set(keys)) == EXPECTED, "duplicate external-reference audit key")
    for row in rows:
        key = row["bib_key"]
        need(row["primary_record"].startswith("https://"), f"{key}: non-HTTPS record")
        need(row["live_check_date"] == "2026-09-21", f"{key}: stale live-check date")
        need(row["record_status"] ==
             "primary_or_persistent_record_resolved; title/authors/year/venue checked",
             f"{key}: incomplete record status")
        need(row["publication_status"] in ALLOWED_PUBLICATION_STATUS,
             f"{key}: unsupported publication status")
        need(row["metadata_match_after_correction"] == "yes",
             f"{key}: unresolved metadata mismatch")
        need(row["citation_use_assessment"] in ALLOWED_USE,
             f"{key}: missing citation-use assessment")
        need("not an exhaustive novelty or priority determination" in row["scope_note"],
             f"{key}: missing scope boundary")
    corrections = {row["bib_key"]: row["changes_made"] for row in rows
                   if row["changes_made"] != "none"}
    need(set(corrections) == {
        "roeder2021linear", "squires2023linear", "goldberg2008normalization"
    }, "unexpected metadata-correction set")
    counts = Counter(row["publication_status"] for row in rows)
    need(counts["preprint_only"] == 3, "unexpected preprint-only count")
    return {
        "accepted": True,
        "reference_count": EXPECTED,
        "metadata_matches_after_correction": EXPECTED,
        "publication_status_counts": dict(sorted(counts.items())),
        "preprint_only_count": counts["preprint_only"],
        "peer_reviewed_or_book_count": EXPECTED - counts["preprint_only"],
        "metadata_corrections": corrections,
        "scope": "retained live primary/persistent-record audit; not exhaustive novelty or priority review",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", nargs="?", type=Path,
                        default=ROOT / "reference_external_audit.csv")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = validate(args.audit)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                               encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
