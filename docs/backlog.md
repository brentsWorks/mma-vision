# Actionable Backlog

> Atomized to-dos derived from the design. Each item is a single sitting's work with an explicit
> **DONE =** condition. Ordered by dependency (not calendar). Phases gate each other:
> **P0 (de-risk) must verdict before P5 (models) is worth building.** This file mirrors the live
> task list. See [`../DESIGN.md`](../DESIGN.md), [`ontology.md`](ontology.md),
> [`tier1-probe.md`](tier1-probe.md), [`workstreams.md`](workstreams.md) for the *why*.

## The dependency spine

```
P0.0 scaffold
   └─► P0 PROBE (gates everything) ──────────────────► P0.8 VERDICT
            │                                               │
   P1 ontology/grammar/decoder ◄── feeds A3 ──┘            │ go/no-go
            │                                               ▼
   P2 rig ──► 3D ground truth ─────────────► P4 eval harness (multi-cam answer key)
            │                                               │
   P3 annotation tool ◄── labels ──────────────────────────┤
                                                            ▼
                              P5 models (regime, swap-detector, joint head, semantic)
                                                            │
                                                            ▼
                              P6 product (event API, View 2, dashboard, lite overlay, VLM)
```

---

## P0 — De-risk first (the probe gates the project)

- **P0.0** Scaffold repo: package layout, env, pinned deps, lint/CI skeleton. *DONE = installs clean, trivial test passes.*
- **P0.1** Assemble ~20-clip probe set per the bucket plan (4 clean / 6 scramble / 4 stacked / 3 camera-variance / 3 stat-aligned; ≥6 fights, ≥2 weight classes). *DONE = clips on disk, tagged, manifest CSV.*
- **P0.2** Probe harness: clip loader + off-the-shelf seg/pose runner → Parquet. *(needs P0.0)* *DONE = 1 clip → per-frame masks/keypoints/confidences in Parquet.*
- **P0.3** Scoring UI: frame-stepper + hotkey human labels (top/bottom, ambiguous, swap). *DONE = per-frame human-label CSV for a clip.*
- **P0.4 → run A2 FIRST** (identity-swap detectability). *(needs P0.1–P0.3)* *DONE = swap-detection recall + PASS/CONCERN/KILL. KILL<50% silent reorders the project.*
- **P0.5** Run A1 (single-view L2). *(needs P0.1–P0.3)* *DONE = per-bucket accuracy + confident-wrong rate + verdict.*
- **P0.6** Run A3 (grammar catches flickers). *(needs P1.2, P1.4)* *DONE = λ-sweep plot + verdict.*
- **P0.7** Run A4 (stat-timestamp alignment). *DONE = offset distribution + verdict.*
- **P0.8** Write the 4-row verdict scorecard + apply go/no-go logic; freeze the 20 clips as **eval-set v0**. *(needs P0.4–P0.7)*

> **A1/A2 are existential** (KILL ⇒ multi-cam becomes a dependency). **A3/A4 are scoping.**

## P1 — Ontology, grammar, decoder (the semantic spine)

- **P1.1** Encode `ontology.yaml` (states, tiers, dual-index, dominance, version tag).
- **P1.2** Encode `grammar.yaml` (transition cost matrices). *(needs P1.1)*
- **P1.3** Define `fightgraph.schema.json` (nodes/edges/global attrs + confidence + occluded-in-all-views).
- **P1.4** Constrained Viterbi/beam decoder with configurable λ. *(needs P1.2)*
- **P1.5** Event-derivation from transitions (SWEEP/PASS/REVERSAL/STANDUP/TAKEDOWN). *(needs P1.4)*

## P2 — Multi-cam rig → ground truth

- **P2.1** Record first 2-phone drilling session (≥60fps, clap-sync, scripted rare states, metadata/consent).
- **P2.2** Audio cross-correlation sync.
- **P2.3** Calibration (intrinsics + extrinsics) with reprojection logging.
- **P2.4** Triangulation → 3D ground-truth track + auto-draft fight-graph (mark/exclude occluded-in-all-views). *(needs P2.1–P2.3, P1.3)*

## P3 — Annotation tool

- **P3.1** Timeline state-segment editor (fixed ontology only; no box-drawing, no free-form).
- **P3.2** Model-proposal pre-population + correct-don't-create workflow. *(needs P3.1)*
- **P3.3** Active-learning surfacing + grammar lint + first-class ambiguity labels + ontology-versioned output. *(needs P3.2)*

## P4 — Eval harness

- **P4.1** Tier/bucket-layered metrics (incl. confident-wrong rate, swap-detection recall, calibration/ECE).
- **P4.2** Versioned, frozen, held-out eval set (seeded from v0; contamination check).
- **P4.3** Multi-cam ground truth as automated answer key (A1/A2 → standing dashboard). *(needs P2.4, P4.1)*
- **P4.4** Regression CI gate (per-bucket) + calibration ship-gate + slice analysis → annotation queue. *(needs P4.1, P4.2)*

## P5 — Models (only worth building once P0 verdicts green)

- **P5.1** Regime classifier (stand/clinch/ground/trans) + shot-boundary gate that resets identity on cuts.
- **P5.2** **Identity-swap DETECTOR** — priority perception R&D; degrade gracefully, don't lie.
- **P5.3** Joint keypoint+identity head (largest novel surface; swappable; beat the decoupled baseline or fall back).
- **P5.4** Semantic temporal model → calibrated per-frame state distributions feeding the decoder. *(needs P1.5, P5.1, P5.3)*

## P6 — Product surfaces (all consume the event stream)

- **P6.1** Event-stream API (atom = semantic event). *(needs P5.4)*
- **P6.2** View 2: relational state diagram + dominance gauge, with calibrated uncertainty in the UI. *(needs P6.1)*
- **P6.3** Coach dashboard (V1 surface). *(needs P6.1)*
- **P6.4** Scrappy lite live overlay (regime + dominance only) — a test instrument, not the product. *(needs P6.1)*
- **P6.5** VLM commentary/highlights from the event stream. *(needs P6.1)*

---

## Cross-cutting invariants (apply to every task)

1. **Calibrated uncertainty everywhere** — every keypoint/state/event carries confidence; low-confidence has defined degrade behavior.
2. **Never guess occluded-in-all-views** — exclude, don't fabricate.
3. **Honest degradation beats fragile precision** — the eval metrics reward it (confident-wrong rate, swap-detection recall).
4. **The event stream is the product API** — not bounding boxes; every view is a thin consumer.
5. **Novelty budget spent only on P5 models** — everything else is proven, boring infrastructure.
