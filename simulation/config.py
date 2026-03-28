"""
config.py — Constantes globales de la simulation ALife.

3 modes d'environnement disponibles :
  "flat"    → ressources uniformes (référence/contrôle)
  "perlin"  → terrain hétérogène statique (zones riches / déserts fixes)
  "drought" → terrain Perlin qui migre lentement (pression temporelle)
"""

# ── Grille ────────────────────────────────────────────────────────
GRID_SIZE    : int   = 80
MAX_RES      : float = 5.0

# ── Terrain Simplex ───────────────────────────────────────────────
NOISE_SCALE  : float = 1.2
NOISE_OCTAVES: int   = 4
NOISE_LAC    : float = 2.0
NOISE_PERSIST: float = 0.5
NOISE_SEED   : int   = 42

# ── Ressources ────────────────────────────────────────────────────
REGEN_ABS       : float = 0.05   # unités absolues régénérées/cellule/tick
FLAT_LEVEL      : float = 0.45   # fraction de MAX_RES pour le mode flat (≈ moyenne Perlin)
DROUGHT_RATE    : float = 0.015  # décalage du terrain par tick en mode drought
PERLIN_CACHE    : int   = 8      # recalcul du champ cible tous les N ticks

# ── Population ────────────────────────────────────────────────────
N_INIT       : int   = 15
ENERGY_INIT  : float = 60.0

# ── Mouvement ─────────────────────────────────────────────────────
SPEED_MIN    : float = 0.5
SPEED_MAX    : float = 2.0
MOVE_COST    : float = 1.5

# ── Alimentation ──────────────────────────────────────────────────
EAT_CAP      : float = 0.5
EAT_GAIN     : float = 5.0

# ── Reproduction ──────────────────────────────────────────────────
ENERGY_REPRO        : float = 150.0
ENERGY_REPRO_PARENT : float =  40.0
ENERGY_REPRO_CHILD  : float =  50.0
MUTATION_STD        : float =   0.06

# ── Mort ──────────────────────────────────────────────────────────
ENERGY_DEATH : float = -10.0

# ── Visualisation ─────────────────────────────────────────────────
ANIMATION_INTERVAL : int = 80
POP_HISTORY_LEN    : int = 400

BG_COLOR     = "#0d1117"
AXES_COLOR   = "#161b22"
SPINE_COLOR  = "#30363d"
TEXT_COLOR   = "#c9d1d9"
MUTED_COLOR  = "#8b949e"

# 15 couleurs de lignée distinctes sur fond sombre
LINEAGE_COLORS = [
    "#ff6b6b","#ffd93d","#6bcb77","#4d96ff","#ff6bff",
    "#ff9f43","#48dbfb","#ff4757","#2ed573","#eccc68",
    "#a29bfe","#fd79a8","#55efc4","#fdcb6e","#74b9ff",
]

# Couleur d'accent par mode (heatmap titre + courbes)
ENV_ACCENT = {
    "flat"   : "#58a6ff",   # bleu calme
    "perlin" : "#3fb950",   # vert forêt
    "drought": "#f78166",   # orange chaud
}

ENV_LABELS = {
    "flat"   : "Flat  — ressources uniformes (contrôle)",
    "perlin" : "Perlin — terrain hétérogène statique",
    "drought": "Drought — terrain qui migre",
}
