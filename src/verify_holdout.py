"""Independently verify every case in the frozen exact-rational stress set."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from check import (I, M, T, add, check_negative, classify_certificate,
                   form_from_covariance, integer_rank, is_psd, matrix, need, times)

EXPECTED_SEED = 20260921
EXPECTED_ARRANGEMENTS = 160
EXPECTED_SCENES = 1600
EXPECTED_WIDE = 40


def verify(payload: dict) -> dict:
    design = payload["design"]
    need(design["seed"] == EXPECTED_SEED, "holdout seed")
    need(design["arrangements"] == EXPECTED_ARRANGEMENTS, "holdout arrangement count")
    need(design["scenes_per_arrangement"] == 10, "holdout scene count per arrangement")
    need(design["wide_witnesses"] == EXPECTED_WIDE, "holdout wide count")
    arrangements = payload["arrangements"]
    need(len(arrangements) == EXPECTED_ARRANGEMENTS, "holdout arrangement coverage")
    seen_ids = set()
    scene_count = failures = recoveries = 0
    by_view = {str(m): {"arrangements": 0, "scene_cases": 0, "recovers": 0, "fails": 0}
               for m in range(3, 9)}
    for index, arrangement in enumerate(arrangements):
        expected_id = f"a{index:03d}"
        need(arrangement["id"] == expected_id and expected_id not in seen_ids, "holdout arrangement order")
        seen_ids.add(expected_id)
        m = arrangement["view_count"]
        need(m == 3 + index % 6, "holdout view-count schedule")
        normals = matrix(arrangement["normals"], rows=m, cols=3)
        need(all(sum(x * x for x in n) == 1 for n in normals), "holdout unit normal")
        need(integer_rank(normals) == 3, "holdout normal span")
        classification = arrangement["classification"]
        classify_certificate(normals, classification)
        basis = [matrix(b, 3, 3) for b in classification["kernel_basis"]]
        scenes = arrangement["scenes"]
        need(len(scenes) == 10, "holdout scene coverage")
        by_view[str(m)]["arrangements"] += 1
        for scene_index, scene in enumerate(scenes):
            need(scene["id"] == f"a{index:03d}-s{scene_index:02d}", "holdout scene order")
            x = matrix(scene["X"], rows=3, cols=4)
            need(all(sum(row) == 0 for row in x) and integer_rank(x) == 3, "holdout scene domain")
            covariance = M(x, T(x))
            need(covariance == matrix(scene["covariance"], 3, 3), "holdout covariance")
            form = form_from_covariance(covariance, basis)
            stored = [] if not basis else matrix(scene["recovery_form"], len(basis), len(basis))
            need((not basis and scene["recovery_form"] == []) or stored == form, "holdout recovery form")
            verdict = not form or is_psd(form)
            need(type(scene["recovers"]) is bool and scene["recovers"] == verdict, "holdout verdict")
            if verdict:
                need("failure" not in scene, "spurious holdout failure witness")
                recoveries += 1
                by_view[str(m)]["recovers"] += 1
            else:
                need("failure" in scene, "missing holdout failure witness")
                failure = scene["failure"]
                need(matrix(failure["X"], 3, 4) == x, "holdout same-scene witness")
                need(matrix(failure["covariance"], 3, 3) == covariance, "holdout witness covariance")
                check_negative(failure)
                failures += 1
                by_view[str(m)]["fails"] += 1
            scene_count += 1
            by_view[str(m)]["scene_cases"] += 1
    need(scene_count == EXPECTED_SCENES, "holdout scene total")
    need(payload["counts_by_view"] == by_view, "holdout reported counts")

    wide = payload["wide_cases"]
    need(len(wide) == EXPECTED_WIDE, "holdout wide coverage")
    for index, case in enumerate(wide):
        need(case["id"] == f"wide-{index:03d}", "holdout wide order")
        need(case["width"] == 5, "holdout wide width")
        check_negative(case)
        normals = matrix(case["normals"])
        v = matrix([case["v"]], rows=1, cols=3)[0]
        beta = max(F(1) - sum(n[j] * v[j] for j in range(3)) ** 2 for n in normals)
        alpha = (beta + 1) / 2
        need(F(case["beta"]) == beta and F(case["alpha"]) == alpha, "holdout wide construction")
        h = add(times(I(3), alpha), times(M([[x] for x in v], [v]), -1))
        need(h == matrix(case["H"], 3, 3), "holdout wide direction")
        for camera in case["cameras"]:
            restriction = M(matrix(camera, 2, 3), M(h, T(matrix(camera, 2, 3))))
            need(is_psd(restriction, strict=True) and integer_rank(restriction) == 2,
                 "holdout wide strict plane restriction")

    return {
        "accepted": True,
        "arrangements": len(arrangements),
        "fixed_scene_cases": scene_count,
        "fixed_scene_recoveries": recoveries,
        "fixed_scene_failures": failures,
        "wide_strict_witnesses": len(wide),
        "counts_by_view": by_view,
        "scope": "independent exact verification of a frozen generated stress set; not statistical generalization",
    }


def mutation_tests(payload: dict) -> list[dict]:
    mutations = []
    cases = []
    p = copy.deepcopy(payload)
    p["arrangements"][0]["scenes"][0]["recovers"] = not p["arrangements"][0]["scenes"][0]["recovers"]
    cases.append(("flip-holdout-verdict", p))
    p = copy.deepcopy(payload)
    p["arrangements"].pop()
    cases.append(("drop-holdout-arrangement", p))
    p = copy.deepcopy(payload)
    p["wide_cases"][0]["strict_gap"] = "0"
    cases.append(("zero-wide-gap", p))
    for name, candidate in cases:
        try:
            verify(candidate)
        except Exception as exc:
            mutations.append({"mutation": name, "rejected": True, "reason": str(exc)})
        else:
            mutations.append({"mutation": name, "rejected": False, "reason": "accepted corrupted payload"})
    need(all(x["rejected"] for x in mutations), "holdout mutation suite")
    return mutations


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--mutation-test", action="store_true")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    result = verify(payload)
    if args.mutation_test:
        result["mutations"] = mutation_tests(payload)
        result["targeted_mutations_rejected"] = sum(x["rejected"] for x in result["mutations"])
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
