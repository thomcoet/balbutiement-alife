"""
visualization.py — Figure multi-panneaux avec suivi génétique.

Disposition (9×11 pouces, fond sombre)
---------------------------------------
┌─────────────────────────────────────────────────────────┐
│  Heatmap 80×80  — agents colorés par lignée             │
├────────────────────┬────────────────────────────────────┤
│  Population        │  Vitesse moyenne + enveloppe        │
├────────────────────┴────────────────────────────────────┤
│  Aire empilée — lignées actives                         │
├─────────────────────────────────────────────────────────┤
│  [Drought slider — visible seulement en mode drought]   │
│  [Mutation slider]   [Bouton Pause]                     │
└─────────────────────────────────────────────────────────┘

Lecture rapide
--------------
  Heatmap    : couleur = ressource (beige → vert foncé).
               Point coloré = agent. Couleur = lignée. Taille = énergie.
  Population : démographie brute. Plateau = env. restrictif bien calibré.
  Vitesse    : trait génétique moyen. Descend = lents favorisés.
               Enveloppe = diversité génétique (écart min–max).
  Lignées    : quelle famille domine. Couleur qui disparaît = extinction.
               En mode DROUGHT, les couleurs peuvent alterner (migrations).
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button
from matplotlib.colors import LinearSegmentedColormap

from config import (
    GRID_SIZE, MAX_RES, N_INIT,
    BG_COLOR, AXES_COLOR, SPINE_COLOR, TEXT_COLOR, MUTED_COLOR,
    LINEAGE_COLORS, POP_HISTORY_LEN,
)


# ── Colormap YlGn avec plancher sombre (déserts visibles sur fond noir) ──
def _make_cmap() -> LinearSegmentedColormap:
    base = plt.get_cmap("YlGn")
    cols = [base(i / 255) for i in range(256)]
    for k in range(20):
        t = k / 19
        cols[k] = (0.08 + t*0.05, 0.10 + t*0.05, 0.04 + t*0.03, 1.0)
    return LinearSegmentedColormap.from_list("ylgn_dark", cols, N=256)

CMAP = _make_cmap()


def _styled_ax(fig, rect, bg=AXES_COLOR) -> plt.Axes:
    """Ajoute un axe positionné avec thème sombre."""
    ax = fig.add_axes(rect)
    ax.set_facecolor(bg)
    for sp in ax.spines.values():
        sp.set_color(SPINE_COLOR); sp.set_linewidth(0.6)
    ax.tick_params(colors=MUTED_COLOR, labelsize=7, length=2, pad=2)
    return ax


def build_figure(resource_grid: np.ndarray, env) -> dict:
    """
    Construit la figure complète selon le mode d'environnement.

    Paramètres
    ----------
    resource_grid : état initial du terrain
    env           : instance de Environment (pour label, couleur, mode)

    Retourne
    --------
    dict contenant tous les artistes matplotlib
    """
    plt.rcParams.update({
        "figure.facecolor": BG_COLOR,
        "text.color"      : TEXT_COLOR,
        "font.family"     : "monospace",
    })

    accent = env.accent_color

    fig = plt.figure(figsize=(9, 11), facecolor=BG_COLOR)

    # ── Heatmap ───────────────────────────────────────────────────
    ax_map = _styled_ax(fig, [0.05, 0.33, 0.78, 0.63], bg=BG_COLOR)
    ax_map.set_xticks([]); ax_map.set_yticks([])

    im = ax_map.imshow(
        resource_grid, cmap=CMAP,
        vmin=0, vmax=MAX_RES,
        interpolation="bilinear", origin="upper", animated=True,
    )

    cax = fig.add_axes([0.845, 0.33, 0.016, 0.63])
    cbar = fig.colorbar(im, cax=cax)
    cbar.set_label("Ressource", color=MUTED_COLOR, fontsize=7, labelpad=5)
    cbar.ax.yaxis.set_tick_params(color=MUTED_COLOR, labelcolor=MUTED_COLOR, labelsize=6)
    cbar.outline.set_edgecolor(SPINE_COLOR)

    scat = ax_map.scatter([], [], s=30, zorder=5,
                          linewidths=0.4, edgecolors="white", alpha=0.9)

    # Pastille colorée indiquant le mode d'environnement
    mode_badge = ax_map.text(
        0.99, 0.985, f" {env.mode.upper()} ",
        transform=ax_map.transAxes,
        color=BG_COLOR, fontsize=8, va="top", ha="right",
        fontfamily="monospace", fontweight="bold",
        bbox=dict(fc=accent, ec="none", pad=3, boxstyle="round,pad=0.3"),
        zorder=11,
    )

    info = ax_map.text(
        0.01, 0.985, "",
        transform=ax_map.transAxes,
        color=TEXT_COLOR, fontsize=7.5, va="top", ha="left",
        fontfamily="monospace",
        bbox=dict(fc="#0d111799", ec=SPINE_COLOR, lw=0.6,
                  pad=3.5, boxstyle="round,pad=0.3"),
        zorder=10,
    )

    ax_map.set_title(
        f"  {env.label}",
        color=MUTED_COLOR, fontsize=8, pad=5, loc="left",
    )

    # ── Population ────────────────────────────────────────────────
    ax_pop = _styled_ax(fig, [0.05, 0.210, 0.36, 0.095])
    ax_pop.set_ylabel("Population", color=MUTED_COLOR, fontsize=7)
    ax_pop.set_xlim(0, POP_HISTORY_LEN); ax_pop.set_ylim(0, N_INIT * 6)
    ax_pop.grid(color=SPINE_COLOR, lw=0.4, alpha=0.7)
    ax_pop.axhline(N_INIT, color=MUTED_COLOR, lw=0.5, ls="--", alpha=0.35)
    ax_pop.text(2, N_INIT + 0.5, f"N₀={N_INIT}",
                color=MUTED_COLOR, fontsize=6, alpha=0.5)

    fill_pop = ax_pop.fill_between([], [], alpha=0.15, color=accent)
    (line_pop,) = ax_pop.plot([], [], color=accent, lw=1.3)

    # ── Vitesse génétique ─────────────────────────────────────────
    ax_spd = _styled_ax(fig, [0.47, 0.210, 0.36, 0.095])
    ax_spd.set_ylabel("Vitesse moy.", color=MUTED_COLOR, fontsize=7)
    ax_spd.set_xlim(0, POP_HISTORY_LEN)
    ax_spd.set_ylim(0.4, 2.1)
    ax_spd.grid(color=SPINE_COLOR, lw=0.4, alpha=0.7)
    ax_spd.axhline(1.0, color=MUTED_COLOR, lw=0.5, ls="--", alpha=0.35)
    ax_spd.text(2, 1.02, "seuil neutre",
                color=MUTED_COLOR, fontsize=6, alpha=0.5)

    fill_spd       = ax_spd.fill_between([], [], alpha=0.12, color=accent)
    fill_spd_range = ax_spd.fill_between([], [], [], alpha=0.06, color=accent)
    (line_spd,)    = ax_spd.plot([], [], color=accent, lw=1.3)

    # ── Stacked area lignées ──────────────────────────────────────
    ax_lin = _styled_ax(fig, [0.05, 0.100, 0.78, 0.090])
    ax_lin.set_ylabel("Lignées", color=MUTED_COLOR, fontsize=7)
    ax_lin.set_xlim(0, POP_HISTORY_LEN); ax_lin.set_ylim(0, N_INIT * 6)
    ax_lin.grid(color=SPINE_COLOR, lw=0.4, alpha=0.5, axis='y')

    lineage_fills = [
        ax_lin.fill_between([], [], [], alpha=0.78,
                            color=LINEAGE_COLORS[i % len(LINEAGE_COLORS)])
        for i in range(N_INIT)
    ]

    # ── Légende lignées ───────────────────────────────────────────
    leg_ax = _styled_ax(fig, [0.845, 0.100, 0.13, 0.090], bg=BG_COLOR)
    leg_ax.set_xticks([]); leg_ax.set_yticks([])
    for sp in leg_ax.spines.values(): sp.set_visible(False)

    legend_texts = []
    for i in range(N_INIT):
        col = LINEAGE_COLORS[i % len(LINEAGE_COLORS)]
        leg_ax.scatter([0.15], [1 - i*0.068], s=18, c=[col],
                       transform=leg_ax.transAxes, zorder=3)
        t = leg_ax.text(0.38, 1 - i*0.068, f"L{i:02d}",
                        transform=leg_ax.transAxes,
                        color=col, fontsize=5.5, va="center",
                        fontfamily="monospace")
        legend_texts.append(t)
    leg_ax.text(0.05, 1.06, "Lignées",
                transform=leg_ax.transAxes, color=MUTED_COLOR, fontsize=6)

    # ── Widgets ───────────────────────────────────────────────────
    # Le slider drought n'est visible qu'en mode drought
    show_drought = (env.mode == "drought")
    drought_bottom = 0.052 if show_drought else 0.036

    ax_sd = fig.add_axes(
        [0.12, drought_bottom, 0.70, 0.016],
        facecolor="#161b22",
        visible=show_drought,
    )
    ax_sm  = fig.add_axes([0.12, 0.028, 0.70, 0.016], facecolor="#161b22")
    ax_btn = fig.add_axes([0.12, 0.006, 0.18, 0.016])

    sl_drought = Slider(ax_sd, "Drought ", 0.0, 10.0, valinit=0.0,
                        color="#f78166", track_color=SPINE_COLOR, initcolor="none")
    sl_mutation = Slider(ax_sm, "Mutation", 0.01, 0.25, valinit=0.06,
                         color=accent, track_color=SPINE_COLOR, initcolor="none")

    for sl in (sl_drought, sl_mutation):
        sl.label.set_color(TEXT_COLOR);    sl.label.set_fontsize(7)
        sl.valtext.set_color(MUTED_COLOR); sl.valtext.set_fontsize(6)
        sl.poly.set_alpha(0.8)

    btn_pause = Button(ax_btn, "⏸  Pause", color="#21262d", hovercolor="#30363d")
    btn_pause.label.set_color(TEXT_COLOR); btn_pause.label.set_fontsize(7)

    return dict(
        fig=fig, ax_map=ax_map, ax_pop=ax_pop, ax_spd=ax_spd, ax_lin=ax_lin,
        im=im, scat=scat, info=info, mode_badge=mode_badge,
        line_pop=line_pop, fill_pop=fill_pop,
        line_spd=line_spd, fill_spd=fill_spd, fill_spd_range=fill_spd_range,
        lineage_fills=lineage_fills, legend_texts=legend_texts,
        sl_drought=sl_drought, sl_mutation=sl_mutation, btn_pause=btn_pause,
    )


def update_frame(ui, resource_grid, agents, pop_history,
                 speed_history, speed_min_history, speed_max_history,
                 lineage_history, tick, drought_val, accent):
    """
    Met à jour tous les artistes pour la frame courante.

    Paramètres
    ----------
    accent : couleur d'accent du mode (pour adapter les fills dynamiquement)
    """
    # ── Heatmap ───────────────────────────────────────────────────
    ui["im"].set_data(resource_grid)

    # ── Agents ────────────────────────────────────────────────────
    if agents:
        xs     = np.array([a.x for a in agents], np.float32)
        ys     = np.array([a.y for a in agents], np.float32)
        colors = [LINEAGE_COLORS[a.lineage % len(LINEAGE_COLORS)] for a in agents]
        sizes  = np.clip([12 + a.energy * 0.15 for a in agents], 8, 60)
        ui["scat"].set_offsets(np.c_[xs, ys])
        ui["scat"].set_color(colors)
        ui["scat"].set_sizes(sizes)
    else:
        ui["scat"].set_offsets(np.empty((0, 2)))

    # ── Population ────────────────────────────────────────────────
    ph = pop_history[-POP_HISTORY_LEN:]
    T  = np.arange(len(ph))
    ui["line_pop"].set_data(T, ph)
    ui["fill_pop"].remove()
    ui["fill_pop"] = ui["ax_pop"].fill_between(T, ph, alpha=0.14, color=accent)
    if ph:
        ui["ax_pop"].set_ylim(0, max(N_INIT * 6, max(ph) * 1.15))

    # ── Vitesse ───────────────────────────────────────────────────
    sh   = speed_history[-POP_HISTORY_LEN:]
    smin = speed_min_history[-POP_HISTORY_LEN:]
    smax = speed_max_history[-POP_HISTORY_LEN:]
    Ts   = np.arange(len(sh))
    ui["line_spd"].set_data(Ts, sh)
    ui["fill_spd"].remove()
    ui["fill_spd"] = ui["ax_spd"].fill_between(Ts, sh, alpha=0.12, color=accent)
    ui["fill_spd_range"].remove()
    ui["fill_spd_range"] = ui["ax_spd"].fill_between(
        Ts, smin, smax, alpha=0.06, color=accent
    )

    # ── Lignées (stacked area) ────────────────────────────────────
    lh = lineage_history[-POP_HISTORY_LEN:]
    if lh:
        Tl    = np.arange(len(lh))
        stack = np.zeros(len(lh))
        for i in range(N_INIT):
            counts  = np.array([d.get(i, 0) for d in lh], dtype=float)
            new_top = stack + counts
            ui["lineage_fills"][i].remove()
            ui["lineage_fills"][i] = ui["ax_lin"].fill_between(
                Tl, stack, new_top,
                alpha=0.78,
                color=LINEAGE_COLORS[i % len(LINEAGE_COLORS)],
            )
            stack = new_top
        ui["ax_lin"].set_ylim(0, max(N_INIT * 6, stack.max() * 1.1))

    # Légende : atténue les lignées éteintes
    alive = set(a.lineage for a in agents)
    for i, t in enumerate(ui["legend_texts"]):
        t.set_alpha(0.9 if i in alive else 0.15)

    # ── Info ──────────────────────────────────────────────────────
    avg_spd  = float(np.mean([a.speed for a in agents])) if agents else 0.0
    res_mean = float(resource_grid.mean())
    max_gen  = max((a.generation for a in agents), default=0)
    n_lin    = len(alive)

    drought_str = f"  drift {drought_val:.2f}" if drought_val > 0 else ""
    ui["info"].set_text(
        f" tick {tick:>5d}  ·  pop {len(agents):>3d}  ·  "
        f"gen_max {max_gen}{drought_str}\n"
        f" res̄ {res_mean:.2f}  ·  spd̄ {avg_spd:.2f}  ·  "
        f"lignées {n_lin}/{N_INIT} "
    )
