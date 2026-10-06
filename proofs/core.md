# Exact geometry selection by calibrated latent codes

These are mathematical proofs for real matrices. The accompanying programs check finite rational instances; they are not a proof assistant. No statement below concerns a learned image encoder, an optimization trajectory or independent image-coordinate noise.

## 1. Model and metric reduction

Let `X` be a centered, full-row-rank 3-by-N matrix, `C=XX^T>0`, and `A_i` a 2-by-3 matrix with `A_i A_i^T=I`. The complete observations are `Y_i=A_i X`, with known correspondences. Assume the vertical stack `A` has rank three. A width-q fit consists of `Z` of size q-by-N and row-orthonormal `B_i` of size 2-by-q, with `B_i Z=Y_i`. The objective is `||Z||_F^2`. Geometry recovery means `Z^T Z=X^T X` for every global minimizer. Translation is removed by centering; global isometries and higher-dimensional isometric embeddings are allowed.

Set `P=X^T C^{-1}X`. This is the orthogonal projection onto the row space of `X`. Because `Y_iP=Y_i`, replacing `Z` by `ZP` preserves fitting and decreases its squared norm by `||Z(I-P)||_F^2`. Thus every optimum has `Z=TX`, where `T=ZX^TC^{-1}`. From `B_iT=A_i` and rank(A)=3, `T` has rank three. Write `T=U S^{-1/2}`, with `U^TU=I` and `S=(T^TT)^{-1}>0`. Complete `U` by orthonormal columns `V`. Then `B_iU=A_iS^{1/2}` and, writing `L_i=B_iV`, calibration is precisely

`R_i(S) := I-A_iSA_i^T = L_iL_i^T >= 0`, with `rank R_i(S) <= q-3`.

Conversely every such S is realized by `Z=[S^{-1/2}X;0]` and `B_i=[A_iS^{1/2},L_i]`. A positive-semidefinite slack of rank at most q-3 has the required real factor. No rational square root is asserted or needed by the rational checker. Different views may use the same extra zero-code coordinates because their `L_i` blocks have no cross-view constraint.

The metric objective is `f_C(S)=tr(CS^{-1})`; the Gram matrix is `X^TS^{-1}X`. The least width realizing a particular metric is `3+max_i rank R_i(S)`. Full row rank of X implies its Gram equals the true Gram exactly when `S=I`.

The minimum exists. Let `G=sum_i A_i^TA_i>0`, `M=2m/lambda_min(G)`, and `c=lambda_min(C)>0`. Feasibility gives `tr(GS)<=2m`, hence `S<=MI`. On the nonempty sublevel set `f_C(S)<=tr C`, it gives `S>=(c/tr C)I`. All slack sign and rank conditions are closed there. This is a compact set, so the minimum is attained. The Hessian along a nonzero symmetric H is

`d^2 f_C(S+tH)/dt^2|_0 = 2 tr(C S^{-1}H S^{-1}H S^{-1}) > 0`.

The matrix after C is nonzero positive semidefinite, as seen by congruence from `(S^{-1/2}H S^{-1/2})^2`. Consequently f is strictly convex on the positive-definite cone, and its gradient at I is `-C`. This does not assert convexity of the width-four feasible set.

### Vanishing-penalty limit

The exact minimum-code-norm problem is the zero-penalty global-minimizer limit of a squared fitting objective. Let

`R(Z,B)=sum_i ||B_i Z-Y_i||_F^2`,  `B=(B_1,...,B_m)` with `B_i B_i^T=I_2`,

and let `r_q` be the minimum of `||Z||_F^2` over exact fits `R(Z,B)=0`. Exact fits exist by the true construction. The minimum exists as well: after comparison with that construction one may restrict to a bounded set of codes, while the product of decoder Stiefel manifolds is compact.

For `lambda>0`, let `(Z_lambda,B_lambda)` be any global minimizer of

`R(Z,B)+lambda ||Z||_F^2`.

A global minimizer exists because the decoder domain is compact and the penalty is coercive in Z. Comparison with a minimum-norm exact fit gives

`R(Z_lambda,B_lambda) <= lambda r_q` and `||Z_lambda||_F^2 <= r_q`.

Hence every sequence `lambda_k -> 0` has a subsequence on which both code and decoders converge. The first bound makes the limiting residual zero. Continuity of the norm gives a limiting squared code norm at most `r_q`, while exact feasibility gives the reverse inequality by definition of `r_q`; therefore the limit has norm exactly `r_q`. Every accumulation point of global penalized minimizers is consequently a global solution of the exact problem. This is a statement about global minimizers and does not assert that a training algorithm reaches them. If an exact fit has norm strictly below the norm of every true-Gram fit, then no penalized global-minimizer limit can have the true Gram matrix.

## 2. Classical width-three identification

At width three every slack vanishes. With at least two distinct normal directions, the observation stack has rank three, and any exact width-three fit has the same row space as X, even without norm minimization. A competing metric is `I-H`, where the quadratic polynomial `x^THx` vanishes on each observed image plane. A quadratic polynomial vanishing on `n^Tx=0` is divisible by that linear form: change coordinates and inspect coefficients independent of that coordinate. Three distinct unoriented normals therefore force three distinct linear divisors of a polynomial of degree two. It must be zero, so H=0.

For two distinct planes the homogeneous metric ambiguity is the one-dimensional space of scalar multiples of `(n_1^Tx)(n_2^Tx)`. For one plane it is the three-dimensional space `(n^Tx)(v^Tx)`. Small multiples preserve positive definiteness of I-H. The one-view claim describes these linear metric equations, not recovery of an unobserved depth from a rank-two observation stack.

## 3. The exact width-four criterion

From here, assume the camera normals `n_i` span R^3. Their normalization and individual signs do not affect the homogeneous kernel

`K = {D in Sym(3): n_i^T D n_i=0 for all i}`.

Represent a symmetric matrix by its three diagonal and three off-diagonal entries. The evaluation matrix has rows `(nx^2,ny^2,nz^2,2nxny,2nxnz,2nynz)`. Its rank is at least three: the outer products of any three independent normals are independent, since `N diag(a) N^T=0` for an invertible N implies a=0. Thus `k=dim K<=3`.

For any basis `D_1,...,D_k`, define the quadratic form

`q_C(t)=-tr(C adj(sum_a t_a D_a)) = t^T Q_C t`.

The adjugate is quadratic in dimension three, so diagonal evaluation and pairwise polarization compute Q exactly. A basis change acts by congruence on Q. Empty K means an empty positive-semidefinite condition, but only after full evaluation rank is verified.

Define the homogeneous cone of feasible width-four directions

`D4={H: A_i H A_i^T>=0 and rank(A_i H A_i^T)<=1 for all i}`.

The feasible metrics are exactly `S=I-H>0` with H in D4. Positive multiples of H remain in D4. Strict convexity implies that I is the unique optimum if `tr(CH)>=0` on D4: for any nonzero feasible H,

`f_C(I-H)>f_C(I)+tr(CH)>=f_C(I)`.

Conversely, a direction with negative covariance trace gives an improving feasible sufficiently small positive step. This first-order test is exact because the direction set is homogeneous; no convexity of D4 is needed.

The plane identity `det(A_i H A_i^T)=n_i^T adj(H)n_i` follows by completing the rows of A_i to an orthogonal basis and taking the remaining principal cofactor. Its validity for singular H follows by polynomial continuity.

No nonzero matrix D in K can be semidefinite: `n_i^TDn_i=0` for D>=0 forces all spanning normals into its nullspace, hence D=0; apply this to -D as well. A nonzero singular D in K therefore has one positive eigenvalue, one negative eigenvalue and one zero eigenvalue. Its negative adjugate is positive semidefinite of rank one.

For H in D4, the plane identity puts adj(H) in K. H cannot have rank two because its adjugate would then be nonzero rank-one semidefinite, contradicting the preceding paragraph. Rank-one negative H is impossible: positivity of the plane restrictions would imply `A_iv=0` for H=-vv^T and every i, contradicting rank(A)=3. Thus rank-one nonzero H is positive semidefinite.

If H is nonsingular, it cannot be positive definite, because then its two-dimensional restrictions have rank two. Nor can it have two negative eigenvalues: the negative two-plane intersects every image two-plane in a nonzero vector. Therefore its inertia is two positive and one negative, and det H<0. For D=adj(H) in K, the identity `adj(adj(H))=(det H)H` shows that H is a positive multiple of -adj(D).

Conversely let D in K be nonsingular. It is indefinite, and H=-adj(D) has two positive and one negative eigenvalue for either possible indefinite inertia of D. The identity `adj(H)=(det D)D` makes every image-plane determinant zero. Each image plane intersects the positive two-dimensional eigenspace, giving a positive quadratic value. A symmetric two-by-two form with determinant zero and a positive value is positive semidefinite of rank one. Thus H lies in D4. Singular D produce the already considered positive-semidefinite rank-one directions.

These facts exhaust D4: its nonzero elements are positive-semidefinite rank-one directions and positive multiples of negative adjugates of nonsingular K elements. Because C is positive definite, its trace on the former directions is positive. Its trace on the latter is controlled exactly by Q_C. Hence

**Width-four recovery holds if and only if Q_C is positive semidefinite.**

If Q has a negative vector, the corresponding D cannot be singular, because singular D has -adj(D)>=0. It therefore supplies a strict improving direction. The criterion includes singular successful Q: strict convexity still makes I the unique recovered metric.

For rational normal directions (with arbitrary nonzero scaling) and rational positive-definite covariance, the evaluation system has only six columns, and Q has order at most three. Exact elimination, adjugates and principal-minor tests have polynomial bit complexity. A negative rational vector can be constructed by symmetric elimination. A negative diagonal gives a coordinate vector. If a zero diagonal has a nonzero off-diagonal b, choose a sufficiently small rational opposite-signed coefficient s so that `2bs+cs^2<0`; for example `s=-b/(|c|+1)` works. If all diagonals are positive, eliminate one positive pivot and recurse on its Schur complement. Lift the negative direction by completing the square. Dimension is fixed, so the divisions and bit lengths remain polynomial.

For the three coordinate cameras, K is the space of symmetric zero-diagonal matrices. In the coefficient order `(a,b,c)` for the `(12),(13),(23)` entries,

`Q_C=[[C33,-C23,-C13],[-C23,C22,-C12],[-C13,-C12,C11]]`.

Since C is positive definite, every one-by-one and two-by-two principal minor of Q is positive. The width-four criterion therefore reduces to `det(Q_C)>=0`. Dividing the determinant by `C11 C22 C33` gives the exact correlation test

`1-rho12^2-rho13^2-rho23^2-2 rho12 rho13 rho23 >= 0`.

The determinant condition for C itself has the opposite sign on the triple-product term. Hence a valid full-rank covariance need not satisfy the recovery condition. If the correlation product is nonpositive, positive definiteness of C makes the recovery expression strictly positive. In the equicorrelated case it factors as `(1+rho)^2(1-2rho)`, so the exact threshold is `rho=1/2`, with equality still recovering. The finite tests evaluate this identity over an exhaustive small exact covariance family and also check congruence of Q under rational kernel-basis changes.

## 4. Uniform recovery and camera counts

Every positive-definite C is the covariance of a centered full-rank scene: multiply any centered isotropic full-rank configuration by a suitable invertible real matrix. Thus universal scene recovery means all C>0.

If all elements of K are singular, every -adj(D) is positive semidefinite and every Q_C is positive semidefinite. Conversely a nonsingular D in K gives an indefinite H=-adj(D). Choose v with `v^THv<0` and then `C=vv^T+epsilon I>0` for sufficiently small epsilon. Its trace on H is negative, so recovery fails. Therefore universal width-four recovery is equivalent to the determinant polynomial of K being identically zero.

That polynomial is a homogeneous cubic in k<=3 variables with at most ten coefficients. Its vanishing may also be verified on the complete grid `{0,1,2,3}^k`, at most 64 points. Repeated application of the univariate degree-three root bound proves that this grid detects a nonzero polynomial. A few random evaluations would not prove an identity. Rank and completeness of the supplied kernel basis are essential to this certificate.

Three spanning normals, under invertible congruence, give all symmetric zero-diagonal matrices; these contain an invertible element. They cannot be universally safe. Four can be safe: take e1,e2,e3,(3,4,0)/5. The kernel has the form `[[0,0,a],[0,0,b],[a,b,0]]`, all singular.

The six directions e1,e2,e3,(2,2,1)/3,(2,1,2)/3,(1,2,2)/3 have evaluation rank six: after the diagonal entries vanish, the remaining rows on off-diagonal coordinates are proportional to (4,2,2),(2,4,2),(2,2,4), an invertible matrix. Their first five have evaluation rank five and contain

`D*=[[0,-1/3,-1/3],[-1/3,0,1],[-1/3,1,0]]`, with det(D*)=2/9.

The first four and first three also contain this nonsingular D* and have full row evaluation rank. Parameterize each camera by its projective direction in `(P^2)^m`; rescaling a normal rescales one evaluation row but leaves its kernel unchanged. On the nonempty Zariski-open full-row-rank locus, the kernel defines a regular map to the appropriate Grassmannian. The Grassmannian subspaces on which the determinant cubic restricts identically to zero form a Zariski-closed set, because all coefficients of the restricted cubic vanish.

The parameter space `(P^2)^m` is irreducible. For m=3,4,5, the explicit full-row-rank example maps outside that closed set because its kernel contains the nonsingular D*. Its preimage is therefore proper, and the complementary failure set is Zariski open and dense. For m>=6, the displayed six-view arrangement has a nonzero six-by-six evaluation minor, so full column rank is a nonempty Zariski-open condition; any larger arrangement containing such a six-subset is also safe. Intersecting with the open normal-span locus proves the generic statement under the theorem's hypothesis. Thus four is the special minimum and six the generic threshold. This proof does not infer genericity from the finite camera pool or assign a probability to a camera distribution.

The normal-span assumption is essential. Normals (0,1,0),(3,4,0)/5,(-3,4,0)/5 have span two and an entirely singular kernel, yet H=diag(1,-1,0) has positive-semidefinite rank-one restrictions with nonzero eigenvalues 1,7/25,7/25. A covariance emphasizing its negative direction yields a strict width-four failure. This rank-two H is exactly the possibility excluded in the spanning proof.

## 5. Width at least five

All two-by-two positive-semidefinite slacks have rank at most two. Thus every width q>=5 has the same convex metric feasible set `F={S>0:A_iSA_i^T<=I}` and a unique optimum by strict convexity. Let

`C_A={sum_i A_i^T Lambda_i A_i: Lambda_i>=0}`.

This cone is closed. If a sequence of represented matrices converges, the traces of all positive-semidefinite blocks Lambda_i are bounded because `tr(sum_i A_i^T Lambda_i A_i)=sum_i tr Lambda_i`. A convergent subsequence of the blocks supplies a representation of the limit.

If C is in this cone, every direction H with positive-semidefinite image restrictions has `tr(CH)=sum_i tr(Lambda_i A_iHA_i^T)>=0`; strict convexity proves recovery. If C is outside the closed convex cone, separation gives H with nonnegative trace against all its generators and negative trace against C. Testing arbitrary rank-one positive-semidefinite Lambda_i shows precisely that `A_iHA_i^T>=0`. A small step I-tH is feasible and improves the objective. Hence wide-model recovery is equivalent to `C in C_A`.

No finite nonempty set of cameras recovers every scene. Choose a unit v outside their finitely many image planes. Put `beta=max_i ||A_iv||^2<1` and choose beta<alpha<1. Then `H=alpha I-vv^T` has positive-definite image restrictions and `v^THv=alpha-1<0`. With `C=vv^T+epsilon I>0` for small epsilon its covariance trace is negative. For sufficiently small positive t, `S=I-tH>0` and every slack is `t A_i H A_i^T>0`, hence has rank two. Apply the converse realization formula directly: factor each slack as `E_iE_i^T`, choose the common code factor `R=S^{-1/2}X`, and set `B_i=[A_iS^{1/2}\ E_i]`. This construction does not use a rank assumption on the stacked camera matrix and realizes the competing metric at width five. The objective derivative at zero is `tr(CH)<0`, so the fit is strictly better. Strict inequalities also survive small camera and covariance perturbations, so failure is not confined to a singular scene. The existence of v follows because a finite union of proper linear subspaces does not cover R^3.

At least three distinct image planes make the linear adjoint map from symmetric image blocks span Sym(3): its orthogonal complement consists of H whose plane restrictions vanish, and Section 2 proves H=0. Images of strictly positive-definite blocks therefore include an open set. There are both good and bad open covariance families. Cone duality is a standard tool; the width-four rank-one adjugate reduction and its contrast with this wide cone are the specific result. More generally, adding a view intersects the feasible metric set with another constraint and therefore cannot destroy recovery, while increasing width weakens the slack-rank bound and therefore cannot create recovery. The true metric belongs to every one of these nested sets, so the statement holds for the full minimizer-set definition rather than only for objective values.

A joint Gram formulation minimizes tr(Q) subject to `[[K,Y],[Y^T,Q]]>=0` and diagonal two-by-two blocks K_ii=I. With an ambient-rank constraint it describes finite width; without that constraint it has the same optimum as the width-five metric problem. A PSD block matrix is a Gram matrix of some common vectors, giving the original fit; row-space projection followed by the metric construction realizes its best value at width five. An exact convex objective is therefore not a certificate of true-geometry recovery.

## 6. Quantitative bounds

For a strict direction with `tr(CH)=-delta<0`, choose rational `h>=||H||_op`, for example the largest absolute row sum. If

`0<t<=min(1/(2h),delta/(4 tr(C) h^2))`, set S=I-tH.

It is positive definite. The identity `S^{-1}=I+tH+t^2H^2S^{-1}` and `||S^{-1}||<=1/(1-th)` give

`f_C(S)<=tr C-t delta+2 t^2 tr(C)h^2<=tr C-t delta/2`.

Slacks remain positive multiples of the corresponding restrictions, with any rank-one requirement preserved. The witness remains a strict direction under a positive-definite covariance perturbation C+E whenever `||E||_F ||H||_F<delta`.

For a fixed kernel basis write `(Q_C)_ab=tr(C K_ab)` and `L=(sum_ab ||K_ab||_F^2)^{1/2}`. Entrywise Cauchy-Schwarz gives `||Q_{C+E}-Q_C||_op<=L||E||_F`. A positive least-eigenvalue margin exceeding this quantity preserves recovery; a negative unit-vector quadratic value of larger magnitude preserves failure. The margin depends on the chosen basis; the exact verdict does not. For a common centered scene perturbation X+Delta,

`||(X+Delta)(X+Delta)^T-XX^T||_F <= 2||X||_op||Delta||_F+||Delta||_F^2`.

Full row rank persists if `||Delta||_op<sigma_min(X)`. This describes perturbations that remain within the exact model, not arbitrary independent perturbations of the Y_i.

On the wide feasible set, `S<=MI` from Section 1. The Hessian bound is `d^2 f_C(S)[H,H]>=2c||H||_F^2/M^3`, by writing `J=S^{-1/2}HS^{-1/2}` and applying the lower bounds on C and S^{-1}. The constrained variational inequality thus gives `||S-S_C||_F<=sqrt(epsilon M^3/c)` for a feasible epsilon-suboptimal metric. If C'>=c'I and `ell=min(c/tr C,c'/tr C')`, both minimizers exceed ell I. Strong monotonicity, their variational inequalities and `||S^{-1}(C-C')S^{-1}||_F<=ell^{-2}||C-C'||_F` give

`||S_C-S_C'||_F <= M^3 ||C-C'||_F/(2c ell^2)`.

For angular coverage put `delta_A=max_{||v||=1} min_i(n_i^Tv)^2<1`. If v is a top eigenvector of a feasible S, select a normal with `(n_i^Tv)^2<=delta_A`, and normalize the projection of v onto its image plane to u. Feasibility gives `u^TSu<=1`, whereas the eigenbasis expansion gives `u^TSu>=lambda_max(S)(1-(n_i^Tv)^2)`. Therefore `S<=(1-delta_A)^{-1}I`.

Write `S^{-1}=(1-delta_A)I+E`, E>=0. If `f_C(S)<=tr C+epsilon`, then `tr(CE)<=delta_A tr C+epsilon`. The true Gram `G0=X^TX` and `X^TEX` are positive semidefinite. The triangle inequality for nuclear norm yields

`||X^TS^{-1}X-G0||_* <= 2 delta_A tr C+epsilon`.

The scalar inequality `(sqrt(t)-1)^2<=|t-1|`, spectral calculus and `|E-delta_A I|<=E+delta_A I` give the same bound on `||S^{-1/2}X-X||_F^2`. This is an admissible isometrically aligned code comparison.

For r>=3 equally spaced unoriented normals in the xy circle, plus e3, choose a normal within pi/(2r) of the perpendicular to any xy projection. Then `delta_A<=sin^2(pi/(2r))`. Three circle constraints annihilate a binary homogeneous quadratic, and e3 eliminates D33, leaving the singular kernel form of the special four-view example. Such designs are universally recovering at width four and have normalized wide-model Gram-error upper bound `2 sin^2(pi/(2r))`. Finite exact failure at width five is consistent with an error bound tending to zero as the number of distinct directions increases.

## 7. Observation-only certification

Choose three independent columns of exact centered rank-three Y as F. Choose three independent rows F_J and set `W=F_J^{-1}Y_J`; check Y=FW. Solve `F_i S0 F_i^T=I` for a unique positive-definite symmetric S0. Inconsistent, nonunique or nonpositive solutions are input-domain failures. The classical Gram is `W^T S0^{-1}W`.

Because Y=AX=FW, an invertible R satisfies F=AR, W=R^{-1}X and S0=R^{-1}R^{-T}. Raw null directions are proportional to `nu_i=R^{-1}n_i`. Their kernel is `K_nu={R^T D R:D in K}`. The necessary covariance is

`Cbar=S0^{-1} W W^T S0^{-1}=R^T C R`, not WWT.

Using `adj(R^TDR)=(det R)^2 R^{-1} adj(D) R^{-T}` proves that the raw-coordinate form has the same sign as the physical form, up to positive scalar and basis congruence. Singularity of kernel matrices is also invariant. All executable operations use Y only and rational arithmetic. When the form is negative, the implementation chooses a rational finite step in this recovered affine gauge, checks positive definiteness and every rank-one plane slack, evaluates the competing objective exactly, and returns the corresponding competing Gram `W^T S_affine^{-1} W`. A descent direction without these finite checks is not labeled a witness.

For a diagnostic example, the isotropic four-point scene under coordinate cameras gives W with rows (1,0,0,-1),(0,1,0,-1),(0,0,1,-1) and S0=(I+J)/4. Then WWT=I+J but Cbar=16I-4J. For the complete raw kernel basis

`D1=[[-1,1,0],[1,-1,0],[0,0,1]]`,
`D2=[[-1,0,1],[0,1,0],[1,0,-1]]`,
`D3=[[1,0,0],[0,-1,1],[0,1,-1]]`,

the correct form is 16I. Substituting WWT produces `11I-5J`, whose all-ones eigenvalue is -4. This reverses the verdict while preserving exact Y=FW and the classical metric. The reporting check recomputes both matrices rather than trusting a printed label.

## 8. The exact four-point transition

Let Z0 have rows (1,1,-1,-1),(1,-1,1,-1),(1,-1,-1,1), so Z0 Z0^T=4I. Take `X(u)=(I+uJ)Z0`, u>=0, and the three coordinate image planes. Put a=1+3u and b=2u+3u^2. Then C=4(I+bJ), and true energy is 4a^2+8. In the off-diagonal kernel basis the width-four form is `4[(1+2b)I-bJ]`, which is positive semidefinite exactly when b<=1, or u<=1/3.

For u<=1/3, the wide-model cone has explicit two-by-two blocks with diagonals 2(1+b) and off-diagonals 4b. They are positive semidefinite and their lifted sum equals C, so I is optimal even at width five.

For u>1/3 put `v=(a-2)/(2(a+1))` and `S=(1-2v)I+vJ`. Its eigenvalues are `3a/(2(a+1))` in the all-ones direction and `3/(a+1)` in the other two directions. Each plane slack is `v[[1,-1],[-1,1]]`, positive semidefinite of rank one. Thus S is feasible at width four. Set each dual block to `4(a+1)^2 J_2/9`. Its pairing with the corresponding slack vanishes, and the lifted sum L satisfies `C=SLS`. Hence the first-order convex optimality condition holds for the wide metric problem; strict convexity makes S its unique optimum. As the same S is width-four feasible, it is also the width-four optimum.

The exact minimum energy is `8(a+1)^2/3`, with improvement `4(a-2)^2/3` over the true geometry. The nonzero eigenvalues of the Gram error are `-4a(a-2)/3`, `4(a-2)/3`, `4(a-2)/3`. Dividing the sum of their squares by `||X^TX||_F^2=16(a^4+2)` gives

`relative squared Frobenius Gram error = (a-2)^2(a^2+2)/(9(a^4+2))`.

At u=1, true energy is 72, optimum 200/3, improvement 16/3 and relative squared Gram error 4/129. As u tends to infinity, the energy ratio tends to 2/3, the relative Frobenius error tends to 1/3 and the normalized nuclear Gram error tends to 1/3. The exact equality case u=1/3 recovers uniquely despite a singular width-four certificate. This establishes the transition algebraically; the 49 retained rational samples validate its implementation but do not prove its continuum quantifier.

## 9. What the finite checker establishes

The arithmetic paths normalize plain integer inputs to rational numbers before division. Forty-one integer-input regressions compare rank, inverse, definiteness, negative-direction construction, recovery forms and the scalar oracle with the independent checker. Eight scales through `2^256` include determinant-one invertible matrices, determinant-minus-one indefinite matrices, and covariances immediately beyond a recovery boundary. The final case uses integer `u=1` in the scalar oracle. Large entries do not justify a floating-point rank or sign decision.

The independent checker verifies complete kernels, not merely kernel membership; exact sign and rank of every image-plane restriction; equality of reported and recomputed objective gaps; and consistency of scene, camera and observation-only fields. In the observation-only path it recomputes the exact rank of the raw null directions and rejects rank below three before a complete or empty serialized kernel can be interpreted as a recovery form. Uniform identities are checked on a degree-complete grid. It uses a separate arithmetic path and imports no producer module. The targeted corruption suite is finite and not a claim of exhaustive adversarial verification.

The structured input design is fixed and transparent. A second fixed-seed stress design uses 160 spanning arrangements, ten new scenes per arrangement, and 40 width-five witnesses. Its fixtures are disjoint from the structured pool, but its generator reuses the shared exact-arithmetic and finite-witness routines. A producer-independent verifier recomputes the forms and verdicts, binds every finite width-four failure to its parent arrangement and scene, verifies the wide-model gaps, and rejects six targeted stress corruptions. There is no model fitting, selected success threshold, solver stopping criterion, or probabilistic accuracy interval. The stress set attacks specialization to the original four fixtures, but it is not a population-generalization or practical-model study. Exact arithmetic decides every retained instance. Mathematical proofs provide the general quantifiers, while executable checks provide independently recomputed finite evidence. Neither kind of evidence substitutes for the other.
