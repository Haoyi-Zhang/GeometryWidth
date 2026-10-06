# View-consistency identifiability

Exact rational certificates for minimum-code-norm orthographic multiview learning. This is a finite synthetic theory artifact: it does not train a neural model, consume images, or report statistical accuracy. General statements are proved mathematically; the executable material checks exact finite consequences and certificate integrity.

## Model and result

A centered full-row-rank `3 x N` scene is observed completely by row-orthonormal two-row cameras with known point correspondence and unknown orientation. A width-`q` learner jointly chooses point codes and row-orthonormal linear decoders, interpolates every observation, and minimizes squared code norm. Recovery means equality of learned and true point Gram matrices.

At width four, under spanning camera normals, fixed-scene recovery is an exact positive-semidefiniteness test on a matrix of order at most three. Uniform recovery is a determinant identity on a kernel of symmetric matrices. At width five and above, a covariance cone replaces the rank-one criterion and no finite camera arrangement is uniformly recovering for every scene. `proofs/core.md` gives a self-contained proof outline and `claim_evidence_ledger.csv` maps claims to evidence.

The observation-only path uses only exact two-dimensional coordinates. A negative verdict includes a finite rational positive-definite metric, exact lower objective, and competing Gram for the same observations; a descent direction alone is never labeled a finite witness.

## Primary reproduction

Use Python 3.10 or later on Linux, without `-O` and without `PYTHONOPTIMIZE`. Only the standard library is required.

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python reproduce.py --output results
python report.py results
```

The first command regenerates and verifies:

- 868 structured fixed-scene certificates;
- 35 targeted base-certificate corruptions and two observation-domain boundary variants;
- 729 symmetric-matrix algebra cases, 41 plain-integer arithmetic regressions, 519 coordinate covariances, 12 kernel-basis congruences, all 168 structured descent bounds, nested-view and repeated-view checks, and rank-deficient width-five witnesses;
- the 55-row internal bibliography audit and the 55-row live-record audit;
- a frozen fixed-seed rational stress set with 1,600 width-four cases, 40 width-five witnesses, and six stress mutations;
- a static audit of the 15 supplied Python files, including the repository-material checker.

The second command independently reconciles the serialized counts, exact oracle CSV, plot CSV, Gram-error formula, wrong-affine-covariance counterexample, reference audits, frozen stress set, and static source audit.

Plain integer inputs are converted to exact fractions before division in row reduction, symmetric elimination, negative-vector construction, recovery-form polarization, and the scalar oracle. The 41 regressions include determinant-one invertible matrices, determinant-minus-one indefinite matrices, definite/semidefinite boundaries, and covariances just beyond the recovery threshold at eight integer scales through `2^256`, plus the integer-input oracle at `u=1`. They are arithmetic checks, not additional scene certificates or corruption counts.

`results/execution.json`, `results/pilot-replay.json`, and `resource_usage.csv` retain historical Linux measurements. They are not timings for a later rerun or for the integer-input extension. Reference-audit checks reconcile the archived records offline; they do not fetch or reread all cited papers.

The flat artifact repository also supplies `.github/workflows/scientific-checks.yml` for Ubuntu 24.04. It runs the finite reproduction, report, pilot, observation-only input and material-integrity gate under one 300-second deadline, with CPU and address-space limits, and uploads raw outputs even when a gate fails. This workflow definition is not evidence of a completed hosted run.

## Individual checks

```sh
python src/check.py results/certificates.json
python tests/test_certificates.py results/certificates.json
python pilot.py --output results/pilot-replay.json
python inspect_views.py inputs/observations.json \
  --output results/observations-audit.json
python src/verify_holdout.py results/holdout-stress.json --mutation-test
python src/reviewer_audit.py .
python check_references.py
python check_reference_external.py
```

Optional conventional test discovery:

```sh
pytest -q tests/test_retained_artifact.py
```

Pytest is only a reviewer convenience; the documented scientific path has no third-party Python dependency.

## Evidence retained

The structured campaign contains all 219 subsets of sizes three through eight from a fixed eight-normal pool. Two are retained outside the normal-span hypothesis. The 217 eligible arrangements crossed with four predetermined scenes produce 868 decisions: 703 recoveries and 165 strict finite failure witnesses.

The separately frozen input design uses 160 new spanning arrangements and ten new full-rank scenes per arrangement. Its generator reuses the artifact's exact-arithmetic and finite-witness routines, while `src/verify_holdout.py` follows a producer-independent verification path. Its 1,600 cases yield 1,165 recoveries and 435 failures; all 435 failure witnesses are now bound to the parent arrangement by exact width, normal, camera, observation, calibration, and `Y=A X` checks. Forty additional width-five instances retain strict witnesses. These counts test implementation breadth, not a probability distribution or model accuracy.

`results/oracle.csv` contains 49 exact rational values for the analytically solved family. At `u=1`, true energy is 72, optimum energy is `200/3`, and relative squared Frobenius Gram error is `4/129`. The transition at `u=1/3` is proved, not fitted.

The reference package contains exactly 55 body-cited records. The retained live-record audit classifies 52 as peer-reviewed papers or a scholarly book and three as preprint-only. It documents three metadata corrections. This is not an exhaustive novelty or priority review.

## Observation-only input

`inspect_views.py` accepts centered exact rational coordinates with two rows per view. Integers and rational strings are allowed; floating-point values are rejected. Size limits are 8 MiB, 512 views, 4096 points, and 256 bits per input numerator or denominator. Rank, factorization consistency, metric uniqueness, positivity, and exact rank-three span of the recovered raw normal directions are checked before any width-four recovery form is interpreted. A domain failure is not mislabeled as geometric nonrecovery.

The command reports `accepted: true` when the certificate is internally valid even if `scene_recovers_width_four` is false. Acceptance and recovery are distinct fields.

## Independence and limitations

The main checker, frozen-stress verifier, and report do not import the producer. The main checker uses separate integer elimination, cofactor determinant, and principal-minor paths. This is implementation separation, not independent human review or formal theorem verification.

There are no trained parameters, tuned thresholds, or train/test accuracy claims. Conventional statistical overfitting therefore does not apply. The frozen stress set addresses fixture-specific implementation risk only. The project does not establish missing-view, perspective-camera, arbitrary image-noise, neural-optimization, unseen-sample, real-image, semantic, or deployment performance.

See `ASSUMPTIONS-AND-NONCLAIMS.md`, `REVIEWER-RISK-REGISTER.md`, `FINAL-BLIND-REVIEW.md`, and `FINAL-ARTIFACT-AUDIT.md` for the final boundaries and audit record.

## Release status

The archive is for internal evaluation. Public release, license choice, authorship/contribution confirmation, repository upload, and venue-required declarations remain human decisions. No submission or upload has been performed.
