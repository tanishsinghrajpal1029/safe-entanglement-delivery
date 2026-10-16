"""Read-only: fetch creation/run timestamps of the two pre-registered IBM jobs (S31, S31b) and compare them with the
GitHub push times of their pre-registrations. Uses the IBM account YOU saved locally (QiskitRuntimeService());
this script never reads, prints or stores a token. It submits nothing and uses no QPU time.
Run:  python3 ibm_job_times.py      (writes ibm_job_times.json next to this file)"""
import json, os
from datetime import datetime, timezone
from qiskit_ibm_runtime import QiskitRuntimeService

JOBS = {"S31": ("db5s7lamb58s738aufbg", "2026-10-11T16:58:44Z"),    # job id, GitHub push time of the pre-registration
        "S31b": ("db5ubf04qg6s73c40k20", "2026-10-11T19:38:07Z")}
iso = lambda x: x.astimezone(timezone.utc).isoformat() if hasattr(x, "astimezone") else (str(x) if x is not None else None)

service = QiskitRuntimeService()
out = {}
for study, (jid, push) in JOBS.items():
    rec = dict(job_id=jid, prereg_push_utc=push)
    try:
        job = service.job(jid)
        rec["backend"] = job.backend().name if job.backend() else None
        rec["status"] = str(job.status())
        rec["creation_date_utc"] = iso(job.creation_date)
        try:
            m = job.metrics()
            ts = m.get("timestamps", {}) or {}
            rec.update({f"metrics_{k}": v for k, v in ts.items()})
            rec["usage"] = m.get("usage")
        except Exception as e:
            rec["metrics_error"] = type(e).__name__
        if rec.get("creation_date_utc"):
            c = datetime.fromisoformat(rec["creation_date_utc"].replace("Z", "+00:00"))
            p = datetime.fromisoformat(push.replace("Z", "+00:00"))
            rec["created_minus_push_s"] = round((c - p).total_seconds(), 1)
            rec["prereg_before_job"] = c > p
    except Exception as e:
        rec["error"] = f"{type(e).__name__}: {e}"[:200]
    out[study] = rec
path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ibm_job_times.json")
json.dump(dict(fetched_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"), jobs=out), open(path, "w"), indent=1)
print(json.dumps(out, indent=1))
