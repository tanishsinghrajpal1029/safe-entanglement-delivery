"""Gate numbers (E63 G3): total events, per-run counts, F+ and F- (MLE and linear inversion), bootstrap SE.
Conventions: qubit |0> = |D> (S1/2 after the mapping pi pulse -> bright), |1> = |D'> (dark); a,b = 0 bright, 1 dark.
Basis labels from Basis_timestamps.png; bright <-> +1 eigenstate of sigma_X/Y/Z (label-based).
Target |Psi+-(phi)> = (|01> +- e^{i phi}|10>)/sqrt2 (paper Eq.1: |D_A D'_B> +- e^{i phi}|D'_A D_B>)."""
import json, sys, hashlib
from common import *
from tomo import *
def analyse(ev,flipYB=False):
    res={}
    rhos={}
    for hname in ['psi+','psi-']:
        C=counts_from(ev[ev.herald==hname]); rhos[hname]=(mle(C,flipYB),linear_inversion(C,flipYB),C)
    # joint phi (single phi for both, |Psi-(phi)> = |Psi+(phi+pi)>): maximise F+ + F- (MLE)
    ph=np.linspace(0,2*np.pi,3601)
    fj=[fid(rhos['psi+'][0],psi(p,1))+fid(rhos['psi-'][0],psi(p,-1)) for p in ph]; pj=ph[int(np.argmax(fj))]
    for hname,sg in [('psi+',1),('psi-',-1)]:
        rm,rl,C=rhos[hname]
        fs,ps=best_phi(rm,sg); fl,pl=best_phi(rl,sg)
        res[hname]=dict(n=int(sum(c.sum() for c in C.values())),
                        F_mle_jointphi=fid(rm,psi(pj,sg)),F_mle_ownphi=fs,phi_own_deg=float(np.degrees(ps)),
                        F_lin_ownphi=fl,F_lin_jointphi=fid(rl,psi(pj,sg)),
                        F_mle_maxME=max_me_fid(rm),min_eig_lin=float(np.linalg.eigvalsh(rl).min()),
                        counts={f'{k[0]}{k[1]}':C[k].astype(int).tolist() for k in C})
    res['phi_joint_deg']=float(np.degrees(pj))
    return res,rhos
if __name__=='__main__':
    ev=pd.read_csv(os.path.join(os.path.dirname(HERE),'events.csv'),dtype={'run':str})
    out={'n_total':int(len(ev)),'per_run':ev.groupby('run').size().to_dict(),'per_herald':ev.herald.value_counts().to_dict()}
    for flip in [False,True]:
        r,_=analyse(ev,flip); out['flipYB' if flip else 'labels_as_table']=r
        print('flipYB' if flip else 'table', json.dumps({k:{kk:(round(vv,4) if isinstance(vv,float) else vv) for kk,vv in v.items() if kk!='counts'} if isinstance(v,dict) else v for k,v in r.items()}))
    print(out['n_total'],out['per_herald'],out['per_run'])
    json.dump(out,open(f'{CACHE}/gate_point.json','w'),indent=1)
