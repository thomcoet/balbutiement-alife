"""
run_multi.py -- Batch runner for multi-seed experiments.

Runs the simulation N times per environment mode with different seeds,
then saves individual results + an aggregated summary for the notebook.

Usage
-----
    # 10 seeds, all 3 modes, 2500 ticks (defaults)
    python run_multi.py

    # Custom
    python run_multi.py --n-seeds 20 --ticks 1000 --modes flat perlin

Output
------
    experiments/multi/
        flat_s42/         <- one folder per (mode, seed)
            results.json
            timeseries.json
            config_run.json
            summary.txt
        flat_s43/
        ...
        aggregate.json    <- all runs summarized in one file (used by notebook)
"""

import sys
import json
import argparse
import time
from pathlib import Path

import numpy as np

SIM_DIR = Path(__file__).resolve().parent / "simulation"
sys.path.insert(0, str(SIM_DIR))

from run import run_simulation, compute_summary


def parse_args():
    p = argparse.ArgumentParser(description="Multi-seed ALife batch runner")
    p.add_argument("--n-seeds",   type=int,   default=10,
                   help="Number of seeds to run per mode (default: 10)")
    p.add_argument("--start-seed", type=int,  default=42,
                   help="First seed value (default: 42)")
    p.add_argument("--ticks",     type=int,   default=2500,
                   help="Ticks per run (default: 2500)")
    p.add_argument("--modes",     nargs="+",  default=["flat", "perlin", "drought"],
                   choices=["flat", "perlin", "drought"],
                   help="Modes to run (default: all 3)")
    p.add_argument("--out-dir",   type=str,   default="experiments/multi",
                   help="Output directory (default: experiments/multi)")
    p.add_argument("--n-agents",  type=int,   default=15)
    p.add_argument("--mutation",  type=float, default=0.06)
    p.add_argument("--regen",     type=float, default=0.05)
    return p.parse_args()


def main():
    args  = parse_args()
    seeds = list(range(args.start_seed, args.start_seed + args.n_seeds))
    out   = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    total = len(args.modes) * len(seeds)
    print(f"\n  Multi-seed batch: {len(args.modes)} modes x {len(seeds)} seeds = {total} runs")
    print(f"  Ticks per run : {args.ticks}")
    print(f"  Output        : {out.resolve()}")
    print(f"  {'='*55}\n")

    all_summaries = []
    t_batch = time.time()
    run_idx = 0

    for mode in args.modes:
        for seed in seeds:
            run_idx += 1
            run_dir = out / f"{mode}_s{seed}"
            run_dir.mkdir(parents=True, exist_ok=True)

            print(f"  [{run_idx:>3}/{total}]  {mode:8s}  seed={seed}", end="", flush=True)
            t0 = time.time()

            data    = run_simulation(mode, args.ticks, seed,
                                     args.n_agents, args.mutation, args.regen)
            summary = compute_summary(data)

            # Save individual run files
            (run_dir / "results.json").write_text(
                json.dumps(summary, indent=2), encoding="utf-8")
            (run_dir / "timeseries.json").write_text(
                json.dumps({
                    "timeseries"  : data["timeseries"],
                    "lineage_ts"  : data["lineage_ts"],
                    "final_agents": data["final_agents"],
                    "meta"        : data["meta"],
                }, indent=2), encoding="utf-8")
            (run_dir / "config_run.json").write_text(
                json.dumps(data["meta"], indent=2), encoding="utf-8")

            all_summaries.append(summary)
            print(f"  ({time.time()-t0:.1f}s)  spd={summary['speed_final']:.3f}"
                  f"  pop={summary['pop_final']}")

    # Aggregate stats per mode
    aggregate = {}
    for mode in args.modes:
        runs = [s for s in all_summaries if s["mode"] == mode]

        def stats(key):
            vals = [r[key] for r in runs if r[key] is not None]
            if not vals:
                return {"mean": None, "std": None, "min": None, "max": None, "values": []}
            return {
                "mean"  : round(float(np.mean(vals)),  4),
                "std"   : round(float(np.std(vals)),   4),
                "min"   : round(float(np.min(vals)),   4),
                "max"   : round(float(np.max(vals)),   4),
                "values": [round(float(v), 4) for v in vals],
            }

        aggregate[mode] = {
            "n_runs"          : len(runs),
            "seeds"           : seeds,
            "speed_final"     : stats("speed_final"),
            "speed_drift"     : stats("speed_drift"),
            "speed_std_final" : stats("speed_std_final"),
            "pop_final"       : stats("pop_final"),
            "pop_stable_mean" : stats("pop_stable_mean"),
            "lineages_final"  : stats("lineages_final"),
            "max_generation"  : stats("max_generation"),
            "res_mean_final"  : stats("res_mean_final"),
            "extinction_count": sum(1 for r in runs if r["extinction"] is not None),
        }

    (out / "aggregate.json").write_text(
        json.dumps(aggregate, indent=2), encoding="utf-8")

    elapsed = time.time() - t_batch
    print(f"\n  {'='*55}")
    print(f"  Batch done in {elapsed:.1f}s  ({total} runs)\n")

    # Quick summary table
    print(f"  {'Mode':<10} {'Speed mean':>12} {'Speed std':>10} {'Pop mean':>10} {'Lineages':>10}")
    print(f"  {'-'*55}")
    for mode in args.modes:
        a = aggregate[mode]
        print(f"  {mode:<10}"
              f"  {a['speed_final']['mean']:>8.3f} ± {a['speed_final']['std']:.3f}"
              f"  {a['pop_stable_mean']['mean']:>10.1f}"
              f"  {a['lineages_final']['mean']:>8.1f} ± {a['lineages_final']['std']:.1f}")

    print(f"\n  Saved to: {(out / 'aggregate.json').resolve()}\n")


if __name__ == "__main__":
    main()
