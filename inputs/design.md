# Fixed and frozen rational input designs

## Structured campaign

The camera pool is the eight unit normals

`e1`, `e2`, `e3`, `(2,2,1)/3`, `(2,1,2)/3`, `(1,2,2)/3`, `(2,-2,1)/3`, and `(-2,1,2)/3`.

Include every subset of sizes three through eight in lexicographic index order. All 219 subsets remain in `certificates.json`. Exactly two three-view subsets have normal span below three and are retained as outside the width-four theorem. The other 217 arrangements are crossed with exactly four centered full-rank scenes.

Let `Z0` have rows `(1,1,-1,-1)`, `(1,-1,1,-1)`, and `(1,-1,-1,1)`. The four scenes are

- `Z0`;
- `(I+J)Z0`;
- `diag(1,2,3)Z0`;
- `[[1,1,0],[0,1,1],[0,0,1]]Z0`.

This produces 868 fixed-scene decisions. The pool, scenes, and crossing rule are fixed independently of their recovery verdicts. Every negative verdict retains an exact same-scene witness.

The exact four-point oracle uses `X(u)=(I+uJ)Z0` at the 49 prescribed values `u=k/12`, `k=0,...,48`, including the threshold `u=1/3` and points on both sides.

## Frozen stress campaign

`holdout_stress.py` uses the fixed integer seed `20260921` to construct a second rational input design that does not reuse the structured camera pool or four structured scenes. The input generator does reuse the shared exact-arithmetic routines in `src/exact.py` and the finite-witness constructor in `src/produce.py`; this campaign separates fixtures and the fixed seed, not producer implementation logic. The generator freezes:

- 160 spanning camera arrangements distributed across three through eight views;
- ten new centered full-rank rational scenes for each arrangement;
- 1,600 width-four fixed-scene decisions in total;
- 40 additional width-five strict-witness instances.

All generated cases are retained. No case is retried or discarded based on its recovery outcome. The serialized file retains every normal, camera, observation block, scene, covariance, metric, and objective field needed for verification. `src/verify_holdout.py` follows a producer-independent arithmetic path: it reconstructs the evaluation kernels, quadratic forms, verdicts, finite witnesses, and wide-model gaps; for every width-four failure it also requires exact width four, complete camera/normal/observation coverage of the parent arrangement, equality of the witness normals with the parent normals, calibrated cameras, and `Y=A X` for the same parent scene. Six serialized mutations are required to be rejected.

The word “holdout” denotes a frozen fixed-seed design whose inputs are separated from the original fixtures. It does not mean that its generator is implementation-independent, and it is not a statistical test set: no model is trained, no hyperparameter or threshold is selected, and no population distribution is asserted. The independent component is the arithmetic verification path, not the generation path.

## Special and boundary cases

The retained structured evidence also includes:

- special four- and five-view uniformly safe arrangements;
- a six-view width-four-safe arrangement that fails at width five;
- a five-view strict width-four failure;
- a normal-span-two boundary arrangement;
- four observation-only fixtures bound in a checked order to the oracle at `u=0`, the oracle at `u=1`, the five-view failure, and the six-view failure fixture.

Completeness and ordering checks prevent repeated legitimate fixtures from impersonating distinct cases. The only floating-point values in the artifact are plot conversions and execution measurements; all verdicts use exact rational arithmetic.
