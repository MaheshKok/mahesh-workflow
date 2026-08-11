---
name: tdd-cycle
description: Enforce strict test-first Red-Green-Refactor discipline with per-phase gates, coverage thresholds, and refactoring triggers. Use when implementing a feature, fixing a bug, or refactoring under TDD — one failing test at a time (incremental) or a full failing suite for a unit (suite mode). Do NOT use to review an existing diff (use code-review-and-quality), to run an already-written suite, or for throwaway spikes. The canonical cycle the tdd-guide agent and the build-review workflow follow.
---

# TDD Cycle — Red · Green · Refactor

Tests are the specification. No production code is written before a test that fails for the right reason. Each phase has a **gate**: you may not enter the next phase until the current gate passes.

## The cycle

### RED — write a failing test
Write the test from the spec's *behavior*, not from the implementation you have in mind. Run it. Confirm it fails, and that it fails for the **expected reason** (missing implementation) — not a typo, import error, or wrong assertion.

- **Gate:** the test fails with a meaningful, expected message. No production code yet. Nothing passes accidentally.

### GREEN — minimal code to pass
Write the least code that turns the test green. No extra features, no speculative generality, no optimization.

- **Gate:** all tests pass. No code beyond what a test demands. No test was edited to make it pass.

### REFACTOR — improve while green
Remove duplication, sharpen names, simplify control flow. Re-run tests after each change; they stay green throughout. Refactoring is **not optional** — a passing test with ugly code is a half-done cycle.

- **Gate:** all tests still pass; complexity and duplication reduced; coverage unchanged or better.

## Thresholds

- Line coverage ≥ 80%, branch coverage ≥ 75%, critical-path coverage = 100%.
- A bug fix ships with a regression test that fails before the fix and passes after.

## Refactoring triggers

Refactor when any holds — during the REFACTOR phase, tests green:

- Cyclomatic complexity > 10
- Function longer than ~20 lines, or file past the project's size norm
- The same code block duplicated 3+ times

## Two modes

- **Incremental** (default): one failing test → make only it pass → refactor → repeat. Best for unclear designs and non-trivial logic — if a test is hard to write, the design needs work.
- **Suite**: write all failing tests for a unit/feature first → implement to pass them all → refactor the unit → broaden to integration tests. Best when the contract is well understood up front.

Broaden coverage the same way you started: write the new (integration/edge/perf) test failing first, then satisfy it.

## Anti-patterns — stop if you catch yourself

- Writing implementation before its test.
- Writing a test that already passes.
- Editing a test to make it go green.
- Skipping REFACTOR.
- Batching several features with no tests between them.
- Testing implementation details (internal state) instead of behavior.

## Failure recovery

If discipline breaks (code written test-last, a test edited to pass, a phase skipped):

1. **Stop** immediately.
2. Identify which gate was violated.
3. Roll back to the last green, in-discipline state.
4. Resume from the correct phase.

## How this skill is driven

- **Interactive** — the `tdd-guide` agent (or Root) follows this cycle directly, running the project's own test/coverage commands.
- **Deterministic multi-agent** — the `build-review` Workflow (`~/.claude/workflows/build-review.js`) hands a Builder this exact RED/GREEN/REFACTOR contract, then a reviewer checks the result. Use it when you want the loop enforced by the harness rather than by adherence.

This skill defines the *cycle discipline* only. Framework-specific test/mock/coverage commands live with the caller (e.g. the tdd-guide agent's `npm test` / `npm run test:coverage`), not here.
