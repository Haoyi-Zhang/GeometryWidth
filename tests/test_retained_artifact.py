"""Pytest-compatible entry points for the retained exact artifact.

Pytest is optional; the documented reproduction command uses only the standard
library.  These wrappers let reviewers who habitually run ``pytest`` exercise
exactly the same retained suites instead of seeing an empty collection.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tests"))

import check
from test_certificates import run_tests
from verify_holdout import mutation_tests, verify


def test_retained_certificate_suite() -> None:
    payload = json.loads((ROOT / "results" / "certificates.json").read_text(encoding="utf-8"))
    assert check.validate(payload)["accepted"]
    result = run_tests(payload)
    assert result["accepted"]
    assert result["targeted_mutation_count"] == 35
    assert result["targeted_mutations_rejected"] == 35


def test_retained_holdout_suite() -> None:
    payload = json.loads((ROOT / "results" / "holdout-stress.json").read_text(encoding="utf-8"))
    result = verify(payload)
    assert result["accepted"]
    mutations = mutation_tests(payload)
    assert len(mutations) == 3
    assert all(row["rejected"] for row in mutations)
