"""
environment.py — Génération et gestion du terrain de ressources.

3 modes d'environnement
------------------------
  "flat"
      Ressources uniformément distribuées à FLAT_LEVEL × MAX_RES.
      Pas de gradient spatial → compétition pure densité-dépendante.
      Usage : référence / groupe contrôle.
      Prédiction : vitesse converge vers le minimum viable,
                   population croît vite (pas de zones mortes).

  "perlin"
      Terrain hétérogène statique généré par Simplex noise fractal.
      Zones riches (oasis) et déserts fixes → pression spatiale constante.
      Usage : étudier la spécialisation géographique des lignées.
      Prédiction : vitesse converge un peu moins vite (les rapides profitent
                   des oasis), diversité génétique maintenue plus longtemps.

  "drought"
      Même terrain Perlin, mais les coordonnées de bruit dérivent
      de DROUGHT_RATE unités par tick → les zones riches migrent lentement.
      Usage : tester l'adaptabilité dynamique, étudier si les rapides
              redeviennent avantageux quand les oasis bougent.
      Prédiction : courbe de vitesse non monotone — descend d'abord
                   (coût trop élevé), puis remonte si le drift est rapide
                   (les rapides rejoignent les nouvelles oasis en premier).

API
---
    env = Environment("perlin", seed=42)
    grid, target = env.initial_state()
    target = env.tick_target(tick)          # à appeler chaque tick
"""

import numpy as np
from config import (
    GRID_SIZE, MAX_RES, FLAT_LEVEL,
    DROUGHT_RATE, PERLIN_CACHE,
    NOISE_SEED,
)
from noise import build_perm, build_terrain


class Environment:
    """
    Encapsule le mode d'environnement et l'état du terrain.

    Attributs publics
    -----------------
    mode          : "flat" | "perlin" | "drought"
    drought_offset: float — décalage courant (0 pour flat/perlin, croît pour drought)
    """

    def __init__(self, mode: str, seed: int = NOISE_SEED):
        if mode not in ("flat", "perlin", "drought"):
            raise ValueError(f"mode doit être 'flat', 'perlin' ou 'drought', reçu '{mode}'")

        self.mode           = mode
        self.seed           = seed
        self.drought_offset = 0.0
        self._perm          = build_perm(seed)
        self._tick          = 0

    # ── Génération du terrain ──────────────────────────────────────

    def _make_field(self, offset: float = 0.0) -> np.ndarray:
        """
        Génère le champ de ressources selon le mode.

        Pour flat : grille constante à FLAT_LEVEL × MAX_RES.
        Pour perlin / drought : terrain Simplex avec courbe en S.
        """
        if self.mode == "flat":
            return np.full(
                (GRID_SIZE, GRID_SIZE),
                MAX_RES * FLAT_LEVEL,
                dtype=np.float32,
            )
        return build_terrain(offset, self._perm)

    def initial_state(self) -> tuple[np.ndarray, np.ndarray]:
        """
        Retourne (resource_grid, perlin_target) pour initialiser la simulation.
        Les deux sont identiques au départ.
        """
        grid = self._make_field(0.0)
        return grid.copy(), grid.copy()

    def tick_target(self, tick: int) -> np.ndarray | None:
        """
        Retourne le nouveau champ cible Perlin si ce tick nécessite un recalcul,
        None sinon (pour éviter le recalcul coûteux chaque tick).

        En mode drought : met à jour drought_offset avant de recalculer.
        """
        self._tick = tick

        # Drought : le terrain dérive à chaque tick
        if self.mode == "drought":
            self.drought_offset += DROUGHT_RATE

        # Recalcul seulement tous les PERLIN_CACHE ticks
        if tick % PERLIN_CACHE == 0:
            return self._make_field(self.drought_offset)

        return None  # pas de recalcul ce tick

    def forced_update(self, drought_offset: float) -> np.ndarray:
        """
        Recalcul immédiat du champ (appelé quand le slider drought change).
        Uniquement pertinent en mode drought.
        """
        self.drought_offset = drought_offset
        return self._make_field(drought_offset)

    @property
    def label(self) -> str:
        """Description courte affichée dans le titre de la figure."""
        from config import ENV_LABELS
        return ENV_LABELS.get(self.mode, self.mode)

    @property
    def accent_color(self) -> str:
        """Couleur d'accent associée à ce mode."""
        from config import ENV_ACCENT
        return ENV_ACCENT.get(self.mode, "#ffffff")
