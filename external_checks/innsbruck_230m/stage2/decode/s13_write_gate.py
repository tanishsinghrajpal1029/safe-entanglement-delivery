import json, hashlib
from common import *
S2=os.path.dirname(HERE)
p=json.load(open(f'{CACHE}/gate_point.json')); boot=json.load(open(f'{CACHE}/boot.json')); sens=json.load(open(f'{CACHE}/sens.json'))
book=json.load(open(f'{CACHE}/bookkeeping.json'))
m=p['labels_as_table']
sha=lambda f: hashlib.sha256(open(f,'rb').read()).hexdigest()
g=dict(
 description='E63 Stage 2 decoding gate numbers (G3). Main table: coincidence |tau|<=1 us, both clicks in [5.5,23] us after the BSM ch0 (Node B Raman-start) trigger; psi+ = same-output pairs (ch2,ch6),(ch4,ch5); psi- = orthogonal cross pairs (ch2,ch5),(ch4,ch6).',
 n_total=p['n_total'], per_run=p['per_run'], per_herald=p['per_herald'],
 F_plus=m['psi+']['F_mle_jointphi'], F_minus=m['psi-']['F_mle_jointphi'], phi_joint_deg=m['phi_joint_deg'],
 F_definition='MLE (R rho R) two-qubit state per herald from 9 basis settings; fidelity to |Psi+-(phi)>=(|01>+-e^{i phi}|10>)/sqrt2 with ONE phi optimised jointly for both heralds (paper: phi optimised, then fixed). |0>=|D> (bright after mapping pulse), |1>=|D_prime> (dark).',
 F_plus_own_phi=m['psi+']['F_mle_ownphi'], F_minus_own_phi=m['psi-']['F_mle_ownphi'],
 F_plus_lin_own_phi=m['psi+']['F_lin_ownphi'], F_minus_lin_own_phi=m['psi-']['F_lin_ownphi'],
 F_plus_maxME=m['psi+']['F_mle_maxME'], F_minus_maxME=m['psi-']['F_mle_maxME'],
 min_eig_linear_inversion={'psi+':m['psi+']['min_eig_lin'],'psi-':m['psi-']['min_eig_lin']},
 counts_by_setting={'psi+':m['psi+']['counts'],'psi-':m['psi-']['counts']},
 bootstrap=dict(n=1000,seed=20261007,scheme='resample events with replacement within each run',**boot),
 rejected_handedness_candidate=dict(note='Node B Y-axis sign flipped (equivalently X<->Y relabelling at B): unphysical',
     F_plus=p['flipYB']['psi+']['F_mle_jointphi'],F_minus=p['flipYB']['psi-']['F_mle_jointphi'],
     min_eig_lin={'psi+':p['flipYB']['psi+']['min_eig_lin'],'psi-':p['flipYB']['psi-']['min_eig_lin']}),
 sensitivity_report_only=sens,
 bookkeeping=book,
 paper_reference=dict(n_1us=491,F_plus_1us=0.882,F_minus_1us=0.822,n_17p5us=3960,F_plus_17p5=0.587,F_minus_17p5=0.580,attempts=13656928),
 G3=dict(count_within_10pct=bool(abs(p['n_total']-491)<=49.1),F_plus_within_0p06=bool(abs(m['psi+']['F_mle_jointphi']-0.882)<=0.06),F_minus_within_0p06=bool(abs(m['psi-']['F_mle_jointphi']-0.822)<=0.06)),
 sha256=dict(events_csv=sha(os.path.join(S2,'events.csv')),runs_csv=sha(os.path.join(S2,'runs.csv')),
             **{os.path.basename(f):sha(f) for f in sorted(__import__('glob').glob(HERE+'/*.py'))}))
json.dump(g,open(os.path.join(S2,'gate.json'),'w'),indent=1)
print(json.dumps({k:g[k] for k in ['n_total','per_run','per_herald','F_plus','F_minus','phi_joint_deg','F_plus_own_phi','F_minus_own_phi','F_plus_maxME','F_minus_maxME','G3']},indent=0))
print({k:v[:16] for k,v in g['sha256'].items()})
