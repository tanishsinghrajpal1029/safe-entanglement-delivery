"""Two-qubit tomography from 9 Pauli settings with single-shot outcomes a,b (0 = +1 eigenstate = bright)."""
import numpy as np
I2=np.eye(2); SX=np.array([[0,1],[1,0]],complex); SY=np.array([[0,-1j],[1j,0]]); SZ=np.diag([1.,-1.]).astype(complex)
PAULI={'X':SX,'Y':SY,'Z':SZ,'I':I2.astype(complex)}
def proj(B,o,flipY=False):
    s=PAULI[B]*(-1 if (flipY and B=='Y') else 1)
    return (I2+(1-2*o)*s)/2
def counts_from(df):
    C={}
    for (bA,bB),g in df.groupby(['basisA','basisB']):
        n=np.zeros((2,2))
        for a,b in zip(g.a,g.b): n[a,b]+=1
        C[(bA,bB)]=n
    return C
def povm(C,flipYB=False):
    ops=[];ns=[];setting=[]
    for k,(bA,bB) in enumerate(C):
        for a in (0,1):
            for b in (0,1):
                ops.append(np.kron(proj(bA,a),proj(bB,b,flipYB))); ns.append(C[(bA,bB)][a,b]); setting.append(k)
    return np.array(ops),np.array(ns),np.array(setting)
def linear_inversion(C,flipYB=False):
    rho=np.zeros((4,4),complex)/4
    E={}
    for (bA,bB),n in C.items():
        N=n.sum(); E[(bA,bB)]=(n[0,0]-n[0,1]-n[1,0]+n[1,1])/N
        E[(bA,'I')]=E.get((bA,'I'),[])+[((n[0,0]+n[0,1])-(n[1,0]+n[1,1]))/N]
        E[('I',bB)]=E.get(('I',bB),[])+[((n[0,0]+n[1,0])-(n[0,1]+n[1,1]))/N]
    rho=np.kron(I2,I2).astype(complex)
    for key,v in E.items():
        val=np.mean(v) if isinstance(v,list) else v
        sA=PAULI[key[0]]; sB=PAULI[key[1]]*(-1 if (flipYB and key[1]=='Y') else 1)
        rho=rho+val*np.kron(sA,sB)
    return rho/4
def mle(C,flipYB=False,iters=3000,tol=1e-10):
    ops,ns,st=povm(C,flipYB)
    # normalise each setting to frequencies (settings have different totals)
    Ntot=np.array([C[k].sum() for k in C])
    rho=np.eye(4,dtype=complex)/4; 
    for it in range(iters):
        p=np.real(np.einsum('kij,ji->k',ops,rho)); p=np.clip(p,1e-12,None)
        R=np.einsum('k,kij->ij',ns/p,ops)
        new=R@rho@R; new/=np.trace(new)
        if np.max(np.abs(new-rho))<tol: rho=new; break
        rho=new
    return rho
def psi(phi,sign=1):
    v=np.zeros(4,complex); v[1]=1; v[2]=sign*np.exp(1j*phi); return v/np.sqrt(2)
def fid(rho,v): return float(np.real(v.conj()@rho@v))
def best_phi(rho,sign=1):
    ph=np.linspace(0,2*np.pi,3601); f=[fid(rho,psi(p,sign)) for p in ph]; i=int(np.argmax(f)); return f[i],ph[i]
def max_me_fid(rho):
    # max fidelity over all maximally entangled states: (1 + sum of singular values of T with sign) / 4
    T=np.array([[np.real(np.trace(rho@np.kron(PAULI[a],PAULI[b]))) for b in 'XYZ'] for a in 'XYZ'])
    s=np.linalg.svd(T,compute_uv=False); d=np.sign(np.linalg.det(T))
    return float((1+s[0]+s[1]-d*s[2])/4)
