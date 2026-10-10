# Decode Node A APD*.raw marker files: big-endian u32 words; 0xf0000000 = frame separator (counter period P units);
# data word: top nibble 0xf, bits 4..27 = time within frame, bits 0..3 = channel (1 = apd_marker0, 2 = apd_marker1).
# Words with top nibble != 0xf (rare) are ignored. Per cycle: marker0 count = 1 (pre-loop) + n_loops_run + 1 (post-branch).
from common import *
import glob
P=13168640  # frame period in counter units (from data: in-loop marker1->marker0 gap with/without an intervening separator)
CYC_GAP=20_000_000  # units (~1.3 ms); in-cycle gaps <= ~6e6, between cycles ~5e7
def decode(f):
    w=np.fromfile(f,dtype='>u4'); issep=w==0xf0000000; ns=np.cumsum(issep)
    m=(~issep)&((w>>28)==15); idx=np.where(m)[0]
    T=ns[idx].astype(np.int64)*P+((w[idx]>>4)&0xFFFFFF).astype(np.int64); ch=(w[idx]&0xF).astype(int)
    ok=(ch==1)|(ch==2); T=T[ok]; ch=ch[ok]
    if len(T)==0: return np.array([],int), 0, 0
    nonmono=int(np.sum(np.diff(T)<0))
    cy=np.concatenate([[0],np.cumsum(np.diff(T)>CYC_GAP)])
    m0=np.bincount(cy[ch==1],minlength=cy[-1]+1); m1=np.bincount(cy[ch==2],minlength=cy[-1]+1)
    return m0-2, nonmono, (m0!=m1).sum()
out={}
for ra,*_ in RUNS:
    fs=sorted(glob.glob(f'{DATA}/Node_A/{ra}/APD*.raw'))
    L=[]; bad=0; ncyc=[]; mism=0
    for f in fs:
        loops,nm,mm=decode(f); L.append(loops); bad+=nm; ncyc.append(len(loops)); mism+=mm
    ncyc=np.array(ncyc)
    out[ra]=dict(files=[os.path.basename(f) for f in fs],loops=L)
    allL=np.concatenate(L)
    print(ra,'files',len(fs),'first',os.path.basename(fs[0]),'last',os.path.basename(fs[-1]),'nonmono',bad,'m0!=m1 cycles',mism,
          'cycles/file uniq',np.unique(ncyc,return_counts=True),'loops<20:',int(np.sum(allL<20)),'loops>20',int(np.sum(allL>20)),flush=True)
import pickle; pickle.dump(out,open(f'{CACHE}/nodeA_loops.pkl','wb'))
