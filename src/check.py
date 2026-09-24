"""Independent certificate checker, using integer elimination and principal minors.

This file imports no producer code. It checks finite rational claims, not the
universal theorems. Malformed or inconsistent evidence raises CertificateError.
"""
import json
from fractions import Fraction
from functools import reduce
from itertools import combinations, permutations, product
from math import gcd, lcm
from pathlib import Path

F = Fraction


class CertificateError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise CertificateError(message)


def matrix(value, rows=None, cols=None):
    need(isinstance(value, list) and value and all(isinstance(r, list) for r in value),
         'matrix must be a nonempty list of rows')
    n = len(value[0])
    need(n > 0 and all(len(r) == n for r in value), 'ragged matrix')
    need(rows is None or len(value) == rows, 'row count')
    need(cols is None or n == cols, 'column count')
    try:
        return [[F(x) for x in row] for row in value]
    except (ValueError, TypeError, ZeroDivisionError) as exc:
        raise CertificateError('invalid rational') from exc


def T(a):
    return list(map(list, zip(*a)))


def M(a, b):
    need(len(a[0]) == len(b), 'product dimensions')
    return [[sum(a[i][k]*b[k][j] for k in range(len(b)))
             for j in range(len(b[0]))] for i in range(len(a))]


def I(n):
    return [[F(i == j) for j in range(n)] for i in range(n)]


def minus(a, b):
    need(len(a) == len(b) and len(a[0]) == len(b[0]), 'difference dimensions')
    return [[x-y for x,y in zip(r,s)] for r,s in zip(a,b)]


def times(a, x):
    return [[x*v for v in row] for row in a]


def ip(a, b):
    return sum(x*y for r,s in zip(a,b) for x,y in zip(r,s))


def tr(a):
    return sum(a[i][i] for i in range(len(a)))


def determinant(a):
    n = len(a)
    need(n == len(a[0]), 'determinant square matrix')
    answer = F(0)
    for perm in permutations(range(n)):
        term = F((-1)**sum(perm[i] > perm[j] for i in range(n) for j in range(i+1,n)))
        for i, j in enumerate(perm):
            term *= a[i][j]
        answer += term
    return answer


def integer_rank(a):
    """Primitive integer row elimination; no division by rational pivots."""
    if not a:
        return 0
    work = []
    for row in a:
        row = [F(x) for x in row]
        den = lcm(*(x.denominator for x in row))
        work.append([int(x*den) for x in row])
    nr, nc, p = len(work), len(work[0]), 0
    for j in range(nc):
        k = next((k for k in range(p,nr) if work[k][j]), None)
        if k is None:
            continue
        work[k], work[p] = work[p], work[k]
        for k in range(p+1,nr):
            if work[k][j]:
                a0, b0 = work[p][j], work[k][j]
                row = [a0*x-b0*y for x,y in zip(work[k], work[p])]
                g = reduce(gcd, (abs(x) for x in row), 0) or 1
                work[k] = [x//g for x in row]
        p += 1
        if p == nr:
            break
    return p


def is_psd(a, strict=False):
    if a != T(a):
        return False
    n = len(a)
    for size in range(1,n+1):
        for ids in combinations(range(n),size):
            d = determinant([[a[i][j] for j in ids] for i in ids])
            if d < 0 or (strict and d == 0):
                return False
    return True


def inverse3(a):
    d = determinant(a)
    need(d != 0, 'singular inverse')
    b = []
    for i in range(3):
        row = []
        for j in range(3):
            ids = [k for k in range(3) if k != j]
            jds = [k for k in range(3) if k != i]
            minor = [[a[k][l] for l in jds] for k in ids]
            row.append((-1)**(i+j)*determinant(minor)/d)
        b.append(row)
    return b


def quadratic(n, a):
    return sum(n[i]*a[i][j]*n[j] for i in range(3) for j in range(3))


def adjugate(a):
    answer = []
    for i in range(3):
        row = []
        for j in range(3):
            ri = [k for k in range(3) if k != j]
            cj = [k for k in range(3) if k != i]
            row.append((-1)**(i+j)*determinant([[a[k][l] for l in cj] for k in ri]))
        answer.append(row)
    return answer


def add(a,b):
    return minus(a,times(b,-1))


def form_from_covariance(c,basis):
    diagonal = [-ip(c,adjugate(b)) for b in basis]
    return [[diagonal[i] if i==j else
             (-ip(c,adjugate(add(basis[i],basis[j])))-diagonal[i]-diagonal[j])/2
             for j in range(len(basis))] for i in range(len(basis))]


def check_scene_checks(payload):
    z0 = [[F(z) for z in row] for row in [[1,1,-1,-1],[1,-1,1,-1],[1,-1,-1,1]]]
    transforms = [I(3),add(I(3),[[F(1)]*3 for _ in range(3)]),
                  [[F(z) for z in row] for row in [[1,0,0],[0,2,0],[0,0,3]]],
                  [[F(z) for z in row] for row in [[1,1,0],[0,1,1],[0,0,1]]]]
    fixtures=payload['scene_fixtures']
    need(len(fixtures)==4,'scene fixture count')
    covariances=[]
    for fixture,transform in zip(fixtures,transforms):
        x=matrix(fixture['X'],3,4)
        c=matrix(fixture['covariance'],3,3)
        need(x==M(transform,z0) and c==M(x,T(x)), 'scene fixture definition')
        covariances.append(c)
    expected={(i,j) for i,d in enumerate(payload['subset_decisions'])
              if d['classification']!='outside_linear_span_assumption' for j in range(4)}
    seen=set(); failures=0
    for record in payload['scene_checks']:
        key=(record['subset_index'],record['fixture_index'])
        need(key in expected and key not in seen,'scene coverage')
        seen.add(key)
        decision=payload['subset_decisions'][key[0]]
        c=covariances[key[1]]
        basis=[matrix(b,3,3) for b in decision['kernel_basis']]
        form=form_from_covariance(c,basis)
        stored=[] if not basis else matrix(record['recovery_form'],len(basis),len(basis))
        need((not basis and record['recovery_form']==[]) or stored==form,'scene quadratic form')
        safe=not form or is_psd(form)
        need(type(record['recovers']) is bool and record['recovers']==safe,'scene recovery verdict')
        if safe:
            need('failure' not in record,'spurious failure witness')
            continue
        failures+=1
        failure=record['failure']
        weights=[F(w) for w in failure['weights']]
        need(len(weights)==len(basis),'negative form weights')
        d=[[sum(w*b[i][j] for w,b in zip(weights,basis)) for j in range(3)] for i in range(3)]
        need(d==matrix(failure['D'],3,3) and determinant(d)!=0,'scene kernel witness')
        h=times(adjugate(d),-1)
        need(h==matrix(failure['H'],3,3) and ip(c,h)<0,'scene negative adjugate')
        # A rational basis of each plane is enough: PSD and rank are preserved
        # by changing that plane basis. This does not reuse the producer frame.
        normals=[matrix(payload['normal_pool'],8,3)[i] for i in decision['subset']]
        for n in normals:
            pivot=next(i for i,z in enumerate(n) if z)
            rows=[]
            for j in range(3):
                if j==pivot: continue
                row=[F(0)]*3; row[j]=n[pivot]; row[pivot]=-n[j]; rows.append(row)
            restricted=M(M(rows,h),T(rows))
            need(is_psd(restricted) and integer_rank(restricted)<=1,'scene width-four feasibility')
        t=F(failure['t']); metric=matrix(failure['S'],3,3)
        need(t>0 and metric==minus(I(3),times(h,t)) and is_psd(metric,strict=True),'scene descent metric')
        energy=tr(M(c,inverse3(metric)))
        need(energy==F(failure['witness_energy'])<tr(c),'scene improvement')
        need(F(failure['strict_gap'])==tr(c)-energy,'scene improvement gap')
    need(seen==expected and len(seen)==868,'scene coverage incomplete')
    return {'scene_check_count':len(seen),'scene_recovers':len(seen)-failures,
            'scene_failure_witnesses':failures}


def classify_certificate(normals, record):
    normals = matrix(normals, cols=3)
    nr = integer_rank(normals)
    if nr != 3:
        need(record.get('normal_rank') == nr, 'excluded normal rank field')
        need(record['classification'] == 'outside_linear_span_assumption', 'missing normal-span exclusion')
        return
    need(record.get('normal_rank') == 3, 'normal rank field')
    evaluation = [[x*x,y*y,z*z,2*x*y,2*x*z,2*y*z] for x,y,z in normals]
    er = integer_rank(evaluation)
    need(record['evaluation_rank'] == er, 'evaluation rank field')
    basis = [matrix(b, 3, 3) for b in record['kernel_basis']]
    need(len(basis) == 6-er, 'kernel dimension')
    need(all(b == T(b) for b in basis), 'kernel symmetry')
    need(all(quadratic(n,b) == 0 for n in normals for b in basis), 'kernel equation')
    vecs = [[b[0][0],b[1][1],b[2][2],b[0][1],b[0][2],b[1][2]] for b in basis]
    need(integer_rank(vecs) == len(basis), 'kernel independence')
    # Distinct verification method: a tensor grid is degree-complete. We do not
    # use or trust the producer's coefficient expansion or its reported zero list.
    all_zero = True
    for weights in product(range(4), repeat=len(basis)):
        d = [[sum(w*b[i][j] for w,b in zip(weights,basis)) for j in range(3)] for i in range(3)]
        if determinant(d) != 0:
            all_zero = False
    label = 'safe_width_four' if all_zero else 'failure_possible_width_four'
    need(record['classification'] == label, 'determinant polynomial classification')
    # Coefficients are an optional producer diagnostic, not claim-critical data.
    # Check that a reported failure also carries a valid, nonzero witness.
    if not all_zero:
        d = matrix(record['invertible_witness'], 3, 3)
        need(d == T(d) and determinant(d) != 0, 'invertible witness')
        need(all(quadratic(n,d) == 0 for n in normals), 'witness not in kernel')
        h = matrix(record['negative_direction'], 3, 3)
        need(h == times(inverse3(d), -determinant(d)), 'negative adjugate')


def setup(case):
    x = matrix(case['X'], rows=3)
    need(integer_rank(x) == 3 and all(sum(r) == 0 for r in x), 'point centering/rank')
    cameras = [matrix(a,2,3) for a in case['cameras']]
    need(cameras, 'no cameras')
    need(all(M(a,T(a)) == I(2) for a in cameras), 'camera calibration')
    need(len(case['Y']) == len(cameras), 'observation block count')
    need(all(M(a,x) == matrix(y,2,len(x[0])) for a,y in zip(cameras,case['Y'])), 'observations')
    c = M(x,T(x))
    need(c == matrix(case['covariance'],3,3), 'covariance')
    s = matrix(case['S'],3,3)
    need(is_psd(s,strict=True), 'metric positive definiteness')
    q = case['width']
    need(isinstance(q,int) and q >= 3, 'width')
    slacks = [minus(I(2),M(M(a,s),T(a))) for a in cameras]
    need(all(is_psd(r) and integer_rank(r) <= q-3 for r in slacks), 'slack positivity/rank')
    cost = tr(M(c,inverse3(s)))
    need(F(case['true_energy']) == tr(c), 'true energy')
    return x,c,cameras,s,slacks,cost


def check_negative(case):
    x,c,cameras,s,slacks,cost = setup(case)
    normals = matrix(case['normals'], rows=len(cameras), cols=3)
    for n,a in zip(normals,cameras):
        need(sum(z*z for z in n) == 1 and M(a,T([n])) == [[0],[0]], 'normal/camera relation')
    h = matrix(case['H'],3,3)
    t = F(case['t'])
    need(h == T(h) and t > 0 and s == minus(I(3),times(h,t)), 'descent path')
    need(ip(c,h) < 0, 'strict descent derivative')
    need(cost < tr(c), 'no strict objective improvement')
    need(F(case['witness_energy']) == cost, 'witness energy')
    need(F(case['strict_gap']) == tr(c)-cost, 'witness gap')


def check_oracle(case):
    x,c,cameras,s,slacks,cost = setup(case)
    blocks = [matrix(b,2,2) for b in case['dual_blocks']]
    need(len(blocks) == len(cameras), 'dual block count')
    need(all(is_psd(b) for b in blocks), 'dual positivity')
    need(all(ip(b,r) == 0 for b,r in zip(blocks,slacks)), 'complementarity')
    dual_sum = [[sum(M(M(T(a),b),a)[i][j] for a,b in zip(cameras,blocks))
                 for j in range(3)] for i in range(3)]
    need(c == M(M(s,dual_sum),s), 'stationarity')
    need(F(case['minimum_energy']) == cost, 'minimum energy')
    need(F(case['gap']) == tr(c)-cost, 'oracle gap')
    g = M(M(T(x),inverse3(s)),x)
    need(g == matrix(case['gram'],len(x[0]),len(x[0])), 'optimized Gram')
    original = M(T(x),x)
    diff = minus(g,original)
    need(F(case['relative_gram_error_squared']) == ip(diff,diff)/ip(original,original), 'Gram error')
    u = F(case['u'])
    z0 = [[F(z) for z in row] for row in [[1,1,-1,-1],[1,-1,1,-1],[1,-1,-1,1]]]
    transform = [[F(i == j)+u for j in range(3)] for i in range(3)]
    need(x == M(transform,z0), 'family input definition')
    formula = 4*(1+3*u)**2+8 if u <= F(1,3) else F(8,3)*(2+3*u)**2
    need(cost == formula, 'closed-form formula')


def check_data_only(record):
    y = matrix(record['Y'])
    need(len(y)%2==0 and all(sum(r)==0 for r in y),'data-only blocks/centering')
    f, w = matrix(record['F'],cols=3), matrix(record['W'],rows=3)
    need(M(f,w) == y and integer_rank(f) == 3 and integer_rank(w) == 3, 'affine factorization')
    cols = record['selected_columns']
    rows = record['selected_rows']
    need(len(cols) == 3 and len(set(cols)) == 3 and all(isinstance(j,int) and 0<=j<len(y[0]) for j in cols), 'selected columns')
    need(f == [[row[j] for j in cols] for row in y], 'column ownership')
    need(len(rows) == 3 and len(set(rows)) == 3 and all(isinstance(i,int) and 0<=i<len(f) for i in rows), 'selected rows')
    need(integer_rank([f[i] for i in rows]) == 3, 'invertible selected block')
    s = matrix(record['baseline_metric'],3,3)
    need(is_psd(s,strict=True), 'baseline metric')
    blocks = [f[i:i+2] for i in range(0,len(f),2)]
    need(all(M(M(a,s),T(a)) == I(2) for a in blocks), 'metric upgrade equation')
    equations = []
    for a in blocks:
        for p,q in [(a[0],a[0]),(a[1],a[1]),(a[0],a[1])]:
            equations.append([p[0]*q[0],p[1]*q[1],p[2]*q[2],p[0]*q[1]+p[1]*q[0],p[0]*q[2]+p[2]*q[0],p[1]*q[2]+p[2]*q[1]])
    need(integer_rank(equations) == 6, 'metric uniqueness')
    gram = M(M(T(w),inverse3(s)),w)
    need(gram == matrix(record['recovered_gram']), 'recovered geometry')
    if 'reference_gram' in record:
        need(gram==matrix(record['reference_gram']),'reference geometry comparison')
    normals = matrix(record['raw_null_directions'],rows=len(blocks),cols=3)
    need(all(any(n) and M(a,T([n])) == [[0],[0]] for n,a in zip(normals,blocks)), 'raw normal directions')
    classification=record['width_four_classification']
    classify_certificate(normals,classification)
    cbar=M(M(inverse3(s),M(w,T(w))),inverse3(s))
    need(cbar==matrix(record['effective_covariance'],3,3),'affine effective covariance')
    basis=[matrix(b,3,3) for b in classification['kernel_basis']]
    form=form_from_covariance(cbar,basis)
    stored=[] if not basis else matrix(record['recovery_form'],len(basis),len(basis))
    need((not basis and record['recovery_form']==[]) or stored==form,'data-only recovery form')
    verdict = not form or is_psd(form)
    need(type(record['scene_recovers_width_four']) is bool and
         record['scene_recovers_width_four'] == verdict, 'data-only recovery verdict')
    if verdict:
        need('finite_failure_witness' not in record, 'spurious data-only failure witness')
    else:
        need('finite_failure_witness' in record, 'missing data-only finite failure witness')
        witness = record['finite_failure_witness']
        weights = [F(x) for x in witness['weights']]
        need(len(weights) == len(basis), 'data-only witness coefficient dimension')
        d = [[sum(weight * b[i][j] for weight, b in zip(weights, basis))
              for j in range(3)] for i in range(3)]
        need(d == matrix(witness['D'], 3, 3), 'data-only witness kernel matrix')
        need(determinant(d) != 0, 'data-only witness invertibility')
        h = times(adjugate(d), -1)
        need(h == matrix(witness['H'], 3, 3), 'data-only witness adjugate direction')
        need(ip(cbar, h) < 0, 'data-only witness descent trace')
        t = F(witness['t'])
        need(t > 0, 'data-only witness step')
        metric = minus(s, times(h, t))
        need(metric == matrix(witness['affine_metric'], 3, 3), 'data-only witness affine metric')
        need(is_psd(metric, strict=True), 'data-only witness metric positivity')
        stored_slacks = [matrix(x, 2, 2) for x in witness['slacks']]
        need(len(stored_slacks) == len(blocks), 'data-only witness slack coverage')
        for block, stored_slack in zip(blocks, stored_slacks):
            slack = minus(I(2), M(M(block, metric), T(block)))
            need(slack == stored_slack, 'data-only witness slack')
            need(is_psd(slack) and integer_rank(slack) <= 1, 'data-only witness slack rank')
        wwt = M(w, T(w))
        true_energy = tr(M(wwt, inverse3(s)))
        witness_energy = tr(M(wwt, inverse3(metric)))
        need(F(witness['true_energy']) == true_energy, 'data-only witness true energy')
        need(F(witness['witness_energy']) == witness_energy, 'data-only witness energy')
        need(F(witness['strict_gap']) == true_energy - witness_energy > 0,
             'data-only witness objective gap')
        competing_gram = M(M(T(w), inverse3(metric)), w)
        need(competing_gram == matrix(witness['competing_gram']), 'data-only competing Gram')
        need(competing_gram != gram, 'data-only competing geometry')
        need(witness['status'] == 'verified_finite_same_observations', 'data-only witness status')


def validate(payload):
    need(payload['model'] == 'complete-visibility-centered-orthographic', 'model identity')
    pool = matrix(payload['normal_pool'],8,3)
    fixed_pool=I(3)+matrix([['2/3','2/3','1/3'],['2/3','1/3','2/3'],
       ['1/3','2/3','2/3'],['2/3','-2/3','1/3'],['-2/3','1/3','2/3']])
    need(pool==fixed_pool, 'frozen normal pool')
    need(all(sum(x*x for x in n)==1 for n in pool), 'unit normal pool')
    expected = {ids for size in range(3,9) for ids in combinations(range(8),size)}
    seen = set()
    for record in payload['subset_decisions']:
        ids = tuple(record['subset'])
        need(ids in expected and ids not in seen, 'missing/duplicate/unexpected subset')
        seen.add(ids)
        classify_certificate([pool[i] for i in ids],record)
    need(seen == expected, 'incomplete subset coverage')
    family = payload['oracle_family']
    need([F(c['u']) for c in family] == [F(k,12) for k in range(49)], 'oracle grid completeness/order')
    coordinate_cameras=[matrix(a) for a in [[[1,0,0],[0,1,0]],[[0,1,0],[0,0,1]],[[0,0,1],[1,0,0]]]]
    for c in family:
        need([matrix(a) for a in c['cameras']]==coordinate_cameras,'coordinate camera definition')
        check_oracle(c)
    cases = payload['negative_cases']
    need([c['id'] for c in cases] == ['five-view-width-four','six-view-isotropic-width-five','coplanar-normal-boundary'], 'negative cases')
    for c in cases:
        check_negative(c)
    for name in ['special_safe_four','special_safe_five','cap_safe_six']:
        classify_certificate(payload[name]['normals'],payload[name])
        need(payload[name]['classification'] == 'safe_width_four', 'special safe classification')
    need(matrix(cases[0]['normals'])==pool[:5],'five-view fixture definition')
    safe_four=I(3)+matrix([['3/5','4/5',0]])
    safe_five=safe_four+matrix([['3/5',0,'4/5']])
    need(matrix(payload['special_safe_four']['normals'])==safe_four and
         matrix(payload['special_safe_five']['normals'])==safe_five,'special fixture definitions')
    cap=[]; r=F(1,10)
    for a,b in [(0,0),(r,0),(-r,0),(0,r),(0,-r),(r,r)]:
        a,b=F(a),F(b)
        den=1+a*a+b*b
        cap.append([2*a/den,2*b/den,(1-a*a-b*b)/den])
    need(matrix(cases[1]['normals'])==cap,'cap fixture definition')
    need(matrix(cases[2]['normals'])==matrix([[0,1,0],['3/5','4/5',0],['-3/5','4/5',0]]),
         'boundary normal definition')
    need(cases[1]['normals'] == payload['cap_safe_six']['normals'], 'cap fixture coupling')
    need(matrix(cases[1]['covariance']) == times(I(3),4), 'isotropic negative control')
    need(integer_rank(matrix(cases[2]['normals'])) == 2, 'coplanar boundary control')
    need(len(payload['data_only_certificates']) == 4, 'data-only count')
    paired = [family[0], family[12], cases[0], cases[1]]
    for record, source in zip(payload['data_only_certificates'], paired):
        expected_y = [row for block in source['Y'] for row in block]
        need(record['Y'] == expected_y, 'data-only fixture coverage and order')
        expected_gram = M(T(matrix(source['X'])), matrix(source['X']))
        need(matrix(record['reference_gram']) == expected_gram, 'data-only source coupling')
        check_data_only(record)
    scene_summary=check_scene_checks(payload)
    axes_basis=[[[F(z) for z in row] for row in values] for values in
       [[[0,1,0],[1,0,0],[0,0,0]],[[0,0,1],[0,0,0],[1,0,0]],[[0,0,0],[0,0,1],[0,1,0]]]]
    for record in family:
        form=form_from_covariance(matrix(record['covariance']),axes_basis)
        need(is_psd(form)==(F(record['u'])<=F(1,3)),'oracle recovery transition')
    # Producer coefficient diagnostics are deliberately not part of the trusted
    # certificate: the full determinant identity was checked independently.
    return {'accepted':True, **scene_summary, 'subset_count':len(seen), 'oracle_count':len(family),
            'negative_cases':len(cases), 'data_only_cases':4,
            'verification':'exact rational finite certificates; not a mechanized general proof'}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certificate',type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(validate(json.loads(args.certificate.read_text())),indent=2))
    except (CertificateError,KeyError,TypeError,IndexError,ValueError) as exc:
        raise SystemExit('REJECT: '+str(exc))
