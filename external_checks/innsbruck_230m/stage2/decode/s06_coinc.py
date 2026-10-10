# Build two-click coincidence candidates per attempt (no ion outcomes). Saves per-run coincidence tables.
from common import *
DET=[2,4,5,6]
W0,W1=0.0,60.0   # us after ch0: collect all clicks in the attempt (the 50 us Raman/detection window + margin)
rows=[]
for ra,rb,b,_,_ in RUNS:
    t,c=load_tags(b); z=np.load(f'{CACHE}/{b}_cycles.npz'); t7=z['t7']; n0=z['n0']; seg=z['seg']; cyc=z['cyc']
    i0=np.where(c==0)[0]; t0=t[i0]
    cyc0=np.searchsorted(t7,t0,side='right')-1
    first=np.searchsorted(cyc0,cyc0,side='left'); att=np.arange(len(t0))-first
    m=np.isin(c,DET); td=t[m]; cd=c[m]
    a=np.searchsorted(t0,td,side='right')-1; ok=a>=0
    td=td[ok]; cd=cd[ok]; a=a[ok]; dt=(td-t0[a])/1e6
    w=(dt>=W0)&(dt<W1); td,cd,a,dt=td[w],cd[w],a[w],dt[w]
    # attempts with >=2 clicks on >=2 distinct detectors
    u,st,cnt=np.unique(a,return_index=True,return_counts=True)
    for k,s,n in zip(u[cnt>=2],st[cnt>=2],cnt[cnt>=2]):
        cc=cd[s:s+n]; tt=dt[s:s+n]
        if len(set(cc.tolist()))<2: continue
        ci=cyc0[k]
        rows.append(dict(run=ra,att_global=int(k),cycle=int(ci),seg=int(seg[ci]) if ci>=0 else -1,cyc_in_seg=int(cyc[ci]) if ci>=0 else -1,
                         attempt=int(att[k]),n_att=int(n0[ci]) if ci>=0 else -1,last_cycle=bool(ci==len(t7)-1),
                         t0_s=t0[k]/1e12,nclick=int(n),chs=','.join(map(str,cc.tolist())),ts=','.join(f'{x:.4f}' for x in tt)))
    print(ra,len(rows),flush=True)
df=pd.DataFrame(rows); df.to_csv(f'{CACHE}/coinc_candidates.csv',index=False)
