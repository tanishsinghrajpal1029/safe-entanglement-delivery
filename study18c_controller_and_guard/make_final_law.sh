#!/bin/bash
# Mechanically derive the final risk-law component from v8 (FINAL_PROTOCOL.md): new seed/run tags, rho 0.2, T 60 s.
set -euo pipefail
python3 - <<'PY'
s = open("drift_queue_des_v8.py").read()
rep = [('RHO, T, M, LOAD, D, H = 0.1, 30.0, 0.0, 0.9, 0.25, 300.0', 'RHO, T, M, LOAD, D, H = 0.2, 60.0, 0.0, 0.9, 0.25, 300.0'),
       ('f"v8|', 'f"flaw|'), ('f"v8seed|', 'f"flawseed|'), ('"v8|{}', '"flaw|{}'),
       ('script="drift_queue_des_v8.py"', 'script="drift_queue_des_final_law.py"'), ('default="des_v8"', 'default="des_final_law"'),
       ('"""Study 18C v8 = v7 code', '"""Study 18C FINAL risk-law component (FINAL_PROTOCOL.md): v8 code with rho 0.2, T 60 s, seed tags flaw.\nStudy 18C v8 = v7 code')]
for a, b in rep:
    assert s.count(a) >= 1, a
    s = s.replace(a, b)
open("drift_queue_des_final_law.py", "w").write(s)
PY
sha256sum drift_queue_des_final_law.py | cut -c1-16
