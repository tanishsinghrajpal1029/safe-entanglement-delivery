"""Study 24: AI v2 (and its linear control) for the guard's prior and the controller's belief.

What is new against AI v1 (Study 23):
  1. inputs are the neighbours' ACCUMULATED counts (all epochs so far), not one window;
  2. two leave-one-out network statistics let the model estimate the correlation strength itself (v1 was told rho = 0.7);
  3. trained on many smooth correlation patterns (ell in 0.75-3, rho ~ U(0, 0.9)); region and outlier patterns and ell = 0.4 are
     never seen in training (held out to test robustness);
  4. it predicts its own uncertainty (a second model for the log squared error), calibrated on validation networks.
The linear control uses exactly the same features, targets and calibration with linear regressions instead of MLPs.
Seeds: training 200000+, validation 300000+, offline test 310000+ (all disjoint from pilot 20241+ and confirmatory 19241+).
Usage: python3 ai_model24.py <hw>  -> ai2_<hw>.npz (MLP + linear weights), ai2_check_<hw>.json
"""
import json, sys, time
import numpy as np
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import LinearRegression
import hw24, corr_net24 as cn
import drift_queue_des_g1 as g1

TPTS = (1, 2, 3, 4, 6, 9, 12, 18, 24, 30)              # epochs of accumulated data the model must handle
NTRAIN, NVAL, NTEST = 2000, 400, 200


def sample(hw, seeds, drawer):
    X, Y = [], []
    P = g1.HW[hw][0]; lam_rate = hw24.RHO_CAL * P["R"] * g1.T; _, r, _, _, _ = hw24.consts(hw)
    for s in seeds:
        rng = np.random.default_rng(s); z = drawer(rng); lam = hw24.lam_from_z(rng, hw, z)
        n = rng.poisson(lam_rate, (max(TPTS), cn.NL)); k = rng.binomial(n, (1 + r * lam) / 2)
        Nc, Kc = np.cumsum(n, 0), np.cumsum(k, 0)
        _, _, _, mu, sdl = hw24.consts(hw); zt = (lam - mu) / sdl
        for e in TPTS:
            zh, v = hw24.zv(hw, Nc[e - 1], Kc[e - 1]); X.append(cn.features2(zh, v)); Y.append(zt)
    return np.vstack(X), np.concatenate(Y)


def fit(X, Y, Xv, Yv, kind):
    h = len(X) * 7 // 10
    if kind == "mlp":
        m = MLPRegressor(hidden_layer_sizes=(64, 64), alpha=1e-3, max_iter=200, random_state=24, early_stopping=True).fit(X[:h], Y[:h])
        res = Y[h:] - m.predict(X[h:])
        q = MLPRegressor(hidden_layer_sizes=(32,), alpha=1e-3, max_iter=200, random_state=25, early_stopping=True).fit(X[h:], np.log(res ** 2 + 1e-4))
    else:
        m = LinearRegression().fit(X[:h], Y[:h]); res = Y[h:] - m.predict(X[h:])
        q = LinearRegression().fit(X[h:], np.log(res ** 2 + 1e-4))
    rv = Yv - m.predict(Xv); c = float(np.sqrt(np.mean(rv ** 2 / np.exp(q.predict(Xv)))))     # calibration on validation
    return m, q, c


def export(m, q, c, kind):
    if kind == "mlp":
        W = {f"mW{i}": a for i, a in enumerate(m.coefs_)}; W.update({f"mb{i}": a for i, a in enumerate(m.intercepts_)})
        W.update({f"qW{i}": a for i, a in enumerate(q.coefs_)}); W.update({f"qb{i}": a for i, a in enumerate(q.intercepts_)})
    else:
        W = {"mW0": m.coef_[:, None], "mb0": np.atleast_1d(m.intercept_), "qW0": q.coef_[:, None], "qb0": np.atleast_1d(q.intercept_)}
    W["c"] = np.array([c]); return W


def forward(W, X, p):
    n = len([k for k in W if k.startswith(p + "W")]); h = X
    for i in range(n - 1): h = np.maximum(0, h @ W[f"{p}W{i}"] + W[f"{p}b{i}"])
    return (h @ W[f"{p}W{n - 1}"] + W[f"{p}b{n - 1}"]).ravel()


def predict(W, X):
    """mean z and calibrated sd (z units)."""
    return forward(W, X, "m"), W["c"][0] * np.exp(0.5 * forward(W, X, "q"))


def main(hw):
    t0 = time.time()
    X, Y = sample(hw, range(200000, 200000 + NTRAIN), cn.draw_train)
    Xv, Yv = sample(hw, range(300000, 300000 + NVAL), cn.draw_train)
    print(hw, "data", X.shape, round(time.time() - t0), "s", flush=True)
    out, store = {}, {}
    for kind in ("mlp", "lin"):
        m, q, c = fit(X, Y, Xv, Yv, kind); W = export(m, q, c, kind)
        store.update({f"{kind}_{k}": v for k, v in W.items()}); out[kind] = {}
        for pat, drawer in cn.PATTERNS.items():
            Xt, Yt = sample(hw, range(310000, 310000 + NTEST), drawer); mu, sd = predict(W, Xt)
            res = Yt - mu; ei = (np.arange(len(Yt)) // cn.NL) % len(TPTS)
            out[kind][pat] = dict(rmse=float(np.sqrt(np.mean(res ** 2))), cover95=float(np.mean(np.abs(res) < 1.96 * sd)),
                                  rmse_by_epoch={str(e): float(np.sqrt(np.mean(res[ei == i] ** 2))) for i, e in enumerate(TPTS)},
                                  mean_sd=float(np.mean(sd)))
        print(hw, kind, json.dumps({p: (round(v["rmse"], 3), round(v["cover95"], 3)) for p, v in out[kind].items()}), round(time.time() - t0), "s", flush=True)
    np.savez(f"ai2_{hw}.npz", **store); json.dump(out, open(f"ai2_check_{hw}.json", "w"), indent=1)


if __name__ == "__main__":
    main(sys.argv[1])
