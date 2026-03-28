"""
agent.py — Agent avec suivi généalogique complet.

Chaque agent connaît sa lignée (ID de fondateur), sa génération,
et son âge. Ces données alimentent les graphes génétiques.

Pression de sélection dans cet environnement restrictif
---------------------------------------------------------
  Vitesse élevée → explore plus → trouve plus de nourriture MAIS
                   brûle speed × 1.5 énergie/tick.
  Agent speed=0.5 : coût=0.75/tick, gain max=2.5 → survit longtemps sans manger
  Agent speed=2.0 : coût=3.0/tick, gain max=2.5 → meurt si cellule vide
  → Sélection naturelle favorise les agents lents dans les zones pauvres,
    les rapides dans les zones riches (ils atteignent l'oasis avant les autres).
"""

import numpy as np
from config import (
    GRID_SIZE, SPEED_MIN, SPEED_MAX,
    MOVE_COST, EAT_CAP, EAT_GAIN,
    ENERGY_REPRO, ENERGY_REPRO_PARENT, ENERGY_REPRO_CHILD,
    ENERGY_DEATH, MUTATION_STD,
)


class Agent:
    """
    Agent autonome avec génome (vitesse) et généalogie.

    Attributs
    ---------
    x, y        : position continue (toroïdale)
    energy      : énergie courante
    speed       : vitesse = trait génétique principal
    lineage     : int — ID de l'ancêtre fondateur (0..N_INIT-1)
    generation  : int — profondeur dans l'arbre généalogique
    age         : int — ticks vécus depuis la naissance
    """
    __slots__ = ('x','y','energy','speed','lineage','generation','age')

    def __init__(self, x, y, energy, speed, lineage=0, generation=0):
        self.x          = float(x) % GRID_SIZE
        self.y          = float(y) % GRID_SIZE
        self.energy     = float(energy)
        self.speed      = float(np.clip(speed, SPEED_MIN, SPEED_MAX))
        self.lineage    = int(lineage)
        self.generation = int(generation)
        self.age        = 0

    def move(self):
        """Déplacement aléatoire. Coût = speed × MOVE_COST."""
        angle   = np.random.uniform(0, 2 * np.pi)
        self.x  = (self.x + self.speed * np.cos(angle)) % GRID_SIZE
        self.y  = (self.y + self.speed * np.sin(angle)) % GRID_SIZE
        self.energy -= self.speed * MOVE_COST

    def eat(self, grid, density_map):
        """
        Mange la ressource de sa cellule, partagée entre colocataires.
        Pression densité-dépendante : N agents sur une cellule → chacun mange 1/N.
        """
        cx, cy   = int(self.x), int(self.y)
        n        = max(1, int(density_map[cy, cx]))
        eaten    = min(grid[cy, cx] / n, EAT_CAP)
        self.energy      += eaten * EAT_GAIN
        grid[cy, cx]      = max(0.0, grid[cy, cx] - eaten)

    def reproduce(self, mut_std=MUTATION_STD):
        """
        Crée un enfant. Coût lourd pour le parent (tombe à ENERGY_REPRO_PARENT).
        Transmission : lignée identique, génération+1, vitesse mutée.
        """
        new_speed = float(np.clip(
            self.speed + np.random.normal(0, mut_std), SPEED_MIN, SPEED_MAX
        ))
        child = Agent(
            x          = self.x + np.random.uniform(-2, 2),
            y          = self.y + np.random.uniform(-2, 2),
            energy     = ENERGY_REPRO_CHILD,
            speed      = new_speed,
            lineage    = self.lineage,
            generation = self.generation + 1,
        )
        self.energy = ENERGY_REPRO_PARENT
        return child

    @property
    def alive(self):
        return self.energy > ENERGY_DEATH

    @property
    def cell(self):
        return int(self.x), int(self.y)


def build_density_map(agents, grid_size=GRID_SIZE):
    """Compte le nombre d'agents par cellule. O(N)."""
    density = np.zeros((grid_size, grid_size), dtype=np.int32)
    for a in agents:
        density[int(a.y), int(a.x)] += 1
    return density


def simulation_step(agents, resource_grid, perlin_target, regen_abs, mut_std=MUTATION_STD):
    """
    Un tick complet : regen → densité → move → eat → reproduce → mort.

    Retourne (tous_agents, nouveau_nes).
    """
    # Régénération absolue plafonnée au champ cible
    delta = np.minimum(regen_abs, np.maximum(perlin_target - resource_grid, 0.0))
    resource_grid += delta

    density  = build_density_map(agents)
    new_born = []

    for a in agents:
        a.move()
        a.eat(resource_grid, density)
        a.age += 1
        if a.energy >= ENERGY_REPRO:
            new_born.append(a.reproduce(mut_std))

    survivors = [a for a in agents if a.alive]
    return survivors + new_born, new_born
