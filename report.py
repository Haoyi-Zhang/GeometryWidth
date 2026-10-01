"""Recompute every published count, oracle CSV value, and finite encoding statistic."""

if not __debug__:
    raise RuntimeError("Optimized Python mode is intentionally unsupported for the retained audit.")

import argparse
import csv
import json
import re
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from check import I, M, T, add, form_from_covariance, is_psd, matrix, times, validate
from check_references import validate as validate_references
from check_reference_external import validate as validate_external_references
from verify_holdout import verify as verify_holdout
from reviewer_audit import audit as reviewer_audit


class ReportAuditError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ReportAuditError(message)


def audit(directory):
    payload = json.loads((directory / "certificates.json").read_text())
    checked = validate(payload)
    summary = json.loads((directory / "summary.json").read_text())
    counts = {}
    for item in payload["subset_decisions"]:
        size = str(len(item["subset"]))
        counts.setdefault(size, {})
        label = item["classification"]
        counts[size][label] = counts[size].get(label, 0) + 1
    require(counts == summary["subset_counts"], "subset counts disagree")
    for key in ["scene_check_count", "scene_recovers", "scene_failure_witnesses",
                "subset_count", "oracle_count"]:
        require(summary[key] == checked[key], f"summary/checker mismatch: {key}")
    for index, row in enumerate(summary["scene_counts_by_fixture"]):
        records = [record for record in payload["scene_checks"]
                   if record["fixture_index"] == index]
        expected = {
            "fixture_index": index,
            "recovers": sum(record["recovers"] for record in records),
            "failures": sum(not record["recovers"] for record in records),
        }
        require(row == expected, f"fixture count mismatch: {index}")
    require(summary["negative_case_count"] == checked["negative_cases"],
            "negative-case count mismatch")
    require(summary["data_only_count"] == checked["data_only_cases"],
            "data-only count mismatch")
    require(summary["cap_six_width_five_gap"] == payload["negative_cases"][1]["strict_gap"],
            "cap witness gap mismatch")
    for key, name in [
        ("special_four_classification", "special_safe_four"),
        ("special_five_classification", "special_safe_five"),
        ("cap_six_classification", "cap_safe_six"),
    ]:
        require(summary[key] == payload[name]["classification"], f"classification mismatch: {name}")
    one = payload["oracle_family"][12]
    expected_one = {key: one[key] for key in
                    ["u", "true_energy", "minimum_energy", "gap", "relative_gram_error_squared"]}
    require(summary["u_one"] == expected_one, "u=1 summary mismatch")

    rows = list(csv.DictReader((directory / "oracle.csv").open(newline="")))
    plot = list(csv.DictReader((directory / "oracle_plot.csv").open(newline="")))
    require(len(rows) == len(plot) == 49, "oracle table length mismatch")
    for certificate, row, plotted in zip(payload["oracle_family"], rows, plot):
        for key, value in row.items():
            require(F(value) == F(certificate[key]), f"oracle exact CSV mismatch: {key}")
        u = F(certificate["u"])
        a = 1 + 3 * u
        expected_error = F(0) if u <= F(1, 3) else (a - 2) ** 2 * (a * a + 2) / (9 * (a ** 4 + 2))
        require(F(certificate["relative_gram_error_squared"]) == expected_error,
                "closed-form Gram error mismatch")
        require(float(plotted["u"]) == float(u), "plot u mismatch")
        require(float(plotted["energy_ratio"]) ==
                float(F(certificate["minimum_energy"]) / F(certificate["true_energy"])),
                "plot energy ratio mismatch")
        require(float(plotted["relative_gram_error"]) == float(expected_error) ** 0.5,
                "plot Gram error mismatch")

    tests = json.loads((directory / "tests.json").read_text())
    expected_test_values = {
        "targeted_mutation_count": 35,
        "targeted_mutations_rejected": 35,
        "data_only_domain_rejection_count": 2,
        "symmetric_matrix_cases": 729,
        "affine_gauge_cases": 3,
        "coordinate_correlation_cases": 519,
        "coordinate_correlation_recoveries": 483,
        "kernel_basis_congruence_cases": 12,
        "rank_deficient_width_five_witnesses": 2,
        "descent_bound_cases": 168,
        "uniform_nested_pairs": 3208,
        "uniform_recovery_implications": 382,
        "fixed_scene_nested_pairs": 12832,
        "fixed_scene_recovery_implications": 8485,
        "repeated_view_cases": 16,
        "width_monotonicity_witnesses": 2,
    }
    require(tests["accepted"], "finite test suite did not accept")
    for key, expected in expected_test_values.items():
        require(tests[key] == expected, f"finite-test count mismatch: {key}")
    require(len(tests["mutations"]) == 35 and all(row["rejected"] for row in tests["mutations"]),
            "targeted mutation details mismatch")
    expected_domain_rejections = [
        {
            "variant": "coplanar-complete-kernel",
            "rejected": True,
            "reason": "data-only domain requires raw normal directions of exact rank three",
        },
        {
            "variant": "coplanar-empty-kernel",
            "rejected": True,
            "reason": "data-only domain requires raw normal directions of exact rank three",
        },
    ]
    require(tests["data_only_domain_rejections"] == expected_domain_rejections,
            "data-only domain rejection details mismatch")
    require(tests["coplanar_boundary_conflict"] == {
        "effective_covariance": [["4", "0", "0"], ["0", "2", "0"], ["0", "0", "2"]],
        "apparent_recovery_form": [["2", "0", "0"], ["0", "4", "0"], ["0", "0", "0"]],
        "retained_true_energy": "8",
        "retained_witness_energy": "2014/255",
        "retained_strict_gap": "26/255",
    }, "coplanar observation-domain regression mismatch")
    require(tests["normal_span_boundary_checked"], "normal-span boundary was not checked")

    reference_audit = validate_references(ROOT / "reference_audit.csv")
    retained_reference_audit = json.loads((directory / "reference-audit.json").read_text())
    require(retained_reference_audit == reference_audit, "reference-audit output mismatch")
    external_reference_audit = validate_external_references(ROOT / "reference_external_audit.csv")
    source_audit = reviewer_audit(ROOT)
    retained_external_reference_audit = json.loads(
        (directory / "reference-external-audit.json").read_text())
    require(retained_external_reference_audit == external_reference_audit,
            "external-reference audit output mismatch")
    holdout_payload = json.loads((directory / "holdout-stress.json").read_text())
    holdout = verify_holdout(holdout_payload)
    retained_holdout = json.loads((directory / "holdout-verification.json").read_text())
    for key, value in holdout.items():
        require(retained_holdout.get(key) == value, f"holdout result mismatch: {key}")
    require(holdout["width_four_parent_bound_failures"] == 435,
            "holdout parent-bound failure count mismatch")
    require(retained_holdout.get("targeted_mutations_rejected") == 6,
            "holdout mutation count mismatch")
    expected_holdout_mutations = [
        "flip-holdout-verdict",
        "drop-holdout-arrangement",
        "zero-wide-gap",
        "drop-synchronized-failure-block",
        "cross-arrangement-failure-blocks",
        "width-five-fixed-scene-witness",
    ]
    require([row["mutation"] for row in retained_holdout.get("mutations", [])]
            == expected_holdout_mutations
            and all(row["rejected"] for row in retained_holdout["mutations"]),
            "holdout mutation details mismatch")
    holdout_reasons = {row["mutation"]: row["reason"]
                       for row in retained_holdout["mutations"]}
    require(holdout_reasons["drop-synchronized-failure-block"]
            == "holdout failure camera/normal/Y block coverage",
            "holdout synchronized-block mutation did not reach explicit binding gate")
    require(holdout_reasons["cross-arrangement-failure-blocks"]
            == "holdout failure normals must match parent arrangement",
            "holdout cross-arrangement mutation did not reach explicit parent gate")
    require(holdout_reasons["width-five-fixed-scene-witness"]
            == "holdout failure width must be exactly four",
            "holdout width mutation did not reach explicit width gate")

    affine = payload["data_only_certificates"][0]
    basis = [matrix(item) for item in affine["width_four_classification"]["kernel_basis"]]
    w = matrix(affine["W"])
    right = form_from_covariance(matrix(affine["effective_covariance"]), basis)
    wrong = form_from_covariance(M(w, T(w)), basis)
    require(right == times(I(3), 16) and is_psd(right), "correct affine covariance check failed")
    expected_wrong = add(times(I(3), 11), times([[F(1)] * 3 for _ in range(3)], -5))
    require(wrong == expected_wrong and not is_psd(wrong), "wrong-affine counterexample check failed")

    bits = []
    def visit(obj):
        if isinstance(obj, dict):
            for value in obj.values():
                visit(value)
        elif isinstance(obj, list):
            for value in obj:
                visit(value)
        elif type(obj) is int or (isinstance(obj, str) and re.fullmatch(r"-?\d+(?:/\d+)?", obj)):
            value = F(obj)
            bits.append((abs(value.numerator).bit_length(), value.denominator.bit_length()))
    visit(payload)
    require(bool(bits), "certificate contained no serialized rationals")

    result = {
        "accepted": True,
        "independently_reconciled_counts": checked,
        "oracle_csv_rows": len(rows),
        "plot_csv_rows": len(plot),
        "closed_form_gram_error_checked": True,
        "wrong_affine_covariance_counterexample_checked": True,
        **expected_test_values,
        "reference_count": reference_audit["reference_count"],
        "reference_audit_accepted": reference_audit["accepted"],
        "externally_resolved_reference_count": external_reference_audit["reference_count"],
        "peer_reviewed_or_book_references": external_reference_audit["peer_reviewed_or_book_count"],
        "preprint_only_references": external_reference_audit["preprint_only_count"],
        "static_source_audit_accepted": source_audit["accepted"],
        "python_source_files": source_audit["python_source_files"],
        "holdout_arrangements": holdout["arrangements"],
        "holdout_fixed_scene_cases": holdout["fixed_scene_cases"],
        "holdout_fixed_scene_recoveries": holdout["fixed_scene_recoveries"],
        "holdout_fixed_scene_failures": holdout["fixed_scene_failures"],
        "holdout_width_four_parent_bound_failures": holdout["width_four_parent_bound_failures"],
        "holdout_wide_strict_witnesses": holdout["wide_strict_witnesses"],
        "holdout_targeted_mutations_rejected": retained_holdout["targeted_mutations_rejected"],
        "total_targeted_adversarial_variants_rejected": (
            expected_test_values["targeted_mutations_rejected"]
            + expected_test_values["data_only_domain_rejection_count"]
            + retained_holdout["targeted_mutations_rejected"]
        ),
        "max_serialized_numerator_bits": max(x for x, _ in bits),
        "max_serialized_denominator_bits": max(y for _, y in bits),
        "serialized_rational_count": len(bits),
        "encoding_scope": "certificate payload values, not all transient arithmetic intermediates",
        "certificate_bytes": (directory / "certificates.json").stat().st_size,
    }
    (directory / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=ROOT / "results")
    arguments = parser.parse_args()
    print(json.dumps(audit(arguments.directory), indent=2))
