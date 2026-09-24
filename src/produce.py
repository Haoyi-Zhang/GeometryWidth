"""Produce bounded, deterministic rational certificates; no numerical optimizer."""
import csv
import json
from itertools import combinations
from pathlib import Path
from fractions import Fraction as Q
from exact import (mat, eye, zeros, trn, mul, add, sub, scale, trace, inner,
                   rank, inv, nullspace, rref, psd, frame, classify, encode,
                   adj3, recovery_form)

ROOT = Path(__file__).resolve().parents[1]


def negative_vector(h):
    """Return a rational v with v' h v < 0, using symmetric elimination."""
    n = len(h)
    for j in range(n):
        if h[j][j] < 0:
            return [Q(k == j) for k in range(n)]
    pivot = next((i for i in range(n) if h[i][i] > 0), None)
    if pivot is None:
        for i in range(n):
            for j in range(i + 1, n):
                if h[i][j]:
                    v = [Q(0)] * n
                    v[i], v[j] = Q(1), Q(-1 if h[i][j] > 0 else 1)
                    return v
        raise ValueError('no negative direction')
    ids = [j for j in range(n) if j != pivot]
    schur = [[h[i][j] - h[i][pivot] * h[pivot][j] / h[pivot][pivot]
              for j in ids] for i in ids]
    z = negative_vector(schur)
    v = [Q(0)] * n
    for j, x in zip(ids, z):
        v[j] = x
    v[pivot] = -sum(h[pivot][j] * v[j] for j in ids) / h[pivot][pivot]
    return v


def point_fixture(h):
    v = negative_vector(h)
    eta = Q(1)
    while True:
        cols = [v, [-x for x in v]]
        for j in range(3):
            e = [eta * (i == j) for i in range(3)]
            cols += [e, [-x for x in e]]
        x = trn(cols)
        c = mul(x, trn(x))
        if inner(c, h) < 0:
            return x
        eta /= 2


def negative_case(normals, h, q, case_id, x=None):
    cameras = [frame(n) for n in normals]
    x = point_fixture(h) if x is None else x
    c = mul(x, trn(x))
    delta = -inner(c, h)
    if delta <= 0:
        raise ValueError('covariance is not separated')
    hbound = max(sum(abs(z) for z in r) for r in h)
    t = min(Q(1) / (2 * hbound), delta / (4 * trace(c) * hbound ** 2))
    s = sub(eye(3), scale(h, t))
    cost = trace(mul(c, inv(s)))
    if not psd(s, strict=True):
        raise ArithmeticError('constructed metric is not positive definite')
    if not cost < trace(c):
        raise ArithmeticError('constructed witness does not strictly improve the objective')
    if not all(psd(sub(eye(2), mul(mul(a, s), trn(a)))) for a in cameras):
        raise ArithmeticError('constructed witness violates a calibration slack constraint')
    return {'id': case_id, 'width': q, 'normals': normals, 'cameras': cameras,
            'X': x, 'Y': [mul(a, x) for a in cameras], 'covariance': c,
            'H': h, 't': t, 'S': s, 'true_energy': trace(c),
            'witness_energy': cost, 'strict_gap': trace(c) - cost}


def oracle(u):
    """A full primal/dual certificate for each point on the symmetric family."""
    z0 = mat([[1, 1, -1, -1], [1, -1, 1, -1], [1, -1, -1, 1]])
    j = mat([[1] * 3] * 3)
    x = mul(add(eye(3), scale(j, u)), z0)
    c = mul(x, trn(x))
    a, b = 1 + 3*u, 2*u + 3*u*u
    cams = [mat([[1, 0, 0], [0, 1, 0]]), mat([[0, 1, 0], [0, 0, 1]]),
            mat([[0, 0, 1], [1, 0, 0]])]
    if u <= Q(1, 3):
        v = Q(0)
        s = eye(3)
        lam = mat([[2*(1+b), 4*b], [4*b, 2*(1+b)]])
        formula = 4*a*a + 8
    else:
        v = (a - 2) / (2*(a + 1))
        s = add(scale(eye(3), 1 - 2*v), scale(j, v))
        lam = scale(mat([[1, 1], [1, 1]]), 4*(a+1)**2/9)
        formula = Q(8, 3)*(a+1)**2
    y = [mul(cam, x) for cam in cams]
    gram = mul(mul(trn(x), inv(s)), x)
    true_gram = mul(trn(x), x)
    error2 = inner(sub(gram, true_gram), sub(gram, true_gram)) / inner(true_gram, true_gram)
    return {'u': u, 'width': 4, 'X': x, 'cameras': cams, 'Y': y,
            'covariance': c, 'S': s, 'dual_blocks': [lam]*3,
            'true_energy': trace(c), 'minimum_energy': formula,
            'gap': trace(c) - formula, 'gram': gram,
            'relative_gram_error_squared': error2}


def metric_row(p, q):
    return [p[0]*q[0], p[1]*q[1], p[2]*q[2],
            p[0]*q[1]+p[1]*q[0], p[0]*q[2]+p[2]*q[0], p[1]*q[2]+p[2]*q[1]]


def data_only(y):
    """Exact affine factorization and the classical metric upgrade from Y only."""
    if not y or len(y)%2 or any(len(r)!=len(y[0]) for r in y):
        raise ValueError('Y must have equally sized rows in two-row view blocks')
    if any(sum(r)!=0 for r in y) or rank(y)!=3:
        raise ValueError('Y must be centered and have exact rank three')
    cols = rref(y)[1][:3]
    f = [[row[j] for j in cols] for row in y]
    rows = rref(trn(f))[1][:3]
    w = mul(inv([f[i] for i in rows]), [y[i] for i in rows])
    equations = []
    raw_normals = []
    for i in range(0, len(f), 2):
        block = f[i:i+2]
        raw_normals.append(nullspace(block)[0])
        for p, q in [(0, 0), (1, 1), (0, 1)]:
            equations.append(metric_row(block[p], block[q]) + [Q(p == q)])
    rr, piv = rref(equations)
    if piv != list(range(6)):
        raise ValueError('the classical metric is not uniquely determined')
    from exact import sym
    s0 = sym([rr[i][-1] for i in range(6)])
    if not psd(s0, strict=True) or mul(f, w) != y:
        raise ValueError('no consistent positive definite classical metric')
    classification = classify(raw_normals)
    if classification['classification']=='outside_linear_span_assumption':
        raise ValueError('normal directions must span three dimensions for the width-four test')
    cbar = mul(mul(inv(s0), mul(w, trn(w))), inv(s0))
    form = recovery_form(cbar, classification['kernel_basis'])
    fixed_safe = not form or psd(form)
    result = {'effective_covariance': cbar, 'recovery_form': form,
              'scene_recovers_width_four': fixed_safe,
              'Y': y, 'selected_columns': cols, 'selected_rows': rows,
              'F': f, 'W': w, 'baseline_metric': s0,
              'recovered_gram': mul(mul(trn(w), inv(s0)), w),
              'raw_null_directions': raw_normals,
              'width_four_classification': classification}
    if not fixed_safe:
        basis = classification['kernel_basis']
        weights = negative_vector(form)
        d = zeros(3, 3)
        for coefficient, matrix in zip(weights, basis):
            d = add(d, scale(matrix, coefficient))
        h = scale(adj3(d), -1)
        if inner(cbar, h) >= 0:
            raise ArithmeticError('observation-only direction is not a strict descent direction')
        blocks = [f[i:i + 2] for i in range(0, len(f), 2)]
        wwt = mul(w, trn(w))
        true_energy = trace(mul(wwt, inv(s0)))
        t = Q(1)
        while True:
            metric = sub(s0, scale(h, t))
            if psd(metric, strict=True):
                slacks = [scale(mul(mul(block, h), trn(block)), t) for block in blocks]
                if all(psd(slack) and rank(slack) <= 1 for slack in slacks):
                    witness_energy = trace(mul(wwt, inv(metric)))
                    if witness_energy < true_energy:
                        break
            t /= 2
            if t.denominator.bit_length() > 4096:
                raise ArithmeticError('failed to find a finite rational observation-only witness')
        result['finite_failure_witness'] = {
            'weights': weights,
            'D': d,
            'H': h,
            't': t,
            'affine_metric': metric,
            'slacks': slacks,
            'true_energy': true_energy,
            'witness_energy': witness_energy,
            'strict_gap': true_energy - witness_energy,
            'competing_gram': mul(mul(trn(w), inv(metric)), w),
            'status': 'verified_finite_same_observations',
        }
    return result


def scene_certificates(pool, decisions):
    z0 = mat([[1,1,-1,-1],[1,-1,1,-1],[1,-1,-1,1]])
    transforms = [eye(3), add(eye(3),mat([[1]*3]*3)),
                  mat([[1,0,0],[0,2,0],[0,0,3]]),
                  mat([[1,1,0],[0,1,1],[0,0,1]])]
    fixtures = []
    for transform in transforms:
        x = mul(transform,z0)
        fixtures.append({'X':x,'covariance':mul(x,trn(x))})
    records = []
    for subset_index, decision in enumerate(decisions):
        if decision['classification'] == 'outside_linear_span_assumption':
            continue
        normals = [pool[i] for i in decision['subset']]
        basis = decision['kernel_basis']
        for fixture_index, fixture in enumerate(fixtures):
            form = recovery_form(fixture['covariance'], basis)
            safe = not form or psd(form)
            record = {'subset_index':subset_index,'fixture_index':fixture_index,
                      'recovery_form':form,'recovers':safe}
            if not safe:
                weights = negative_vector(form)
                d = [[sum(w*b[i][j] for w,b in zip(weights,basis))
                      for j in range(3)] for i in range(3)]
                h = scale(adj3(d),-1)
                witness = negative_case(normals,h,4,'scene-negative',fixture['X'])
                record['failure'] = {'weights':weights,'D':d,
                                    **{key:witness[key] for key in
                                       ['H','t','S','witness_energy','strict_gap']}}
            records.append(record)
    return fixtures,records


def generate(output=None):
    output = ROOT / 'results' if output is None else Path(output)
    output.mkdir(parents=True, exist_ok=True)
    axes = eye(3)
    pool = axes + mat([['2/3', '2/3', '1/3'], ['2/3', '1/3', '2/3'],
                       ['1/3', '2/3', '2/3'], ['2/3', '-2/3', '1/3'],
                       ['-2/3', '1/3', '2/3']])
    decisions = []
    counts = {}
    for size in range(3, 9):
        counts[size] = {}
        for inds in combinations(range(8), size):
            result = classify([pool[i] for i in inds])
            decisions.append({'subset': list(inds), **result})
            label = result['classification']
            counts[size][label] = counts[size].get(label, 0) + 1
    family = [oracle(Q(k, 12)) for k in range(49)]
    five = pool[:5]
    h = classify(five)['negative_direction']
    bad5 = negative_case(five, h, 4, 'five-view-width-four')
    # A six-view set inside a narrow cap: full quadratic rank, yet width five fails
    # for an isotropic tetrahedron. No near-singular point configuration is used.
    cap = []
    r = Q(1, 10)
    for p, q in [(0,0), (r,0), (-r,0), (0,r), (0,-r), (r,r)]:
        d = 1+p*p+q*q
        cap.append([2*p/d, 2*q/d, (1-p*p-q*q)/d])
    if classify(cap)['classification'] != 'safe_width_four':
        raise ArithmeticError('six-view cap fixture lost its width-four-safe classification')
    max_proj = max(1-n[2]*n[2] for n in cap)
    alpha = (max_proj + Q(1, 3))/2
    cap_h = sub(scale(eye(3), alpha), mat([[0,0,0],[0,0,0],[0,0,1]]))
    isotropic = mat([[1,1,-1,-1],[1,-1,1,-1],[1,-1,-1,1]])
    bad6 = negative_case(cap, cap_h, 5, 'six-view-isotropic-width-five', isotropic)
    special = axes + mat([['3/5','4/5',0], ['3/5',0,'4/5']])
    boundary_normals = mat([[0,1,0], ['3/5','4/5',0], ['-3/5','4/5',0]])
    boundary_h = mat([[1,0,0],[0,-1,0],[0,0,0]])
    boundary = negative_case(boundary_normals, boundary_h, 4, 'coplanar-normal-boundary')
    end_to_end = []
    for case in [family[0], family[12], bad5, bad6]:
        cert = data_only([r for block in case['Y'] for r in block])
        cert['reference_gram'] = mul(trn(case['X']), case['X'])
        if cert['recovered_gram'] != cert['reference_gram']:
            raise ArithmeticError('observation-only reconstruction changed the fixture Gram matrix')
        end_to_end.append(cert)
    fixtures, scene_checks = scene_certificates(pool, decisions)
    payload = {'scene_fixtures':fixtures, 'scene_checks':scene_checks,
               'model': 'complete-visibility-centered-orthographic',
               'normal_pool': pool, 'subset_decisions': decisions,
               'oracle_family': family, 'negative_cases': [bad5, bad6, boundary],
               'special_safe_four': {'normals': special[:4], **classify(special[:4])},
               'special_safe_five': {'normals': special, **classify(special)},
               'cap_safe_six': {'normals': cap, **classify(cap)},
               'data_only_certificates': end_to_end}
    (output/'certificates.json').write_text(json.dumps(encode(payload), indent=2)+'\n')
    with (output/'oracle.csv').open('w', newline='') as f:
        fields = ['u', 'true_energy', 'minimum_energy', 'gap', 'relative_gram_error_squared']
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in family:
            writer.writerow({k: str(row[k]) for k in fields})
    with (output/'oracle_plot.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['u', 'energy_ratio', 'relative_gram_error'])
        for row in family:
            writer.writerow([float(row['u']), float(row['minimum_energy']/row['true_energy']),
                             float(row['relative_gram_error_squared'])**0.5])
    summary = {'scene_check_count':len(scene_checks),
               'scene_recovers':sum(c['recovers'] for c in scene_checks),
               'scene_failure_witnesses':sum(not c['recovers'] for c in scene_checks),
               'scene_counts_by_fixture':[{'fixture_index':i,
                    'recovers':sum(r['recovers'] for r in scene_checks if r['fixture_index']==i),
                    'failures':sum(not r['recovers'] for r in scene_checks if r['fixture_index']==i)}
                     for i in range(4)],
               'subset_count': len(decisions), 'subset_counts': counts,
               'oracle_count': len(family), 'negative_case_count': 3,
               'data_only_count': len(end_to_end),
               'u_one': {k:family[12][k] for k in ['u','true_energy','minimum_energy','gap','relative_gram_error_squared']},
               'special_four_classification': classify(special[:4])['classification'],
               'special_five_classification': classify(special)['classification'],
               'cap_six_classification': classify(cap)['classification'],
               'cap_six_width_five_gap': bad6['strict_gap']}
    (output/'summary.json').write_text(json.dumps(encode(summary), indent=2)+'\n')
    return summary


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, default=ROOT/'results')
    args = ap.parse_args()
    print(json.dumps(encode(generate(args.output)), indent=2))
