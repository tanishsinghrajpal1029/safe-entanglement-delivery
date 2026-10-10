# Segment BSM tags into experiment cycles (ch7 = IQOQI cycle start) and scan steps (gaps > 20 ms)
from common import *
SEG_GAP=20e9  # ps; within-step cycle spacing is <= 12 ms, step gaps >= ~200 ms
for ra,rb,b,_,_ in RUNS:
    t,c=load_tags(b); t7=t[c==7]
    d=np.diff(t7); big=np.where(d>SEG_GAP)[0]
    seg=np.zeros(len(t7),int); seg[big+1]=1; seg=np.cumsum(seg)
    starts=np.concatenate([[0],big+1]); cyc=np.arange(len(t7))-starts[seg]
    n0=np.bincount(np.searchsorted(t7,t[c==0],side='right')-1+1,minlength=len(t7)+1)[1:]
    n3=np.bincount(np.searchsorted(t7,t[c==3],side='right')-1+1,minlength=len(t7)+1)[1:]
    np.savez(f'{CACHE}/{b}_cycles.npz',t7=t7,seg=seg,cyc=cyc,n0=n0,n3=n3)
    segn=np.bincount(seg)
    print(ra,b,'cycles',len(t7),'segs',len(segn),'seg sizes != 200:',[(i,s) for i,s in enumerate(segn) if s!=200],
          'n3-n0 uniq',np.unique(n3-n0),'ch0/ch3 before first ch7',np.sum(t[c==0]<t7[0]),np.sum(t[c==3]<t7[0]),
          'early-ended cycles (n0<20)',int(np.sum(n0<20)),'n0>20',int(np.sum(n0>20)))
