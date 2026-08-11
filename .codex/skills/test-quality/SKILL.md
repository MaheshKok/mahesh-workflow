---
name: test-quality
description: Use when designing, writing, or reviewing tests from a behavioral contract across languages, especially for adversarial edge cases, failure paths, mutation resistance, and mock boundaries. Do not use for implementation-only work, coverage reporting alone, or merely running an unchanged test suite.
---

# Test Quality

Produce tests that can expose plausible defects. Treat coverage as a diagnostic signal, not the objective.

## Required Inputs

- The behavior to protect: specification, public contract, bug report, or acceptance criteria.
- The test surface and available test framework.
- Relevant external boundaries and stateful dependencies.

If the intended behavior is missing and cannot be inferred from callers or public interfaces, return `blocked` with the smallest question needed to establish it.

## Workflow

1. Restate the behavioral contract and list assumptions separately.
2. Map each important requirement or regression to at least one test that would fail if that behavior broke.
3. Select the smallest useful mix: contract or integration tests for main flows, unit tests for real branching logic, and one regression test per verified bug.
4. Probe applicable adversarial cases: empty and boundary values, missing fields, malformed types, ordering and repeated calls, concurrency, dependency failures, cleanup, and partial state changes.
5. Keep expectations independent of the implementation. Reading implementation is allowed for diagnosis and coverage gaps, but do not reproduce its algorithm in assertions.
6. Mock only boundaries where real execution is impractical or unsafe. Prefer realistic database and filesystem behavior when the test tier permits it.
7. Apply a mutation check: identify a plausible operator, branch, early-return, or off-by-one mutation and confirm a test would fail.
8. Run the narrowest relevant tests first, then broader checks when shared behavior is affected.

## Quality Rules

- A passing test must distinguish correct behavior from at least one plausible wrong behavior.
- Include success, rejection, and recovery paths when the contract has them.
- Avoid snapshots that merely record current output; assert the meaningful contract.
- Keep tests independent and order-insensitive; avoid shared mutable state.
- Name tests by scenario and expected result.
- Do not test framework, language, or standard-library behavior.
- Do not add cases solely to raise a coverage percentage.

## Output Contract

Return:

- `summary`: the behavior protected.
- `tests`: each scenario, expected result, and defect it would catch.
- `assumptions`: contract interpretations not directly verified.
- `risks`: meaningful gaps, unavailable environments, or over-mocked boundaries.
- `verification`: commands run and observed results, or `not_run` with the reason.
- `next_action`: the smallest remaining action, or `none`.
