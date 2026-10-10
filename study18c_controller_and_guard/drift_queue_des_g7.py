"""Study 18C G7: a MORE SENSITIVE fault alarm for small link faults (pre-registration: README_G7.md, written after the dev pilot).

G6 (E81): the single-epoch alarm ('galarm': one epoch's upper bound below the guard's lower bound, level 1e-3) caught every
4-sd fault but only 87% of all faults (2-sd faults on ionproj: 58%), leaving 9-15 late bad pairs per group.

New alarm 'gglr': a generalized-likelihood-ratio (GLR) change detector per link. Within the data since the link's last
restart, for each candidate change point c in the last W = 4 epochs, compare the parity rate before (N0, K0) and after
(N1, K1) c:  GLR_c = l(K0,N0) + l(K1,N1) - l(K0+K1, N0+N1), with l(K,N) = K log(K/N) + (N-K) log(1-K/N), counted only
if the rate after c is LOWER (a fault lowers quality). Alarm if max_c GLR_c > h. On alarm: discard the link's counts, restart
the confidence sequence, spend alpha as 6 alpha / (pi^2 c^2) (as galarm). Pooling several epochs gives power for small drops.
Two thresholds: gglr (h = H_STD) and gglr_s (h = H_SENS, more sensitive, more false alarms). Values set from the dev pilot
(disclosed in the README); the confirmatory run uses fresh seeds.
Scenarios: F2 (2-sd drops, as G6) and F1 (1-sd drops, harder). Controllers: cal, galarm (G6), gglr, gglr_s.
"""
import hashlib, json, sys
import numpy as np
import drift_queue_des_g1 as g1
import drift_queue_des_g2 as g2
import drift_queue_des_g6 as g6

W, MIN_N0 = 4, 50
H_STD, H_SENS = 9.0, 6.0
g6.DROP.update({"F1": 1.0})
SEEDS = (19161, 19162, 19163, 19164)        # fresh confirmatory; dev pilot used 20161-20164
CTRLS = ("cal", "galarm", "gglr", "gglr_s")


def ll(K, N):
    p = np.clip(K / np.maximum(N, 1), 1e-12, 1 - 1e-12)
    return np.where(N > 0, K * np.log(p) + (N - K) * np.log1p(-p), 0.0)


class NetG7(g6.NetG6):
    def __init__(s, hw, scen, ctrl, seed):
        super().__init__(hw, scen, ctrl if ctrl in ("cal", "galarm") else "galarm", seed)
        s.gctrl = ctrl; s.hthr = {"gglr": H_STD, "gglr_s": H_SENS}.get(ctrl)
        s.hist_n = [[] for _ in range(s.nl)]; s.hist_k = [[] for _ in range(s.nl)]; s.false_al = 0

    def level(s):
        if s.gctrl in ("gglr", "gglr_s"): return g6.ALPHA * 6 / (np.pi ** 2 * s.ncyc ** 2) / s.Lmax
        return g6.NetG6.level(s)

    def epoch_data(s, e):
        if s.gctrl not in ("gglr", "gglr_s"): return g6.NetG6.epoch_data(s, e)
        if e == s.ep: return
        keep = s.lam; s.lam = s.lam_epoch(e); g1.Net.epoch_data(s, e); s.lam = keep
        if e <= s.acc_ep: return
        s.acc_ep = e
        for l in range(s.nl):
            s.hist_n[l].append(int(s.n[l])); s.hist_k[l].append(int(s.kc[l]))
            hn = np.array(s.hist_n[l], float); hk = np.array(s.hist_k[l], float); m = len(hn)
            best = 0.0
            for w in range(1, min(W, m - 1) + 1):
                N1, K1 = hn[-w:].sum(), hk[-w:].sum(); N0, K0 = hn[:-w].sum(), hk[:-w].sum()
                if N0 < MIN_N0 or N1 == 0 or K1 / N1 >= K0 / N0: continue
                best = max(best, float(ll(K0, N0) + ll(K1, N1) - ll(K0 + K1, N0 + N1)))
            if best > s.hthr:
                s.false_al += int((not s.faulted[l]) or e < s.fep[l])
                s.hist_n[l] = []; s.hist_k[l] = []; s.N[l] = 0; s.K[l] = 0; s.ncyc[l] += 1; s.alarms[l] += 1
                if s.alarm_ep[l] < 0 or (s.faulted[l] and s.alarm_ep[l] < s.fep[l]): s.alarm_ep[l] = e
                continue
            s.N[l] += s.n[l]; s.K[l] += s.kc[l]
        plo = g2.cs_lower(s.N, s.K, s.level()); s.lamlo = np.clip((2 * plo - 1) / s.r, 0, 1)

    def run(s):
        out = g6.NetG6.run(s)
        # detection = an alarm at or after the fault epoch (false alarms before the fault do not count as detection)
        det = [(s.alarm_ep[l] - s.fep[l]) for l in np.where(s.faulted & (s.alarm_ep >= s.fep))[0]]
        out["detected"] = len(det); out["mean_delay_ep"] = float(np.mean(det)) if det else -1.0
        if s.gctrl in ("gglr", "gglr_s"): out["alarms_false"] = s.false_al
        return out


def tasks():
    return [["G7", hw, scen, c, i] for hw in ("ion2020", "ionproj") for scen in ("F2", "F1") for c in CTRLS for i in range(g6.NNET)]


def run_id(t):
    return hashlib.sha256("g7|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, scen, ctrl, idx = t
    nseed = int(hashlib.sha256(f"g7net|{hw}|{scen}|{idx}".encode()).hexdigest()[:8], 16)
    rseed = int(hashlib.sha256(f"g7run|{hw}|{scen}|{idx}".encode()).hexdigest()[:8], 16)
    net = NetG7(hw, scen, ctrl, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    return dict(run=run_id(t), block=blk, hw=hw, scen=scen, ctrl=ctrl, idx=idx, **net.run())


if __name__ == "__main__":
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
