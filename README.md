# ALife Learning Lab

A personal sandbox for learning **Artificial Life** concepts through code.

I'm a software engineer (Java/backend background) starting to explore ALife and evolutionary dynamics. This repo documents what I build, what I observe, and what I don't understand yet.

---

## What this is

An agent-based simulation where small creatures live on a resource landscape, eat, spend energy moving, and reproduce — passing their speed to their children with slight mutations. No explicit fitness function. Selection emerges from the mechanics.

The only genetic trait: **speed**. Fast agents explore more but burn more energy. Slow agents are frugal but might starve in resource-poor areas. Who survives depends on the environment.

---

## What I've been learning

**Step 1 — Getting the energy balance right**

The hardest part wasn't the code, it was calibrating the energy balance. My first attempts had populations explode to 1000 agents in 30 ticks and devour all resources. The fix required understanding that `energy /= 2` on reproduction is wrong — it creates runaway growth because a parent at 200 energy drops to 100 and immediately reproduces again. The real fix: reproduction drops the parent to a fixed low value (40), making it a genuine sacrifice with a real recovery cost.

**Step 2 — Adding terrain with Simplex noise**

Implemented 2D Simplex noise from scratch (pure numpy, no library). Added a drought mode where the resource landscape slowly drifts — forcing agents to follow the oases or die. The `YlGn` colormap with a darkened floor makes resource gradients much more readable than plain green on black.

**Step 3 — Watching evolution happen**

With 15 agents and a restrictive environment, each lineage is individually tracked. The speed distribution consistently drifts downward over 400 ticks — slow agents survive better when food is scarce. In Perlin mode the drift is slightly slower (`-0.424` vs `-0.513` in flat), suggesting oases give fast agents a local advantage that partially counteracts the global pressure. I don't have enough runs yet to say this confidently.

---

## Current open questions

- Does terrain heterogeneity meaningfully preserve genetic diversity, or does it just delay the same outcome?
- At what drought migration speed do fast agents become advantageous again?
- What happens with a second heritable trait?

---

## Run it

```bash
pip install numpy matplotlib
cd sim
python main.py          # choose environment at launch
python main.py flat     # uniform resources (control)
python main.py perlin   # heterogeneous static terrain
python main.py drought  # terrain that slowly drifts
```

**Controls:** `Drought` slider shifts the resource landscape · `Mutation` slider adjusts genetic mutation rate · `Pause` button

---

## Structure

```
sim/
├── config.py         # all constants, documented
├── noise.py          # 2D Simplex noise, pure numpy
├── agent.py          # Agent class + simulation loop
├── environment.py    # flat / perlin / drought modes
├── visualization.py  # matplotlib multi-panel figure
└── main.py           # entry point with mode selector
```

---

## Stack

`numpy` · `matplotlib` · Python 3.11 · no ML frameworks

The goal is to understand the mechanics, not to use a library that hides them.

---

## What's next

- [ ] Comparison notebook — side-by-side analysis of the 3 environments
- [ ] Multi-seed runs to separate signal from noise in the speed drift
- [ ] Second genetic trait to observe co-evolutionary dynamics