---
name: subagent-prechallenged-tdd-workflow
description: Use when executing an implementation plan that ALREADY survived adversarial review (claudex-grill / claudex-review sign-off, a PLAN-REVIEW-LOG verdict, or the user states the plan is pre-challenged) in the current Codex session; coordinates isolated subagent implementation and root correction/review gates without re-running the plan challenge ("codex subagent without challenge"). Do not use for draft or unchallenged plans (use subagent-tdd-workflow), trivial edits, read-only answers, or research-only requests.
---

# Codex Subagent-Driven Development — Pre-Challenged Plan Variant

Local Codex supervisor inspired by Superpowers. Keep the upstream Superpowers checkout unchanged. Identical to `subagent-tdd-workflow` except stage 1: the plan challenge is replaced by a provenance gate, because the plan already survived adversarial review upstream.

## Contract

- Every plan enters execution with PROVEN prior adversarial review (provenance gate below); an unchanged approved plan is never re-challenged.
- Every non-trivial planned implementation delegates at least one bounded implementation task.
- Root owns the plan, synthesis, integration, and final acceptance.
- Trivial edits and non-implementation answers are exempt.

Non-trivial means the implementation changes production behavior, has multiple dependent steps, or carries meaningful regression risk.

For every smallest executable-behavior slice in an approved non-trivial implementation plan, use this sequence regardless of writer: Fable Gates 1–3; capture a non-destructive pre-edit baseline (relevant file state and pre-existing check results, not a clean worktree); map criteria to public-behavior tests; run focused RED that fails for the intended reason; make the minimum GREEN change; refactor only for a concrete issue and rerun focused checks; repeat per slice; run broader relevant checks; writer Gate 4 self-verification; independent Gate 4 acceptance; Gate 5 calibrated report. Existing failures alone are not RED: record exact command, intended failure, observed failure, and chronology before production implementation. Never destructively revert a dirty or shared worktree; use a safe pre-change reference or worktree when available.

Policy, docs, configuration, research, architecture, review, verification, and repair lanes skip TDD only if they do not change executable behavior; use the smallest sufficient evidence. Behavior-changing configuration follows the sequence above.

Narrow recorded exceptions require fallback evidence:

- No test seam: characterize current behavior, introduce the seam under preservation evidence, then resume RED.
- Pure behavior-preserving refactor with adequate tests: record GREEN characterization before and after; do not fabricate RED.
- Emergency implementation-first: only with explicit user authorization; add the regression test immediately and label it a non-TDD fallback.

Root-as-writer follows the same sequence. Root cannot independently verify itself: dispatch a fresh read-only verifier for independent Gate 4 evidence, while root remains the acceptance decision-maker. For a qualifying bounded, settled, test-first executable-behavior slice, Luna is the writer: use `max` where the dispatch path accepts an explicit effort, otherwise use its role-fixed `xhigh` path and report the effective setting. Root supplies scope, criteria, and Gates 1–3; Luna runs compact RED/GREEN plus deterministic self-checks and stops on ambiguity. If Luna cannot be resolved, stop and report the environment fault; do not substitute Terra or another tier.

## Delegated writer mode

Activate this mode only when the **first work-order message** begins at its first byte with this exact standalone first line:

`EXECUTION_MODE: delegated-writer-v1`

The line must have no prefix, indentation, quoting, list marker, code-fence context, or trailing content. Any occurrence after the first line, in a later message, or inside a quote, example, or code fence does not activate this mode. A malformed or missing first line also does not activate it. In all such cases, follow the normal contract and full workflow unchanged.

When activated, this session is already the bounded delegated writer. Do not recursively run the root plan challenge, invoke another Codex recursively, or dispatch/delegate a subagent. Treat the approved plan as frozen: do not redesign it, broaden its scope, or substitute a new plan. The writer must still capture a non-destructive baseline; map criteria to public-behavior tests; run an authentic focused RED that fails for the intended reason; make the minimum GREEN change; refactor only to address a concrete issue and rerun focused checks; complete writer Gate 4 self-verification; report calibrated evidence; and record any applicable exception with its fallback evidence.

In this mode, do not run an independent verifier or acceptance gate, broad proof unless the work order explicitly assigns it, commit, or claim outer-orchestrator acceptance. The outer orchestrator owns the planning challenge, independent Gate 4, broader proof, final acceptance, Gate 5, and commit. Use the required subagent report schema below for the writer handoff with these delegated-mode overrides: `Fable/baseline` records the delegated receipt and captured baseline without rerunning Gates 1–3; `Tests/checks` reports focused checks only unless the work order explicitly assigns a broader command.

## 1. Provenance gate (replaces the plan challenge)

Skipping the challenger is earned by evidence, never assumed:

1. The plan is frozen text on disk (`PLAN.md` or a named plan file), AND
2. at least one of:
   - an adversarial review record covering THIS plan version — e.g. `PLAN-REVIEW-LOG.md` with a `VERDICT: APPROVED` / grill sign-off. Confirm the record matches the current plan bytes (phase headings and dates line up; the log's last reviewed revision is the plan as it stands now), not merely that the file exists;
   - the user's invocation explicitly states the plan is already challenged.
3. Echo one line at kickoff and record it in the session report:
   `CHALLENGE SKIPPED — provenance: <log file + verdict line | user assertion>`

Provenance absent or stale (plan edited after the recorded review, log referencing different phases) → do NOT proceed challenge-free: run the fallback challenge below for the whole plan. **An edited plan is an unchallenged plan.**

No per-phase re-challenge: one plan-level provenance check at kickoff covers every phase of that frozen plan. (Measured: per-phase challenge lanes on an already-grilled plan spent an extra subagent plus a serial stage per phase re-reviewing text that had already survived six adversarial rounds.)

**Scope drift re-arms the challenge.** The pre-challenge covers only what was reviewed. If implementation forces a material plan change — new steps, changed interfaces, dropped constraints; not typo-level corrections — the changed slice is unchallenged: run the fallback challenge for THAT slice only, before implementing it, and log `RE-CHALLENGED: <slice>`. Everything untouched by the change keeps its provenance.

**Fallback challenge lane** (used only when provenance fails or scope drifts): dispatch a fresh planning subagent with the complete draft plan (or changed slice) and relevant project context.

- Apply Fable: define done, identify load-bearing unknowns, inspect evidence, attack assumptions, and name verification.
- Do not edit files.
- Skip TDD; this lane returns `verdict`, `gaps`, `risks`, `acceptance_checks`, and `recommended_changes`.
- Root reviews the evidence and corrects the plan before execution.

## 2. Select and dispatch

Use the active global `AGENTS.md` as the only model and effort selection source. Use isolated context when overriding model or effort: `fork_turns="none"`. Every non-trivial planned implementation delegates at least one bounded implementation task; root may write remaining slices. For delegated slices, use one fresh implementation subagent per independent delegated task, sequentially unless file ownership is isolated. Every dispatch prompt includes:

- exact model, effort, role/duties, and gate state;
- full task text, definition of done, working directory, allowed file scope, architecture/dependencies, and constraints/non-goals;
- baseline, criteria/test map, commands, acceptance checks, and required report schema.

## Waiting on subagents (binding)

Every `wait_agent` timeout is a paid root turn at full context; waits are budgeted, not free.

- **Wait ladder:** first `wait_agent` on a task at `timeout_ms=60000`; still running → 120000; thereafter 300000 or the tool's maximum (probe the ceiling once and reuse it). Never sit below 60000 after the first wait. Target: **fewer than 10 wait-turns per subagent.** Measured on a real run: 156 `wait_agent` calls at 30–60 s timeouts averaged 46-char "still running" returns and burned ~21M input tokens — 41% of the orchestrator's entire spend.
- **No consecutive empty waits.** A timed-out wait that returned nothing new is followed by queued useful work — draft the next slice's work order, update the log, prepare the acceptance checklist, run a read-only lane — or by a strictly longer wait. Two empty waits back-to-back with nothing between them is the red-flag pattern.
- **`list_agents` only when the roster changes** (immediately after a spawn or termination), never as a status check — `wait_agent`, `send_message`, and `followup_task` already address tasks by name. Measured: 25 roster calls in one run, ~16 pure repeats.
- **Root effort:** run the orchestrator at `high`; escalate a single turn to `xhigh` only for an acceptance decision or a plan correction, within the active `AGENTS.md` ladder. Poll, routing, and dispatch turns never need it.
- **Handoff into the session is a pointer, not a payload:** the log/plan file paths plus a ≤15-line state table. A 28.6K-char inline handoff helped compact a real orchestrator 15 minutes into its run.
- **Read-only lanes may overlap:** the verifier lane can run while the next slice's work order is drafted — single-writer applies to writers only.

## 3. Required subagent report

Return:

- `Status`: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`
- `Summary`
- `Files changed`
- `Classification/exception`: executable or non-executable; any exception and fallback evidence
- `Fable/baseline`: Gates 1–3 state, captured pre-edit state, and pre-existing check results
- `Criteria/test map`
- `RED/GREEN`: exact commands and intended/observed results, or explicit not-applicable reason
- `Gate 4 self-verification`: claim-layer evidence
- `Tests/checks`: broader commands and exact results
- `Assumptions`
- `Risks`
- `Next action`

Never hide uncertainty. `NEEDS_CONTEXT` requests missing facts. `BLOCKED` names the failed assumption or obstacle.

## 4. Root acceptance gate

For every subagent result, root must:

1. Inspect the diff and the verifier-flagged locations; never trust the report alone. Root SAMPLES where stakes concentrate — the spec-fidelity core, flagged lines, high-risk domains — it does not breadth-read whole files the verifier lane already covered (measured: ~640K chars of root breadth-reads forced two compactions in one run; breadth is the verifier's job, judgment is root's).
2. Check literal spec compliance first: missing, extra, or misunderstood behavior.
3. Re-run or independently verify tests and evidence.
4. Review correctness, security, performance, maintainability, and missing tests.
5. Send actionable findings back to the implementer.
6. Re-review the corrected diff and evidence until accepted.

Do not mark a task complete with open spec or important quality findings. Escalate to the user when the plan is wrong, authority must expand, or a high-risk issue remains unresolved.

## Red flags

- Full-history fork used while requesting a model or effort override.
- Multiple writers touching overlapping files.
- Implementation before a failing check when executable behavior changed.
- Root accepts a summary without reading the diff.
- Quality review starts before spec compliance passes.
- Correction accepted without re-review.
- Consecutive empty `wait_agent` timeouts with no work between them, or more than ~10 wait-turns on one subagent.
- Root breadth-reading files the verifier lane already covered instead of sampling the diff and flagged locations.
- `list_agents` used as a status poll.
- Challenge skipped without the `CHALLENGE SKIPPED — provenance:` echo, or provenance claimed from a log that does not match the current plan bytes.
- Plan edited after the recorded review (or scope drifted mid-build) and executed without the fallback challenge on the changed part.
