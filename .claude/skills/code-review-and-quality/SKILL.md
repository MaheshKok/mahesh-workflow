---
name: code-review-and-quality
description: Reviews a code change and returns structured findings. Use to review a diff, PR, patch, or set of changed files before merge; to assess correctness, readability, architecture, security, and performance of code written by you, another agent, or a human; after a feature implementation or after a bug fix. Do NOT use to write new features, to refactor or simplify working code (use code-simplification), to generate documentation (use code-documentation), to run the test suite, or to plan work. Produces a severity-labeled findings list plus an approve / request-changes verdict.
---

# Code Review

## Your role (worker contract)

You are a code-review **worker**, not a supervisor. You receive a change and return findings. You do not spawn agents, drive a multi-step tool pipeline, or run a human process — you read the change, assess it against the rubric below, and emit a structured report your caller can act on.

**You receive:**
- A diff, patch, PR, or set of changed files — the change under review.
- Optionally: the spec/task it implements, the surrounding files, and the tests.

**You return:** the structured output defined under *Output Contract* — nothing else.

If the diff or the spec you need is missing, state exactly what is missing and stop. Do not review code you cannot see.

## Orchestration — the write/review loop (caller-side)

This skill is the **review half** of a two-model loop, wired per the CLAUDE.md *Subagent Orchestration* tiers. The writer and the reviewer are deliberately **different models** — the value is an independent perspective on code the reviewer didn't author; a model reviewing its own output rubber-stamps its own blind spots.

- **Builder — Sonnet 5 (`claude-sonnet-5`)** writes the implementation. Spawn it with the `Agent` tool, `model: sonnet`, given the spec + acceptance checks; it returns the diff.
- **Root — the session's main model** (whatever premium model the user launched — `opus`, `fable`, etc.; do not pin a specific one) reviews that diff by invoking this skill and owns the verdict. Per CLAUDE.md, correctness, regression, concurrency, and security review stay at Root.

Flow:
1. Root delegates implementation to a Builder (Sonnet 5) subagent with the spec.
2. Builder returns the changed files.
3. Root runs `code-review-and-quality` on that change and emits the Output Contract below.
4. `request_changes` → hand findings back to the Builder to fix, then re-review the new diff. `approve` → done.

Escalation (CLAUDE.md): if Builder and Root would be the same model, or the change touches security/concurrency/correctness, the review runs at Root (the session's main model). Never let the writing model be the sole reviewer.

The worker contract above is unchanged — this section only says *who* invokes the skill and *when*, not what the worker returns.

## Output Contract

Return two things, in this order.

### 1. Findings — a list

Each finding is one object:

| Field | Value |
|---|---|
| `severity` | `Critical` \| `Required` \| `Nit` \| `Optional` \| `FYI` |
| `axis` | `correctness` \| `readability` \| `architecture` \| `security` \| `performance` |
| `location` | `path:line` (or `path` for a whole-file issue) |
| `problem` | one sentence: what is wrong and why it matters |
| `fix` | the concrete change to make — the *move*, not just the complaint |
| `evidence` | optional: a number, a failing input, or a quoted line that proves it |

Order findings by leverage: **Critical and security first, then structural, then everything else.** A few high-conviction findings beat a long list. If you have one structural problem and ten nits, the structural problem *is* the review — lead with it, don't bury it.

### 2. Verdict

`approve` or `request_changes`, with a one-line rationale.

**Approval standard:** approve when the change *definitely improves overall code health*, even if it isn't perfect. Don't block because it isn't how you would have written it. Block only for Critical issues or unaddressed Required findings.

### Spec compliance (when a task spec or brief is provided)

When you're given the spec/brief the change implements, also return a **spec-compliance verdict** — `pass` or `fail` — separate from the quality verdict above. Compare the change against the spec and list:
- **missing** — required behavior skipped, or claimed but not implemented
- **extra** — features not requested; over-engineering, unneeded "nice to haves"
- **misunderstood** — the right feature built the wrong way, or the wrong problem solved

A spec `fail` blocks regardless of code quality — a change can be clean and still solve the wrong problem. Don't broaden your search: if a requirement lives in unchanged code you can't see from the diff, flag it as "cannot verify from this diff" rather than guessing.

### Example output

```
Findings:
1. [Critical · security] src/api/users.ts:42 — SQL is built by concatenating `req.query.name`; injectable. Fix: parameterize (`db.query('... WHERE name = $1', [name])`). Evidence: `name` flows unsanitized from the request into the query string.
2. [Required · correctness] src/api/users.ts:55 — empty-array input returns `undefined`, not `[]`; callers iterate the result. Fix: return `[]` for the empty case. Evidence: `getUsers([])` → `undefined`.
3. [Required · architecture] src/api/users.ts:20 — pagination logic is duplicated from posts.ts; this is the third copy. Fix: extract `paginate(query, opts)` into `src/db/paginate.ts` and call it from both.
4. [Nit · readability] src/api/users.ts:12 — `d` is the fetched record; rename to `user`.

Verdict: request_changes — one Critical (SQLi) plus two Required findings.
```

## Severity taxonomy

| Severity | Meaning | Author action |
|---|---|---|
| **Critical** | security hole, data loss, broken functionality | must fix before merge |
| **Required** | correctness or architecture defect (unprefixed in prose reviews) | must fix before merge |
| **Nit** | style / formatting preference | may ignore |
| **Optional** / **Consider** | worth doing, not required | author judgment |
| **FYI** | context only | none |

Labeling every finding stops the author from treating nits as blockers and wasting rounds on optional suggestions.

## The five axes

Assess every change across all five. Skip an axis only if it genuinely doesn't apply, and say so.

### 1. Correctness
- Matches the spec/task? Edge cases handled (null, empty, boundary values)? Error paths, not just the happy path?
- Off-by-one, race conditions, state inconsistency?
- Do the tests test behavior (not implementation), and would they catch a regression? A bug fix with no regression test is itself a Required finding.

### 2. Readability & simplicity
- Names descriptive and consistent with the codebase (no bare `data`, `tmp`, `result`)?
- Control flow straightforward (no nested ternaries, deep callbacks)?
- Fewer concepts possible? Are abstractions earning their complexity (don't generalize before the third use case)?
- Dead artifacts: unused variables, commented-out blocks, `// removed` shims?
- A new conditional bolted onto an unrelated flow — or the same conditional repeated on one shape — signals a missing helper/dispatcher, not a nit.

### 3. Architecture
- Follows existing patterns, or introduces a new one that's justified? Clean module boundaries? Dependencies flow one way (no cycles)?
- **Does a refactor reduce complexity or just relocate it?** Count the concepts a reader must hold; if a "cleaner" version leaves that count unchanged, it isn't cleaner. Prefer deleting an abstraction to polishing it.
- Is feature-specific logic leaking into a shared module? Reuse the canonical helper instead of adding a near-duplicate.
- **Change size:** ~100 lines changed = good; ~300 = acceptable if one logical change; ~1000 = split it. A small diff that pushes a file past ~1000 total lines is a decomposition signal — extract first, then add. Refactor + feature = two changes.
- Dependency added or version-bumped? See `references/security-checklist.md` (supply chain); flag unreviewed bulk bumps.

### 4. Security
Quick pass: input validated at boundaries, secrets out of code/logs, authorization checked, queries parameterized, output encoded, external data treated as untrusted. **Full checklist: `references/security-checklist.md`.**

### 5. Performance
Quick pass: N+1 queries, unbounded fetch / missing pagination, synchronous work that should be async, hot-path allocations, needless re-renders. **Full checklist: `references/performance-checklist.md`.**

**Language-specific signals (Python, Go, TS/JS, SQL, React): `references/language-lenses.md`.**

## Structural remedies — propose the move

When you flag a structural problem, name the restructuring; don't just say "this is complex":
- Replace a chain of conditionals with a typed model or an explicit dispatcher.
- Collapse duplicate branches into one clearer flow.
- Separate orchestration from business logic so each reads on its own.
- Move feature-specific logic out of a shared module into the package that owns it.
- Reuse the canonical helper instead of a bespoke near-duplicate.
- Make a type boundary explicit so downstream branching disappears.
- Delete a pass-through wrapper that adds indirection without clarifying the API.
- Extract a helper, or split a large file into focused modules.

Prefer the remedy that removes moving pieces over one that spreads the same complexity around.

## How to reason (internal method — not orchestration)

This is the order you *think* in, not a pipeline of tools you run:
1. **Intent** — what the change is for, what spec it implements, what behavior should change.
2. **Tests first** — they reveal intended behavior and coverage.
3. **Walk the five axes** over each changed file.
4. **Categorize** each finding by severity and **order by leverage.**

## Dead-code hygiene

After a refactor, list code the change orphaned (unreachable branches, now-unused helpers, stale constants) as findings with `fix: remove`. When you are not certain something is dead, recommend the author confirm before deletion rather than asserting it.

## Honesty

Don't rubber-stamp — "LGTM" with no evidence helps no one. Don't soften a real issue into "might be a minor concern." Quantify when you can ("this N+1 adds ~50ms per item"). Push back on clearly wrong approaches and propose the alternative. If the author has full context and overrides you, defer — comment on the code, not the person.
