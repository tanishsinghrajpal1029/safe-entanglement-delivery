import numpy as np, pandas as pd, os, sys
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data','Data','Calibrations','Node A','Local_ion_photon_entanglement')
S="1650.02 1651 1652 1652.02 1653 1653.02 1654 1655 1655.02 1656 1657.02 1658 1659 1700 1701 1702.02 1703 1703.02".split()
def load_pt(path, header=True):
    if header: t=pd.read_csv(path,sep=r'\s+')
    else: t=pd.read_csv(path,sep=r'\s+',header=None,names=['Scan_point','Loop','APD1','APD2','APD3','APD4'])
    return t
for s in S:
    d=np.loadtxt(f'{D}/{s}/{s}.dat',skiprows=1,delimiter='\t')
    t=load_pt(f'{D}/{s}/Photons_time.dat')
    nsp=t.Scan_point.max(); nb=nsp//200
    a3=[(t[(t.Scan_point-1)//200==b].APD3>0).sum() for b in range(nb)]
    a4=[(t[(t.Scan_point-1)//200==b].APD4>0).sum() for b in range(nb)]
    a12=int((t[['APD1','APD2']].values>0).sum())
    dat3=d[:,5].astype(int); dat4=d[:,6].astype(int)
    offs=[o for o in range(0,len(dat3)-nb+1) if (dat3[o:o+nb]==a3).all() and (dat4[o:o+nb]==a4).all()]
    nraw=len([f for f in os.listdir(f'{D}/{s}') if f.endswith('.raw')])
    af=f'{D}/{s}/all_files_in_one/photons_time.dat'
    extra=''
    if os.path.exists(af):
        a=load_pt(af,header=False)
        an=a.Scan_point.max()
        b3=[(a[(a.Scan_point-1)//200==b].APD3>0).sum() for b in range(an//200)]
        o2=[o for o in range(0,len(dat3)-len(b3)+1) if (dat3[o:o+len(b3)]==b3).all()]
        extra=f' | allinone rows={len(a)} maxSP={an} APD3-match-offsets={o2}'
    print(f'{s}: dat rows={len(d)} PTrows={len(t)} maxSP={nsp} nraw={nraw} APD1/2 clicks={a12} offsets matching APDscounts(3,4)={offs}{extra}')
