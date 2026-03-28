"""
main.py — Point d'entrée ALife v3.

Usage
-----
    python main.py              → menu interactif au lancement
    python main.py flat         → démarre directement en mode flat
    python main.py perlin       → démarre directement en mode perlin
    python main.py drought      → démarre directement en mode drought

Ce que tu observes
------------------
  Heatmap     : terrain de ressources. Points colorés = agents.
                Couleur du point = lignée (famille). Taille = énergie.
                Un gros point = agent bien nourri, proche de se reproduire.

  Population  : combien d'agents vivent. Plateau = équilibre.
                Explosion = conditions favorables (ex: drought amène des oasis).

  Vitesse     : trait génétique moyen de la population.
                C'est LA mesure de l'évolution : les agents "apprennent" à
                quelle vitesse il faut se déplacer pour survivre dans CET env.
                - Flat   → descend vite (économiser suffit, pas besoin de chercher)
                - Perlin → descend moins vite (les oasis récompensent les rapides)
                - Drought → oscillations si le terrain change trop vite
                L'enveloppe = diversité génétique (écart-type min/max).

  Lignées     : quelle famille domine à chaque tick.
                Une couleur qui disparaît = lignée totalement éteinte.
                Compare entre modes : les mêmes lignées survivent-elles ?

Benchmark conseillé
-------------------
  1. Lance flat   → laisse tourner 400 ticks → note vitesse finale, pop
  2. Lance perlin → même durée → compare les courbes
  3. Lance drought → augmente le slider pour accélérer la migration
  Question : est-ce que le terrain hétérogène ralentit la convergence vers
             les agents lents ? Est-ce que le drought inverse la tendance ?
"""

import sys
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from config import (
    GRID_SIZE, N_INIT, ENERGY_INIT, SPEED_MIN, SPEED_MAX,
    NOISE_SEED, REGEN_ABS, PERLIN_CACHE,
    ANIMATION_INTERVAL, POP_HISTORY_LEN,
)
from noise         import build_perm
from agent         import Agent, simulation_step
from environment   import Environment
from visualization import build_figure, update_frame


# ── Sélection du mode ─────────────────────────────────────────────

def _choose_mode() -> str:
    """
    Demande le mode à l'utilisateur si non spécifié en argument.
    Retourne "flat", "perlin" ou "drought".
    """
    if len(sys.argv) > 1 and sys.argv[1] in ("flat", "perlin", "drought"):
        return sys.argv[1]

    print("\n" + "═"*52)
    print("  ALife v3  —  Choisir l'environnement")
    print("═"*52)
    print("  [1]  flat    — ressources uniformes (contrôle)")
    print("  [2]  perlin  — terrain hétérogène statique")
    print("  [3]  drought — terrain qui migre lentement")
    print("═"*52)
    print("\n  Benchmark conseillé : lance les 3 dans l'ordre")
    print("  et compare la courbe de vitesse entre les modes.\n")

    choices = {"1": "flat", "2": "perlin", "3": "drought",
               "flat": "flat", "perlin": "perlin", "drought": "drought"}
    while True:
        raw = input("  Ton choix [1/2/3] : ").strip().lower()
        if raw in choices:
            return choices[raw]
        print("  → Tape 1, 2 ou 3.")


# ── Initialisation des agents ─────────────────────────────────────

def _init_agents(n: int, rng: np.random.Generator) -> list[Agent]:
    """
    Crée N agents fondateurs.
    Chaque agent a un identifiant de lignée unique (0..N-1)
    et une vitesse tirée uniformément dans [SPEED_MIN, SPEED_MAX].
    """
    return [
        Agent(
            x          = rng.uniform(0, GRID_SIZE),
            y          = rng.uniform(0, GRID_SIZE),
            energy     = ENERGY_INIT,
            speed      = rng.uniform(SPEED_MIN, SPEED_MAX),
            lineage    = i,
            generation = 0,
        )
        for i in range(n)
    ]


# ── Main ──────────────────────────────────────────────────────────

def main():
    mode = _choose_mode()
    print(f"\n  Démarrage en mode : {mode.upper()}\n")

    rng = np.random.default_rng(NOISE_SEED)
    env = Environment(mode, seed=NOISE_SEED)

    resource_grid, perlin_target = env.initial_state()

    # État complet de la simulation dans un dict (évite les globals)
    state = dict(
        tick              = 0,
        running           = True,
        resource_grid     = resource_grid,
        perlin_target     = perlin_target,
        agents            = _init_agents(N_INIT, rng),
        pop_history       = [],
        speed_history     = [],
        speed_min_history = [],
        speed_max_history = [],
        lineage_history   = [],
    )

    ui = build_figure(state["resource_grid"], env)

    # ── Callbacks widgets ─────────────────────────────────────────

    def on_drought(val):
        """Slider drought : recalcul immédiat du terrain cible."""
        if env.mode == "drought":
            state["perlin_target"] = env.forced_update(val)

    def toggle_pause(_):
        state["running"] = not state["running"]
        ui["btn_pause"].label.set_text(
            "▶  Play" if not state["running"] else "⏸  Pause"
        )

    ui["sl_drought"].on_changed(on_drought)
    ui["btn_pause"].on_clicked(toggle_pause)

    # ── Boucle principale ─────────────────────────────────────────

    def update(_frame):
        if not state["running"]:
            return

        state["tick"] += 1
        tick = state["tick"]

        # Mise à jour du champ Perlin (peut retourner None si pas ce tick)
        new_target = env.tick_target(tick)
        if new_target is not None:
            state["perlin_target"] = new_target

        # Un tick de simulation
        state["agents"], _ = simulation_step(
            agents        = state["agents"],
            resource_grid = state["resource_grid"],
            perlin_target = state["perlin_target"],
            regen_abs     = REGEN_ABS,
            mut_std       = ui["sl_mutation"].val,
        )

        # Collecte des métriques
        agents = state["agents"]
        state["pop_history"].append(len(agents))

        if agents:
            spds = [a.speed for a in agents]
            state["speed_history"].append(float(np.mean(spds)))
            state["speed_min_history"].append(float(np.min(spds)))
            state["speed_max_history"].append(float(np.max(spds)))
        else:
            for k in ("speed_history","speed_min_history","speed_max_history"):
                state[k].append(0.0)

        lc = {}
        for a in agents:
            lc[a.lineage] = lc.get(a.lineage, 0) + 1
        state["lineage_history"].append(lc)

        # Purge mémoire (fenêtre glissante × 2 pour confort)
        for key in ("pop_history","speed_history","speed_min_history",
                    "speed_max_history","lineage_history"):
            if len(state[key]) > POP_HISTORY_LEN * 2:
                state[key] = state[key][-POP_HISTORY_LEN:]

        # Rendu
        update_frame(
            ui                = ui,
            resource_grid     = state["resource_grid"],
            agents            = agents,
            pop_history       = state["pop_history"],
            speed_history     = state["speed_history"],
            speed_min_history = state["speed_min_history"],
            speed_max_history = state["speed_max_history"],
            lineage_history   = state["lineage_history"],
            tick              = tick,
            drought_val       = env.drought_offset,
            accent            = env.accent_color,
        )

    ani = animation.FuncAnimation(   # noqa: F841
        ui["fig"], update,
        interval=ANIMATION_INTERVAL, blit=False, cache_frame_data=False,
    )

    try:
        ui["fig"].canvas.manager.set_window_title(f"ALife v3 — {mode.upper()}")
    except Exception:
        pass

    plt.show()


if __name__ == "__main__":
    main()
