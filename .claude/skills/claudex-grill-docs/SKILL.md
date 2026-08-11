---
name: claudex-grill-docs
description: Claude×Codex collaboration — full plan-hardening lifecycle with living documentation. ACT 1 (you ↔ Claude) — Claude interviews you relentlessly about a plan, one question at a time, challenging it against your project's existing domain model and glossary (CONTEXT.md), sharpening fuzzy terms, stress-testing with concrete scenarios, cross-referencing code, and updating CONTEXT.md + ADRs inline as decisions crystallise. ACT 2 (Claude ↔ Codex) — Claude writes the locked plan to PLAN.md and OpenAI Codex (gpt-5.6-sol) adversarially reviews it in a read-only sandbox (VERDICT:APPROVED/REVISE), Claude revises and re-submits to the same Codex session while it stays resumable (fresh-reseeded past the context ceiling) until APPROVED or a MAX_ROUNDS cap, then you sign off before any code. ACT 3 (optional) — Codex builds it (gpt-5.6-luna at xhigh reasoning effort) and Claude reviews the diff. Use when the user says "/claudex-grill-docs", "grill me against the docs then have codex review", "stress-test this against our domain model then get a second model on it", or is about to build something high-stakes in a project with established terminology/ADRs and wants alignment, documentation, AND a cross-model sanity check. Builds on Matt Pocock's grill-with-docs (MIT). For the plain variant use /claudex-grill; for the Codex review only use /claudex-review. NOT for reviewing already-written code (use /codex:review) and NOT for trivial changes.
---

# Claudex-Grill-Docs — Grill Against Your Domain, Then Get Reviewed

Two acts, plus an optional third. Act 1 aligns intent *and* keeps your living docs honest; Act 2 has a different model attack the result; Act 3 (optional) flips roles so Codex builds and Claude reviews.

- **Act 1** is Matt Pocock's `grill-with-docs`, used under MIT (see `THIRD-PARTY-NOTICES.md`). It interrogates you, challenges your plan against `CONTEXT.md`/ADRs, and updates them inline.
- **Act 2** is the `claudex-review` engine, executed by reference (one canonical protocol, no drift between copies) — cross-model (`gpt-5.6-sol`), read-only, bounded — with two docs-aware prompt additions below.
- **Act 3** is the `claudex-build` role-flip — Codex (`gpt-5.6-luna` at `xhigh`) writes, Claude reviews the diff.

You enter at two points: answering the grill, and signing off the converged plan.

---

## ACT 1 — GRILL WITH DOCS (you ↔ Claude)

Snapshot `git status -sb` before the first question — the Act-2→build plan-checkpoint commit may only auto-commit paths that were clean at this kickoff.

<what-to-do>
Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.

Ask the questions one at a time, waiting for feedback on each question before continuing.

If a question can be answered by exploring the codebase, explore the codebase instead.
</what-to-do>

<supporting-info>

### Domain awareness

During codebase exploration, also look for existing documentation. Most repos have a single context (a root `CONTEXT.md` + `docs/adr/`); larger repos split into multiple contexts under a root `CONTEXT-MAP.md`. Create files **lazily** — only when you have something to write. If no `CONTEXT.md` exists, create one when the first term is resolved; if no `docs/adr/` exists, create it when the first ADR is needed.

### During the session

- **Challenge against the glossary.** When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately. "Your glossary defines 'cancellation' as X, but you seem to mean Y — which is it?"
- **Sharpen fuzzy language.** When the user uses a vague or overloaded term, propose a precise canonical term. "You're saying 'account' — do you mean the Customer or the User? Those are different things."
- **Discuss concrete scenarios.** When domain relationships are being discussed, invent specific scenarios that probe edge cases and force the user to be precise about the boundaries between concepts.
- **Cross-reference with code.** When the user states how something works, check whether the code agrees. On a contradiction, surface it: "Your code cancels entire Orders, but you just said partial cancellation is possible — which is right?"
- **Update CONTEXT.md inline.** When a term is resolved, update `CONTEXT.md` right there — don't batch. Use the format in [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md). `CONTEXT.md` is a glossary and nothing else — no implementation details, not a spec, not a scratchpad.
- **Offer ADRs sparingly.** Only offer to create an ADR when all three are true: (1) hard to reverse, (2) surprising without context, (3) the result of a real trade-off. If any is missing, skip it. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md).

</supporting-info>

### Handoff to Act 2

When the decision tree is resolved, the glossary/ADRs are updated, and you're aligned, **write the agreed plan to `PLAN.md`** (using the canonical terms from `CONTEXT.md`), then run Act 2:

```markdown
# Plan: <task>
_Locked via grill-with-docs — by Claude + <user>. Terms per CONTEXT.md._
## Goal
<one paragraph, in the project's ubiquitous language>
## Approach
<numbered, concrete steps>
## Key decisions & tradeoffs
<the contestable choices the grill resolved — link any ADRs created>
## Risks / open questions
<anything still open>
## Out of scope
<bounds>
```

Initialize `PLAN-REVIEW-LOG.md`:

```markdown
# Plan Review Log: <task>
Act 1 (grill-with-docs) complete — plan locked, CONTEXT.md/ADRs updated. MAX_ROUNDS=<n>. Reviewer: <REVIEW_MODEL>/<REVIEW_EFFORT>.
```

---

## ACT 2 — REVIEW (Claude ↔ Codex, via the claudex-review engine)

Open `~/.claude/skills/claudex-review/SKILL.md` and execute its **full flow** — Models, per-round effort schedule, CLI mechanics, session hygiene, structured findings contract ([CRITICAL|REQUIRED|MINOR] + severity-gated verdict), disposition ledger, delta-scoped re-review prompts, verdict parsing, hard rules — with exactly these overrides:

1. **Skip its Step 1** (Claude plans): `PLAN.md` already exists from Act 1, and `PLAN-REVIEW-LOG.md` is already initialized with the grill-docs kickoff line above.
2. **Its Step 0** (kickoff) is already satisfied — the grill was the kickoff; do not re-ask scope.
3. **Round-1 prompt, docs additions:** after "Read the plan at `PLAN.md`" insert "(and `CONTEXT.md`/ADRs for the domain language)", and add `domain-language mismatches` to the flaw list.
4. **Re-review prompts (rounds 2+), docs addition:** the changed-sections re-read instruction also asks Codex to re-check the revised sections against `CONTEXT.md`.
5. **Resolution ask** (its human gate #2, APPROVED case) becomes: *"Grilled against the docs + survived N rounds of Codex. Implement it now — Codex builds it (`/claudex-build`), Claude builds it, or stop here?"* — credit both acts in the 3-bullet summary.
6. Everything else — tunables (`MAX_ROUNDS=5` default), defaults, deadlock handling, hard rules, what-NOT-to-do — is claudex-review's, unmodified.

**No code is written during either act.**

### ACT 3 (optional) — BUILD (Codex ↔ Claude, roles flipped)

If the user picks Codex: invoke `claudex-build` with `SPEC_FILE=PLAN.md` and the same `LOG_FILE` (it appends `## Act 3 — Build`). Codex writes with access, Claude reviews the diff and runs the proof. If the user picks Claude, implement directly.

---

## Hard rules (docs-specific — Act 2 rules live in claudex-review)

- Act 1 always precedes Act 2 — don't write `PLAN.md` until the grill has resolved the decision tree and the docs are updated.
- `CONTEXT.md` is a glossary only — no implementation details.
- The Act-2 protocol is executed from `claudex-review/SKILL.md`, not from memory — if this file and that one ever disagree about the review loop, that one wins.
- Code only after the user's final sign-off. `LOG_FILE` is the deliverable.

## What NOT to do

- Don't review already-written code — that's `/codex:review`.
- Don't skip Act 1, and don't treat `CONTEXT.md` as a spec.
- Don't re-implement the review loop inline from this file's description — open and follow `claudex-review/SKILL.md`.
