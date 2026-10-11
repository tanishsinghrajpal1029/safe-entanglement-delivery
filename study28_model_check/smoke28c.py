import time
from multiprocessing import Pool
import study28 as s
T = [["P28","ion2020","field",a,c,0] for a,c in (("kgM","o0.044_m0|p10"),("kgP","o0.044_m0|p10"),("kgM","ro|p10"),("kgM","o0.044_m0|p20"))] + [["P28","nv2","field","kgM","ro|p10",0]]
keys=["delivered","bad","p10_kept_bad","users_bad","p10_tests","alarms","first_alarm_ep","fa_first_t","fa_seg_t","inc_max","seg_n_min","dec_final","bad_after_alarm","deliv_after_alarm","qual","oracle_qual","p10_viol","p10_L","p10_F"]
def f(t):
    t0=time.time(); r=s.run_one(t); return t[1], t[3], t[4], round(time.time()-t0,1), {k:round(float(r[k]),4) for k in keys}
if __name__=="__main__":
    with Pool(2) as p:
        for x in p.imap(f, T): print(*x, flush=True)
