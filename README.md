# MMA Computer Vision Analysis

A computer vision system for Mixed Martial Arts — fighter tracking, spatial awareness, and a 2D
tactical overlay, reimagined for the chaotic, entangled, semantically rich environment of MMA
(rather than copied from soccer paradigms). Works on recorded video first; live overlay later.

**Scope:** starts as a **home project** — self-recorded or found public footage, single consumer
GPU, solo builder. The architecture is designed to shrink gracefully to this scope and scale later
without a rewrite.

## The one-line thesis

> MMA vision is **not** a tracking problem with a semantics layer on top. It is a
> **relational-state-estimation problem** where tracking is a (sometimes unsolvable) sub-task. The
> core job is "what is the relationship between these two bodies and what is each trying to do."
> The 2D radar is a *visualization* of that relational state — not the primary product.

## Documents

| Doc | What it is | Read it when |
|---|---|---|
| **[DESIGN.md](DESIGN.md)** | The full living design document — thesis, model design, semantics, the radar reframe, pipeline, data strategy, tech stack, architecture, addon evaluation, locked decisions, the assumption de-risking map, and open uncertainties. | You want the whole argument and the *why* behind every decision. |
| **[docs/ontology.md](docs/ontology.md)** | The position ontology + transition grammar (the load-bearing spec). | You're defining states, the fight-graph schema, or the constrained decoder. |
| **[docs/tier1-probe.md](docs/tier1-probe.md)** | The runnable de-risking probe with pre-committed thresholds. | **First.** Before building anything substantial. |
| **[docs/workstreams.md](docs/workstreams.md)** | Rig + annotation tool + eval harness as one flywheel. | You're building the data/eval infrastructure. |
| **[docs/backlog.md](docs/backlog.md)** | The atomized, dependency-ordered to-do list (P0–P6) with DONE conditions. | You're picking the next thing to build. |

## Where to start

1. **Read [DESIGN.md](DESIGN.md) §0–§3** for the thesis and the reframes (why not soccer; why the
   relational state diagram, not a top-down radar).
2. **Run the [Tier-1 probe](docs/tier1-probe.md)** — ~20 clips + off-the-shelf tools answer the
   four existential questions for days of effort. **Run sub-probe A2 (identity-swap detectability)
   first** — it's the failure that's both catastrophic and silent.
3. **Stand up the [three workstreams](docs/workstreams.md)** as one loop: the 2-phone rig makes
   ground truth → the annotation tool refines it → the eval harness measures and routes weaknesses
   back to the annotation queue.

## The non-negotiable commitments (from DESIGN.md §10)

1. **Every self-capture is multi-cam** — the existential-risk antidote, free at capture time.
2. **Calibrated uncertainty surfaces in the UI** — for expert users, *trust is the product*; a
   confident lie costs more than an honest "not sure."
3. **Self-captured footage is the ground-truth answer key** for grading single-view on found
   footage — the bimodal corpus is a validation ladder, not a liability.

## The risk to lose sleep over

**Undetected identity swaps** in fast scrambles — catastrophic (they invert the headline "who's
winning" output) and silent. The priority perception R&D is a robust identity-swap *detector*, not
a better separator. **Honest degradation beats fragile precision.**
