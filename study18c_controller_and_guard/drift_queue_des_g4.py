"""Study 18C G4: the anytime guard under DRIFT and under PHYSICS-MODEL ERROR (pre-registered in README_G4.md).

G2/G3 (E69, E73): the guard delivered 0 bad pairs, but partly by construction (stationary links, exact physics). G4 breaks both.

Scenario D (drift). Each link drifts down linearly at g = 1e-5 /s and is re-aligned every Tre = 0.02/g = 2,000 s (the
  C2 sawtooth, amplitude 0.02), with a random phase on the 100-s epoch grid. Physics exact.
  * gnaive: the G2 guard (accumulates all counts since t = 0; ignores drift)            -> predicted UNSAFE
  * gdrift: Proposition 6' guard: restart the confidence sequence at each known re-alignment; bound the CURRENT lambda by
            lambda(L) - g*(t - t_reset), where L is the Beta-mixture lower bound from the counts since the reset; alpha
            spent over a link's cycles c = 1, 2, ... as 6 alpha / (pi^2 c^2).  Validity: within a cycle every event has
            lambda_e <= lambda_now + g (t - t_reset), so the bits are stochastically dominated (bitwise coupling) by iid bits
            at that value; the Beta-mixture lower bound is monotone in the counts, hence covers it anytime (Ville).
Scenario M (model error; no drift). Truth: preset T2 and gate error e. The controller (Bayesian part AND guard) believes
  T2_c = 1.25 T2 and e_c = 0.8 e (optimistic by 25% / 20%).  Scenario M50: T2_c = 1.5 T2, e_c = 0.6 e (the declared
  +-25% set of grobust then does NOT cover the truth: worst case 1.125 T2 and 0.75 e).
  * gnom:    guard evaluated with the controller's (wrong) nominal physics                   -> predicted UNSAFE
  * grobust: guard evaluated at the worst case of a DECLARED uncertainty set around the nominal model,
             T2 in [0.75, 1] T2_c and e in [e_c, 1.25 e_c]  (covers the truth: 0.9375 T2 and exactly e).
In both scenarios 'cal' (no guard) is reported for reference. Everything else is G2 (5 x 5 grid, best routing).
"""
import hashlib, json, sys
import numpy as np
import ptm_model as ptm
import drift_queue_des_g1 as g1
import drift_queue_des_g2 as g2

ALPHA = g2.ALPHA; G = 1e-5; TRE = 0.02 / G; NEP_CYCLE = int(round(TRE / g1.T)); NNET = 64
SEEDS = (19131, 19132, 19133, 19134)        # fresh confirmatory; cloud dev pilot used 20131-20134
CTRLS = {"D": ("cal", "gnaive", "gdrift"), "M": ("cal", "gnom", "grobust"), "M50": ("cal", "gnom", "grobust")}
MERR = {"M": (1.25, 0.8), "M50": (1.5, 0.6)}      # controller belief / truth for T2 and gate error e


class NetG4(g1.Net):
    def __init__(s, hw, scen, ctrl, seed):
        super().__init__(hw, "grid", 0, "cal", "best", seed)
        s.scen, s.gctrl = scen, ctrl; s.Ptrue = dict(s.P); s.Pc = dict(s.P)
        net_rng = np.random.default_rng(list(seed[2:]) + [41])
        if scen == "D":
            # the G1 draw gave lambda0 - 0.02 u; re-draw the phase on the epoch grid and keep lambda0 = (4F0 - 1)/3
            F0 = g1.v18.draw_F0(s.P, 1, s.nl, np.random.default_rng(seed[2:]), "normal")[:, 0]
            s.lam0 = np.clip((4 * F0 - 1) / 3, 0, 1); s.off = net_rng.integers(0, NEP_CYCLE, s.nl)    # phase in epochs
            s.lam = s.lam_at(0.0)
        else:
            ft, fe = MERR[scen]; s.Pc["T2"] = ft * s.P["T2"]; s.Pc["e"] = fe * s.P["e"]
        s.N = np.zeros(s.nl); s.K = np.zeros(s.nl); s.cyc_id = np.full(s.nl, -10 ** 6); s.ncyc = np.zeros(s.nl, int)
        s.lamlo = np.zeros(s.nl); s.acc_ep = -10 ** 9; s.pstat = {}

    # ---- drift helpers (scenario D) ----
    def phase(s, t): return (t + s.off * g1.T) % TRE                                     # time since last re-alignment
    def lam_at(s, t): return np.clip(s.lam0 - G * s.phase(t), 0, 1)
    def cycle_of(s, t): return np.floor((t + s.off * g1.T) / TRE).astype(int)

    def epoch_data(s, e):
        if e == s.ep: return
        if s.scen == "D":                                   # counts measure the epoch-average lambda (exact for the sawtooth)
            a = e * g1.T; ts = a + (np.arange(20) + 0.5) / 20 * g1.T
            keep = s.lam; s.lam = np.mean([s.lam_at(x) for x in ts], axis=0)
            g1.Net.epoch_data(s, e); s.lam = keep
        else:
            g1.Net.epoch_data(s, e)
        if e <= s.acc_ep: return
        s.acc_ep = e
        if s.gctrl in ("gdrift",):
            cid = s.cycle_of(np.full(s.nl, e * g1.T)); new = cid != s.cyc_id
            s.N[new] = 0; s.K[new] = 0; s.ncyc[new] += 1; s.cyc_id = cid
        s.N += s.n; s.K += s.kc
        if s.gctrl == "gdrift":
            lev = ALPHA * 6 / (np.pi ** 2 * s.ncyc ** 2) / s.Lmax
        else:
            lev = np.full(s.nl, ALPHA / s.Lmax)
        plo = g2.cs_lower(s.N, s.K, lev); s.lamlo = np.clip((2 * plo - 1) / s.r, 0, 1)

    def guard_lam(s, links, t):
        lk = list(links); lo = s.lamlo[lk].copy()
        if s.gctrl == "gdrift":
            same = s.cycle_of(np.full(s.nl, t))[lk] == s.cyc_id[lk]             # data must come from the current cycle
            lo = np.where(same, np.clip(lo - G * s.phase(t)[lk], 0, 1), 0.0)
        return lo

    def guard_F(s, links, t, w1, w2, hold):
        lo = s.guard_lam(links, t)[None, :]
        if s.gctrl == "grobust":
            return float(ptm.delivered_F(lo, w1, w2, hold, 1.25 * s.Pc["e"], np.inf, 0.75 * s.Pc["T2"])[0])
        return float(ptm.delivered_F(lo, w1, w2, hold, s.Pc["e"], np.inf, s.Pc["T2"])[0])

    def trueF(s, links, w1, w2, hold):
        return float(ptm.delivered_F(s.lam[list(links)][None, :], w1, w2, hold, s.Ptrue["e"], np.inf, s.Ptrue["T2"])[0])

    def run(s):
        Pc = s.Pc; t = 0.0; H = g1.NEPOCH * g1.T; guard = s.gctrl != "cal"
        out = dict(requests=0, delivered=0, bad=0, qual=0, oracle_qual=0, guard_blocks=0)
        arr = s.rng.exponential(1 / s.rate)
        while arr < H:
            t = max(t, arr); arr += s.rng.exponential(1 / s.rate)
            if s.scen == "D": s.lam = s.lam_at(t)
            cset = s.cands[int(s.rng.integers(len(s.cands)))]
            s.epoch_data(int(t // g1.T) - 1)
            path = cset[int(np.argmax([np.log(np.maximum(s.est[list(c)], 1e-9)).sum() for c in cset]))] if len(cset) > 1 else cset[0]
            meas = t >= g1.WARM_EPOCH * g1.T
            if meas: out["requests"] += 1
            op = cset[int(np.argmax([np.log(np.maximum(s.lam[list(c)], 1e-9)).sum() for c in cset]))]; to = t
            for _ in range(g1.BUDGET):
                w1, w2, hold, to = s.chains(s.orng, to, len(op))
                if s.trueF(op, w1, w2, hold) >= s.tau:
                    if meas: out["oracle_qual"] += 1
                    break
            for _ in range(g1.BUDGET):
                w1, w2, hold, t = s.chains(s.rng, t, len(path)); s.epoch_data(int(t // g1.T) - 1)
                if s.scen == "D": s.lam = s.lam_at(t)
                Ft = s.trueF(path, w1, w2, hold); ld = s.draws(path)
                Fs = ptm.delivered_F(ld, w1, w2, hold, Pc["e"], np.inf, Pc["T2"]); pbad = ((Fs < s.tau).sum() + 0.5) / (g1.M + 1)
                thr = s.choose_t(); s.pb[s.nb % g1.WIN] = pbad; s.nb += 1
                ok = pbad <= thr
                if ok and guard and s.guard_F(path, t, w1, w2, hold) < s.tau:
                    ok = False
                    if meas: out["guard_blocks"] += 1
                if ok:
                    if meas:
                        out["delivered"] += 1; out["bad"] += int(Ft < s.tau); out["qual"] += int(Ft >= s.tau)
                        st = s.pstat.setdefault(path, [0, 0]); st[0] += 1; st[1] += int(Ft < s.tau)
                    break
        out["paths_delivered"] = sum(1 for v in s.pstat.values() if v[0] > 0)
        out["paths_bad"] = sum(1 for v in s.pstat.values() if v[1] > 0)
        out["max_path_bad"] = max([v[1] for v in s.pstat.values()] or [0])
        return out


def tasks():
    return [["G4", hw, scen, c, i] for hw in ("ion2020", "ionproj") for scen in ("D", "M", "M50") for c in CTRLS[scen] for i in range(NNET)]


def run_id(t):
    return hashlib.sha256("g4|{}|{}|{}|{}|{}".format(*t).encode()).hexdigest()[:12]


def run_one(t, seeds=SEEDS):
    blk, hw, scen, ctrl, idx = t
    nseed = int(hashlib.sha256(f"g4net|{hw}|{scen}|{idx}".encode()).hexdigest()[:8], 16)        # paired across controllers
    rseed = int(hashlib.sha256(f"g4run|{hw}|{scen}|{idx}".encode()).hexdigest()[:8], 16)
    net = NetG4(hw, scen, ctrl, [rseed, seeds[1], nseed, seeds[0] + seeds[2]])
    return dict(run=run_id(t), block=blk, hw=hw, scen=scen, ctrl=ctrl, idx=idx, **net.run())


if __name__ == "__main__":
    if sys.argv[1:2] == ["--write-tasks"]:
        ts = tasks()
        with open(sys.argv[2], "w") as f:
            for t in ts: f.write(json.dumps(t) + "\n")
        print(f"wrote {len(ts)} tasks")
