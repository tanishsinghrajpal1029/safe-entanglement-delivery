"""Study 23: train the RL router by policy search (cross-entropy method, CEM) on separate TRAINING networks.

One PSC array element trains one configuration (index 0-7):
    (hw, data, arm) in ion2020/ionproj x dense/thin x rg/arg     ('rg' = fleet belief + Beta guard, 'arg' = AI + AI guard)
Training networks are correlated (rho_c = 0.7) and drawn from seeds 50000+ (never used by the pilot or confirmatory runs).
CEM: policy theta (5 weights; the hop weight is fixed at 0 because all candidates have equal hops). Each generation samples POP
policies around the current mean, evaluates each on the SAME K training networks (common random numbers), keeps the best ELITE
by mean fraction-of-oracle good pairs (the reward: good pairs delivered; a bad pair cannot be delivered with the guard on),
and refits mean and sd. Generation 0 includes the greedy policy so the result can only match or beat greedy on training data.
Usage: python3 train_rl.py <config index 0-7> <workers>      -> policy_<hw>_<data>_<arm>.json, trainlog_<hw>_<data>_<arm>.json
"""
import json, os, sys, time
import numpy as np
from multiprocessing import Pool
import study23 as s23

CONFIGS = [(hw, data, arm) for hw in ("ion2020", "ionproj") for data in ("dense", "thin") for arm in ("rg", "arg")]
POP, ELITE, K, GENS = 20, 5, 4, 8
SD0 = np.array([0.5, 1.0, 0.0, 2.0, 2.0])


def evaluate(args):
    hw, data, arm, theta, netseed = args
    net = s23.Net23(hw, 0.7, data, arm, [netseed, 7, netseed + 1, 11], theta=theta)
    o = net.run(); return o["qual"] / max(o["oracle_qual"], 1)


def main(ci, workers):
    hw, data, arm = CONFIGS[ci]; rng = np.random.default_rng(5000 + ci)
    mean = s23.GREEDY.copy(); sd = SD0.copy(); log = []; t0 = time.time()
    with Pool(workers) as pool:
        for gen in range(GENS):
            cand = mean[None, :] + sd[None, :] * rng.normal(0, 1, (POP, 5))
            if gen == 0: cand[0] = s23.GREEDY
            cand[1] = mean
            seeds = [50000 + 1000 * ci + 10 * gen + j for j in range(K)]
            jobs = [(hw, data, arm, list(c), sd_) for c in cand for sd_ in seeds]
            sc = np.array(pool.map(evaluate, jobs)).reshape(POP, K).mean(1)
            el = np.argsort(sc)[::-1][:ELITE]
            log.append(dict(gen=gen, best=float(sc[el[0]]), elite_mean=float(sc[el].mean()), mean_policy_score=float(sc[1]),
                            greedy_score=float(sc[0]) if gen == 0 else None, mean=mean.tolist(), sd=sd.tolist(), sec=round(time.time() - t0)))
            print(json.dumps(log[-1]), flush=True)
            mean = cand[el].mean(0); sd = np.maximum(cand[el].std(0), 0.05 * SD0)
            sd[2] = 0.0; mean[2] = 0.0
    # final check: mean policy vs greedy on fresh training networks
    seeds = [59000 + 100 * ci + j for j in range(16)]
    with Pool(workers) as pool:
        fin = np.array(pool.map(evaluate, [(hw, data, arm, list(th), sd_) for th in (mean, s23.GREEDY) for sd_ in seeds])).reshape(2, 16)
    res = dict(hw=hw, data=data, arm=arm, theta=mean.tolist(), final_mean_policy=float(fin[0].mean()), final_greedy=float(fin[1].mean()),
               final_paired_gain=float((fin[0] - fin[1]).mean()), final_paired_gain_se=float((fin[0] - fin[1]).std(ddof=1) / 4))
    json.dump(res, open(f"policy_{hw}_{data}_{arm}.json", "w"), indent=1)
    json.dump(log, open(f"trainlog_{hw}_{data}_{arm}.json", "w"), indent=1)
    print(json.dumps(res), flush=True)


if __name__ == "__main__":
    main(int(sys.argv[1]), int(sys.argv[2]))
