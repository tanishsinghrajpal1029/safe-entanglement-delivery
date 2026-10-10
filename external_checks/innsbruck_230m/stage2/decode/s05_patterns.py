# Which detector pairs trigger the hardware herald (loop exit)? Uses only click patterns & loop counts (no ion outcomes).
from common import *
from collections import Counter
DET=[2,4,5,6]
tot_term=Counter(); tot_non=Counter()
for ra,rb,b,_,_ in RUNS:
    t,c=load_tags(b); z=np.load(f'{CACHE}/{b}_cycles.npz'); t7=z['t7']; n0=z['n0']
    i0=np.where(c==0)[0]; t0=t[i0]
    cyc0=np.searchsorted(t7,t0,side='right')-1
    # attempt index within cycle
    first=np.searchsorted(cyc0,cyc0,side='left'); att=np.arange(len(t0))-first
    ok=cyc0>=0
    nc=np.zeros(len(t0),int); nc[ok]=n0[cyc0[ok]]
    is_term=ok&(att==nc-1)&(nc<20)
    is_last_cyc=cyc0==len(t7)-1
    m=np.isin(c,DET); td=t[m]; cd=c[m]
    a=np.searchsorted(t0,td,side='right')-1; okd=a>=0
    dt=np.full(len(td),np.nan); dt[okd]=(td[okd]-t0[a[okd]])/1e6
    win=okd&(dt>=0)&(dt<60)
    # per attempt: set of detectors clicked within [0,60) us
    from itertools import combinations
    att_ids=a[win]; chs=cd[win]
    order=np.argsort(att_ids,kind='stable'); att_ids=att_ids[order]; chs=chs[order]
    u,st=np.unique(att_ids,return_index=True); en=np.append(st[1:],len(att_ids))
    for k,s,e in zip(u,st,en):
        if is_last_cyc[k]: continue
        pat=tuple(sorted(set(chs[s:e].tolist())))
        if len(pat)<2: 
            if is_term[k]: tot_term[pat]+=1
            continue
        if is_term[k]: tot_term[pat]+=1
        else: tot_non[pat]+=1
    nterm=int(is_term.sum()-is_term[is_last_cyc].sum())
    print(ra,'terminal attempts',nterm,flush=True)
print('terminal (loop exited) attempt patterns:',tot_term.most_common(20))
print('non-terminal attempts with >=2 detectors:',tot_non.most_common(20))
