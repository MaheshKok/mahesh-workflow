---
name: subagent-tdd-workflow
description: Use when executing an approved non-trivial implementation plan. The authoritative task-level TDD procedure — slice sequence, recorded exceptions, Luna limits, writer Gate 4, independent Gate 4 acceptance. Root owns, one writer writes, Luna workers fan out in parallel on disjoint mechanical lanes, and every phase ends in a commit plus a context reset.
---

# Codex Subagent-Driven Development

Referenced by `AGENTS.md` → *Subagents*. This file is the procedure that reference promises.

**The shape:** Root owns, one Writer writes, Workers fan out. Root never delegates the spec, the verdict, or acceptance.

## Roles

| Lane | Model | Owns |
|---|---|---|
| **Root** | `gpt-5.6-sol` `xhigh` | Spec, Gates 1–3 judgment, review, independent Gate 4 acceptance, integration, the commit |
| **Writer** | Luna at `xhigh` | One bounded slice of executable behavior, test-first, sequential and fresh |
| **Worker** | Luna — `agent_type="luna"`, `fork_turns="none"` | Mechanical, judgment-free, independently verifiable lanes, run in parallel |
| **Challenger** | Sol per risk | Attacks the plan's assumptions before approval; returns gaps, risks, acceptance checks, verdict |

**Luna is the implementor.** Writer and Worker are the same model under different lane
discipline — the Writer owns one executable-behavior slice sequentially; Workers run
mechanical lanes in parallel. There is no second builder tier and no silent fallback: if
Luna cannot be resolved, that is an environment fault to fix and report, not a reason to
build on something else. A slice that quietly ran on a different model produces a diff you
cannot compare against any other slice.

**`xhigh` on every dispatch path — the two now agree.** The role-fixed `agent_type="luna"`
is pinned by configuration to `xhigh` (`AGENTS.md:51`), and the CLI path takes it explicitly
— `codex exec -m gpt-5.6-luna -c model_reasoning_effort="xhigh"`. One effort, so a slice is
comparable across paths and the log never has to disclaim which route it got.

`max` costs roughly 4× the tokens and did not buy correctness. Measured on one campaign, two
`max` rounds, same repo and same reviewer: the round that spent **76% more reasoning turns
and 2.7× the transcript was the one rejected**, on 7 findings, five of them the same failure
— deleting the semantic distinction being measured instead of raising it above the floor.
Extra effort optimizes harder against the objective the prompt states; it does not repair a
mis-stated one. Spec quality and Root review moved outcomes; the tier did not. So `max` is
never a recovery move for a rejected slice — rewrite the spec's acceptance criteria and
forbidden patterns instead. Take `max` only on an explicit user instruction for that lane,
and say so in the dispatch line.

Verify the effective model and effort from runtime logs after any configuration or
Codex-version change — never call an inherited setting exact.

Everything else about model and effort selection is `AGENTS.md` → *Model and effort matrix*;
this file never restates it.

## The loop

1. **Scope (Root).** State what done means and the check that proves it. Name the 1–3 load-bearing unknowns. Hard or uncertain → run `fable-method` first. **Never delegate a spec you cannot state.**
2. **Fan out mechanical prep (Root → Workers).** Before and alongside the build, dispatch Luna workers on separable judgment-free lanes: file and usage inventories, "find the test command and the existing patterns to match", cross-file repetitive edits, evidence collation, deterministic test sharding, docs generated from supplied sources. **Dispatch all independent workers in ONE message so they run in parallel.** Skip this step when no mechanical lane exists.
3. **Delegate the slice (Root → Writer).** One Writer, one bounded slice, with the spec, acceptance checks, in-scope files, working directory, output contract, and whatever the Workers gathered. One primary writer per module. Writers are sequential and fresh — never two alive at once, never overlapping files.
4. **Build (Writer).** Task-level TDD on the slice sequence below. Returns the diff **and** the RED/GREEN evidence — the failing output before, the passing output after.
5. **Review (Root).** Spec compliance FIRST, then code quality — never the reverse. Read the actual diff; the report is a claim, not evidence. Check the RED evidence for the anti-patterns: did the test fail for the *expected* reason, was any test edited to go green, was REFACTOR skipped. A writer that returns only a passing suite has not shown RED — send it back. Findings → same lane fixes → re-review. **Never delegate the review.**
6. **Verify and integrate (Root).** Independent Gate 4 acceptance, cross-cutting synthesis, final edits, then the phase commit. Correctness, regression, concurrency, and security review stay at Root. Workers still fan out here: dispatch them in parallel on the mechanical checks — lint, type-check, "the diff touches only in-scope files", a grep for stray debug output — but **Root judges every result**. A worker reports what the command printed; it never decides whether that is acceptable.

## Worker fan-out — the parallel lane

Workers are the only lane that runs in parallel, and only because they are not implementation writers.

- **Disjoint files, always.** Two workers never touch the same file. Overlapping file sets is a scoping error — fix the split, do not serialize around it.
- **One small self-contained mission each.** Give the bounded task, not the task history. A worker that needs the plan's reasoning is a Writer lane in disguise.
- **Judgment-free and auto-verifiable**, or it is not a Worker lane. If the acceptance check cannot be a command or an exact-match comparison, it belongs to a Writer.
- **A worker that hits real judgment STOPS and escalates.** It does not guess. Escalation is `BLOCKED` or `NEEDS_CONTEXT` with what it hit — never a plausible guess in the shape of a result.
- **Substantial enough to amortize startup.** A single command or a tiny lookup is Root's own work; spawning for it is pure overhead.
- This does not license parallel writers. `AGENTS.md:75` stands: no parallel implementation writers into overlapping files.

## Slice sequence (task-level TDD)

Every smallest slice of **executable behavior** runs this, regardless of writer — Root, Sol, or Luna:

1. **RED** — one test written from the spec's stated behavior, run, observed failing, and failing *for the expected reason*. A test that errors on a typo is not RED.
2. **GREEN** — the least code that passes it. Run it. Capture the output.
3. **REFACTOR** — clean up with the suite green throughout.

Slice at one behavior, not one file. If a slice cannot state its RED test, it is not yet specified — return to step 1 of the loop.

The RED and GREEN outputs are the deliverable alongside the diff. Absent evidence fails closed: no RED output means not accepted, never "the writer says it passed".

## Recorded exceptions

Task-level TDD is skipped only for these, and only with a one-line record in the phase log naming the substitute evidence:

| Exception | Substitute evidence |
|---|---|
| Non-executable policy, docs, comments | The rendered/read artifact itself |
| Pure mechanical transformation under a total gate (rename, import move) | The gate's clean run — compiler, type-check, or exact-match diff |
| Generated artifacts from a checked generator | The generator's own test plus a regenerate-and-diff |

**Behavior-changing configuration is NOT exempt** — a config value that changes what the system does is executable behavior. An unrecorded exception is a protocol violation, not a shortcut.

## Luna limits

Luna is the implementor, not the decider. It owns none of: planning, architecture, diagnosis, critical review, security judgment, final acceptance. Root supplies scope, criteria, Gates 1–3 judgment, and acceptance.

Luna owns **one settled executable-behavior slice** at a time, with compact RED/GREEN checks. *Settled* means no open design question remains — if the slice still needs a decision, it is not a Luna lane yet, it is Root's Gate 1 work. **Luna stops on ambiguity rather than guessing**, and a guess in the shape of a result is the failure this rule exists to prevent.

If Luna cannot be resolved, stop and report the environment fault. Do not substitute another tier.

## Gate 4 — twice, by two parties

- **Writer Gate 4:** the writer proves its own claim at the layer the claim lives on, before returning. "The tests pass" proves the tests pass; it does not prove the behavior changed. Return the exact command and the exact counts.
- **Independent Gate 4 acceptance (Root):** Root re-runs the proof itself and inspects the actual diff. **A writer's evidence is never acceptance.** Sample normal and edge cases. Root's own bytes are not self-certified either — a takeover diff written by Root gets an independent verifier lane.

Any mismatch between a lane's claim and the repo or log state halts the run and goes to the user. Never build the next slice over a mismatch.

## Per-phase discipline: commit, then reset

The spec, the phase log, and the committed tree ARE the state. Nothing load-bearing lives in session context.

- **Every phase ends in a commit.** Not a summary, not a "ready to commit" — the commit.
- **Compact at each phase boundary, after the commit.** `/compact` immediately following the phase commit, so the next phase starts near-empty and re-reads its state from disk. Do not carry a phase's diff, worker output, or review thread past its commit. Proactive, never a wait-for-autocompact — a controlled reset at a boundary you chose is cheaper and safer than an uncontrolled one firing mid-slice. Skip it on the session's final phase only: there is no next phase to save context for.
- **Compaction never halts the run.** Do not stop at a phase boundary because a compaction fired or is imminent — commit, compact, launch the next phase. Keep the log current at every commit (base ref, resolved tunables, one line per committed phase) so a compacted session continues from disk.
- **Do not stop between phases to ask whether to continue.** State the assumption and proceed. The run ends when every phase is committed, or on an explicit HALT with a reason.
- A decision the work order cannot answer is `HALT: needs-human — <the question>`, surfaced once, not a silent pause.

## Output contract (every lane)

`Status` — `DONE` | `DONE_WITH_CONCERNS` | `NEEDS_CONTEXT` | `BLOCKED` — plus summary, files changed, tests and checks with **exact** results, assumptions, risks, next action.

Root's handling: `DONE` → review. `DONE_WITH_CONCERNS` → read the concerns before reviewing; correctness or scope concerns get resolved first. `NEEDS_CONTEXT` → supply what was missing, re-dispatch. `BLOCKED` → diagnose the blocker: context problem → more context, same tier; needs more reasoning → one rung up; too large → split it; plan is wrong → escalate to the user. **Never re-dispatch the same lane unchanged.** If it said it was stuck, something has to change.

## Dispatch mechanics

Per `AGENTS.md`: post `Dispatching: <mission> (<exact model> - <effort>)` before every `spawn_agent`; `task_name` as `<mission>_<sanitized-model>_<effort>`, with `_role_fixed` appended for role-fixed agents; explicit `model` and `reasoning_effort`; `fork_turns="none"` for fresh isolated context. Never describe an inherited or unknown setting as exact.

## Not this skill

- Reviewing an existing diff → `code-review-and-quality`.
- The Red-Green-Refactor cycle's own gates and coverage thresholds → the TDD skill; this file delegates and never restates it. Disagreement → that one wins.
- One lane, no delegation → write it directly with task-level TDD.
- Trivial edits, pure research, documentation → do it directly.
- Plan hardening before approval → the challenger lane, before this skill starts.
