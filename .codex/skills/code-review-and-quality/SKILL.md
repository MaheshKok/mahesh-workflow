---
name: code-review-and-quality
description: Review a provided diff, patch, PR, or bounded set of changed files for spec compliance, correctness, readability, architecture, security, performance, and missing tests. Return severity-labeled findings plus an approve or request-changes verdict. Do not use to implement fixes, refactor working code, generate documentation, plan work, or merely run tests.
---

# Code Review and Quality

Act as a review worker. Assess the supplied change and return findings; do not supervise other agents, implement fixes, or operate a write-review loop.

## Required Inputs

- The diff, patch, PR, or changed files under review.
- The intended behavior or task spec when compliance matters.
- Relevant tests and surrounding code when needed to verify a finding.

If the change is unavailable, return `blocked` and name the missing artifact. If a requirement cannot be verified from the supplied scope, say `cannot_verify`; do not guess or treat an absent artifact as evidence.

## Review Method

1. Establish the intended behavioral change and acceptance criteria.
2. Read tests before judging implementation details.
3. Review every changed path across five axes:
   - `correctness`: contract, edge cases, state, concurrency, errors, regression coverage.
   - `readability`: names, control flow, duplication, dead code, unnecessary concepts.
   - `architecture`: boundaries, dependency direction, project conventions, change size.
   - `security`: trust boundaries, authn/authz, injection, secrets, unsafe dependencies.
   - `performance`: N+1 access, unbounded work, blocking I/O, leaks, hot-path cost.
4. Verify each proposed finding against current code and relevant context.
5. Keep only actionable, high-conviction findings and order them by severity and leverage.

For a verified bug fix, a missing regression test is normally a `Required` finding. If the relevant test layer is unavailable or unsuitable, report that constraint explicitly rather than pretending the regression is covered.

For structural findings, specify the smallest concrete remedy: for example, collapse duplicate branches, introduce a named predicate or explicit type boundary, move feature logic to its owner, reuse an existing helper, or delete a pass-through wrapper. Reject a proposed refactor when it merely relocates the same concepts across files or adds indirection without reducing the reader's mental model.

Report orphaned or dead code only with direct evidence such as removed references, an unreachable path, or an unused symbol result. Otherwise label it `cannot_verify` and recommend confirmation before deletion.

Read the bundled references only when applicable:

- Security-sensitive changes: `references/security-checklist.md`.
- Performance-sensitive changes: `references/performance-checklist.md`.
- Python, Go, TypeScript/JavaScript, SQL, or React changes: `references/language-lenses.md`.

## Severity

- `Critical`: exploitable security issue, data loss, or broken required behavior.
- `Required`: correctness, architecture, or regression defect that must be fixed.
- `Nit`: non-blocking readability or style issue.
- `Optional`: useful improvement left to author judgment.
- `FYI`: context only; no action required.

Approve when the change improves code health and has no `Critical` or unresolved `Required` findings. Do not block on personal preference.

## Evidence Calibration

- `observed`: cite a changed line, executable behavior, test result, or confirmed call path.
- `inferred`: state the assumption and keep the severity proportional to it.
- `cannot_verify`: name the missing code, test, requirement, or runtime evidence; do not turn it into a speculative defect.

Use `evidence` to make the finding reproducible. A vague concern is not a finding.

## Output Contract

Return:

- `summary`: one sentence describing the reviewed change.
- `axis_coverage`: every axis set to `reviewed`, `not_applicable`, or `cannot_verify`, with a short reason for the latter two.
- `findings`: ordered items with `severity`, `axis`, `location`, `problem`, `fix`, and optional `evidence`.
- `spec_compliance`: `pass`, `fail`, or `not_provided`; when `fail`, list `missing`, `extra`, and `misunderstood` behavior.
- `assumptions`: facts inferred but not verified.
- `risks`: remaining uncertainty or untested behavior.
- `verdict`: `approve`, `request_changes`, or `blocked`, with one-line rationale.
- `next_action`: the smallest evidence-gathering or author action, or `none`.

If no actionable findings survive verification, return an empty `findings` list and `approve`. Never manufacture findings for completeness. For `blocked`, still return all five `axis_coverage` entries as `cannot_verify` unless an axis was genuinely not applicable.
