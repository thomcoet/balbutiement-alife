"""
noise.py — Simplex Noise 2D vectorisé (pur NumPy, sans dépendance externe).

API publique :
    build_perm(seed)          → table de permutation (512,) int32
    simplex2(x, y, perm)      → bruit brut ≈ [-1, 1], arrays quelconques
    fractal_noise(xs, ys, perm, octaves, lacunarity, persistence)
                              → bruit fractal normalisé [0, 1]
    build_terrain(drought_offset, perm, grid_size, max_res)
                              → grille (G, G) float32 de ressources [0, max_res]

Notes d'implémentation :
    - Simplex 2D de Ken Perlin (2001), calcul exactement 3 contributions
      par point grâce aux simplexes triangulaires du plan.
    - Vectorisé : toute la grille est calculée en un seul appel NumPy
      (pas de double boucle Python).
    - La courbe en S finale (smoothstep cubique) accentue le contraste
      pour donner de vraies zones riches vs désertiques.
"""

import numpy as np
from config import (
    NOISE_SCALE, NOISE_OCTAVES, NOISE_LAC, NOISE_PERSIST,
    NOISE_SEED, GRID_SIZE, MAX_RES,
)

# ── Constantes du simplexe 2D ─────────────────────────────────────
_F2 = 0.5 * (np.sqrt(3.0) - 1.0)   # facteur d'espace → skew
_G2 = (3.0 - np.sqrt(3.0)) / 6.0   # facteur de retour → unskew

# 12 vecteurs gradient de longueur unité dans le plan
_GRAD3 = np.array([
    [ 1,  1], [-1,  1], [ 1, -1], [-1, -1],
    [ 1,  0], [-1,  0], [ 0,  1], [ 0, -1],
    [ 1,  1], [-1,  1], [ 0, -1], [ 0,  1],
], dtype=np.float64)


def build_perm(seed: int = NOISE_SEED) -> np.ndarray:
    """
    Génère une table de permutation aléatoire de 512 entiers.

    Paramètres
    ----------
    seed : graine du générateur (reproductibilité du terrain)

    Retourne
    --------
    perm : ndarray int32 (512,)  — duplication [0..255, 0..255] mélangé
    """
    rng = np.random.default_rng(seed)
    p   = np.arange(256, dtype=np.int32)
    rng.shuffle(p)
    return np.concatenate([p, p])


def simplex2(x: np.ndarray, y: np.ndarray, perm: np.ndarray) -> np.ndarray:
    """
    Simplex Noise 2D vectorisé.

    Paramètres
    ----------
    x, y : arrays NumPy de même forme — coordonnées du bruit
    perm : table de permutation retournée par build_perm()

    Retourne
    --------
    noise : array de même forme, valeurs ≈ [-1, 1]

    Algorithme (bref)
    -----------------
    1. Skew de l'espace → repère simplexe (triangles équilatéraux)
    2. Trouver le triangle contenant (x,y) et ses 3 sommets
    3. Pour chaque sommet : contribution = rampe(distance) × produit_scalaire(gradient, offset)
    4. Somme des 3 contributions × 70 (normalisation empirique)
    """
    # 1. Transformation vers l'espace skewé
    s = (x + y) * _F2
    i = np.floor(x + s).astype(np.int32)
    j = np.floor(y + s).astype(np.int32)

    # 2. Retour dans l'espace original : coin inférieur du simplexe
    t  = (i + j) * _G2
    x0 = x - (i - t)   # offset depuis le coin 0
    y0 = y - (j - t)

    # Quel triangle du simplexe contient (x,y) ?
    i1 = np.where(x0 > y0, 1, 0)
    j1 = 1 - i1

    # Offsets des coins 1 et 2
    x1 = x0 - i1 + _G2
    y1 = y0 - j1 + _G2
    x2 = x0 - 1.0 + 2.0 * _G2
    y2 = y0 - 1.0 + 2.0 * _G2

    def _contrib(dx: np.ndarray, dy: np.ndarray,
                 ci: np.ndarray, cj: np.ndarray) -> np.ndarray:
        """Contribution d'un sommet du simplexe."""
        gi  = perm[(ci & 255) + perm[cj & 255]] % 12   # index du gradient
        t2  = 0.5 - dx**2 - dy**2                       # influence (nul si > 0.5)
        mask = t2 >= 0
        t2c  = np.where(mask, t2, 0.0)
        dot  = _GRAD3[gi, 0] * dx + _GRAD3[gi, 1] * dy  # produit scalaire
        return np.where(mask, t2c**4 * dot, 0.0)

    n0 = _contrib(x0, y0, i,    j   )
    n1 = _contrib(x1, y1, i+i1, j+j1)
    n2 = _contrib(x2, y2, i+1,  j+1 )

    return 70.0 * (n0 + n1 + n2)


def fractal_noise(
    xs        : np.ndarray,
    ys        : np.ndarray,
    perm      : np.ndarray,
    octaves   : int   = NOISE_OCTAVES,
    lacunarity: float = NOISE_LAC,
    persistence:float = NOISE_PERSIST,
) -> np.ndarray:
    """
    Bruit fractal (fBm) = superposition d'octaves de Simplex Noise.

    Chaque octave ajoute des détails plus fins (fréquence × lacunarity)
    avec une amplitude décroissante (amplitude × persistence).

    Retourne des valeurs dans [0, 1].
    """
    out, amp, freq, max_amp = np.zeros_like(xs, dtype=float), 1.0, 1.0, 0.0
    for _ in range(octaves):
        out     += simplex2(xs * freq, ys * freq, perm) * amp
        max_amp += amp
        amp     *= persistence
        freq    *= lacunarity
    # Normalise [-max_amp, max_amp] → [0, 1]
    return (out / max_amp + 1.0) / 2.0


def build_terrain(
    drought_offset: float,
    perm          : np.ndarray,
    grid_size     : int   = GRID_SIZE,
    max_res       : float = MAX_RES,
    noise_scale   : float = NOISE_SCALE,
) -> np.ndarray:
    """
    Génère la grille de ressources à partir du bruit Simplex.

    Paramètres
    ----------
    drought_offset : décalage en X des coordonnées → fait "migrer" le terrain
                     vers la droite quand on l'augmente
    perm           : table de permutation (build_perm())
    grid_size      : nombre de cellules par côté
    max_res        : valeur maximale de ressource
    noise_scale    : étendue spatiale — plus petit = zones plus grandes

    Pipeline
    --------
    1. Grille de coordonnées [0, noise_scale] décalée par drought_offset
    2. Bruit fractal normalisé [0, 1]
    3. Courbe en S cubique (smoothstep) pour accentuer les contrastes :
       - Valeurs < 0.5 compressées vers 0 (déserts vrais)
       - Valeurs > 0.5 étirées vers 1 (oasis vraies)
    4. Multiplication par max_res
    """
    gx = np.linspace(0.0, noise_scale, grid_size) + drought_offset
    gy = np.linspace(0.0, noise_scale, grid_size)
    XX, YY = np.meshgrid(gx, gy)

    raw   = np.clip(fractal_noise(XX, YY, perm), 0.0, 1.0)
    # Courbe en S (smoothstep cubique) : accentue les extrêmes
    curve = np.where(raw < 0.5,
                     2.0 * raw**2,
                     1.0 - 2.0 * (1.0 - raw)**2)
    return (curve * max_res).astype(np.float32)
