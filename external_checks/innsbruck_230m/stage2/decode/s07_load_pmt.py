# Load per-cycle PMT counts: Node A (.dat PMTcounts(0..199), handles 1819 rows with one missing field) and Node B (PMT1_2)
from common import *
def nodeA_pmt(ra):
    f=f'{DATA}/Node_A/{ra}/{ra}.dat'
    lines=open(f).read().splitlines(); hdr=lines[0].split('\t'); nh=len(hdr)
    i0=hdr.index('PMTcounts(0)'); isum=hdr.index('PMTcounts(sum)')
    out=[]; nfix=0; bad=0
    for L in lines[1:]:
        v=L.split('\t')
        if len(v)==nh-4 and v[2]=='':   # 1819 rows>=3: the five APDscounts fields collapsed into one empty field
            v=v[:2]+['nan']*5+v[3:]; nfix+=1
        if len(v)!=nh: bad+=1; out.append(np.full(200,-1)); continue
        p=np.array(v[i0:i0+200],float)
        if abs(p.sum()-float(v[isum]))>0.5: bad+=1
        out.append(p)
    return np.array(out), nfix, bad
def nodeB_pmt(rb):
    d=pd.read_csv(f'{DATA}/Node_B/{rb}/PMT1_2.txt',sep='\t')
    cols=[f'PMT1_2({i})' for i in range(200)]
    p=d[cols].values.astype(float)
    sumok=np.all(np.abs(p.sum(1)-d['PMT1_2(sum)'].values)<0.5)
    return p, d, sumok
if __name__=='__main__':
    HA=np.zeros(301); HB=np.zeros(301)
    for ra,rb,*_ in RUNS:
        pa,nfix,bad=nodeA_pmt(ra); pb,d,ok=nodeB_pmt(rb)
        HA+=np.bincount(np.clip(pa.ravel().astype(int),0,300),minlength=301); HB+=np.bincount(np.clip(pb.ravel().astype(int),0,300),minlength=301)
        print(ra,rb,'A rows',pa.shape,'fixed rows',nfix,'bad rows',bad,'| B rows',pb.shape,'B sum ok',ok)
    print('A hist 0..80:',HA[:81].astype(int).tolist())
    print('B hist 0..80:',HB[:81].astype(int).tolist())
    print('B hist 80..200 by 10:',[int(HB[i:i+10].sum()) for i in range(80,200,10)])
