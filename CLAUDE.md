# Project context

Agent-based ALife simulation in Python. Agents live on a resource grid, move (energy cost proportional to speed), eat, and reproduce by cloning with mutation. Speed is the only genetic trait. Selection is implicit: no fitness function, just survival mechanics.

## Key files

- `simulation/config.py` — all constants. Touch this first when changing simulation parameters.
- `simulation/agent.py` — Agent class + `simulation_step()`. One tick: regen, move, eat, reproduce, cull dead.
- `simulation/environment.py` — 3 modes: flat (uniform), perlin (heterogeneous static), drought (perlin that drifts).
- `simulation/noise.py` — 2D Simplex noise, pure NumPy. No external noise library.
- `simulation/main.py` — interactive GUI entry point (matplotlib animation).
- `run.py` — headless runner. Outputs `results.json`, `timeseries.json`, `config_run.json`, `summary.txt` to a given `--out-dir`.
- `comparison_notebook.ipynb` — reads experiment JSONs from `experiments/`, produces comparison plots.

## Experiment structure

```
experiments/
  exp_flat/        # python run.py --mode flat    --out-dir experiments/exp_flat
  exp_perlin/      # python run.py --mode perlin  --out-dir experiments/exp_perlin
  exp_drought/     # python run.py --mode drought --out-dir experiments/exp_drought
```

Each folder contains: `results.json` (aggregated metrics), `timeseries.json` (full time series), `config_run.json`, `summary.txt`.

## Energy balance (critical)

```
move_cost  = speed * 1.5  per tick
eat_gain   = min(resource/n_agents_on_cell, 0.5) * 5.0
repro_cost = parent drops to 40 energy (fixed, not percentage)
death      = energy < -10
repro      = energy >= 150
```

The mathematical speed attractor is ~0.67 (gain_max / move_cost = 2.5 / 1.5). All environments converge there at equilibrium. Environment only affects the transient trajectory.

## What has been done

- 3 environments implemented and compared (2500 ticks, seed=42)
- Results show all modes converge to same speed attractor (~0.64)
- Perlin maintains slightly higher genetic diversity (sigma 0.117 vs 0.104) and one extra lineage
- Drought creates early resource accumulation but stabilizes like flat at equilibrium
- Comparison notebook complete with observations and interpretation

## What's next (in order)

1. **Multi-seed runs** — run each mode N times with different seeds, average results, add confidence intervals to notebook plots
2. **Second genetic trait** — add perception range to the genome, couple it to a sensing behavior in `agent.move()`
3. **Unpredictable drought** — random drift direction each tick instead of constant, test if fast agents regain advantage

## Stack

Python 3.12, numpy, matplotlib, jupyterlab. Virtual env at `.venv/`. Run with `.venv/bin/python`.

## Style notes

No em-dashes in produced text.
