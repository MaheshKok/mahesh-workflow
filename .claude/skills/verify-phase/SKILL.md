---
name: verify-phase
description: Grill a phase implementation against its plan. Use when the user says "verify phase N", "i am done with phase N", "grill it", or after another LLM claims a phase is complete. Read-only, findings-first, ends with a done / not-done verdict.
---

# Phase Verifier

Adversarial review of a claimed phase implementation. You are trying to prove
the phase is NOT done; it earns "done" only by surviving that.

## Procedure

1. Read the plan section for the phase (usually `docs/plans/`). Extract every
   concrete requirement into a checklist: behaviors, files, tests, gates.
2. Verify each item against the CODE, not the plan's own claims and not the
   implementer's summary. Read the actual diffs (`git diff main...HEAD` or the
   phase's commits).
3. Run the gates for real: full test suite, type check, lint, coverage
   (`make qa` if the repo has it). Paste actual failures, never summaries of
   assumed success.
4. Check tests are real: spec-derived assertions, adversarial cases, not
   implementation mirrors. A phase with mirrored tests is NOT done.
5. Report findings in severity order, each anchored to file:line:

   [P1] <requirement violated> — <file:line> — <what is wrong>

6. End with exactly one verdict line:
   - `VERDICT: Phase N done.` — every requirement verified, gates green.
   - `VERDICT: Phase N NOT done.` — followed by the minimal list of what is
     missing.

## Rules

- Read-only. Do not fix anything, do not commit, do not touch the plan.
- Do not assume anything works without running it.
- If verdict is done and the user asked for it, hand off to /phase-prompt for
  the next phase.
