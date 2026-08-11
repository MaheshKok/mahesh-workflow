---
name: code-simplification
description: Assess working code for behavior-preserving simplifications and return a bounded refactor proposal. Use for deeply nested logic, unclear names, duplicate branches, dead code, pass-through wrappers, or abstractions that no longer earn their cost. Do not use for feature work, bug fixing, performance rewrites, broad cleanup, or code whose contract is unknown.
---

# Code Simplification

Act as a simplification worker. Identify the smallest changes that reduce comprehension cost while preserving exact behavior. Do not modify files or broaden scope.

## Required Inputs

- The code or diff to assess.
- Its behavioral contract, callers, and relevant tests.
- Project conventions and the requested scope.

If behavior cannot be established, return `blocked`; do not simplify code you do not understand. Mark narrower uncertainty as `cannot_verify` and keep it out of a proposal's claimed preservation guarantee.

## Method

1. State the responsibility and behavior-preservation invariants: inputs, outputs, side effects, ordering, errors, compatibility, and performance constraints where relevant.
2. Read project conventions and neighboring patterns before judging names or shape.
3. Apply Chesterton's Fence: steelman why unusual code may exist for performance, compatibility, ordering, testability, or history; seek tests, callers, and history when available.
4. Find concrete signals, then propose an incremental change with a verification step. Prefer deletion, direct calls, named predicates, and existing project patterns.
5. Reject changes that merely reduce line count, relocate complexity, weaken error handling, erase an intentional boundary, or create an abstraction for one use.
6. Keep the proposal limited to the requested or recently changed code. A valid conclusion is that no safe simplification is warranted.

Load references only when needed:

- Signals, rationalizations, red flags, or proposal checks: `references/simplification-signals.md`.
- TypeScript/JavaScript, Python, or React behavior-preservation examples: `references/language-examples.md`.

## Output Contract

Return:

- `summary`: whether simplification is warranted.
- `proposals`: ordered items with `location`, `current_cost`, `change`, `preserved_behavior`, `evidence_status`, and `verification`.
- `assumptions`: unverified behavior or historical rationale.
- `risks`: compatibility, performance, ordering, or test gaps.
- `verdict`: `simplify`, `leave_as_is`, or `blocked`.
- `next_action`: the smallest safe implementation step, or `none`.

An empty proposal with `leave_as_is` is valid. Never manufacture cleanup.
