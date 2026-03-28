"""
run.py — Runner headless pour une expérience ALife.

Lance la simulation sans interface graphique, collecte les métriques
tick par tick, et sauve tout dans results.json à la fin.

Usage
-----
    # Depuis le dossier d'une expérience (ex: experiments/exp_001_flat_baseline/)
    python run.py

    # Ou en spécifiant le mode directement
    python run.py --mode flat --ticks 600 --seed 42

    # Pour relancer exactement la même expérience
    python run.py --from-config config_run.json

Résultat
--------
    results/
        results.json       ← métriques agrégées (lisibles par le notebook)
        timeseries.json    ← séries temporelles complètes (pop, speed, lignées)
        config_run.json    ← snapshot exact des paramètres utilisés
        summary.txt        ← résumé humain imprimable

Ce fichier est pensé pour être lancé depuis le dossier d'une expérience.
Il remonte automatiquement dans sim/ pour importer les modules.
"""

import sys
import os
import json
import argparse
import time
from datetime import datetime
from pathlib import Path

import numpy as np

# ── Import des modules sim (chemin relatif robuste) ───────────────
SIM_DIR = Path(__file__).resolve().parent / "simulation"
sys.path.insert(0, str(SIM_DIR))

from config    import *
from noise     import build_perm
from agent     import Agent, simulation_step
from environment import Environment


# ── Argument parsing ──────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="ALife headless runner")
    p.add_argument("--mode",  default="flat",
                   choices=["flat","perlin","drought"],
                   help="Mode d'environnement")
    p.add_argument("--ticks", type=int,   default=600,
                   help="Nombre de ticks à simuler")
    p.add_argument("--seed",  type=int,   default=NOISE_SEED,
                   help="Graine aléatoire (reproductibilité)")
    p.add_argument("--n-agents", type=int, default=N_INIT,
                   help="Nombre d'agents initiaux")
    p.add_argument("--mutation", type=float, default=MUTATION_STD,
                   help="Écart-type de mutation")
    p.add_argument("--regen",   type=float, default=REGEN_ABS,
                   help="Taux de régénération absolu")
    p.add_argument("--from-config", type=str, default=None,
                   help="Recharge les paramètres depuis un config_run.json")
    p.add_argument("--out-dir", type=str, default="results",
                   help="Dossier de sortie (créé si absent)")
    return p.parse_args()


# ── Simulation headless ───────────────────────────────────────────

def run_simulation(mode, ticks, seed, n_agents, mutation, regen):
    """
    Exécute la simulation et retourne toutes les métriques collectées.

    Retourne
    --------
    dict avec :
        timeseries   : dict de listes (pop, speed_mean, speed_min, speed_max,
                       speed_std, res_mean, n_lineages) — une valeur par tick
        lineage_ts   : dict {lineage_id: [count_par_tick]}
        final_agents : liste de dicts décrivant chaque agent survivant
        meta         : informations sur le run
    """
    rng = np.random.default_rng(seed)
    env = Environment(mode, seed=seed)
    resource_grid, perlin_target = env.initial_state()

    agents = [
        Agent(
            x=rng.uniform(0, GRID_SIZE), y=rng.uniform(0, GRID_SIZE),
            energy=ENERGY_INIT, speed=rng.uniform(SPEED_MIN, SPEED_MAX),
            lineage=i, generation=0,
        )
        for i in range(n_agents)
    ]

    # Séries temporelles
    ts = dict(
        pop=[], speed_mean=[], speed_min=[], speed_max=[],
        speed_std=[], res_mean=[], res_std=[], n_lineages=[],
        n_births=[], n_deaths=[],
    )
    lineage_ts = {i: [] for i in range(n_agents)}
    extinction_tick = None

    print(f"\n  Mode: {mode.upper()}  |  Ticks: {ticks}  |  Seed: {seed}  |  Agents: {n_agents}")
    print(f"  {'─'*55}")
    print(f"  {'tick':>6}  {'pop':>5}  {'res̄':>6}  {'spd̄':>6}  {'lin':>5}  {'gen_max':>7}")
    print(f"  {'─'*55}")

    t_start = time.time()

    for tick in range(1, ticks + 1):
        new_target = env.tick_target(tick)
        if new_target is not None:
            perlin_target = new_target

        prev_count = len(agents)
        agents, new_born = simulation_step(
            agents, resource_grid, perlin_target, regen, mutation
        )
        births = len(new_born)
        deaths = prev_count - (len(agents) - births)

        # Métriques du tick
        spds = [a.speed for a in agents]
        lc   = {}
        for a in agents:
            lc[a.lineage] = lc.get(a.lineage, 0) + 1

        ts["pop"].append(len(agents))
        ts["speed_mean"].append(float(np.mean(spds)) if spds else 0.0)
        ts["speed_min"].append(float(np.min(spds)) if spds else 0.0)
        ts["speed_max"].append(float(np.max(spds)) if spds else 0.0)
        ts["speed_std"].append(float(np.std(spds)) if spds else 0.0)
        ts["res_mean"].append(float(resource_grid.mean()))
        ts["res_std"].append(float(resource_grid.std()))
        ts["n_lineages"].append(len(lc))
        ts["n_births"].append(births)
        ts["n_deaths"].append(deaths)

        for i in range(n_agents):
            lineage_ts[i].append(lc.get(i, 0))

        # Log console tous les 100 ticks
        if tick % 100 == 0 or tick == 1:
            max_gen = max((a.generation for a in agents), default=0)
            print(f"  {tick:>6}  {len(agents):>5}  {resource_grid.mean():>6.3f}"
                  f"  {np.mean(spds) if spds else 0:>6.3f}  {len(lc):>5}  {max_gen:>7}")

        if not agents:
            extinction_tick = tick
            print(f"\n  ⚠  Extinction totale au tick {tick}")
            break

    elapsed = time.time() - t_start

    # Snapshot des agents survivants
    final_agents = [
        dict(lineage=a.lineage, generation=a.generation,
             speed=round(float(a.speed), 4), energy=round(float(a.energy), 2),
             age=a.age, x=round(float(a.x), 2), y=round(float(a.y), 2))
        for a in agents
    ]

    print(f"\n  {'─'*55}")
    print(f"  Run terminé en {elapsed:.1f}s ({ticks/elapsed:.0f} ticks/s)")

    return dict(
        timeseries   = ts,
        lineage_ts   = {str(k): v for k, v in lineage_ts.items()},
        final_agents = final_agents,
        meta = dict(
            mode=mode, ticks_run=len(ts["pop"]), ticks_requested=ticks,
            seed=seed, n_agents_init=n_agents,
            mutation=mutation, regen=regen,
            extinction_tick=extinction_tick,
            elapsed_s=round(elapsed, 2),
            timestamp=datetime.now().isoformat(),
        ),
    )


# ── Métriques agrégées ────────────────────────────────────────────

def compute_summary(data: dict) -> dict:
    """
    Calcule les métriques agrégées d'un run pour comparaison rapide.

    Ces valeurs sont celles qu'on compare entre les 3 modes dans le notebook.
    """
    ts   = data["timeseries"]
    meta = data["meta"]
    T    = len(ts["pop"])
    agents = data["final_agents"]

    # Vitesse : drift total et taux de convergence
    spd_start = ts["speed_mean"][min(9, T-1)]   # moyenne des 10 premiers ticks
    spd_final = float(np.mean(ts["speed_mean"][-50:])) if T >= 50 else ts["speed_mean"][-1]
    spd_drift = spd_final - spd_start

    # Population
    pop_max   = max(ts["pop"]) if ts["pop"] else 0
    pop_final = ts["pop"][-1] if ts["pop"] else 0
    pop_stable_mean = float(np.mean(ts["pop"][-100:])) if T >= 100 else pop_final

    # Biodiversité génétique
    spd_std_final = float(np.mean(ts["speed_std"][-50:])) if T >= 50 else 0
    n_lin_final   = ts["n_lineages"][-1] if ts["n_lineages"] else 0

    # Ressources
    res_final = float(np.mean(ts["res_mean"][-50:])) if T >= 50 else ts["res_mean"][-1]

    # Génération max atteinte
    max_gen = max((a["generation"] for a in agents), default=0)

    return dict(
        mode             = meta["mode"],
        seed             = meta["seed"],
        ticks_run        = meta["ticks_run"],
        extinction       = meta["extinction_tick"],
        # Évolution génétique
        speed_initial    = round(spd_start, 4),
        speed_final      = round(spd_final, 4),
        speed_drift      = round(spd_drift, 4),
        speed_std_final  = round(spd_std_final, 4),
        # Démographie
        pop_max          = pop_max,
        pop_final        = pop_final,
        pop_stable_mean  = round(pop_stable_mean, 1),
        # Biodiversité
        lineages_final   = n_lin_final,
        lineages_initial = meta["n_agents_init"],
        max_generation   = max_gen,
        # Ressources
        res_mean_final   = round(res_final, 4),
        # Perf
        elapsed_s        = meta["elapsed_s"],
    )


def format_summary_txt(summary: dict, data: dict) -> str:
    """Résumé humain lisible (pour summary.txt)."""
    s = summary
    m = data["meta"]
    lines = [
        "═" * 58,
        f"  ALife Experiment — {s['mode'].upper()} environment",
        f"  Timestamp : {m['timestamp'][:19]}",
        f"  Seed      : {s['seed']}   Ticks: {s['ticks_run']}",
        "═" * 58,
        "",
        "  ÉVOLUTION GÉNÉTIQUE",
        f"    Vitesse initiale  : {s['speed_initial']:.3f}",
        f"    Vitesse finale    : {s['speed_final']:.3f}",
        f"    Drift total       : {s['speed_drift']:+.3f}  "
          + ("← lents favorisés" if s['speed_drift'] < -0.2 else
             "← rapides favorisés" if s['speed_drift'] > 0.1 else
             "← pas de pression forte"),
        f"    Diversité génét.  : σ={s['speed_std_final']:.3f}  "
          + ("← pop. homogène" if s['speed_std_final'] < 0.15 else "← diversité maintenue"),
        "",
        "  DÉMOGRAPHIE",
        f"    Population max    : {s['pop_max']}",
        f"    Population finale : {s['pop_final']}",
        f"    Pop. stable (moy) : {s['pop_stable_mean']}",
        f"    Extinction        : {'tick ' + str(s['extinction']) if s['extinction'] else 'non'}",
        "",
        "  BIODIVERSITÉ",
        f"    Lignées initiales : {s['lineages_initial']}",
        f"    Lignées finales   : {s['lineages_final']}",
        f"    Extinction rate   : {(1 - s['lineages_final']/s['lineages_initial'])*100:.0f}%",
        f"    Génération max    : {s['max_generation']}",
        "",
        "  RESSOURCES",
        f"    Res. moyenne fin  : {s['res_mean_final']:.3f} / {MAX_RES}",
        f"    Occupation        : {s['res_mean_final']/MAX_RES*100:.0f}%",
        "",
        "═" * 58,
    ]
    return "\n".join(lines)


# ── Entrée principale ─────────────────────────────────────────────

def main():
    args = parse_args()

    # Rechargement depuis config si demandé
    if args.from_config:
        with open(args.from_config) as f:
            cfg = json.load(f)
        mode, ticks, seed    = cfg["mode"], cfg["ticks_requested"], cfg["seed"]
        n_agents, mutation   = cfg["n_agents_init"], cfg["mutation"]
        regen                = cfg["regen"]
    else:
        mode, ticks, seed    = args.mode, args.ticks, args.seed
        n_agents, mutation   = args.n_agents, args.mutation
        regen                = args.regen

    # Dossier de sortie
    out = Path(args.out_dir)
    out.mkdir(exist_ok=True)

    # Run
    data    = run_simulation(mode, ticks, seed, n_agents, mutation, regen)
    summary = compute_summary(data)

    # ── Sauvegarde ────────────────────────────────────────────────
    # results.json : métriques agrégées (légères, pour comparaisons)
    (out / "results.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )

    # timeseries.json : séries complètes (plus lourd, pour les graphes)
    (out / "timeseries.json").write_text(
        json.dumps({
            "timeseries"  : data["timeseries"],
            "lineage_ts"  : data["lineage_ts"],
            "final_agents": data["final_agents"],
            "meta"        : data["meta"],
        }, indent=2), encoding="utf-8"
    )

    # config_run.json : snapshot reproductible
    (out / "config_run.json").write_text(
        json.dumps(data["meta"], indent=2), encoding="utf-8"
    )

    # summary.txt : résumé humain
    txt = format_summary_txt(summary, data)
    (out / "summary.txt").write_text(txt, encoding="utf-8")
    print("\n" + txt)

    print(f"\n  Fichiers sauvés dans : {out.resolve()}")
    print("    results.json    ← métriques agrégées")
    print("    timeseries.json ← séries temporelles complètes")
    print("    config_run.json ← paramètres pour relancer à l'identique")
    print("    summary.txt     ← résumé humain\n")


if __name__ == "__main__":
    main()
