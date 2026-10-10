# Study 23: a global AI model and RL routing under the safety guard. 4-day trial plan (10–13 Oct 2026)

**Folder:** `prx_work/23_ai_rl_guard/`. It is separate from Study 18C, and nothing in 18C changes.

**Rule:** if the go/no-go checks below fail, we stop and write the paper from Study 18C (G1–G7) as it is. A failure here is still reported in one paragraph of the main paper or in a short note.

## Research question

When link qualities are **correlated** (links that share hardware, a building or a fibre route tend to be similarly good or bad), can:

1. a **global AI model** that learns from the whole network's data, and
2. an **RL router** that learns which paths to try,

deliver more good pairs than the current Bayesian controller, **while the guard still keeps every user safe**?

## Why it is new, and why it might fail

- **New: the guard can use the AI's knowledge without losing its proof.** The guard's math allows any starting belief (prior), as long as that prior does not use the link's *own* data. A prior predicted from *neighbouring* links' data qualifies. If the AI predicts well, the guard's bound gets tighter, more good pairs pass, and the guarantee is unchanged.
- **New: RL can learn to route around uncertainty.** The current router picks the path with the best *average* estimate. The guard then blocks paths whose links are poorly measured. An RL router can learn to prefer paths the guard will accept.
- **Why it might fail:**
  - If correlations are weak, the AI has nothing to learn.
  - With ~5,500 checks per link per 100-s epoch, each link's own data may already be so good that neighbour information adds little after the first epochs. Thin-data hardware (NV) is where it should matter most.
  - RL matched but did not beat the planner in Studies 08–17.

## What gets built

| Day | Work | Output |
|---|---|---|
| **1 (10 Oct)** | Correlated-network simulator: each link's quality = fleet mean + shared regional factor + own noise, with the **same overall spread as the fleet**, so the old fleet prior stays honest on average. Train the global AI model: a small neural network that predicts a link's quality from its neighbours' data. Offline accuracy check. | `corr_net.py`, `ai_model.py`, trained weights `ai_weights.npz`, accuracy table |
| **2 (11 Oct)** | AI prior inside the Bayesian controller and inside the guard (fixed after warm-up, as the proof requires). RL router (policy gradient) trained on separate training networks, then frozen. Cloud pilot. | `study23.py`, pilot table, **go/no-go #2** |
| **3 (12 Oct)** | Pre-registration (hypotheses, locked analysis, hashes), then the PSC run | `README_23.md`, `analyze_23.py`; you run PSC |
| **4 (13 Oct)** | Analysis, write-up, decision: separate paper or a section of the main paper | `RESULTS_23.md` |

## Arms (planned)

| Arm | Belief | Router | Guard |
|---|---|---|---|
| `bg` (baseline, as G2) | Fleet prior | Greedy best estimate | Yes |
| `ag` | **AI prior** from neighbours | Greedy | Yes, with **AI prior** |
| `arg` | AI prior | **RL** | Yes, with AI prior |
| `ar` | AI prior | RL | **No** (shows why the guard is needed) |

**Scenarios:**
- correlation on (ρ = 0.7) and off (ρ = 0, a control where the AI should not help);
- hardware ion2020 and NV (thin data).

## Go/no-go checks (fixed now)

1. **End of day 1:** on held-out correlated networks, the AI must cut the prediction error of early-epoch link quality by **≥ 20%** relative to the fleet prior. If not, stop.
2. **End of day 2 (pilot):** `ag` or `arg` must deliver **≥ 2 points** more of oracle throughput than `bg` on correlated networks, with 0 bad pairs. If not, stop: write the main paper and report the negative result in one paragraph.
3. **PSC budget:** ceiling **64 SU**, only after your OK.

## What success would let you say

> "A global AI model and an RL router can raise throughput on correlated quantum networks, and a guard with a mathematical proof keeps every user safe whatever the AI does."

That is RL plus safety, a direct bridge to learned decoders (MIT) and learned chemistry models (Toronto).
