import json, sys
from common import *
from s10_gate import analyse
import s09_build_events as B
variants=[('thrA30',dict(thrA=30)),('thrA44',dict(thrA=44)),('thrB3',dict(thrB=3)),('thrB6',dict(thrB=6)),
          ('win-0.5',dict(lo=5.0,hi=22.5)),('win+0.5',dict(lo=6.0,hi=23.5)),('T0.75',dict(T=0.75)),('T1.5',dict(T=1.5)),('T17.5',dict(T=17.5))]
sel=sys.argv[1:] or [v[0] for v in variants]
out={}
try: out=json.load(open(f'{CACHE}/sens.json'))
except Exception: pass
for name,kw in variants:
    if name not in sel: continue
    ev,o,book,rr=B.main(write=False,**kw)
    o=o.copy()
    r,_=analyse(o)
    out[name]=dict(n=int(len(o)),n_plus=int((o.herald=='psi+').sum()),n_minus=int((o.herald=='psi-').sum()),
                   Fp_joint=r['psi+']['F_mle_jointphi'],Fm_joint=r['psi-']['F_mle_jointphi'],Fp_own=r['psi+']['F_mle_ownphi'],Fm_own=r['psi-']['F_mle_ownphi'],phi_joint=r['phi_joint_deg'])
    print(name,{k:(round(v,4) if isinstance(v,float) else v) for k,v in out[name].items()},flush=True)
    json.dump(out,open(f'{CACHE}/sens.json','w'),indent=1)
