# Position Ontology & Transition Grammar

> The load-bearing spec. Designed to be (a) human-legible to coaches, (b) machine-usable as a
> constrained-decoding grammar, (c) honest about fuzzy states. Everything in the system keys off
> this. See [`../DESIGN.md`](../DESIGN.md) §2 for why an explicit ontology beats a learned latent
> state space.

## 1. Design principles

1. **States are relational, dual-indexed.** One physical configuration → two per-fighter labels
   (guard-top vs. guard-bottom). Dominance is asymmetric.
2. **`SCRAMBLE` is a first-class state**, not an absence of state — prevents flickering and
   expresses genuine undefined-ness.
3. **The grammar is SOFT.** Transitions have *cost*, not boolean legality. Illegal-looking jumps
   are heavily penalized but never forbidden (real fights teleport in violent scrambles). Marked
   `DIRECT` / `RARE` / `FORBIDDEN*` (* = only via SCRAMBLE).
4. **Granularity is tiered** — collapse to Tier 1 by merging leaf states (ships earlier, degrades
   gracefully).

## 2. State hierarchy

**Tier 0 — Regime (always emitted):** `R-STAND`, `R-CLINCH`, `R-GROUND`, `R-TRANS`
(transitional: takedown/sprawl/stand-up in progress).

**Tier 1 — Core positions**

*Standing:* `S-OPEN` (striking range, symmetric) · `S-PRESS` (pressing/retreating) ·
`S-CAGE` (cage-controlling/cage-pinned).

*Clinch:* `C-NEUTRAL` (50/50) · `C-DOMINANT` (clinch-control/defending) · `C-CAGE`
(cage-pressing/pinned).

*Ground (dual-indexed top/bottom, with top-dominance):*

| ID | Top | Bottom | Dominance (top) |
|---|---|---|---|
| `G-GUARD` | in-guard | full-guard | low |
| `G-HALF` | half-guard-top | half-guard-bottom | low-mid |
| `G-SIDE` | side-control-top | side-control-bottom | mid-high |
| `G-NS` | north-south-top | north-south-bottom | mid-high |
| `G-MOUNT` | mount-top | mounted | high |
| `G-BACK` | back-control | back-taken | highest |
| `G-TURTLE` | turtle-top | turtle | mid |

*Universal:* `X-SCRAMBLE` (undefined/flux) · `X-SEPARATED` (broken apart, standup imminent).

**Tier 2 — Sub-positions (addon; collapse up to Tier 1):** e.g. `G-GUARD` → {closed, open,
butterfly, de-la-riva, …}; `G-BACK` → {both-hooks, one-hook, body-triangle, crucifix};
`C-DOMINANT` → {rear-body-lock, double-under, …}.

**Tier 3 — Action/event overlay (instantaneous; ride on the state stream):** `TAKEDOWN_ATTEMPT`,
`TAKEDOWN_LAND`, `SWEEP`, `REVERSAL`, `GUARD_PASS`, `SUBMISSION_ATTEMPT{type}`,
`SUBMISSION_DEFEND`, `STRIKE_ATTEMPT{zone}`, `STRIKE_LAND{zone}`, `KNOCKDOWN`, `STANDUP{ref|vol}`.

## 3. Ground transition cost matrix (top-fighter perspective)

`D`=direct/cheap · `R`=rare/expensive · `—`=forbidden-except-via-SCRAMBLE · `=`=self.

| from ↓ \ to → | GUARD | HALF | SIDE | NS | MOUNT | BACK | TURTLE | SCRAMBLE | SEP |
|---|---|---|---|---|---|---|---|---|---|
| **GUARD** | = | D | R | R | — | R | D | D | D |
| **HALF** | D | = | D | R | R | R | D | D | R |
| **SIDE** | R | D | = | D | D | R | D | D | R |
| **NS** | R | R | D | = | R | D | D | D | R |
| **MOUNT** | — | D | D | R | = | D | R | D | R |
| **BACK** | — | R | R | D | D | = | D | D | R |
| **TURTLE** | D | D | D | D | R | D | = | D | D |
| **SCRAMBLE** | D | D | D | D | D | D | D | = | D |

Design choices baked in:
- `MOUNT→GUARD` forbidden-except-scramble (catches a huge class of perception flicker errors — a
  sweep is *definitionally* a scramble).
- `SCRAMBLE` is the low-cost pressure-release valve, reachable from/to everything.
- `GUARD→MOUNT` forbidden but `GUARD→BACK` merely rare (encodes real grappling asymmetry).
- `TURTLE` connects cheaply to everything (the great branching point).

**Regime-level grammar:** `STAND→GROUND` and `GROUND→STAND` are forbidden-except-via-`R-TRANS`
(there is *always* a takedown/pull between them — catches dropped-frame errors automatically).

## 4. How the grammar is used (the data-efficiency payoff)

1. The semantic head emits a **distribution** over states per frame (not argmax).
2. **Constrained Viterbi/beam decode** over a window:
   `arg max Σ [ log P(state|frame) − λ · transition_cost ]`.
3. **`λ` is the single most important post-perception knob.** High λ = trust grammar, smooth,
   risks missing fast real transitions; low λ = trust pixels, jittery. **Live → higher λ; offline
   → lower λ (has lookahead, can trust evidence).**
4. **Events are DERIVED from transitions, not detected independently.** A
   `G-GUARD → SCRAMBLE → G-SIDE` with top/bottom inversion *emits a SWEEP*. Guard pass, reversal,
   stand-up, takedown — all transitions. A large fraction of MMA "events" are specific transitions
   in this grammar, so semantic richness comes mostly from the grammar, not from ever-more
   detection heads (this is **leap L1** in `DESIGN.md` §11).

## 5. Honest gaps

- **The top/bottom dual-index breaks for true neutral-ground / leg-entanglement** (50/50,
  ashi-garami, double-guard-pull) where *neither* is on top. Currently shoehorned into
  `X-SCRAMBLE` / `G-GUARD` — wrong. A complete ontology needs a `G-NEUTRAL-GROUND` /
  `G-LEG-ENTANGLE` branch. Left out of Tier 1 deliberately (rarer in MMA than pure grappling)
  but flagged as a real incompleteness.
- **Dominance-as-scalar is an approximation** — control quality (locked side control vs. one with
  an escape in progress) isn't captured by the position label alone. Useful Tier-1 approximation;
  do not oversell.
- **Inter-annotator agreement risk lives here** (half vs. quarter guard is a continuum). The
  adjacent-state-low-cost design makes a mislabel *cheap*, but the training target is still fuzzy.
