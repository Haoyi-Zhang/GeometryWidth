"""Generate a frozen exact-rational stress set not used by the structured campaign.

This is implementation falsification on all retained generated cases.  It is not a
sample from a deployment population, a train/test estimate, or a proof of a
universal theorem.
"""

from __future__ import annotations

if not __debug__:
    raise RuntimeError("Optimized Python mode is intentionally unsupported for the retained audit.")

import argparse
import json
import random
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from exact import add, classify, det3, encode, eye, mat, mul, psd, recovery_form, scale, sub, trn
from produce import negative_case, negative_vector

SEED = 20260921
ARRANGEMENTS = 160
SCENES_PER_ARRANGEMENT = 10
WIDE_WITNESSES = 40
VIEW_COUNTS = tuple(range(3, 9))


def stereo(p: int, q: int) -> list[F]:
    d = 1 + p * p + q * q
    return [F(2 * p, d), F(2 * q, d), F(1 - p * p - q * q, d)]


def direction_key(n: list[F]) -> tuple[F, F, F]:
    """Canonicalize an unoriented rational direction."""
    for x in n:
        if x:
            return tuple(n if x > 0 else [-z for z in n])
    raise ValueError("zero direction")


def random_normal(rng: random.Random, used: set[tuple[F, F, F]]) -> list[F]:
    while True:
        p = rng.randint(-7, 7)
        q = rng.randint(-7, 7)
        n = stereo(p, q)
        key = direction_key(n)
        if key not in used:
            used.add(key)
            return n


def random_arrangement(rng: random.Random, m: int) -> list[list[F]]:
    while True:
        used: set[tuple[F, F, F]] = set()
        normals = [random_normal(rng, used) for _ in range(m)]
        if classify(normals)["classification"] != "outside_linear_span_assumption":
            return normals


def random_scene(rng: random.Random) -> list[list[F]]:
    z0 = mat([[1, 1, -1, -1], [1, -1, 1, -1], [1, -1, -1, 1]])
    while True:
        transform = mat([[rng.randint(-4, 4) for _ in range(3)] for _ in range(3)])
        if det3(transform):
            return mul(transform, z0)


def combine(coefficients: list[F], basis: list[list[list[F]]]) -> list[list[F]]:
    out = mat([[0, 0, 0], [0, 0, 0], [0, 0, 0]])
    for coefficient, matrix in zip(coefficients, basis):
        out = add(out, scale(matrix, coefficient))
    return out


def fixed_scene_record(normals: list[list[F]], classification: dict, x: list[list[F]], case_id: str) -> dict:
    covariance = mul(x, trn(x))
    basis = classification["kernel_basis"]
    form = recovery_form(covariance, basis)
    recovers = not form or psd(form)
    record = {
        "id": case_id,
        "X": x,
        "covariance": covariance,
        "recovery_form": form,
        "recovers": recovers,
    }
    if not recovers:
        coefficients = negative_vector(form)
        d = combine(coefficients, basis)
        from exact import adj3
        h = scale(adj3(d), -1)
        failure = negative_case(normals, h, 4, case_id + "-witness", x=x)
        failure["coefficients"] = coefficients
        failure["D"] = d
        record["failure"] = failure
    return record


def wide_record(normals: list[list[F]], rng: random.Random, case_id: str) -> dict:
    used = {direction_key(n) for n in normals}
    while True:
        v = random_normal(rng, used)
        dots = [sum(a * b for a, b in zip(n, v)) for n in normals]
        if all(d != 0 for d in dots):
            break
    beta = max(1 - d * d for d in dots)
    alpha = (beta + 1) / 2
    vv = mul([[x] for x in v], [v])
    h = sub(scale(eye(3), alpha), vv)
    case = negative_case(normals, h, 5, case_id)
    case["v"] = v
    case["beta"] = beta
    case["alpha"] = alpha
    return case


def generate(output: Path) -> dict:
    rng = random.Random(SEED)
    arrangements = []
    counts = {str(m): {"arrangements": 0, "scene_cases": 0, "recovers": 0, "fails": 0}
              for m in VIEW_COUNTS}
    for index in range(ARRANGEMENTS):
        m = VIEW_COUNTS[index % len(VIEW_COUNTS)]
        normals = random_arrangement(rng, m)
        classification = classify(normals)
        scenes = []
        for scene_index in range(SCENES_PER_ARRANGEMENT):
            record = fixed_scene_record(normals, classification, random_scene(rng),
                                        f"a{index:03d}-s{scene_index:02d}")
            scenes.append(record)
            bucket = counts[str(m)]
            bucket["scene_cases"] += 1
            bucket["recovers" if record["recovers"] else "fails"] += 1
        counts[str(m)]["arrangements"] += 1
        arrangements.append({
            "id": f"a{index:03d}",
            "view_count": m,
            "normals": normals,
            "classification": classification,
            "scenes": scenes,
        })

    wide_cases = []
    for index in range(WIDE_WITNESSES):
        arrangement = arrangements[(37 * index + 11) % len(arrangements)]
        wide_cases.append(wide_record(arrangement["normals"], rng, f"wide-{index:03d}"))

    result = {
        "design": {
            "seed": SEED,
            "arrangements": ARRANGEMENTS,
            "scenes_per_arrangement": SCENES_PER_ARRANGEMENT,
            "wide_witnesses": WIDE_WITNESSES,
            "view_counts": list(VIEW_COUNTS),
            "normal_generator": "rational stereographic map with integer parameters in [-7,7]",
            "scene_generator": "invertible 3x3 integer transform in [-4,4] applied to fixed centered four-point frame",
            "selection": "all generated in-domain arrangements and all generated scenes retained; no outcome filtering",
            "scope": "implementation stress test, not statistical generalization or deployment sampling",
        },
        "counts_by_view": counts,
        "arrangements": arrangements,
        "wide_cases": wide_cases,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(encode(result), indent=2) + "\n", encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results" / "holdout-stress.json")
    args = parser.parse_args()
    result = generate(args.output)
    summary = {
        "accepted": True,
        "seed": SEED,
        "arrangements": len(result["arrangements"]),
        "fixed_scene_cases": sum(len(x["scenes"]) for x in result["arrangements"]),
        "fixed_scene_failures": sum(not s["recovers"] for a in result["arrangements"] for s in a["scenes"]),
        "wide_strict_witnesses": len(result["wide_cases"]),
        "scope": result["design"]["scope"],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
