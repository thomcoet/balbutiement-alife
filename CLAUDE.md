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

**Observed speed attractor: ~0.64** (emergent, not derivable from a single formula).

The simple ceiling without competition: `EAT_CAP * EAT_GAIN / MOVE_COST = 0.5 * 5.0 / 1.5 = 1.667`. This is the maximum speed that is energy-neutral when a cell is full and uncontested -- not an attractor.

The actual attractor (~0.64) is pulled down by competition. It is determined by the interplay of three constraints in order of dominance:

1. **Resource regeneration / grid carrying capacity** -- total energy injected per tick: `REGEN_ABS * GRID_SIZE^2 * EAT_GAIN = 0.05 * 6400 * 5.0 = 1600 energy/tick`. This sets the population ceiling (~1500 agents observed, ~1667 theoretical).
2. **Competition** -- at ~1500 agents on 6400 cells, effective food per agent is far below the maximum, which drags the viable speed down to ~0.64.
3. **Movement cost** -- cost scales linearly with speed; at high density, faster agents burn more than they gain.

With very few agents (e.g. N=5), competition is negligible and speed tends toward the ceiling (1.667). Population then grows until constraint 1 kicks in and competition restores the attractor.

All three environments converge to the same attractor. The environment only affects the transient trajectory.

## What has been done

- 3 environments implemented and compared (2500 ticks, seed=42)
- Results show all modes converge to same speed attractor (~0.64)
- Single-seed: Perlin appeared to maintain slightly higher genetic diversity (sigma 0.117 vs 0.104) and one extra lineage -- but this was a seed-42 artifact
- Drought creates early resource accumulation but stabilizes like flat at equilibrium
- Comparison notebook complete (fully in English)
- **Multi-seed runs completed** (10 seeds x 3 modes = 30 runs, seeds 42-51)
  - No statistically significant difference between any pair of modes on any metric (all p >> 0.05, Mann-Whitney U)
  - Final speed: flat 0.643 +/- 0.032, perlin 0.642 +/- 0.049, drought 0.634 +/- 0.048
  - Lineages: flat 6.6 +/- 1.5, perlin 7.0 +/- 1.5, drought 6.2 +/- 1.4
  - Conclusion: the energy-balance attractor fully dominates; environment type has no measurable effect on equilibrium outcome
- Multiseed notebook complete with confidence intervals, box plots, statistical tests, and conclusions

## Key insight from multi-seed analysis

The single-seed differences (Perlin slightly better) were within natural variability. The attractor formula in early notes was wrong (2.5/1.5 = 1.667, not 0.67). The ~0.64 attractor is emergent from competition + resource flux, not derivable from energy balance alone.

## What's next (in order)

1. **Unpredictable drought** -- random drift direction each tick instead of constant. Hypothesis: fast agents regain a durable advantage because the terrain changes faster than the population can adapt, temporarily relaxing competition pressure near moving oases. However, the advantage won't be permanent: as fast agents proliferate, competition rises and pulls speed back down.
2. **Second genetic trait** -- add perception range to the genome, couple it to a sensing behavior in `agent.move()`

## Stack

Python 3.12, numpy, matplotlib, jupyterlab. Virtual env at `.venv/`. Run with `.venv/bin/python`.

## Style notes

No em-dashes in produced text.
