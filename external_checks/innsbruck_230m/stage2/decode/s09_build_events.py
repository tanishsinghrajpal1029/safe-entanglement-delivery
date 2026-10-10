"""Stage 2 decoder, final assembly (E63). Inputs: caches from s01 (tags), s02 (cycles), s03 (Node A markers), s06 (coincidence candidates).
Writes stage2/events.csv, stage2/runs.csv (main: T=1 us) and decode/cache/events_all.csv (all T, all patterns, for gate/sensitivity).
No within-run time-resolved statistic is computed here."""
import sys, json, pickle
from common import *
from s07_load_pmt import nodeA_pmt, nodeB_pmt
from s08_events_raw import heralds, PAT
THR_A=36   # Node A bright iff PMT counts > 36 (histogram minimum, same as Stage 1)
THR_B=4    # Node B bright iff PMT1_2 counts > 4 (histogram minimum)
T_MAIN=1.0 # us, paper's main coincidence window
LO,HI=5.5,23.0
KA={'1819':-4}  # Node A .dat row = seg + KA (default -2); Node B PMT1_2 row = seg
A=pickle.load(open(f'{CACHE}/nodeA_loops.pkl','rb'))
def main(lo=LO,hi=HI,thrA=THR_A,thrB=THR_B,T=T_MAIN,write=True,tag=''):
    h=heralds(lo,hi)
    allev=[]; runrows=[]; book=[]
    for ra,rb,b,bA,bB in RUNS:
        z=np.load(f'{CACHE}/{b}_cycles.npz'); seg=z['seg']; t7=z['t7']; n0=z['n0']
        kA=KA.get(ra,-2); kfile=kA-1   # raw file index = seg + kA - 1
        pa,_,_=nodeA_pmt(ra); pb,_,_=nodeB_pmt(rb)
        nseg=seg.max()+1; L=A[ra]['loops']
        # validated segments: Node A raw file exists and its per-cycle loop counts equal BSM per-cycle Raman-trigger counts
        valid=np.zeros(nseg,bool)
        for j in range(nseg):
            i=j+kfile; r=j+kA
            if i<0 or i>=len(L) or r<0 or r>=len(pa) or j>=len(pb): continue
            x=n0[seg==j]; l=L[i]
            if j==nseg-1: x=x[:-1]   # last tagged cycle is truncated by the end of the tag file
            if len(l)>=len(x) and np.array_equal(l[:len(x)],x): valid[j]=True
        vj=np.where(valid)[0]; first=vj.min(); lastseg=vj.max()
        # contiguous block from first validated seg to the last validated seg; record any invalid inside
        holes=[int(j) for j in range(first,lastseg+1) if not valid[j]]
        tz=t7[0]
        t_start=(t7[seg==first][0]-tz)/1e12
        t_end=(t7[-1]-tz)/1e12 if lastseg==nseg-1 else (t7[seg==lastseg][-1]-tz)/1e12 + 0.0119
        runrows.append(dict(run=ra,t_start_s=round(t_start,6),t_end_s=round(t_end,6)))
        g=h[(h.run==ra)].copy()
        g=g[(g.attempt==g.n_att-1)&(~g.last_cycle)]
        nterm=len(g)
        g=g[g.seg.isin(vj)]
        ra_=g.seg.values+kA; rb_=g.seg.values; cy=g.cyc.values
        g['cntA']=pa[ra_,cy]; g['cntB']=pb[rb_,cy]
        g['a']=(g.cntA<=thrA).astype(int); g['b']=(g.cntB<=thrB).astype(int)   # 0 = bright, 1 = dark
        g['t_s']=(g.t0_s - tz/1e12) + g.t2*1e-6
        g['basisA']=bA; g['basisB']=bB; g['rowA']=ra_; g['rowB']=rb_
        allev.append(g)
        book.append(dict(run=ra,segs=int(nseg),valid_segs=int(valid.sum()),first_valid_seg=int(first),holes=holes,
                         in_window_2click_terminal=int(nterm),kept=int(len(g))))
    ev=pd.concat(allev,ignore_index=True)
    main_=ev[(ev.tau<=T)&(ev.kind.isin(['psi+','psi-']))].copy()
    main_['herald']=main_.kind
    out=main_[['run','t_s','herald','basisA','basisB','a','b']].sort_values(['run','t_s'])
    if write:
        ROOT2=os.path.dirname(HERE)
        out.to_csv(os.path.join(ROOT2,'events.csv'),index=False,float_format='%.6f')
        pd.DataFrame(runrows).to_csv(os.path.join(ROOT2,'runs.csv'),index=False)
        ev.to_csv(f'{CACHE}/events_all{tag}.csv',index=False)
        json.dump(book,open(f'{CACHE}/bookkeeping{tag}.json','w'),indent=1)
    return ev,out,book,runrows
if __name__=='__main__':
    ev,out,book,rr=main()
    for x in book: print(x)
    print(rr)
    print('main events (T=1us, psi+/-):',len(out),out.herald.value_counts().to_dict())
    print('per run:',out.groupby('run').size().to_dict())
