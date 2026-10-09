# Model assumptions and scope

## Mathematical assumptions

- `X` is a centered real `3 x N` matrix of row rank three.
- Every view observes every point in the same known correspondence order.
- Each true camera block has two orthonormal rows; intrinsics and scale are already calibrated.
- Camera orientations are not supplied to the learner.
- The learner uses one latent code per observed point, row-orthonormal linear decoders, exact interpolation, and the squared latent-code norm objective.
- Recovery means equality of point Gram matrices, hence equality of the centered geometry up to an ambient isometry.
- The width-four fixed-scene and uniform criteria require camera normals to span three dimensions.
- The observation-only theorem assumes exact rational rank-three observations that satisfy a unique positive-definite classical metric upgrade.

## What is proved

The paper proves the metric/slack reduction, the width-three baseline, the width-four fixed-scene and uniform criteria, special and generic camera-count consequences, the width-five covariance-cone boundary, no-finite-arrangement impossibility, monotonicity, finite descent, stability bounds, an observation-only certificate, and the exact four-point family. It also proves a subsequential global-minimizer limit for a vanishing code penalty.

## What the artifact checks

The artifact checks exact finite instances, certificate serialization, producer-independent arithmetic recomputation, mutation rejection, the frozen rational stress set, bibliography closure, and source-code invariants. The stress generator reuses shared exact/producer routines with fixed-seed fixtures separated from the structured campaign. The general theorem arguments are supplied in the manuscript and `proofs/core.md`.

## Explicit non-claims

The project does not claim:

- missing-view or visibility-hypergraph identifiability;
- perspective, uncalibrated, unknown-scale, or unknown-correspondence recovery;
- robustness to arbitrary independently corrupted image coordinates;
- convergence of gradient descent or any other training algorithm to a global minimizer;
- neural-encoder, vision-language-model, semantic, real-image, deployment, or runtime performance;
- population generalization or a statistical accuracy estimate;
- that 1,600 frozen cases are representative of a camera distribution;
- formal proof-assistant verification, exhaustive fuzzing, or security certification.

## Interpreting “overfitting”

No parameter is learned from the finite campaign, no decision threshold is tuned, and no result is chosen by test-set performance. Conventional statistical overfitting therefore does not apply. A narrower implementation risk remains: code may accidentally depend on the original fixtures. The disjoint fixed-seed stress inputs and producer-independent verifier are designed to attack that risk; the generator is not a separately implemented algorithm. They do not turn the study into an empirical generalization evaluation.
