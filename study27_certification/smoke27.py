import sys, time; sys.path.insert(0, "/home/claude/s27")
import study27 as S
for t in [("S27","ion2020","field","kg","-|hot",0),("S27","ion2020","field","b","o0.044_m0|hot",0),("S27","nv2","field","kg","fault|uni",0),
          ("S27","siv","field","plug","n0.184_a|hot",0),("S27","ionproj","field","kg","n0.184_a|uni",1)]:
    t0=time.time(); r=S.run_one(list(t))
    print(t[1:5], f"{time.time()-t0:.1f}s deliv {r['delivered']} bad {r['bad']}",
          {k: (round(v,4) if isinstance(v,float) else v) for k,v in r.items() if k.startswith("p10") or k.startswith("p05_u_viol") or k.startswith("p20_u_viol")})
