# Tier-1 Probe — "Is the single-view core real?"

> Retire assumptions A1–A4 (the load-bearing, cheap-to-test ones) with **measured numbers** using
> off-the-shelf tools + ~20 clips + one scorer. No novel models. Doubles as eval-set v0 and the
> eval harness's first run. **Thresholds are written down BEFORE running** so results can't be
> rationalized after the fact. See [`../DESIGN.md`](../DESIGN.md) §11 for the assumption map.

## 1. Clip set (~20 clips, 5–15s, adversarially weighted toward the hard cases)

| Bucket | # | Stresses | Criteria |
|---|---|---|---|
| Clean ground control | 4 | A1 baseline / ceiling | sustained mount/side/back, clear angle |
| Scrambles / fast transitions | 6 | A1 hard + A2 swaps | sweeps, reversals, back-takes |
| Stacked / heavy occlusion | 4 | A1 floor | bottom fighter largely occluded |
| Camera variance | 3 | robustness | broadcast-cuts / cage-side-fence / fixed |
| Stat-aligned events | 3 | A4 | clips with public play-by-play timestamps |

Diversity guardrails: ≥6 fights, ≥2 weight classes (body-size ratio), varied glove-color
contrast. **Don't let 20 clips secretly be 3 fights.**

## 2. Sub-probes (method → metric → PASS / CONCERN / KILL)

### A1 — single-view L2 (who's-on-top) recoverable
Off-the-shelf seg+pose → per-frame top/bottom call vs. human ground truth (with
`genuinely-ambiguous` excluded from the denominator). Metric: L2 accuracy **per bucket** +
**confident-wrong rate** (the real question is "when wrong, does it know?").
- **PASS:** clean ≥90 / scramble ≥70 / stacked ≥50, with the rest *abstaining* (not wrong).
- **CONCERN:** scramble 55–70 or stacked 35–50 → viable but needs temporal/grammar/multi-cam lift.
- **KILL:** scramble <55 with high confident-wrong → single-view core needs multi-cam to exist.

### A2 — identity swaps DETECTABLE (the one to lose sleep over)
Seed IDs at a clean entry frame; log mask-confidence, appearance distance, mask-overlap. For each
*true* swap, was there a precursor signal in the ~0.5s before? Metric: **swap-detection recall** +
false-alarm rate.
- **PASS:** ≥80% precursor recall → "flag as identity-suspect & degrade" is buildable.
- **CONCERN:** 50–80% → partially buildable; needs a real re-ID embedding (not just color).
- **KILL:** <50% silent → the most dangerous failure is undetectable off-the-shelf. **The single
  most important result in the probe.**

### A3 — grammar catches illegal flickers
Feed noisy / synthetically-corrupted state sequences through constrained Viterbi; sweep λ. Metric:
% flicker suppressed × % real transitions preserved. **No new models, no clip dependency — the
cheapest sub-probe.**
- **PASS:** ∃ λ with ≥85% suppressed AND ≥90% preserved → pick as the offline default λ.
- **CONCERN:** no clean window → demote grammar to light smoothing; lean on offline lookahead.

### A4 — public-stat timestamp alignment
For each official event (takedown / strike / sub attempt) with a published timestamp, find the
true visual frame; compute offset. Metric: offset distribution + whether it's *constant* (fixable
skew) or *variable* (irreducible slop).
- **PASS:** ±1s constant → single global per-fight alignment; weak labels usable.
- **CONCERN:** ±1–3s variable → coarse temporal anchors only; recost annotation.
- **KILL:** >3s wildly variable → needs per-event human anchoring; cheapest data lever is gone.

## 3. Verdict logic

| Outcome | Consequence |
|---|---|
| All PASS/CONCERN | Core is real on single-view; proceed carrying CONCERNs as known mitigations. |
| **A1 or A2 KILL** | **Multi-cam reclassified from addon to DEPENDENCY** for the core dominance product. The big strategic fork — discovered for days of effort, not months. |
| A3 KILL | Grammar demoted to smoothing (survivable). |
| A4 KILL | Data plan reworked (survivable; doesn't block perception). |

> Asymmetry to internalize: **A1/A2 are existential** (reorder the whole project); **A3/A4 are
> scoping** (cost a feature or a plan revision). If run in sequence, **run A2 first.**

## 4. Tooling & effort

Thin harness: clip loader → run each off-the-shelf model → dump per-frame outputs to **Parquet**
(the embryonic fight-graph format — not throwaway). A scoring UI: a notebook with a frame-stepper
and hotkeys for human labels. No GPU training; single-GPU inference is plenty. This is
**days-of-work-not-weeks** — that is what earns it "do before believing anything." The scored
clips become eval-set v0.
