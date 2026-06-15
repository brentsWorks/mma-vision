# MMA Computer Vision Analysis — Living Design Document

> **Status:** First-principles design, scoped to a **home project**. This is a living
> document — where decisions changed during reasoning, the trail is kept visible; where
> genuine uncertainty remains, it is flagged rather than papered over.
>
> **Scope assumption (governs everything below):** This starts as a home project. Training,
> observation, and testing footage is **hand-recorded (self-captured) or found public
> fighting footage**. Single consumer GPU / Colab-class hardware. Solo builder. The
> architecture is designed to *shrink gracefully* to this scope and *scale later* without
> a rewrite.

---

## 0. Core Thesis — why MMA is not soccer

The instinct is to copy soccer vision (player tracking → pitch homography → 2D tactical
radar). **That is a trap.** Soccer is cooperatively legible: players are spatially
separated, the field is a known flat plane with painted fiducials, "position" is a
meaningful 2D quantity, and actions are discrete and separable. MMA violates every one of
those:

1. **Two bodies, constant entanglement.** In the clinch and on the ground the athletes are
   a single fused blob of interpenetrating limbs. This is the central problem; everything
   else is downstream.
2. **The relevant geometry is the bodies relative to *each other*, not to the cage.** Where
   a fighter stands matters far less than whether he has back control.
3. **The state space is vertical and topological, not planar.** Standing vs. ground is a
   categorical regime change. "Mount" vs. "side control" is a *topological relationship
   between two bodies*, not a position on a plane.
4. **Actions are continuous, overlapping, semantically dense.** No ball to disambiguate
   intent.
5. **Annotated data barely exists.** There is no StatsBomb for MMA.

> **THESIS:** MMA vision is **not a tracking problem with a semantics layer on top. It is a
> relational-state-estimation problem where tracking is a (sometimes unsolvable) sub-task.**
> The system's core job is "what is the relationship between these two bodies and what is
> each trying to do." The 2D radar is a *secondary visualization* of that relational state —
> not the primary product.

---

## 1. Computer Vision Model Design

### 1.1 The atom is the keypoint and the relation — NOT the bounding box
A box around a grappling exchange contains both athletes and is nearly useless. Design
around keypoints + relations, not boxes.

### 1.2 Model families (decisions, with the alternatives that were argued and rejected)

- **Detection / regime:** YOLO-class person + regime detector for the global frame (how many
  bodies, standing vs. ground, cage localization). *Rejected as the core:* YOLO alone gives
  one wobbly box on a grappling pile — solves the easy 30%, fails the defining 70%.
- **Identity through entanglement:** **promptable video segmentation with a memory bank
  (SAM 2-class).** Seed identity once when bodies are separable, propagate the mask through
  the scramble. This is the load-bearing perception choice.
- **Pose + identity — JOINT, not separate (changed my mind here):** initially wanted a clean
  separate pose model; concluded keypoints and identity are **inseparable in MMA** and must
  be solved jointly — a custom head emitting keypoints with a learned soft A/B assignment,
  trained for temporal consistency. **This is the largest novel trained surface; treat as
  high-risk/high-value and keep it swappable behind the fight-graph interface.**
- **Action/semantics:** NOT a giant end-to-end video net (data-hungry, no spatial output,
  hallucinates). Two-stage: per-clip visual encoder feeding a temporal model over the
  *structured* pose/relation stream (see §2).

### 1.3 The VLM was demoted (changed my mind)
A fine-tuned video-language model was considered as the perception core and **rejected**
(latency, data hunger for fine transitions, no coordinate output, hallucination). It
survives at the **edges**: weak-labeling/annotation oracle (§5) and commentary/highlights
(§9). Good example of a feature that sounds impressive as a centerpiece but earns its place
only at the periphery.

### 1.4 Train from scratch: NOTHING
Data scarcity makes from-scratch suicidal. Everything is transfer learning / fine-tuning on
pretrained backbones. The only genuinely novel trained components: (1) joint keypoint+identity
head, (2) the MMA-state temporal model, (3) action heads. Keep novel surface area minimal —
that is where data risk concentrates.

### 1.5 Footage-type variance is the norm, not an edge case
A **shot-boundary / camera-regime classifier** is a mandatory front gate. On a broadcast cut,
identity assignment MUST reset and re-anchor — pretending tracking persists across a cut
silently corrupts everything. Footage domain (broadcast / cage-side / self-captured) is an
explicit conditioning input, possibly with per-regime heads.

### 1.6 Design for failure (the recurring principle)
Full ground separation is sometimes **physically unrecoverable** from a single 2D view. Every
keypoint, identity assignment, and state label carries **calibrated confidence**. Downstream
consumers have defined low-confidence behavior (e.g. the radar collapses two bodies into one
"entangled" glyph). **A system that hallucinates precise pose in a scramble is worse than one
that honestly says "ground, entangled, ~70% A on top."**

---

## 2. Semantic Understanding Layer (the heart)

### 2.1 Define the ontology before any model
You cannot recognize states you have not named. MMA needs an explicit finite-state ontology
with transition rules. Full spec in **§ Appendix A**.

### 2.2 Explicit ontology beats learned-latent (decision)
A learned latent state space is cleaner and less anthropocentric, but rejected for the core
because: (a) output must be human-legible to coaches; (b) domain priors can be injected as
**hard-ish grammar constraints** (you cannot teleport mount→standing), which massively
regularizes a data-starved model; (c) you can only evaluate against expert agreement if labels
are named. **The ontology is a grammar, and illegal transitions are prunable — this is the
single biggest lever against data scarcity.**

### 2.3 The intermediate representation: the FIGHT GRAPH
The bridge from pixels to semantics is a structured per-frame **fight graph**, not raw
detections:
- **Nodes:** fighter A, fighter B, their keypoints/limb segments.
- **Edges:** contact relations (A's arm controls B's neck), relative position (A's hips above
  B's), pressure direction.
- **Global attrs:** regime, who's-on-top probability, against-cage flag.

> **THE KEY SEAM:** perception's job is to produce the best possible fight graph; semantics'
> job is to interpret the *sequence* of fight graphs. This boundary lets the two halves be
> built, tested, and sourced independently.

### 2.4 Core vs. addon within semantics
- **Mandatory:** regime classification, ground-position recognition + dominance, strike-attempt
  & takedown detection.
- **Addon:** submission *type*, sweep/reversal, fine clinch taxonomy.
- **Honestly uncertain:** "landed" vs. "attempted" strike from a single broadcast angle is
  sometimes physically undecidable. Do not pretend single-view landed-strike detection is
  reliable.

---

## 3. The 2D Spatial Overlay / "Radar" (reframed — changed my mind)

The literal soccer-style top-down radar is **near-worthless** in MMA: cage position is
low-information; the tactically loaded quantity is the *relational state*. Rejected as the
headline. Reshaped into **two distinct views**:

- **View 1 — Cage radar (LOW priority, standing-only).** Genuine top-down of the octagon,
  useful *only* for cage control / cage-cutting in striking. Hands off to View 2 the moment
  they hit the ground. Needs cage homography (cage geometry as fiducial).
- **View 2 — Relational state diagram (HIGH priority, the real product).** Not a map — a
  schematic of the two-body relationship: position icon (mount/back/etc.), dominance gauge,
  active threats. This encodes the *topological* state a map fundamentally cannot.

> The vertical-dimension problem is NOT solved by projecting 3D into 2D. It is solved by
> recognizing ground state is **topological, not spatial**, and rendering it as a known-position
> diagram driven by the semantic layer.

Same semantic backend, different renderers per audience (coach / general viewer / stats).
Confirms the semantic layer is the product and the radar is *a view*.

---

## 4. Real-Time vs. Offline (two products, shared components)

- **Offline (uploaded video) — V1, the home project's path.** No latency budget → full,
  un-distilled, **bidirectional** temporal models (lookahead massively improves entanglement
  resolution — knowing what happens 2s later disambiguates a scramble *now*). This is also
  where active-learning data harvesting happens.
- **Real-time (live overlay) — DEFERRED.** ~100–150ms budget forbids large models; requires
  distillation/quantization, screen compositing, identity-under-load. ~60% of the engineering
  pain for ~20% of validated value. **A scrappy "lite" overlay (regime + dominance gauge only)
  is built early as a *test/debug visualization*, not a product.**

> **Decision: offline-first.** More defensible, generates the data flywheel, validates the
> semantic layer before paying the real-time tax. Confirmed by home-project hardware reality.

---

## 5. Data Strategy (the actual hardest problem)

### 5.1 Bootstrap sequence
1. **Pretrained backbones do the heavy lifting** — we only ever *adapt*.
2. **Weak/auto-labeling first.** Public fight stats / play-by-play timestamps ("takedown at
   2:31") as **weak temporal labels** aligned to footage. Cheapest large-scale MMA-specific
   signal. (Alignment tightness is probed — see Appendix B / A4.)
3. **VLM as a weak labeler** — propose coarse labels, humans *verify* (cheap) not *create*
   (expensive).
4. **Active-learning loop** — the offline pipeline flags low-confidence segments (scrambles) →
   human labels them → fine-tune → repeat. The system's weaknesses drive what gets labeled.

### 5.2 Self-captured footage = the ground-truth answer key (home-project superpower)
Two-phone self-recorded drilling is *multi-view* and therefore **ground-truthable** (Appendix
C). It becomes the answer key that grades single-view predictions on found footage. The bimodal
corpus (clean self-captured vs. found broadcast) is a **validation ladder, not a liability**:
train/validate hard CV on ground-truthed self-captured footage, test generalization on found
footage.

### 5.3 Synthetic data — accept, but scoped
Worth it *specifically* for the entanglement / occluded-keypoint problem (where real labels are
near-impossible). NOT worth it for what real footage already covers. Sim-to-real for deformable,
contact-rich grappling is severe and **unproven — treat as a measured experiment with a kill
switch**, not a primary corpus.

### 5.4 Annotation tooling is a first-class deliverable — see Workstream 2.

---

## 6. Tech Stack (opinionated; novelty budget spent ONLY on the models)

- **Training:** PyTorch. Experiment tracking (W&B-class). Thin trainer.
- **Backbones:** SAM 2-class video segmentation; ViT-based pose; self-supervised-pretrained
  video transformer for action encoding. Hugging Face for weights.
- **Inference:** ONNX Runtime / TensorRT for any real-time path (later); plain Torch fine for
  offline/home.
- **Semantic/temporal layer:** lightweight transformer + **grammar-constrained decoding**.
- **Overlay rendering:** decoupled from inference via a shared state buffer; Skia/WebGPU for the
  scrappy lite overlay.
- **Pipeline orchestration (offline):** start simple (scripts) at home; Ray when scale demands.
- **Storage:** raw video on disk/object store; fight-graphs + features in **Parquet**; semantic
  events + states in **Postgres** (later); vector store only if/when "find every armbar-from-
  guard" becomes real.
- **API:** the product API atom is the **semantic event**, not the bounding box.

> Through-line: **modern, but boring where it can be.** Spend the entire novelty budget on the
> perception + semantic models; everything around them is proven infrastructure.

---

## 7. System Architecture

```
                 ┌─────────────────────────────────────────────┐
   VIDEO IN ───► │  INGEST / SHOT-BOUNDARY / CAMERA-REGIME GATE │
 (offline first) └───────────────┬─────────────────────────────┘
                                 │ (resets identity on cuts)
                 ┌───────────────▼──────────────┐
                 │  PERCEPTION CORE             │
                 │  • regime + cage detect      │
                 │  • video-seg identity memory │  ◄── emits CALIBRATED
                 │  • joint keypoint+ID head    │      UNCERTAINTY
                 │  • contact-topology head     │
                 │  • IDENTITY-SWAP DETECTOR     │
                 └───────────────┬──────────────┘
                                 │  FIGHT-GRAPH (per frame)  ◄── KEY SEAM
                 ┌───────────────▼──────────────┐
                 │  SEMANTIC LAYER              │
                 │  • ontology state machine    │ ◄─┐ thin "predicted-state
                 │  • grammar-constrained decode│   │ prior" feedback path
                 │  • events = transitions      │   │ (ABLATABLE flag)
                 └───────────────┬──────────────┘ ──┘
                                 │  SEMANTIC EVENT STREAM (the product API)
          ┌──────────────────────┼──────────────────────────┐
          ▼                      ▼                           ▼
   RELATIONAL VIEW (V2)    CAGE RADAR (V1)        DASHBOARDS / STATS / VLM
   + dominance gauge       (standing only)        COMMENTARY / EXPORT
```

**Two clean seams:** Perception →(fight graph)→ Semantics →(event stream)→ all consumers.

**A thin feedback path (revised in):** the grammar's posterior biases next-frame perception
("predicted-state prior"). Materially helps borderline who's-on-top calls. **Kept behind an
ablatable flag** to avoid confirmation-bias lock-in; ship feed-forward-only as the safe baseline.

**Hardest integration points (named honestly):**
1. Identity persistence through entanglement and across cuts (mitigated, not solved).
2. Fight-graph quality under occlusion (garbage in → garbage out, worst exactly when it matters).
3. Temporal cadence mismatch (fast detection / slow semantics / display-rate render) — shared
   state buffer.
4. Real-time vs. offline model divergence (later concern).

---

## 8. Core vs. Addon — the ruthless cut

**Mandatory core** (system is meaningless without): regime classification; fighter identity/
separation with calibrated uncertainty; ground-position + dominance; strike-attempt & takedown
detection; fight-graph + semantic event stream; relational state view (V2) + dominance gauge.

**Valuable addons** (depth, not existence): submission-type classification; cage radar (V1);
coach dashboards; VLM commentary/highlights; stats-API integration.

---

## 9. Addon Evaluation (accept / reject / reshape)

| Addon | Verdict | Reasoning |
|---|---|---|
| **Biometric estimation (reach/height)** | **Mostly reject** | Unreliable from monocular footage; the numbers are *already published facts*. Reshape: ingest official tale-of-the-tape as a **prior to improve pose scale calibration**. |
| **Strike velocity / force** | **Reject force, reshape velocity** | "Force" is uncomputable from video — fake physics destroys credibility. Velocity is estimable but noisy; offline only, with error bars, never "force." |
| **Predictive (submission likelihood, fatigue)** | **Accept as downstream analytics** | Tractable sequence model on the event stream. **Fatigue = proxy indicators** (output-rate decline, posture droop), NOT a fabricated scalar. |
| **Multi-camera fusion** | **Accept; strongest mitigation for the core failure mode** | Second angle directly attacks entanglement ambiguity & landed-vs-attempted. Architecturally first-class; at home, realized via the 2-phone rig (Workstream 1). |
| **Commentary / highlights** | **Accept — where the demoted VLM shines** | Feed the *event stream* (not pixels) to an LLM → grounded play-by-play & auto-clips. Grounding prevents hallucination. |
| **Coach tactical dashboards** | **Accept — flagship, the V1 product** | Highest value density, pure event-stream consumer, zero new perception risk. |
| **Fight-data API integration** | **Accept — pull EARLIER than "addon"** | Double duty: weak-labeling training source AND cross-check to validate the model's own detections. |

---

## 10. Locked Decisions (this project's constraints)

| Decision | Choice | Consequence |
|---|---|---|
| **Scope** | Home project | Solo, single GPU/Colab, offline-first hard. |
| **Footage** | Hand-recorded + found public footage | Bimodal corpus → answer-key ladder (§5.2). Public footage fine for research; revisit if commercializing. |
| **V1 customer** | Team/coach tactical tool, with a thin wider-audience packaging layer | Event stream + dashboards are the product; semantic correctness, not latency, is the bar. |
| **Live overlay** | Deferred; scrappy "lite" version (regime + dominance only) built early as a **test instrument** | Avoids the real-time tax; keeps a cheap demo/debug surface. |
| **Multi-cam** | Realized at home as **2 phones on tripods** | Existential-risk antidote + ground-truth source — free at capture time. |

**Three non-negotiable load-bearing commitments:**
1. **Every self-capture is multi-cam** — the existential-risk antidote, free at capture time.
2. **Calibrated uncertainty surfaces in the UI** — for expert users, *trust is the product*; a
   confident lie costs more than an honest "not sure."
3. **Self-captured footage is the ground-truth answer key** for grading single-view on found
   footage — bimodal corpus becomes a validation ladder, not a liability.

---

## 11. Assumption De-Risking Map

The failure mode of an innovative system is not *having* leaps of faith — it's **not knowing
which assumptions are leaps and which are just untested laziness.** Every load-bearing assumption
is sorted below.

### Tier 1 — KILL-FIRST (high leverage, cheap to test → the Tier-1 Probe, Appendix B)
- **A1** Single-view L2 (who's-on-top) is recoverable in most ground frames.
- **A2** Identity swaps are *detectable* even if not preventable. **(The one I'd lose sleep
  over — silent + inverts the headline output.)**
- **A3** The grammar catches illegal flickers (MOUNT→GUARD without scramble).
- **A4** Public-stat timestamps align tightly enough to footage to be weak labels.

### Tier 2 — MONITOR (high leverage, expensive → instrument, don't pre-test)
- **B1** Inter-annotator agreement on the ontology (on the critical path because V1 is a coach
  tool). At home: self-consistency check (relabel weeks apart).
- **B2** The joint keypoint+identity head (largest novel surface) — kept swappable behind the
  fight-graph interface; falls back to decoupled baseline if it loses.
- **B3** Real-time quality under distillation (deferred with the live product).
- **B4** Sim-to-real transfer (measured experiment with a kill switch).

### Tier 3 — LEAP (genuine faith bets; accept, but the architecture makes each cheap to be
wrong about)
- **L1** Events-as-grammar-transitions replaces most action-detection heads. *Wrong = add some
  detectors back to the same event-stream interface. No rebuild.*
- **L2** The relational diagram (View 2), not the radar, is what users want. *Wrong = build
  View 1 from the same event stream. Already cheap.*
- **L3** The semantics→perception feedback prior helps net without confirmation lock-in. *Wrong
  = flip the ablation flag off.*

> A leap whose failure rebuilds the system is recklessness; a leap whose failure costs a feature
> or a flag flip is innovation. All three remaining leaps are the latter.

---

## 12. The Three Workstreams (one self-improving loop)

> **Rig (WS1) makes ground truth → Annotation (WS2) refines it & trains → Eval (WS3) measures &
> finds weaknesses → weaknesses route back to WS2's active-learning queue → new data → better
> model.** Three tools, one flywheel. All three are achievable solo at home.

### Workstream 1 — Multi-Cam Capture Rig (home: 2-phone bootstrap)
*Purpose: the existential-risk antidote. The only physical cure for occlusion is a second
viewpoint; it also manufactures the ground-truth answer key.*

- **Home scale:** 2 phones/webcams on tripods filming own drilling. (Principle scales to 3–4
  around a cage later; see Appendix C for the full geometry.)
- **C1 is intentionally the WORST (broadcast-realistic) angle**; the other camera(s) exist to
  *grade* C1.
- **Sync:** software, via a clap/transient + audio cross-correlation; capture ≥60fps so residual
  sync error is a small fraction of a frame.
- **Calibration:** printed checkerboard for intrinsics; checkerboard/ChArUco (or cage geometry,
  later) for extrinsics; log reprojection error per session.
- **Ground-truth mechanism:** run pose/seg on all views → **triangulate** keypoints (recovering
  joints occluded in C1) → compute L2/L3 geometrically → this is the **answer key for C1's
  single-view frame.**
- **Honest limit:** joints occluded in *all* views are marked `occluded-in-all-views` and
  excluded from the answer key — never guessed. 2 views (vs 3) means more such gaps; acceptable.
- **Protocol:** consent/releases logged; **scripted coverage of rare ontology states** (the rig
  is a *scenario generator*, not just a recorder); metadata incl. body-size ratio, lighting,
  glove-color contrast.
- **Output:** synced video per cam + calibration bundle + **3D ground-truth track** + auto-drafted
  fight-graph → feeds WS2 (as a high-quality proposal) and WS3 (as ground truth).

### Workstream 2 — Model-Assisted Annotation Tool (home: single-annotator timeline tool)
*Purpose: label quality hard-caps model quality. For a coach tool, the labels ARE the product's
vocabulary. Must make a human 10× faster by **correcting model proposals, not labeling from
scratch.***

- **Unit of annotation = timeline state segments + transition points**, NOT boxes. Interface is a
  video timeline with a state track underneath (like an audio editor), not a frame box-drawer.
- **Workflow:** load a clip *pre-segmented* by the model (or, for self-captured, by the WS1
  ground-truth draft — near-perfect) → annotator adjusts boundaries, relabels, confirms
  (one keystroke). Effort concentrates on the scrambles the model flubbed.
- **Active-learning surfacing:** the tool jumps the annotator to the **lowest-confidence segments
  first** — time spent where labels are most valuable.
- **Grammar-aware:** flags illegal sequences in the human's *own* labels ("MOUNT→GUARD with no
  scramble — missed a transition?").
- **IAA handling (home):** multi-expert mode deferred; **self-consistency check** (relabel weeks
  apart, measure own drift). Schema ready for multi-annotator later. **First-class ambiguity
  labels** (`genuinely-ambiguous` / `low-confidence`) feed the model's calibrated-uncertainty
  target. Labels are **ontology-versioned**.
- **Scoped OUT:** no box-drawing as a primary feature; no free-form labels (fixed ontology only);
  not a general-purpose platform. A local web app, not a hosted product.
- **Output:** human-verified fight-graph + state-segment timeline + event list, versioned, with
  per-segment confidence & agreement metadata → training data AND eval ground truth.

### Workstream 3 — Eval Harness (home: fully feasible — the project's discipline)
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

- **Two metrics in lights:** **confident-wrong rate** (L2) and **swap-detection recall**
  (identity) — both encode *honest degradation beats fragile precision*.
- **Eval set:** seeded by the Tier-1 probe's clips (= v0); grown via active learning; **stratified,
  frozen per version, strictly held-out** (a contaminated eval set manufactures false confidence —
  worst possible failure for a trust-based product).
- **Killer feature:** the WS1 multi-cam 3D track is **automated ground truth** → grade single-view
  (C1) against multi-view truth *at scale, without hand-labeling*. **This converts the scariest
  open risk (A1/A2) from a one-time probe into a standing dashboard.**
- **Regression CI:** every model change runs the full harness before shipping; **per-bucket** gate
  (an overall gain that regresses scrambles FAILS). Sliceable by footage domain / body-size /
  lighting → catches the B1 domain gap.
- **Calibration is a ship-gate**, not a nice-to-have — it is the quantitative form of the trust
  promise.
- **Output:** versioned scorecard + regression verdict + worst-slice list → feeds back into WS2's
  active-learning queue.

---

## 13. Genuine Open Uncertainties (not papered over)

1. **Single-view ground separation may cap at the coarse level** ("entangled, ~70% A on top") in
   the worst scrambles/stacks. Empirical; the rig measures it but cannot make the physically
   invisible visible. *Partly resolved:* the core was scoped to need only L1–L2 + discriminative
   features, which survive; the deep layer (full pose, submission-limb tracking, velocity) is
   gated on multi-cam.
2. **Inter-annotator (or self-) agreement on the ontology.** If labels aren't stable, there is no
   stable training target. Adjacent-state-low-cost design partially mitigates; must be measured.
3. **Sim-to-real transfer for synthetic grappling** — plausible, unproven.
4. **Real-time quality under a distilled/single-GPU budget** — may force live down to "regime +
   dominance only." Deferred.
5. **Landed-vs-attempted strike from a single broadcast angle** — sometimes physically undecidable;
   depends on multi-cam availability.

> The one risk to lose sleep over remains **A2: undetected identity swaps** — catastrophic
> (inverts the headline) and silent. The priority perception R&D is a robust identity-swap
> *detector*, not a better separator: **honest degradation beats fragile precision.**

---

# Companion Documents

The detailed specs live in their own files so they can be opened independently while building:

- **[`docs/ontology.md`](docs/ontology.md)** — the position ontology, dual-indexed state hierarchy,
  the transition cost matrix, how the grammar is used at inference, and the honest gaps. *The
  load-bearing spec; everything keys off it.*
- **[`docs/tier1-probe.md`](docs/tier1-probe.md)** — the runnable Tier-1 probe (clip set,
  sub-probes A1–A4 with pre-committed PASS/CONCERN/KILL thresholds, verdict logic). *Do this
  before believing the design.*
- **[`docs/workstreams.md`](docs/workstreams.md)** — the three workstreams as one self-improving
  loop: the multi-cam rig (incl. full geometry), the annotation tool, and the eval harness, each
  with its output contract.

See also **[`README.md`](README.md)** for the orientation / where-to-start index.
