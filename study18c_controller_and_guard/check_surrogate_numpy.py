"""Exact 4-qubit circuit check (NumPy, independent of any project code) of the two closed forms used in
drift_floor.py / nearterm_calibration_regimes.py:
 (1) DEJMPS on two Werner pairs: F' = (F1F2+b1b2)/N, N=(F1+b1)(F2+b2)+4b1b2, b=(1-F)/3
 (2) gate-error model: output-only depolarization (1-e)F'+e/4  vs  depolarizing e on each qubit after the CNOTs."""
import numpy as np, itertools
I=np.eye(2); X=np.array([[0,1],[1,0]]); Y=np.array([[0,-1j],[1j,0]]); Z=np.diag([1,-1])
phi=np.array([1,0,0,1])/2**.5; PHI=np.outer(phi,phi)
def werner(F): return F*PHI+(1-F)/3*(np.eye(4)-PHI)
def kron(*m):
    o=m[0]
    for x in m[1:]: o=np.kron(o,x)
    return o
def op(U,q,n=4): return kron(*[U if i==q else I for i in range(n)])
def cnot(c,t,n=4):
    P0=np.diag([1,0]);P1=np.diag([0,1]); a=[I]*n; b=[I]*n; a[c]=P0; b[c]=P1; b[t]=X; return kron(*a)+kron(*b)
def depol(rho,q,e,n=4): return (1-e)*rho+e/4*sum(op(P,q,n)@rho@op(P,q,n).conj().T for P in (I,X,Y,Z))
Rx=lambda th: np.cos(th/2)*I-1j*np.sin(th/2)*X
def dejmps_circuit(F1,F2,e):
    # qubit order: A1,B1 (pair1), A2,B2 (pair2)
    rho=np.kron(werner(F1),werner(F2))
    U=op(Rx(np.pi/2),0)@op(Rx(-np.pi/2),1)@op(Rx(np.pi/2),2)@op(Rx(-np.pi/2),3)
    rho=U@rho@U.conj().T
    C=cnot(0,2)@cnot(1,3); rho=C@rho@C.conj().T
    for q in range(4): rho=depol(rho,q,e)
    keep=0; Fout=0
    for mA,mB in ((0,0),(1,1)):
        P=op(np.diag([1-mA,mA]),2)@op(np.diag([1-mB,mB]),3)
        r=P@rho@P; p=np.real(np.trace(r)); r=r.reshape(2,2,2,2,2,2,2,2)
        ab=np.einsum('abijcdij->abcd',r).reshape(4,4)
        keep+=p; Fout+=np.real(np.trace(PHI@ab))
    return Fout/keep, keep
def dejmps_closed(F1,F2):
    b1,b2=(1-F1)/3,(1-F2)/3; N=(F1+b1)*(F2+b2)+4*b1*b2; return (F1*F2+b1*b2)/N, N
mx0=0; mxp=0; rows=[]
for F1,F2 in itertools.product((0.75,0.85,0.9,0.95,0.99),repeat=2):
    fc,pc=dejmps_circuit(F1,F2,0.0); fa,pa=dejmps_closed(F1,F2)
    mx0=max(mx0,abs(fc-fa)); mxp=max(mxp,abs(pc-pa))
print(f"(1) ideal gates: max |F_circuit - F_closed| = {mx0:.2e}, max |p_succ diff| = {mxp:.2e}")
for e in (0.003,0.005,0.01):
    worst=0; worst_case=None
    for F1,F2 in itertools.product((0.85,0.9,0.95,0.99),repeat=2):
        fc,_=dejmps_circuit(F1,F2,e); fa,_=dejmps_closed(F1,F2); fs=(1-e)*fa+e/4
        if abs(fc-fs)>worst: worst=abs(fc-fs); worst_case=(F1,F2,round(fc,4),round(fs,4))
    print(f"(2) gate error e={e}: max |circuit - surrogate((1-e)F'+e/4)| = {worst:.4f} at (F1,F2,circ,surr)={worst_case}")
