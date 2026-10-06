"""Small rational linear algebra used by the certificate producer.

No floating-point rank decisions or external symbolic algebra are used.
"""
from fractions import Fraction as Q
from itertools import permutations, product


def mat(rows):
    return [[Q(x) for x in row] for row in rows]


def eye(n):
    return [[Q(i == j) for j in range(n)] for i in range(n)]


def zeros(n, m):
    return [[Q(0) for _ in range(m)] for _ in range(n)]


def trn(a):
    return [list(r) for r in zip(*a)]


def mul(a, b):
    if not a or not b or len(a[0]) != len(b):
        raise ValueError('incompatible matrix dimensions')
    return [[sum(x*y for x, y in zip(r, c)) for c in zip(*b)] for r in a]


def add(a, b):
    return [[x+y for x,y in zip(r,s)] for r,s in zip(a,b)]


def scale(a, s):
    return [[Q(s)*x for x in r] for r in a]


def sub(a,b):
    return add(a,scale(b,-1))


def trace(a):
    return sum(a[i][i] for i in range(len(a)))


def inner(a,b):
    return sum(x*y for r,s in zip(a,b) for x,y in zip(r,s))


def rref(a):
    # Integers are exact rational inputs too: int/int would otherwise introduce
    # binary floating point during pivot normalization.
    a=[[Q(x) for x in r] for r in a]
    if not a:
        return a, []
    nr,nc=len(a),len(a[0]); piv=[]; row=0
    for j in range(nc):
        p=next((i for i in range(row,nr) if a[i][j]),None)
        if p is None:
            continue
        a[row],a[p]=a[p],a[row]
        d=a[row][j]; a[row]=[x/d for x in a[row]]
        for i in range(nr):
            if i != row and a[i][j]:
                d=a[i][j]; a[i]=[x-d*y for x,y in zip(a[i],a[row])]
        piv.append(j); row+=1
        if row == nr:
            break
    return a,piv


def rank(a):
    return len(rref(a)[1])


def inv(a):
    n=len(a)
    b,p=rref([a[i]+eye(n)[i] for i in range(n)])
    if p[:n] != list(range(n)):
        raise ValueError('singular matrix')
    return [r[n:] for r in b]


def nullspace(a):
    b,p=rref(a); free=[j for j in range(len(a[0])) if j not in p]
    out=[]
    for j in free:
        v=[Q(0)]*len(a[0]); v[j]=Q(1)
        for i,k in enumerate(p):
            v[k]=-b[i][j]
        out.append(v)
    return out


def det3(a):
    return (a[0][0]*(a[1][1]*a[2][2]-a[1][2]*a[2][1])
          - a[0][1]*(a[1][0]*a[2][2]-a[1][2]*a[2][0])
          + a[0][2]*(a[1][0]*a[2][1]-a[1][1]*a[2][0]))


def adj3(a):
    out=zeros(3,3)
    for i in range(3):
        for j in range(3):
            rr=[r for r in range(3) if r!=j]; cc=[c for c in range(3) if c!=i]
            out[i][j]=(-1)**(i+j)*(a[rr[0]][cc[0]]*a[rr[1]][cc[1]]-a[rr[0]][cc[1]]*a[rr[1]][cc[0]])
    return out


def psd(a, strict=False):
    """Exact symmetric elimination; zero PSD pivots require a zero row."""
    if a != trn(a):
        return False
    # Keep the Schur complement exact even when callers supply plain integers.
    a=[[Q(x) for x in r] for r in a]; n=len(a)
    for k in range(n):
        p=a[k][k]
        if p < 0 or (strict and p == 0):
            return False
        if p == 0:
            if any(a[k][j] != 0 for j in range(k+1,n)):
                return False
            continue
        for i in range(k+1,n):
            for j in range(i,n):
                a[i][j]-=a[i][k]*a[k][j]/p
                a[j][i]=a[i][j]
    return True


def sym(v):
    a,b,c,d,e,f=v
    return [[a,d,e],[d,b,f],[e,f,c]]


def evaluation(normals):
    return [[x*x,y*y,z*z,2*x*y,2*x*z,2*y*z] for x,y,z in normals]


def frame(n):
    """Rational Householder frame with null direction n (unit rational)."""
    if sum(x*x for x in n)!=1:
        raise ValueError('normal is not exactly unit')
    if n == [Q(0),Q(0),Q(1)]:
        return eye(3)[:2]
    v=[n[0],n[1],n[2]-1]; d=sum(x*x for x in v)
    h=sub(eye(3),scale(mul([[x] for x in v],[v]),Q(2)/d))
    a=h[:2]
    if mul(a,trn(a)) != eye(2) or mul(a,[[x] for x in n]) != zeros(2,1):
        raise ArithmeticError('constructed frame failed exact orthonormality/null check')
    return a


def polynomial(basis):
    """Coefficients of det(sum t_j B_j), keys are sorted triples."""
    out={}; k=len(basis)
    for p in permutations(range(3)):
        sign=(-1)**sum(p[i]>p[j] for i in range(3) for j in range(i+1,3))
        for inds in product(range(k),repeat=3):
            key=tuple(sorted(inds))
            val=Q(sign)
            for r in range(3): val*=basis[inds[r]][r][p[r]]
            out[key]=out.get(key,Q(0))+val
    return {key:v for key,v in out.items() if v}


def classify(normals):
    normal_rank = rank(normals)
    if normal_rank != 3:
        return {'normal_rank': normal_rank, 'classification':'outside_linear_span_assumption'}
    e=evaluation(normals); bs=[sym(v) for v in nullspace(e)]
    coeff=polynomial(bs)
    result={'normal_rank':3,'evaluation_rank':rank(e),'kernel_basis':bs,
            'determinant_coefficients':{','.join(map(str,k)):v for k,v in coeff.items()},
            'classification':'safe_width_four' if not coeff else 'failure_possible_width_four'}
    if coeff:
        for t in product(range(4),repeat=len(bs)):
            d=zeros(3,3)
            for c,b in zip(t,bs): d=add(d,scale(b,c))
            if det3(d):
                result['invertible_witness']=d
                result['negative_direction']=scale(adj3(d),-1)
                break
        else:
            raise ArithmeticError('nonzero cubic vanished on degree-complete grid')
    return result


def encode(x):
    if isinstance(x,Q): return str(x)
    if isinstance(x,dict): return {str(k):encode(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)): return [encode(v) for v in x]
    return x


def recovery_form(covariance, basis):
    """Matrix of -tr(C adj(sum t_j D_j)); a fixed-covariance width-four test."""
    covariance = mat(covariance)
    basis = [mat(d) for d in basis]
    def q(d):
        return -inner(covariance, adj3(d))
    diagonal = [q(d) for d in basis]
    return [[diagonal[i] if i == j else
             (q(add(basis[i],basis[j]))-diagonal[i]-diagonal[j])/2
             for j in range(len(basis))] for i in range(len(basis))]
