import sys, json, time
sys.path.insert(0, '/home/claude/s30')
import study30 as s
t = json.loads(sys.argv[1]); t0 = time.time(); r = s.run_one(t)
keys = ("delivered","bad","bad_after_alarm_all","deliv_after_alarm_all","viol_all","below_all","decreases","mc_k","alarms","first_alarm_ep","bad_after_alarm","deliv_after_alarm","users_bad_post","users_post","users_bad",
        "users_total","dec_mean_after","opt_mean_after","dec_final","probes","cs_n","cs_k","restarts","p10_tests","fa_seg_t","qual","oracle_qual")
print(json.dumps(t), round(time.time()-t0), {k: (round(r[k],4) if isinstance(r[k],float) else r[k]) for k in keys}, flush=True)
