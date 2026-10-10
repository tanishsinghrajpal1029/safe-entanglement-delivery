"""Study 23, day 1: train the global AI model (MLP) that predicts a link's quality from its NEIGHBOURS' data only,
then check it offline against the fleet prior (go/no-go #1).

Usage: python3 ai_model.py train <hw>   -> ai_weights_<hw>.npz, ai_check_<hw>.json
Data: one calibration epoch per link (counts n ~ Poisson(rho_cal R T), k ~ Bin(n, (1 + r lambda)/2)), hardware ion2020.
Two data regimes: dense (rho_cal = 0.3, the G-series default, ~5,460 checks per epoch) and thin (rho_cal = 0.03, ~546).
Training networks use seeds 100000-121499; held-out check networks use seeds 23900-24299 (never used in training).
"""
import json, sys
import numpy as np
from sklearn.neural_network import MLPRegressor
import corr_net as cn
import drift_queue_des_g1 as g1

HW = sys.argv[2] if len(sys.argv) > 2 else "ion2020"


def hw_consts(hw):
    P = g1.HW[hw][0]; sdf = (1 - P["F0"]) * 0.2
    return P, (1 - 2 * P["q"]) ** 2, sdf, (4 * P["F0"] - 1) / 3 - g1.AMP * 0.5, np.sqrt((4 / 3 * sdf) ** 2 + g1.AMP ** 2 / 12)


P, R_PAR, SD_F, LAM_MU, SD_L = hw_consts(HW)
RHO_CAL = {"dense": 0.3, "thin": 0.03}


def draw_network(rng, rho_c):
    z = cn.draw_z(rng, rho_c); F0 = np.clip(P["F0"] + SD_F * z, 0.3, 0.9999)
    return np.clip((4 * F0 - 1) / 3 - g1.AMP * rng.uniform(0, 1, cn.NL), 0, 1)


def one_epoch(rng, lam, regime):
    n = rng.poisson(RHO_CAL[regime] * P["R"] * g1.T, cn.NL); k = rng.binomial(n, (1 + R_PAR * lam) / 2)
    lhat = np.clip((2 * (k + 0.5) / (n + 1) - 1) / R_PAR, 0, 1); se = 2 / R_PAR * np.sqrt(0.25 / np.maximum(n, 1))
    se = 2 / R_PAR * np.sqrt(np.clip((k + 0.5) / (n + 1) * (1 - (k + 0.5) / (n + 1)), 1e-6, 1) / np.maximum(n, 1))
    return n, k, lhat, se


def feats(lhat, n):
    zh = (lhat - LAM_MU) / SD_L
    return cn.features(zh, n, SD_L)


def build(seeds, regime, rho_c):
    X, Y, OWN, SE = [], [], [], []
    for s in seeds:
        rng = np.random.default_rng(s); lam = draw_network(rng, rho_c); n, k, lhat, se = one_epoch(rng, lam, regime)
        X.append(np.c_[feats(lhat, n), np.full(cn.NL, rho_c)]); Y.append((lam - LAM_MU) / SD_L); OWN.append(lhat); SE.append(se)
    return np.vstack(X), np.concatenate(Y), np.concatenate(OWN), np.concatenate(SE)


def mlp_forward(W, X):
    h = X
    for i in range(len(W) // 2 - 1):
        h = np.maximum(0, h @ W[f"W{i}"] + W[f"b{i}"])
    i = len(W) // 2 - 1
    return (h @ W[f"W{i}"] + W[f"b{i}"]).ravel()


def train():
    out = {}; Ws = {}
    for regime in ("dense", "thin"):
        Xs, Ys = [], []
        for j, rho_c in enumerate((0.0, 0.35, 0.7)):          # train across correlation strengths; rho_c is an input
            X, Y, _, _ = build(range(100000 + 10000 * j, 100000 + 10000 * j + 1500), regime, rho_c); Xs.append(X); Ys.append(Y)
        m = MLPRegressor(hidden_layer_sizes=(32, 32), alpha=1e-3, max_iter=300, random_state=23, early_stopping=True)
        m.fit(np.vstack(Xs), np.concatenate(Ys))
        W = {}
        for i, (c, b) in enumerate(zip(m.coefs_, m.intercepts_)): W[f"W{i}"] = c; W[f"b{i}"] = b
        Ws[regime] = W
        for rho_c in (0.0, 0.7):
            X, Y, OWN, SE = build(range(23900, 24300), regime, rho_c)
            pred = mlp_forward(W, X); res = Y - pred
            s_ai = float(np.std(res)); rmse_prior_fleet = float(np.sqrt(np.mean(Y ** 2))); rmse_prior_ai = float(np.sqrt(np.mean(res ** 2)))
            # posterior after ONE own epoch, Gaussian approximation: fleet prior N(0,1) vs AI prior N(pred, s_ai^2) (z units)
            zo = (OWN - LAM_MU) / SD_L; v_own = (SE / SD_L) ** 2
            post_f = zo / v_own / (1 / v_own + 1); post_a = (zo / v_own + pred / s_ai ** 2) / (1 / v_own + 1 / s_ai ** 2)
            rp_f = float(np.sqrt(np.mean((Y - post_f) ** 2))); rp_a = float(np.sqrt(np.mean((Y - post_a) ** 2)))
            out[f"{regime}_rho{rho_c}"] = dict(prior_rmse_fleet=rmse_prior_fleet, prior_rmse_ai=rmse_prior_ai,
                                               prior_reduction_pct=100 * (1 - rmse_prior_ai / rmse_prior_fleet),
                                               post1_rmse_fleet=rp_f, post1_rmse_ai=rp_a, post1_reduction_pct=100 * (1 - rp_a / rp_f),
                                               ai_resid_sd_z=s_ai, own_se_z_median=float(np.median(np.sqrt(v_own))))
    np.savez(f"ai_weights_{HW}.npz", **{f"{r}_{k}": v for r, W in Ws.items() for k, v in W.items()},
             meta=json.dumps(dict(hw=HW, lam_mu=LAM_MU, sd_l=SD_L, rho_cal=RHO_CAL)))
    json.dump(out, open(f"ai_check_{HW}.json", "w"), indent=1)
    for k, v in out.items(): print(k, {a: round(b, 3) for a, b in v.items()})


if __name__ == "__main__":
    if sys.argv[1:2] == ["train"]: train()
