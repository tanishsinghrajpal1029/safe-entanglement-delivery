import time
from multiprocessing import Pool
import study29 as s
T = [["R28","ion2020","field",a,"o0.044_m0|p10",19] for a in ("kgM","kgMJ","kgMT")] + [["P29","ion2020","field","kgMT","-F|p10",0],["P29","ion2020","field","kgMT","o0.044_m0|p10",0],["P29","ion2020","field","kgMTa","-|p10",0]]
keys=["delivered","bad","alarms","forced","first_alarm_ep","seg_n_first","dec_final","dec_mean_after","dec_min_after","looks","decreases","bad_after_alarm","deliv_after_alarm","below_after_alarm","qual","oracle_qual","fa_first_t"]
def f(t):
    t0=time.time(); r=s.run_one(t); return t[0], t[1], t[3], t[4], round(time.time()-t0,1), {k:round(float(r[k]),4) for k in keys}
if __name__=="__main__":
    with Pool(2) as p:
        for x in p.imap(f, T): print(*x, flush=True)
