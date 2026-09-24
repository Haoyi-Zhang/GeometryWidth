"""Targeted corruption tests and small exact algebra cross-checks."""

if not __debug__:
    raise RuntimeError("Optimized Python mode is intentionally unsupported for the retained audit.")

import copy
import json
import sys
from fractions import Fraction as F
from itertools import product
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
import check
import exact



class ExactTestFailure(AssertionError):
    """Raised when an exact finite test invariant fails."""


def require(condition, message):
    if not condition:
        raise ExactTestFailure(message)


def run_tests(payload):
    outcomes = []
    bad_index = next(i for i,r in enumerate(payload['subset_decisions'])
                     if r['classification'] == 'failure_possible_width_four')
    safe_index = next(i for i,r in enumerate(payload['subset_decisions'])
                      if r['classification'] == 'safe_width_four')
    out_index = next(i for i,r in enumerate(payload['subset_decisions'])
                     if r['classification'] == 'outside_linear_span_assumption')
    scene_bad=next(i for i,r in enumerate(payload['scene_checks']) if not r['recovers'])
    scene_good=next(i for i,r in enumerate(payload['scene_checks']) if r['recovers'] and r['recovery_form'])
    data_bad=next(i for i,r in enumerate(payload['data_only_certificates']) if not r['scene_recovers_width_four'])
    mutations = [
        ('repeated-data-only-fixture', lambda p: p['data_only_certificates'].__setitem__(1,copy.deepcopy(p['data_only_certificates'][0]))),
        ('reordered-data-only-fixtures', lambda p: p['data_only_certificates'].reverse()),
        ('wrong-excluded-normal-rank', lambda p: p['subset_decisions'][out_index].update(normal_rank=3)),
        ('missing-scene', lambda p: p['scene_checks'].pop()),
        ('wrong-scene-verdict', lambda p: p['scene_checks'][scene_bad].update(recovers=True)),
        ('wrong-scene-form', lambda p: p['scene_checks'][scene_good]['recovery_form'][0].__setitem__(0,'987')),
        ('wrong-scene-adjugate', lambda p: p['scene_checks'][scene_bad]['failure']['H'][0].__setitem__(0,'987')),
        ('wrong-scene-gap', lambda p: p['scene_checks'][scene_bad]['failure'].update(strict_gap='0')),
        ('wrong-affine-covariance', lambda p: p['data_only_certificates'][0]['effective_covariance'][0].__setitem__(0,'987')),
        ('wrong-data-only-verdict', lambda p: p['data_only_certificates'][data_bad].update(scene_recovers_width_four=True)),
        ('wrong-data-only-finite-gap', lambda p: p['data_only_certificates'][data_bad]['finite_failure_witness'].update(strict_gap='0')),
        ('missing-subset', lambda p: p['subset_decisions'].pop()),
        ('duplicate-subset', lambda p: p['subset_decisions'].append(copy.deepcopy(p['subset_decisions'][0]))),
        ('wrong-normal-rank', lambda p: p['subset_decisions'][bad_index].update(normal_rank=2)),
        ('wrong-evaluation-rank', lambda p: p['subset_decisions'][bad_index].update(evaluation_rank=6)),
        ('missing-kernel-vector', lambda p: p['subset_decisions'][bad_index]['kernel_basis'].pop()),
        ('false-safe-label', lambda p: p['subset_decisions'][bad_index].update(classification='safe_width_four')),
        ('false-failure-label', lambda p: p['subset_decisions'][safe_index].update(classification='failure_possible_width_four')),
        ('omit-span-exclusion', lambda p: p['subset_decisions'][out_index].update(classification='safe_width_four')),
        ('singular-failure-witness', lambda p: p['subset_decisions'][bad_index].update(invertible_witness=[[0]*3 for _ in range(3)])),
        ('wrong-adjugate-sign', lambda p: p['subset_decisions'][bad_index].update(negative_direction=[[0]*3 for _ in range(3)])),
        ('missing-family-point', lambda p: p['oracle_family'].pop()),
        ('wrong-minimum-energy', lambda p: p['oracle_family'][12].update(minimum_energy='72')),
        ('wrong-metric', lambda p: p['oracle_family'][12]['S'][0].__setitem__(0,'1')),
        ('negative-dual', lambda p: p['oracle_family'][12]['dual_blocks'][0][0].__setitem__(0,'-1')),
        ('changed-observation', lambda p: p['oracle_family'][12]['Y'][0][0].__setitem__(0,'987')),
        ('changed-point', lambda p: p['oracle_family'][12]['X'][0].__setitem__(0,'987')),
        ('rank-three-impostor', lambda p: p['oracle_family'][12].update(width=3)),
        ('wrong-gram-error', lambda p: p['oracle_family'][12].update(relative_gram_error_squared='0')),
        ('wrong-strict-gap', lambda p: p['negative_cases'][1].update(strict_gap='0')),
        ('too-narrow-failure-width', lambda p: p['negative_cases'][1].update(width=4)),
        ('wrong-covariance', lambda p: p['negative_cases'][1]['covariance'][0].__setitem__(0,'5')),
        ('wrong-factorization', lambda p: p['data_only_certificates'][0]['W'][0].__setitem__(0,'876')),
        ('wrong-baseline-metric', lambda p: p['data_only_certificates'][0]['baseline_metric'][0].__setitem__(0,'876')),
        ('wrong-recovered-gram', lambda p: p['data_only_certificates'][0]['recovered_gram'][0].__setitem__(0,'876')),
    ]
    for name, mutation in mutations:
        mutant = copy.deepcopy(payload)
        mutation(mutant)
        try:
            check.validate(mutant)
        except check.CertificateError as exc:
            outcomes.append({'mutation':name, 'rejected':True, 'reason':str(exc)})
        else:
            raise AssertionError('accepted mutation: '+name)
    # Exhaustive small symmetric matrices: producer elimination versus verifier
    # principal-minor test. This is algorithmic diversity, not external review.
    psd_cases = 0
    for values in product(range(-1,2), repeat=6):
        a = exact.sym([F(v) for v in values])
        require(exact.psd(a) == check.is_psd(a), 'exact test invariant failed near original line 79')
        require(exact.psd(a,strict=True) == check.is_psd(a,strict=True), 'exact test invariant failed near original line 80')
        require(exact.rank(a) == check.integer_rank(a), 'exact test invariant failed near original line 81')
        require(exact.det3(a) == check.determinant(a), 'exact test invariant failed near original line 82')
        if exact.det3(a):
            require(exact.inv(a) == check.inverse3(a), 'exact test invariant failed near original line 84')
        psd_cases += 1
    # Gauge invariance of the width-four classification under an invertible
    # rational change of affine coordinates; individual normals need not be unit.
    gauge = exact.mat([[1,2,0],[0,1,1],[1,0,1]])
    gauge_cases = 0
    for key in ['special_safe_four','special_safe_five','cap_safe_six']:
        normals = exact.mat(payload[key]['normals'])
        changed = exact.mul(normals,gauge)
        record = exact.classify(changed)
        check.classify_certificate(exact.encode(changed),exact.encode(record))
        require(record['classification'] == payload[key]['classification'], 'exact test invariant failed near original line 95')
        gauge_cases += 1
    # Exact coordinate-camera correlation criterion.  This is an exhaustive
    # small covariance family, not a statistical sample.  The off-diagonal
    # kernel basis is ordered as (12), (13), (23).
    coordinate_basis = [
        exact.sym([0,0,0,1,0,0]),
        exact.sym([0,0,0,0,1,0]),
        exact.sym([0,0,0,0,0,1]),
    ]
    correlation_cases = 0
    correlation_recoveries = 0
    for diagonals in product(range(1,4), repeat=3):
        for off_diagonals in product(range(-1,2), repeat=3):
            c11,c22,c33 = map(F, diagonals)
            c12,c13,c23 = map(F, off_diagonals)
            covariance = exact.mat([[c11,c12,c13],[c12,c22,c23],[c13,c23,c33]])
            if not exact.psd(covariance, strict=True):
                continue
            form = exact.recovery_form(covariance, coordinate_basis)
            expected = exact.mat([[c33,-c23,-c13],[-c23,c22,-c12],[-c13,-c12,c11]])
            determinant = (c11*c22*c33-c33*c12*c12-c22*c13*c13
                           -c11*c23*c23-2*c12*c13*c23)
            require(form == expected, 'exact test invariant failed near original line 118')
            require(exact.det3(form) == determinant, 'exact test invariant failed near original line 119')
            require(check.determinant(form) == determinant, 'exact test invariant failed near original line 120')
            require(exact.psd(form) == check.is_psd(form) == (determinant >= 0), 'exact test invariant failed near original line 121')
            # Positive rescaling of the scene covariance cannot change the verdict.
            require(exact.recovery_form(exact.scale(covariance,7),coordinate_basis) == exact.scale(form,7), 'exact test invariant failed near original line 123')
            correlation_cases += 1
            correlation_recoveries += determinant >= 0

    # Congruence under rational changes of the kernel basis.  Columns of T
    # contain the new basis vectors in old coordinates.
    transforms = [
        exact.mat([[1,0,0],[0,1,0],[0,0,1]]),
        exact.mat([[0,1,0],[1,0,0],[0,0,-1]]),
        exact.mat([[1,1,0],[0,1,1],[1,0,1]]),
        exact.mat([[1,0,0],[2,1,0],[0,-1,1]]),
    ]
    covariances = [
        exact.mat([[1,0,0],[0,1,0],[0,0,1]]),
        exact.mat([[2,1,0],[1,2,1],[0,1,2]]),
        exact.mat([[3,1,1],[1,3,-1],[1,-1,3]]),
    ]
    basis_congruence_cases = 0
    for covariance in covariances:
        require(exact.psd(covariance,strict=True), 'exact test invariant failed near original line 142')
        original = exact.recovery_form(covariance,coordinate_basis)
        for transform in transforms:
            require(exact.det3(transform) != 0, 'exact test invariant failed near original line 145')
            changed = []
            for j in range(3):
                matrix = exact.zeros(3,3)
                for i in range(3):
                    matrix = exact.add(matrix,exact.scale(coordinate_basis[i],transform[i][j]))
                changed.append(matrix)
            changed_form = exact.recovery_form(covariance,changed)
            expected_form = exact.mul(exact.trn(transform),exact.mul(original,transform))
            require(changed_form == expected_form, 'exact test invariant failed near original line 154')
            require(check.determinant(changed_form) == exact.det3(changed_form), 'exact test invariant failed near original line 155')
            require(exact.psd(changed_form) == check.is_psd(changed_form), 'exact test invariant failed near original line 156')
            require(exact.psd(changed_form) == exact.psd(original), 'exact test invariant failed near original line 157')
            basis_congruence_cases += 1

    # The no-finite-camera width-five construction does not depend on rank(A)=3.
    # A single coordinate camera, and two repetitions of it, both have stacked
    # rank two.  The explicit rational step has rank-two positive slacks and a
    # strictly smaller objective.
    a = exact.mat([[1,0,0],[0,1,0]])
    h = exact.mat([[F(1,2),0,0],[0,F(1,2),0],[0,0,F(-1,2)]])
    covariance = exact.mat([[F(1,4),0,0],[0,F(1,4),0],[0,0,F(5,4)]])
    step = F(1,4)
    metric = exact.sub(exact.eye(3),exact.scale(h,step))
    require(exact.psd(covariance,strict=True) and exact.psd(metric,strict=True), 'exact test invariant failed near original line 169')
    true_objective = exact.inner(covariance,exact.eye(3))
    competing_objective = exact.inner(covariance,exact.inv(metric))
    independent_objective = exact.inner(covariance,check.inverse3(metric))
    require(competing_objective == independent_objective < true_objective, 'exact test invariant failed near original line 173')
    rank_deficient_width_five_witnesses = 0
    for cameras in [[a],[a,a]]:
        require(exact.rank([row for camera in cameras for row in camera]) == 2, 'exact test invariant failed near original line 176')
        for camera in cameras:
            restriction = exact.mul(camera,exact.mul(h,exact.trn(camera)))
            slack = exact.sub(exact.eye(2),exact.mul(camera,exact.mul(metric,exact.trn(camera))))
            require(exact.psd(restriction,strict=True) and check.is_psd(restriction,strict=True), 'exact test invariant failed near original line 180')
            require(exact.rank(restriction) == check.integer_rank(restriction) == 2, 'exact test invariant failed near original line 181')
            require(slack == exact.scale(restriction,step), 'exact test invariant failed near original line 182')
        rank_deficient_width_five_witnesses += 1

    # Every retained strict witness also satisfies the quantitative finite-step
    # descent bound used in Proposition 13.  This covers the three named negative
    # controls and all 165 scene-specific failures, rather than a selected example.
    descent_bound_cases = 0
    for case in payload['negative_cases']:
        covariance = exact.mat(case['covariance'])
        direction = exact.mat(case['H'])
        step = F(case['t'])
        delta = -exact.inner(covariance, direction)
        gap = F(case['strict_gap'])
        require(delta > 0, 'named negative case is not a descent direction')
        require(gap >= step * delta / 2, 'named negative case violates descent bound')
        descent_bound_cases += 1
    fixtures = [exact.mat(item['covariance']) for item in payload['scene_fixtures']]
    for record in payload['scene_checks']:
        if record['recovers']:
            continue
        failure = record['failure']
        covariance = fixtures[record['fixture_index']]
        direction = exact.mat(failure['H'])
        step = F(failure['t'])
        delta = -exact.inner(covariance, direction)
        gap = F(failure['strict_gap'])
        require(delta > 0, 'scene failure is not a descent direction')
        require(gap >= step * delta / 2, 'scene failure violates descent bound')
        descent_bound_cases += 1

    # Exact finite monotonicity checks attack the quantifiers used in the paper:
    # a uniformly safe subset stays safe after adding views, and a recovered fixed
    # scene stays recovered for every retained superset.
    eligible = [
        (index, frozenset(record['subset']), record)
        for index, record in enumerate(payload['subset_decisions'])
        if record['classification'] != 'outside_linear_span_assumption'
    ]
    uniform_nested_pairs = 0
    uniform_recovery_implications = 0
    fixed_scene_nested_pairs = 0
    fixed_scene_recovery_implications = 0
    scene_lookup = {
        (record['subset_index'], record['fixture_index']): record['recovers']
        for record in payload['scene_checks']
    }
    for small_index, small_set, small in eligible:
        for large_index, large_set, large in eligible:
            if not small_set < large_set:
                continue
            uniform_nested_pairs += 1
            if small['classification'] == 'safe_width_four':
                uniform_recovery_implications += 1
                require(large['classification'] == 'safe_width_four',
                        'uniform recovery was lost after adding retained views')
            for fixture_index in range(len(fixtures)):
                fixed_scene_nested_pairs += 1
                if scene_lookup[(small_index, fixture_index)]:
                    fixed_scene_recovery_implications += 1
                    require(scene_lookup[(large_index, fixture_index)],
                            'fixed-scene recovery was lost after adding retained views')

    # Duplicating a view adds no metric constraint.  Test both uniform and
    # scene-specific decisions on safe and failing arrangements.
    repeated_view_cases = 0
    representative_indices = [
        next(i for i, r in enumerate(payload['subset_decisions'])
             if r['classification'] == 'safe_width_four' and len(r['subset']) == 4),
        next(i for i, r in enumerate(payload['subset_decisions'])
             if r['classification'] == 'failure_possible_width_four' and len(r['subset']) == 4),
        next(i for i, r in enumerate(payload['subset_decisions'])
             if r['classification'] == 'safe_width_four' and len(r['subset']) == 6),
        next(i for i, r in enumerate(payload['subset_decisions'])
             if r['classification'] == 'failure_possible_width_four' and len(r['subset']) == 5),
    ]
    pool = exact.mat(payload['normal_pool'])
    for subset_index in representative_indices:
        original = payload['subset_decisions'][subset_index]
        normals = [pool[i] for i in original['subset']]
        duplicated = exact.classify(normals + [normals[0]])
        require(duplicated['classification'] == original['classification'],
                'duplicating a view changed the uniform classification')
        require(duplicated.get('evaluation_rank') == original.get('evaluation_rank'),
                'duplicating a view changed evaluation rank')
        for fixture_index, covariance in enumerate(fixtures):
            basis = duplicated.get('kernel_basis', [])
            verdict = not basis or exact.psd(exact.recovery_form(covariance, basis))
            require(verdict == scene_lookup[(subset_index, fixture_index)],
                    'duplicating a view changed a fixed-scene verdict')
            repeated_view_cases += 1

    # Width monotonicity is witnessed in both strict directions used by the text.
    # The width-four failure has rank-one slacks and is therefore also feasible at
    # width five; the cap example has rank-two positive-definite slacks and cannot
    # be a width-four metric witness.
    width_monotonicity_witnesses = 0
    for case_index, expected_rank in [(0, 1), (1, 2)]:
        case = payload['negative_cases'][case_index]
        metric = exact.mat(case['S'])
        cameras = [exact.mat(camera) for camera in case['cameras']]
        ranks = []
        for camera in cameras:
            slack = exact.sub(exact.eye(2), exact.mul(camera, exact.mul(metric, exact.trn(camera))))
            require(exact.psd(slack), 'stored width-monotonicity slack is infeasible')
            ranks.append(exact.rank(slack))
        require(all(rank_value == expected_rank for rank_value in ranks),
                'unexpected calibration-slack rank in width monotonicity witness')
        width_monotonicity_witnesses += 1

    # The exact normal-span boundary is deliberately outside the width-four theorem.
    boundary = exact.mat(payload['negative_cases'][2]['normals'])
    from exact import evaluation, nullspace, sym, polynomial
    basis = [sym(v) for v in nullspace(evaluation(boundary))]
    require(not polynomial(basis) and exact.rank(boundary) == 2, 'exact test invariant failed near original line 189')
    return {'accepted':True, 'targeted_mutation_count':len(outcomes),
            'targeted_mutations_rejected':sum(r['rejected'] for r in outcomes),
            'symmetric_matrix_cases':psd_cases, 'affine_gauge_cases':gauge_cases,
            'coordinate_correlation_cases':correlation_cases,
            'coordinate_correlation_recoveries':correlation_recoveries,
            'kernel_basis_congruence_cases':basis_congruence_cases,
            'rank_deficient_width_five_witnesses':rank_deficient_width_five_witnesses,
            'descent_bound_cases':descent_bound_cases,
            'uniform_nested_pairs':uniform_nested_pairs,
            'uniform_recovery_implications':uniform_recovery_implications,
            'fixed_scene_nested_pairs':fixed_scene_nested_pairs,
            'fixed_scene_recovery_implications':fixed_scene_recovery_implications,
            'repeated_view_cases':repeated_view_cases,
            'width_monotonicity_witnesses':width_monotonicity_witnesses,
            'normal_span_boundary_checked':True, 'mutations':outcomes}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certificate',type=Path)
    args = parser.parse_args()
    print(json.dumps(run_tests(json.loads(args.certificate.read_text())),indent=2))
