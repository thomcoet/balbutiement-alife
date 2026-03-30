# balbutiement-alife

Simulation d'agents évolutifs en Python — exploration des dynamiques de sélection naturelle selon trois types d'environnements (flat, Perlin, drought). Premier projet A-Life, orienté apprentissage.

---

## What this is

An agent-based simulation where small creatures live on a resource landscape, eat, spend energy moving, and reproduce — passing their speed to their children with slight mutations. No explicit fitness function. Selection emerges from the mechanics.

The only genetic trait: **speed**. Fast agents explore more but burn more energy. Slow agents are frugal but might starve in resource-poor areas. Who survives depends on the environment.

Three environments to compare:
- **flat** — uniform resources, used as control
- **perlin** — heterogeneous static terrain with oases and deserts
- **drought** — same Perlin terrain, but the landscape slowly drifts over time

---

## What I learned building this

**Getting the energy balance right**

The hardest part wasn't the code — it was calibrating the energy balance. Early attempts had populations explode to 1000 agents in 30 ticks. The fix: reproduction drops the parent to a fixed low energy value (40), making it a genuine cost with a real recovery time. `energy /= 2` creates runaway growth; a fixed penalty doesn't.

**Building Simplex noise from scratch**

Implemented 2D Simplex noise in pure NumPy (no library). The drought mode drifts the noise coordinates each tick, making oases slowly migrate across the grid.

**Discovering the model's own limits**

After running 2500-tick experiments across all three modes, all environments converge to the same genetic attractor (~0.64 speed). The environment only changes *how fast* selection happens, not *where it ends up*. This is a direct consequence of the energy equations — there's a fixed mathematical optimum. Discovering this through data rather than intuition was the most valuable part of the project.

---

## Key results (seed=42, 2500 ticks)

| Metric | Flat | Perlin | Drought |
|---|---|---|---|
| Final speed | 0.639 | 0.664 | 0.629 |
| Speed drift | -0.721 | -0.697 | -0.731 |
| Speed diversity σ | 0.105 | 0.117 | 0.104 |
| Surviving lineages | 5/15 | 6/15 | 5/15 |
| Final population | 1542 | 1431 | 1556 |

Perlin is the only mode that consistently preserves one extra lineage and slightly higher genetic diversity — spatial heterogeneity creates refuges.

---

## Run it

```bash
# Create and activate virtual environment
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Interactive visualization (choose environment at launch)
.venv/bin/python simulation/main.py

# Headless experiment runner
.venv/bin/python run.py --mode flat    --ticks 2500 --out-dir experiments/exp_flat
.venv/bin/python run.py --mode perlin  --ticks 2500 --out-dir experiments/exp_perlin
.venv/bin/python run.py --mode drought --ticks 2500 --out-dir experiments/exp_drought

# Comparison notebook (after running experiments)
.venv/bin/jupyter lab comparison_notebook.ipynb
```

---

## Structure

```
simulation/
├── config.py         # all constants, documented
├── noise.py          # 2D Simplex noise, pure numpy
├── agent.py          # Agent class + simulation loop
├── environment.py    # flat / perlin / drought modes
├── visualization.py  # matplotlib multi-panel figure
└── main.py           # interactive entry point

run.py                # headless runner, outputs JSON + summary
comparison_notebook.ipynb  # side-by-side analysis of the 3 environments
experiments/          # generated experiment results (JSON + summaries)
```

---

## Stack

`numpy` · `matplotlib` · `jupyterlab` · `scipy` · Python 3.12 · no ML frameworks

The goal is to understand the mechanics, not to hide them behind a library.

---

## Contributing

```bash
git clone https://github.com/YOUR_USERNAME/balbutiement-alife.git
cd balbutiement-alife
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Requires Python 3.12+.

---

## What's next

- [ ] Multi-seed runs to separate signal from noise
- [ ] Second genetic trait (perception range) to observe trade-offs
- [ ] Unpredictable drought (random direction) to test if fast agents regain advantage
