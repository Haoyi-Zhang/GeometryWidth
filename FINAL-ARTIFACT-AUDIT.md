# Final artifact audit

## Reproduction commands

From the standalone artifact root:

```sh
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  python reproduce.py --output results
python report.py results
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

Optional conventional test-discovery entry:

```sh
pytest -q tests/test_retained_artifact.py
```

## Expected scientific closure

- 868 structured fixed-scene decisions: 703 recovery, 165 strict failure.
- 1,600 frozen stress decisions: 1,165 recovery, 435 failure.
- All 435 width-four stress failures bound to parent width, complete camera/normal/observation blocks, parent normals, calibration, and same-scene `Y=A X`.
- 40 frozen width-five strict witnesses.
- 35 base corruptions, two observation-domain boundary variants, and six stress corruptions rejected (43 targeted adversarial variants in total).
- 55 bibliography records, all body-cited and live-record resolved after three metadata corrections.
- 52 peer-reviewed papers or scholarly book; three preprint-only records.
- Static audit accepted for 14 Python source files.

## Independence boundary

The main checker, frozen-stress verifier, and report do not import the producer. The main checker uses different elimination and positivity paths. The fixed-seed stress generator does reuse shared exact-arithmetic and finite-witness routines; separation applies to its fixtures and verification path, not to generation logic. This is implementation separation, not an independent team, formal verification, or a mathematical proof by execution.

## Determinism boundary

Scientific JSON/CSV values are deterministic. Timing, peak RSS, local timestamps, and temporary-path fields are not required to be byte-identical. `clean_reproduction.json` records which retained files were compared after final archive extraction.

## Environment boundary

The science commands use Python 3.10+ standard-library modules and one process. No package installation, network, GPU, model API, external solver, private data, or scientific child worker is required. The manuscript build separately requires LaTeX, the supplied JMLR style, TikZ, and PGFPlots.

## Security boundary

Input parsing has explicit file, view, point, and rational-bit limits. The static source audit rejects dynamic evaluation and network/process imports in the retained scientific source set. This is not a security audit of Python, LaTeX, the host, or future modifications.
