---
name: fix-findings
description: Triage and fix pasted review findings from another reviewer (Codex, CodeRabbit, another LLM, a human). Use when the user pastes P1/P2 findings, "codex finding", "fix these review done by another llm", or review comments. Verifies each finding against current code before touching anything.
---

# External Findings Triage

The user pastes findings from an outside reviewer. Findings may be stale,
wrong, or already fixed. Never fix blind.

## Procedure

1. Parse the pasted text into discrete findings. Number them.
2. For EACH finding, verify against the current code first:
   - Still valid -> fix it, minimal diff, no drive-by refactoring.
   - Already fixed / stale -> skip, one-line reason with file:line evidence.
   - Reviewer is wrong -> skip, one-line rebuttal with evidence.
3. Never bypass a check to satisfy a finding: no disabling lint rules, no
   deleting tests, no loosening types. Fix the cause (the user has explicitly
   rejected rule-disabling before).
4. After fixes: run the repo gate (`make qa` or equivalent). All green before
   reporting.
5. Report as a table: finding, verdict (fixed / skipped-stale / rejected),
   evidence file:line.
6. Commit only if the user asked. Conventional format, no AI attribution.

## Rules

- Minimal changes. The findings define the scope; nothing else moves.
- If a P1 finding reveals a deeper bug, fix the bug (correct fix over quick
  fix) and say so explicitly — do not silently expand scope.
- If two findings conflict, surface the conflict and ask instead of guessing.
