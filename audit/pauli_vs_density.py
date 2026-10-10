"""Independent check: Pauli/Bell-diagonal (twirled) fidelity model vs exact density matrices
for a 2-link swap with amplitude damping + dephasing (T1,T2) on stored qubits.
Per-BSM-outcome fidelity after Pauli correction is what a decision conditioned on the
observed outcome sees. No NetSquid; written from scratch for the audit."""
import itertools, numpy as np
I=np.eye(2); X=np.array([[0,1],[1,0]]); Z=np.diag([1,-1]); Y=1j*X@Z
k0=np.array([1,0]); k1=np.array([0,1])
bell=[(np.kron(k0,k0)+np.kron(k1,k1))/2**.5,(np.kron(k0,k1)+np.kron(k1,k0))/2**.5,
      (np.kron(k0,k1)-np.kron(k1,k0))/2**.5,(np.kron(k0,k0)-np.kron(k1,k1))/2**.5]   # Phi+,Psi+,Psi-,Phi-
PHI=np.outer(bell[0],bell[0])
def depol2(rho,p):  # (1-p) rho + p I/4 on a 2-qubit pair  -> lambda = 1-p
    return (1-p)*rho+p*np.eye(4)/4
def op_on(U,q,n):
    mats=[I]*n; mats[q]=U; out=mats[0]
    for m in mats[1:]: out=np.kron(out,m)
    return out
def ad_deph(rho,q,n,t,T1,T2):
    """amplitude damping to |0> with gamma=1-exp(-t/T1), plus pure dephasing so that coherence decays exp(-t/T2)"""
    if t<=0: return rho
    g=1-np.exp(-t/T1)
    K0=np.array([[1,0],[0,np.sqrt(1-g)]]); K1=np.array([[0,np.sqrt(g)],[0,0]])
    rho=sum(op_on(K,q,n)@rho@op_on(K,q,n).conj().T for K in (K0,K1))
    # extra pure dephasing: total coherence factor exp(-t/T2) = sqrt(1-g)*lam  -> lam
    lam=np.exp(-t/T2)/np.sqrt(1-g)
    assert lam<=1+1e-12, "need T2<=2T1"
    pz=(1-lam)/2; Zq=op_on(Z,q,n)
    return (1-pz)*rho+pz*Zq@rho@Zq
def swap(rho4):
    """qubits order A,R1,R2,B ; BSM on R1,R2 ; returns list of (prob, corrected AB state)"""
    out=[]
    paulis=[I,X,Y,Z]
    # find correction for each outcome using ideal input
    ideal=np.kron(PHI,PHI)
    for k,b in enumerate(bell):
        P=np.kron(np.kron(I,np.outer(b,b.conj())),I)
        def proj(r):
            m=P@r@P; pr=np.real(np.trace(m))
            # partial trace over R1,R2 (qubits 1,2)
            m=m.reshape(2,2,2,2,2,2,2,2)
            ab=np.einsum('aijbckjd->abcd',m).reshape(4,4)
            return pr, ab/pr
        _,ab_ideal=proj(ideal)
        corr=max(paulis,key=lambda U: np.real(np.trace(PHI@np.kron(I,U)@ab_ideal@np.kron(I,U).conj().T)))
        pr,ab=proj(rho4)
        C=np.kron(I,corr); out.append((pr,C@ab@C.conj().T))
    return out
F=lambda r: float(np.real(np.trace(PHI@r)))
rows=[]
T1=1.0
for p,t_wait,T2r,t_after in itertools.product([0.0,0.02,0.05,0.1],[0,0.01,0.02,0.05,0.1,0.2,0.5,1,2],[2.0,1.0,0.5],[0,0.02,0.1]):
    T2=T2r*T1
    # link1 (A,R1) waits t_wait for link2; link2 (R2,B) fresh
    L1=depol2(PHI,p); L2=depol2(PHI,p)
    rho=np.kron(L1,L2)
    rho=ad_deph(rho,0,4,t_wait,T1,T2); rho=ad_deph(rho,1,4,t_wait,T1,T2)
    res=swap(rho)
    # deliver after t_after storage on both endpoints
    res=[(pr,ad_deph(ad_deph(ab,0,2,t_after,T1,T2),1,2,t_after,T1,T2)) for pr,ab in res]
    # Pauli/twirled model (study-13/18 'event_estimator' form)
    lx=(1-p)**2*np.exp(-2*t_wait/T2)*np.exp(-2*t_after/T2); lz=(1-p)**2*np.exp(-2*t_wait/T1)*np.exp(-2*t_after/T1)
    Fp=(1+2*lx+lz)/4
    for k,(pr,ab) in enumerate(res):
        rows.append((p,t_wait,T2r,t_after,k,pr,F(ab),Fp))
import pandas as pd
d=pd.DataFrame(rows,columns="p t_wait T2_over_T1 t_after outcome prob F_true F_pauli".split())
d["err"]=d.F_pauli-d.F_true
avg=d.assign(w=d.prob*d.F_true).groupby(["p","t_wait","T2_over_T1","t_after"]).agg(Ftrue_avg=("w","sum"),F_pauli=("F_pauli","first")).reset_index()
avg["err_avg"]=avg.F_pauli-avg.Ftrue_avg
pd.set_option("display.width",200)
print("max |err| per-outcome, all cases:", round(d.err.abs().max(),4), " outcome-averaged:", round(avg.err_avg.abs().max(),4))
for lo in (0.95,0.9,0.85,0.8,0.7,0.5):
    s=d[(d.F_true>=lo)|(d.F_pauli>=lo)]; a=avg[(avg.Ftrue_avg>=lo)|(avg.F_pauli>=lo)]
    print(f"cases with F>= {lo}: n={len(s)}  max|err| per outcome {s.err.abs().max():.4f}   outcome-avg max|err| {a.err_avg.abs().max():.4f}")
s=d[(d.F_true.between(0.85,0.95))]
print("\nworst per-outcome cases with true F in [0.85,0.95]:")
print(s.reindex(s.err.abs().sort_values(ascending=False).index).head(8).round(4).to_string(index=False))
print("\nsign of per-outcome error near threshold: Pauli overestimates in", int((s.err>1e-9).sum()), "of", len(s), "cases")
# misclassification at threshold 0.9 by outcome
mis=d[((d.F_pauli>=0.9)&(d.F_true<0.9))|((d.F_pauli<0.9)&(d.F_true>=0.9))]
print("threshold-0.9 misclassified (per-outcome) cases:", len(mis), "of", len(d))
print(mis.round(4).head(10).to_string(index=False))
