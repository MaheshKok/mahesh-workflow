# Simplification Signals

Use this reference when a proposal needs concrete evidence of complexity or a guard against cosmetic cleanup. A signal starts investigation; it is not proof that a change is safe.

## Signals

| Area | Signal | Proposal direction |
| --- | --- | --- |
| Structure | Three or more nested decisions or mixed parsing, policy, and I/O | Guard clause, named phase, or focused helper only if it names a real responsibility. |
| Structure | Same branch shape repeated for the same domain case | Consolidate under the existing owner or a named predicate. |
| Structure | Pass-through wrapper adds no policy, translation, or stable boundary | Remove it and call the underlying contract directly. |
| Naming | Generic or misleading name hides a mutation, unit, or ownership | Rename to the domain action or value while preserving public compatibility. |
| Redundancy | Repeated validation, conversion, or error mapping drifts across paths | Reuse the canonical helper or extract one only when the shared contract is real. |
| Hygiene | Unused import, unreachable branch, stale comment, or removed call site | Propose removal only after direct reference and reachability evidence. |

## Anti-rationalizations

- Fewer lines is not simpler when it hides ordering, error handling, or domain meaning.
- A type assertion, utility, factory, or configuration object is not justified by a possible future use.
- Matching personal style is churn unless it aligns with project conventions or clarifies behavior.
- Passing tests alone does not prove a change preserves a missing edge case; use callers, contract, and relevant test cases.
- Existing code may be deliberate. Check compatibility, performance, ordering, and historical context before removing its fence.

## Red Flags

- Replacing explicit errors with a fallback value.
- Changing evaluation order, mutation timing, cleanup, retries, or logging during a readability change.
- Combining independent concepts into one helper to reduce file count.
- Moving branching to a different module and calling the result simpler.
- Editing tests only to match a changed behavior rather than proving the original contract.
- Broad cleanup outside the supplied scope.

## Proposal Verification

For each proposal, identify the invariant, evidence source, smallest behavioral check, and rollback point. Verify normal, boundary, error, and ordering cases when relevant. If a claim cannot be established, use `cannot_verify` or leave the code unchanged.
