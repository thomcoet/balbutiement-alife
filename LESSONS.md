# Lessons learned

Mistakes made during this project, kept deliberately visible.

---

## 1. Wrong attractor formula (caught 2026-03-31)

**What was written** in CLAUDE.md and notebooks:

> "The mathematical speed attractor is ~0.67 (gain_max / move_cost = 2.5 / 1.5)"

**Why it was wrong:**

- The arithmetic is wrong: 2.5 / 1.5 = **1.667**, not 0.67
- The concept is wrong: 1.667 is the energy-neutral ceiling for a solo agent with no competition. It is not an attractor.
- The observed ~0.64 was never explained -- it was assumed to match a formula that does not produce it

**What the attractor actually is:**

An emergent property of three interacting constraints:

1. Resource regeneration caps total population at ~1500 (REGEN_ABS * GRID_SIZE^2 * EAT_GAIN / cost per agent)
2. Competition at that density drags the viable speed down from 1.667 to ~0.64
3. Movement cost linearly penalizes fast agents at high density

No closed-form formula produces 0.64 from the config parameters alone. It must be measured from simulation.

**How it was caught:** comprehension question during a review session -- "where does the ~0.67 come from?" led to checking the arithmetic.

---

## 2. Single-seed conclusions are not conclusions (caught 2026-03-31)

**What was written:**

> "Perlin maintains slightly higher genetic diversity (sigma 0.117 vs 0.104) and one extra lineage"

This was stated as a result, not a hypothesis.

**Why it was wrong:**

One seed is one trajectory. The initial positions, initial speeds, and resource layout all depend on the seed. "Perlin sigma > flat sigma on seed 42" only means that particular run went that way.

**What the multi-seed analysis showed:**

Across 10 seeds: flat sigma = 0.108, perlin sigma = 0.107. No statistically significant difference on any metric (all Mann-Whitney U p >> 0.05). The single-seed result was noise.

**Rule going forward:** never state a between-condition difference as a finding until it survives multiple seeds. Single-seed results belong in "observations", not "conclusions".
