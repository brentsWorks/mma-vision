---
name: backlog-task
description: >
  Use when starting, resuming, or implementing any backlog P-item (e.g. "do P1.4",
  "resume the backlog", "work on P0.2") in the MMA vision project. Grounds the task in
  the original design docs (DESIGN.md, docs/ontology.md, docs/tier1-probe.md,
  docs/workstreams.md) before any code is written, then proceeds test-first. Prevents
  implementing from the one-line backlog summary alone, which drifts from the plan.
---

# Implementing a backlog P-item

The backlog (`docs/backlog.md`) is intentionally terse — one line per task. The *why*,
the precise contracts, and the constraints live in the design docs. Building straight from
the one-liner drifts from the plan. So **before writing code for any P-item, produce a short
grounding brief from the original docs, then implement test-first.**

## Step 1 — Read the backlog entry and follow its links

`docs/backlog.md` already tells you which docs matter:

- Its header links the four source docs: `DESIGN.md`, `docs/ontology.md`,
  `docs/tier1-probe.md`, `docs/workstreams.md`.
- Each P-item's `*(needs …)*` notes name its upstream dependencies.
- The phase tells you the primary doc (derive this live; don't hardcode a stale map):
  - **P0.x** (probe/de-risk) → `docs/tier1-probe.md` (sub-probes, PASS/CONCERN/KILL thresholds)
    + `DESIGN.md` §11 (the A1–A4 assumption map).
  - **P1.x** (ontology/grammar/decoder) → `docs/ontology.md` (the load-bearing spec; §3 for the
    grammar, §4 for how the decoder uses λ) + `DESIGN.md` §2.
  - **P2.x** (rig/ground truth) → `docs/workstreams.md` WS1.
  - **P3.x** (annotation) → `docs/workstreams.md` WS2.
  - **P4.x** (eval harness) → `docs/workstreams.md` WS3 + `docs/tier1-probe.md` (metrics).
  - **P5.x** (models) → `DESIGN.md` (model design; novelty budget) — and only after P0 verdicts.
  - **P6.x** (product) → `DESIGN.md` (product/views; event stream as the API atom).

Read the relevant sections — actually open them, don't recall from memory.

## Step 2 — Write the grounding brief (a few lines, shown to the user)

- **Task + DONE condition** — quote the backlog's `DONE =` clause verbatim.
- **Source sections** — which doc sections you read and the contract they impose (cite as
  `docs/ontology.md §3`, `DESIGN.md §11`, etc. — these are clickable).
- **Applicable cross-cutting invariants** — from `docs/backlog.md`'s invariants list, name the
  ones this task must honor (e.g. calibrated uncertainty, never-guess-occluded, honest
  degradation, event-stream-is-the-API, novelty-budget).
- **Open questions / risks** — anything underspecified that could drift from the design.

## Step 3 — Implement test-first

Per the repo working agreement (`CLAUDE.md`): minimal, atomic, one P-item.

1. Write the failing test that pins behavior to the spec section you cited.
2. Minimal code to pass.
3. Refactor with tests green.

Then run the definition-of-done loop: `uv run pytest -q`, `uv run ruff check src tests`,
`uv run ruff format --check src tests`, and tick the `docs/backlog.md` checkbox.

## Step 4 — Branch → commit → PR (one feature branch per P-item)

Every P-item gets its own branch, merged into `main` only via a PR the user confirms. This
gives the user a reviewable checkpoint at every feature boundary — never commit a P-item
straight to `main`.

1. **Branch at the START of the P-item** (before writing code), off an up-to-date `main`:
   `git switch -c p1.4-constrained-decoder` (name: lowercased P-id + short slug). If you only
   realize mid-work that you're on `main`, branch now — the commits move with you.
2. **Commit** on that branch when the definition-of-done loop is green. Minimal, atomic, one
   P-item per commit. **No `Co-Authored-By` trailer.** First line: `P1.4 <what>`.
3. **Push and open a PR** with `gh` once the user approves. PR body: the grounding brief
   (DONE condition + cited design sections + invariants honored) so the review carries the
   full background, plus the verification output (tests/lint/format). End the PR body with the
   `🤖 Generated with [Claude Code]` line.
4. **The user reviews and merges** — do not merge for them. After merge, `git switch main &&
   git pull` before the next P-item.
5. **Check in** after the P-item before starting the next.

Confirm before each outward step: branch and local commits are fine to make, but **pushing and
opening the PR wait for the user's go-ahead.**

## Note for spawned agents

If a subagent implements a P-item, it must run this same ritual — the grounding brief is
how an agent that started cold inherits the design intent instead of inventing it.
