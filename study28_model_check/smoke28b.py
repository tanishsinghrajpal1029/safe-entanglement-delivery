import time, sys, json
from multiprocessing import Pool
import study28 as s
T = [["P28","ion2020","field",a,c,0] for c in ("n0.184_a|p10","fault|p10") for a in ("kg","kgM")] + [["P28","nv2","field","kgM","o0.044_m0|p10",0], ["P28","siv","field","kgM","-|p10",0]]
keys=["delivered","bad","users_bad","tested","alarms","first_alarm_ep","first_null_viol_ep","false_alarm","bad_after_alarm","deliv_after_alarm","dec_final","qual","oracle_qual","bad_post_fault","deliv_post_fault"]
def f(t):
    t0=time.time(); r=s.run_one(t); return t[1], t[3], t[4], round(time.time()-t0,1), {k:(round(float(r[k]),4)) for k in keys}
if __name__=="__main__":
    with Pool(2) as p:
        for x in p.imap(f, T): print(*x, flush=True)
