"""Replay the exact five/six-view and u=1 intake oracle."""

if not __debug__:
    raise RuntimeError("Optimized Python mode is intentionally unsupported for the retained audit.")

import argparse
import json
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))
from exact import *


class PilotError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise PilotError(message)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "results/pilot-replay.json")
    args = parser.parse_args()
    start_wall = time.perf_counter()
    start_cpu = time.process_time()
    axes = eye(3)
    normals = axes + mat([["2/3", "2/3", "1/3"], ["2/3", "1/3", "2/3"],
                          ["1/3", "2/3", "2/3"]])
    class5 = classify(normals[:5])
    class6 = classify(normals)
    direction = class5["negative_direction"]
    require(all(psd(mul(mul(frame(normal), direction), trn(frame(normal))))
                for normal in normals[:5]), "five-view direction violates plane positivity")

    u = Q(1)
    b = 2 * u + 3 * u * u
    a = 1 + 3 * u
    covariance = scale(add(eye(3), scale(mat([[1] * 3] * 3), b)), 4)
    v = (a - 2) / (2 * (a + 1))
    metric = add(scale(eye(3), 1 - 2 * v), scale(mat([[1] * 3] * 3), v))
    dual = scale(mat([[1, 1], [1, 1]]), 4 * (a + 1) ** 2 / 9)
    cameras = (mat([[1, 0, 0], [0, 1, 0]]),
               mat([[0, 1, 0], [0, 0, 1]]),
               mat([[0, 0, 1], [1, 0, 0]]))
    assembled = zeros(3, 3)
    for camera in cameras:
        slack = sub(eye(2), mul(mul(camera, metric), trn(camera)))
        require(psd(slack) and rank(slack) == 1 and inner(dual, slack) == 0,
                "oracle complementary-slackness check failed")
        assembled = add(assembled, mul(mul(trn(camera), dual), camera))
    require(covariance == mul(mul(metric, assembled), metric), "oracle stationarity check failed")
    cost = trace(mul(covariance, inv(metric)))
    require(cost == Q(200, 3) and trace(covariance) == 72, "oracle objective check failed")

    output = {
        "passed": True,
        "workers": 1,
        "five_camera_classification": class5,
        "six_camera_classification": class6,
        "oracle": {
            "u": u,
            "metric": metric,
            "true_energy": trace(covariance),
            "minimum_energy": cost,
            "gap": trace(covariance) - cost,
        },
        "wall_seconds": time.perf_counter() - start_wall,
        "cpu_seconds": time.process_time() - start_cpu,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(encode(output), indent=2) + "\n")
    print(json.dumps(encode(output), indent=2))


if __name__ == "__main__":
    main()
