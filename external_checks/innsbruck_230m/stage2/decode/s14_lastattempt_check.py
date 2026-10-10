"""Coordinator check (post-G3): is every main-table coincidence in the LAST attempt of its cycle on the BSM clock?
Also: early-ended cycles (n_att<20) without a qualifying coincidence in their last attempt. No within-run time-resolved statistic."""
from common import *
from collections import Counter
S2=os.path.dirname(HERE)
ev=pd.read_csv(f'{CACHE}/events_all.csv',dtype={'run':str})
main=ev[(ev.tau<=1.0)&ev.kind.isin(['psi+','psi-'])].copy()
cand=pd.read_csv(f'{CACHE}/coinc_candidates.csv',dtype={'run':str})
PAT={(2,6):'psi+',(4,5):'psi+',(2,5):'psi-',(4,6):'psi-',(2,4):'par',(5,6):'par'}
tab=[]; early=Counter(); early_run={}
for ra,rb,b,_,_ in RUNS:
    t,c=load_tags(b); z=np.load(f'{CACHE}/{b}_cycles.npz'); t7=z['t7']; n0=z['n0']; seg=z['seg']
    t0=t[c==0]; t3=t[c==3]
    g=main[main.run==ra]
    T0=np.round(g.t0_s.values*1e12).astype(np.int64)
    # locate attempt ch0 (exact tag) and next ch7
    k=np.searchsorted(t0,T0-5); assert np.all(np.abs(t0[k]-T0)<1000)
    nxt7=t7[np.searchsorted(t7,t0[k],side='right')]
    n0after=np.searchsorted(t0,nxt7)-np.searchsorted(t0,t0[k],side='right')
    # ch3 = Node A Raman trigger (2-5 us after its ch0) plus ONE extra ch3 per cycle ~1.6 ms after the last attempt (Node A raises
    # 397sig_sw for the next cycle's handshake after its readout). Count only attempt-type ch3 (within 10 us after a ch0).
    j=np.searchsorted(t0,t3,side='right')-1; att3=t3[(j>=0)&((t3-t0[np.clip(j,0,None)])<10**7)]
    n3after=np.searchsorted(att3,nxt7)-np.searchsorted(att3,t0[k]+10**7,side='left')
    hs=t3[~np.isin(t3,att3)]; nhs=np.searchsorted(hs,nxt7)-np.searchsorted(hs,t0[k])
    assert np.all(nhs==1), 'expected exactly one cycle-end handshake ch3 after the herald'
    last=(n0after==0)&(n3after==0)
    for h in ['psi+','psi-']:
        m=g.kind.values==h
        tab.append(dict(run=ra,herald=h,last=int((last&m).sum()),not_last=int((~last&m).sum())))
    # early-ended cycles within validated steps (exclude truncated last cycle)
    vsegs=set(ev[ev.run==ra].seg.unique())  # placeholder; use bookkeeping instead
    import json
    bk={x['run']:x for x in json.load(open(f'{CACHE}/bookkeeping.json'))}[ra]
    first=bk['first_valid_seg']
    i0=np.where(c==0)[0]; cyc0=np.searchsorted(t7,t0,side='right')-1
    lastatt_idx={}
    # last attempt ch0 index for each cycle
    ok=cyc0>=0; idx=np.arange(len(t0))[ok]; cc=cyc0[ok]
    lastidx=np.full(len(t7),-1); lastidx[cc]=idx   # later overwrite keeps last
    cyc_early=np.where((n0<20)&(seg>=first))[0]; cyc_early=cyc_early[cyc_early<len(t7)-1]
    # candidate (>=2 distinct-detector clicks) attempts keyed by global attempt index
    cr=cand[cand.run==ra].set_index('att_global')
    cnt=Counter()
    mainatt=set(np.searchsorted(t0,T0-5).tolist())
    # single-click info: detectors in [0,60] us of the last attempt
    det=np.isin(c,[2,4,5,6]); td=t[det]
    for ci in cyc_early:
        ka=lastidx[ci]
        if ka in mainatt: cnt['qualifying psi (main table)']+=1; continue
        if ka in cr.index:
            r=cr.loc[ka]; chs=list(map(int,str(r.chs).split(','))); ts=list(map(float,str(r.ts).split(',')))
            sel=[(q,x) for q,x in zip(chs,ts) if 5.5<=x<=23]; d=set(q for q,_ in sel)
            if len(sel)==2 and len(d)==2:
                p=PAT[tuple(sorted(d))]
                tau=abs(sel[0][1]-sel[1][1])
                cnt['parallel-pol pair, in window' if p=='par' else 'psi pattern in window but |tau|>1us']+=1
            elif len(sel)>2: cnt['>2 clicks in window']+=1
            else: cnt['2+ distinct-detector clicks in attempt but not both in [5.5,23] us']+=1
        else:
            n=np.searchsorted(td,t0[ka]+60*10**6)-np.searchsorted(td,t0[ka])
            cnt[f'{n} detector click(s) in [0,60] us of last attempt']+=1
    early_run[ra]=dict(early_cycles=int(len(cyc_early)),**cnt); early.update(cnt)
T=pd.DataFrame(tab); print(T.pivot(index='run',columns='herald',values=['last','not_last']).to_string()); print('totals last',T['last'].sum(),'not last',T.not_last.sum())
print('early-ended cycles (validated steps):',sum(v['early_cycles'] for v in early_run.values())); print(dict(early))
import json; json.dump(dict(per_run_herald=tab,early=early_run,early_total=dict(early)),open(f'{CACHE}/lastattempt_check.json','w'),indent=1)
