"""Bootstrap SE for F+/F- (resampling events with replacement within each run, seed 20261007) and sensitivity variants (report only)."""
import json, time
from common import *
from tomo import *
from s10_gate import analyse
import s09_build_events as B
ev=pd.read_csv(os.path.join(os.path.dirname(HERE),'events.csv'),dtype={'run':str})
rng=np.random.default_rng(20261007)
NB=int(os.environ.get('NBOOT','200'))
bs={'psi+':[], 'psi-':[], 'psi+_own':[], 'psi-_own':[]}
t0=time.time()
for i in range(NB):
    parts=[g.iloc[rng.integers(0,len(g),len(g))] for _,g in ev.groupby('run')]
    r,_=analyse(pd.concat(parts))
    bs['psi+'].append(r['psi+']['F_mle_jointphi']); bs['psi-'].append(r['psi-']['F_mle_jointphi'])
    bs['psi+_own'].append(r['psi+']['F_mle_ownphi']); bs['psi-_own'].append(r['psi-']['F_mle_ownphi'])
boot={k:dict(se=float(np.std(v,ddof=1)),p16=float(np.percentile(v,16)),p84=float(np.percentile(v,84))) for k,v in bs.items()}
print('boot',NB,round(time.time()-t0,1),'s',json.dumps(boot))
json.dump(boot,open(f'{CACHE}/boot.json','w'),indent=1)
