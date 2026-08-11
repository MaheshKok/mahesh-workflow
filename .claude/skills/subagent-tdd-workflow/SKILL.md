---
name: subagent-tdd-workflow
description: Structure implementation as the CLAUDE.md Root/Builder/Worker subagent loop. Use when starting to build a feature, a multi-file change, or any non-trivial implementation — Root (the session model) owns spec, review, and integration; a Builder (Sonnet) writes to spec under `tdd-cycle`'s Red-Green-Refactor discipline; Haiku Workers fan out on mechanical lanes. Do NOT use to review an existing diff (use code-review-and-quality), for the bare test-first cycle with no delegation (use tdd-cycle directly), for trivial one-line edits, pure research, or to write documentation. Loads when starting a feature.
---

# Subagent TDD Workflow — the build/review loop

Give implementation the structure `code-review-and-quality` applies after the fact: **Root owns, a Builder writes, Workers fan out.** Tier definitions and the escalation ladder live in CLAUDE.md → *Subagent Orchestration*; this skill is only the operational loop.

## The loop

1. **Scope (Root).** Own the spec: what "done" means, the acceptance checks, the load-bearing unknowns. Hard or uncertain → run `fable-method` first. Never delegate a spec you can't yet state.
2. **Fan out mechanical prep (Root → Workers).** Before and alongside the build, spawn **Haiku Workers** (`model: haiku`) on the separable, verifiable, judgment-free lanes: file/usage inventories, "find the test command + the existing patterns to match", cross-file repetitive edits, boilerplate-test scaffolds, dead-code/TODO sweeps. One small self-contained mission each; launch independent Workers in a SINGLE message so they run in parallel. A Worker that hits real judgment stops and escalates to a Builder — it does not guess. Skip this step when no mechanical lane exists.
3. **Delegate the build (Root → Builder).** Spawn a **Builder — Sonnet (`model: sonnet`)** with the spec, acceptance checks, in-scope files, and whatever the Workers gathered. One primary writer per module; `isolation: worktree` when Builders or Workers write in parallel. Tell it to invoke `tdd-cycle` for the build itself, and `fable-method` when its lane is hard.
4. **Build (Builder).** Runs `tdd-cycle` — RED (a test written from the spec's behavior, failing for the expected reason) → GREEN (least code that passes) → REFACTOR (green throughout). Returns the diff **and** the RED/GREEN evidence: the failing output before, the passing output after.
5. **Review (Root).** Review the diff with `code-review-and-quality`, and check the RED evidence against `tdd-cycle`'s anti-patterns — the test must have failed for the right reason, no test edited to go green, REFACTOR not skipped. A Builder that returns only a passing suite has not shown RED; send it back. `request_changes` → findings back to the Builder → re-review the new diff. `approve` → continue. Never delegate the review.
6. **Verify + integrate (Root).** Final edits, cross-cutting synthesis, verification against the Gate-1 spec. Correctness, regression, concurrency, and security review stay at Root. A Worker may run the mechanical checks (lint, "diff touches only in-scope files", grep for stray debug) — but Root judges the result.
7. **Compact (Root).** Phase done, verified, integrated → run `/compact` before starting the next phase's loop. Proactive, not a wait-for-autocompact — cheaper than an uncontrolled mid-phase compaction. Skip only on the final phase of the session (nothing left to save for).

## Delegate, or write it directly?

Two gates: **are there ≥2 lanes with no cross-dependency?** and **does an independent perspective cut a real blind spot?** Neither → Root writes it. Blanket-delegating every edit burns coordination and loses context — spawn by tier, not reflexively.

Route by the nature of the lane: mechanical + auto-verifiable → **Worker (haiku)**; separable implementation or context-heavy exploration → **Builder (sonnet)**; judgment, synthesis, security/correctness/concurrency → **Root**. A lane that outgrows its tier escalates one rung (`haiku → sonnet → root`).

## Not this skill

- Reviewing an existing diff → `code-review-and-quality`.
- The Red-Green-Refactor cycle itself, its gates and coverage thresholds → `tdd-cycle`. This skill delegates to it and never restates it; if the two ever disagree, `tdd-cycle` wins.
- Test-first with no delegation (one lane, Root writes it) → `tdd-cycle` directly.
- Trivial edits, pure research, documentation → do it directly / use the right skill.
- Deterministic write-then-review that must not depend on Root's adherence → the `build-review` Workflow (stage 1 Sonnet builds test-first, stage 2 Root reviews, loops findings). This skill is the manual protocol; that Workflow is the harness.
