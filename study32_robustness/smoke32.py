import sys, json, time
sys.path.insert(0, '/home/claude/s32')
import study32 as s
t = json.loads(sys.argv[1]); t0 = time.time(); r = s.run_one(t)
keys = ("delivered","bad","alarms","forced","first_alarm_ep","bad_after_alarm_all","deliv_after_alarm_all","users_bad_post","users_post","dec_mean_after","opt_mean_after","dec_final","cs_n","decreases","mc_k","qual","oracle_qual","users_bad_all","users_total")
print(json.dumps(t), round(time.time()-t0), {k: (round(float(r[k]),4) if isinstance(r[k],float) else r[k]) for k in keys}, flush=True)
