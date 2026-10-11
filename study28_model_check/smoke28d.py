import time
from multiprocessing import Pool
import study28 as s
T = [["P28",hw,"field","kgM",c,i] for hw,c,i in (("ion2020","o0.044_m0|p10",0),("ion2020","o0.044_m0|p20",0),("ionproj","o0.044_m0|p10",0),("ionproj","o0.044_m0|p20",0))]
keys=["delivered","bad","p10_kept_bad","users_bad","alarms","first_alarm_ep","inc_max","dec_final","bad_after_alarm","deliv_after_alarm","qual","oracle_qual"]
def f(t):
    t0=time.time(); r=s.run_one(t); return t[1], t[3], t[4], round(time.time()-t0,1), {k:round(float(r[k]),4) for k in keys}
if __name__=="__main__":
    with Pool(2) as p:
        for x in p.imap(f, T): print(*x, flush=True)
