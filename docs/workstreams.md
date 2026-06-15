# The Three Workstreams (one self-improving loop)

> **Rig (WS1) makes ground truth → Annotation (WS2) refines it & trains → Eval (WS3) measures &
> finds weaknesses → weaknesses route back to WS2's active-learning queue → new data → better
> model.** Three tools, one flywheel. All three are achievable solo at home. See
> [`../DESIGN.md`](../DESIGN.md) for the full design and locked decisions.

---

## Workstream 1 — Multi-Cam Capture Rig (home: 2-phone bootstrap)

*Purpose: the existential-risk antidote. The only physical cure for occlusion is a second
viewpoint; it also manufactures the ground-truth answer key.*

- **Home scale:** 2 phones/webcams on tripods filming own drilling. Scales to a 3–4-cam cage rig
  later (geometry below).
- **C1 is intentionally the WORST (broadcast-realistic) angle**; the other camera(s) exist to
  *grade* C1. The rig's output isn't "good footage" — it's "C1's hard footage + the answer key."
- **Sync:** software, via a clap/transient + audio cross-correlation; capture ≥60fps (120 pref.)
  so residual sync error is a small fraction of a frame and fast scrambles have resolution.
- **Calibration:** printed checkerboard for intrinsics; checkerboard/ChArUco (or cage geometry,
  later) for extrinsics; **log reprojection error per session** — if it drifts (camera bumped),
  flag that session's ground truth as suspect.
- **Ground-truth mechanism:** run pose/seg on all views → **triangulate** keypoints (recovering
  joints occluded in C1 but visible elsewhere) → compute L2 (who's-on-top, geometric) & L3
  (limb ownership) → this is the **answer key for C1's single-view frame.** Lets you measure,
  at scale, how often single-view matches multi-view truth — the scaled version of probe A1/A2.
- **Honest limit:** joints occluded in *all* views are marked `occluded-in-all-views` and
  excluded from the answer key — never guessed. 2 views (vs 3) means more such gaps; acceptable.
  The rig knows what it can't see.
- **Protocol:** consent/releases logged (the clean-licensing half of the corpus); **scripted
  coverage of rare ontology states** (the rig is a *scenario generator*, not just a recorder);
  metadata incl. body-size ratio, lighting, glove-color contrast.
- **Output contract:** synced video per cam + calibration bundle + **3D ground-truth track** +
  auto-drafted fight-graph → feeds WS2 (as a high-quality proposal) and WS3 (as ground truth).

### Rig geometry (full / future scale)

| Cam | Position | Height | Job |
|---|---|---|---|
| **C1 — Broadcast-proxy** | cage-side corner, chest height | ~1.2m | the *worst*, broadcast-realistic angle — the one being graded |
| **C2 — Opposite oblique** | diagonally opposite, raised | ~2.5m | primary disambiguation partner (sees C1's blind spots) |
| **C3 — Long-side elevated** | midpoint long side, high | ~3m | third triangulation leg; covers the C1–C2 shared blind axis |
| **C4 — Overhead (optional)** | center ceiling, down-looking | ceiling | the dream "radar" angle; makes L2 near-trivial |

**3 cameras is the sweet spot** (for almost any entanglement, ≥2 keep a usable view) — research-
grade ground truth without a volumetric lab. Cameras placed so blind spots *don't coincide*.
Home starts at 2 phones; shared-blind-axis gaps are excluded, never guessed.

---

## Workstream 2 — Model-Assisted Annotation Tool (home: single-annotator timeline tool)

*Purpose: label quality hard-caps model quality. For a coach tool, the labels ARE the product's
vocabulary. Must make a human 10× faster by **correcting model proposals, not labeling from
scratch.***

- **Unit of annotation = timeline state segments + transition points**, NOT boxes. Interface is a
  video timeline with a state track underneath (like an audio editor), not a frame box-drawer.
- **Workflow:** load a clip *pre-segmented* by the model (or, for self-captured footage, by the
  WS1 ground-truth draft — near-perfect) → annotator adjusts boundaries, relabels, confirms
  (one keystroke). Effort concentrates on the scrambles the model flubbed.
- **Active-learning surfacing:** the tool jumps the annotator to the **lowest-confidence segments
  first** — time spent where labels are most valuable.
- **Grammar-aware:** flags illegal sequences in the human's *own* labels ("MOUNT→GUARD with no
  scramble — missed a transition?").
- **IAA handling (home):** multi-expert mode deferred; **self-consistency check** (relabel a clip
  weeks apart, measure own drift). Schema ready for multi-annotator later. **First-class ambiguity
  labels** (`genuinely-ambiguous` / `low-confidence`) feed the model's calibrated-uncertainty
  target. Labels are **ontology-versioned** (the ontology will evolve — see the leg-entanglement
  gap in [`ontology.md`](ontology.md) §5).
- **Scoped OUT:** no box-drawing as a primary feature; no free-form labels (fixed ontology only);
  not a general-purpose platform. A local web app, not a hosted product.
- **Output contract:** human-verified fight-graph + state-segment timeline + event list, versioned,
  with per-segment confidence & agreement metadata → training data AND eval ground truth.

---

## Workstream 3 — Eval Harness (home: fully feasible — the project's discipline)

*Purpose: silent regression is the death mechanism for an expert-user tool. Also IS the Tier-1
probe — the probe is the harness's first run.*

- **Tier/bucket-layered metrics** (no lying averages):

  | Layer | Metric | Bar |
  |---|---|---|
  | Regime | accuracy, confusion matrix | near-solved |
  | **L2 dominance** | accuracy + **confident-wrong rate** | core; per bucket |
  | Position class | accuracy + adjacent-vs-distant error | adjacent errors forgiven |
  | Transitions/events | precision/recall + **temporal IoU** | sub-attempt expected weak |
  | **Identity** | **swap rate + swap-detection recall** | the existential one |
  | **Calibration** | reliability diagram, ECE | **ship-gate** |

- **Two metrics in lights:** **confident-wrong rate** (L2) and **swap-detection recall** (identity)
  — both encode *honest degradation beats fragile precision*. A model that's 85% accurate but
  knows its 15% beats a 90% model that's confidently wrong on the 10%.
- **Eval set:** seeded by the Tier-1 probe clips (= v0); grown via active learning; **stratified,
  frozen per version, strictly held-out** (a contaminated eval set manufactures false confidence —
  the worst possible failure for a trust-based product).
- **Killer feature:** the WS1 multi-cam 3D track is **automated ground truth** → grade single-view
  (C1) against multi-view truth *at scale, without hand-labeling*. **This converts the scariest
  open risk (A1/A2) from a one-time probe into a standing dashboard.**
- **Regression CI:** every model change runs the full harness before shipping; **per-bucket** gate
  (an overall gain that regresses scrambles FAILS). Sliceable by footage domain / body-size /
  lighting → catches the scraped-vs-captured domain gap.
- **Calibration is a ship-gate**, not a nice-to-have — it is the quantitative form of the trust
  promise to coaches.
- **Output contract:** versioned scorecard + regression verdict + worst-slice list → feeds back
  into WS2's active-learning queue. This closes the flywheel.
