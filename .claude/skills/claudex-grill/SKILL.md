---
name: claudex-grill
description: Claude×Codex collaboration — full plan-hardening lifecycle. ACT 1 (you ↔ Claude) — Claude interviews you relentlessly about a plan or design, one question at a time, recommending an answer for each and exploring the codebase when it can answer itself, until every branch of the decision tree is resolved. ACT 2 (Claude ↔ Codex) — Claude writes the locked plan to PLAN.md and OpenAI Codex (gpt-5.6-sol) adversarially reviews it in a read-only sandbox (VERDICT:APPROVED/REVISE), Claude revises and re-submits to the same Codex session while it stays resumable (fresh-reseeded past the context ceiling) until APPROVED or a MAX_ROUNDS cap. ACT 3 (automatic on convergence) — the flow hands PLAN.md straight to claudex-build: Codex builds it (gpt-5.6-luna at xhigh reasoning effort) and Claude reviews the diff; claudex-build's kickoff confirmation is the one human gate before code. Use when the user says "/claudex-grill", "grill me then have codex review", "grill me and stress-test the plan", "interview me about this plan then get a second model on it", or is about to build something high-stakes (auth, schema, concurrency, migrations, payments) and wants both alignment AND a cross-model sanity check before implementation. Builds on Matt Pocock's grill-me (MIT). For the docs-aware variant use /claudex-grill-docs; if you already have a plan and want only the Codex review use /claudex-review. NOT for reviewing already-written code (use /codex:review) and NOT for trivial changes.
---

# Claudex-Grill — Get Grilled, Then Get Reviewed

Two acts, two different jobs — then an optional third where the roles flip:

- **Act 1 fixes the #1 failure mode: building the wrong thing.** Claude interrogates *you* until intent is locked — no guessing at ambiguity. (This act is Matt Pocock's `grill-me`, used under MIT — see `THIRD-PARTY-NOTICES.md`.)
- **Act 2 fixes the #2 failure mode: a plan that sounds right but breaks.** A *different model* (Codex, `gpt-5.6-sol`) adversarially attacks the locked plan. Cross-model = no echo chamber.
- **Act 3 (automatic) flips the roles:** when Act 2 converges, Codex (`gpt-5.6-luna` at `xhigh`) builds from the frozen plan via `claudex-build` and Claude reviews the diff like a contributor PR — no "who builds?" ask in between.

You enter at two points only: answering the grill, and claudex-build's one-line kickoff confirmation. Codex is read-only for the whole review and never touches a file until the build act.

**Act 2 is not re-specified here** — it IS the `claudex-review` engine, executed by reference (one canonical protocol, no drift between copies). Act 3 is the `claudex-build` contract. This skill adds Act 1 on the front and the handoff glue.

---

## ACT 1 — GRILL (you ↔ Claude)

Snapshot `git status -sb` before the first question — the Act-2→build plan-checkpoint commit may only auto-commit paths that were clean at this kickoff.

> Interview me relentlessly about every aspect of this plan until we reach a shared understanding. Walk down each branch of the design tree, resolving dependencies between decisions one-by-one. For each question, provide your recommended answer.
>
> Ask the questions one at a time, waiting for my answer before continuing.
>
> If a question can be answered by exploring the codebase, explore the codebase instead.

When the decision tree is resolved and you're aligned, **write the agreed plan to `PLAN.md`** in this structure, then move to Act 2:

```markdown
# Plan: <task>
_Locked via grill — by Claude + <user>_
## Goal
<one paragraph — reflects what the grilling actually settled>
## Approach
<numbered, concrete steps>
## Key decisions & tradeoffs
<the contestable choices the grill resolved — name them so Codex has something to bite>
## Risks / open questions
<anything still genuinely open>
## Out of scope
<bounds the grill established>
```

Initialize `PLAN-REVIEW-LOG.md`:

```markdown
# Plan Review Log: <task>
Act 1 (grill) complete — plan locked with the user. MAX_ROUNDS=<n>. Reviewer: <REVIEW_MODEL>/<REVIEW_EFFORT>.
```

---

## ACT 2 — REVIEW (Claude ↔ Codex, via the claudex-review engine)

Open `~/.claude/skills/claudex-review/SKILL.md` and execute its **full flow** — Models, per-round effort schedule, CLI mechanics, session hygiene, structured findings contract ([CRITICAL|REQUIRED|MINOR] + severity-gated verdict), disposition ledger, delta-scoped re-review prompts, verdict parsing, hard rules — with exactly these overrides:

1. **Skip its Step 1** (Claude plans): `PLAN.md` already exists from Act 1, and `PLAN-REVIEW-LOG.md` is already initialized with the grill kickoff line above.
2. **Its Step 0** (kickoff) is already satisfied — the grill was the kickoff; do not re-ask scope.
3. **Resolution (its human gate #2, APPROVED case) is replaced by the auto-build handoff**: do NOT ask who implements. Announce in one line — *"Grilled + survived N rounds of Codex — handing to claudex-build"* (credit both acts in a 3-bullet summary) — then immediately invoke the `claudex-build` skill with `SPEC_FILE=PLAN.md` and the same `LOG_FILE`. claudex-build's own Step-0 scope confirmation becomes the single remaining human gate before code. If the review instead deadlocks at MAX_ROUNDS, present the unresolved points and ask (extra round / arbitrated close → auto-build / stop) — deadlock still needs the human.
4. Everything else — tunables (`MAX_ROUNDS=5` default), defaults, deadlock handling, hard rules, what-NOT-to-do — is claudex-review's, unmodified.

**No code is written during either act.**

### ACT 3 (automatic) — BUILD (Codex ↔ Claude, roles flipped)

On Act-2 convergence (APPROVED, or a user-arbitrated close after deadlock), invoke `claudex-build` with `SPEC_FILE=PLAN.md` and the same `LOG_FILE` — it appends `## Act 3 — Build` so one artifact tells the whole story (grilled → reviewed → built → verified). Roles flip: Codex writes with access, Claude reviews the diff and runs the proof. The user can still say "Claude builds it" or "stop" at claudex-build's kickoff confirmation — that gate is the escape hatch, not a menu re-ask.

---

## Hard rules (grill-specific — Act 2 rules live in claudex-review)

- Act 1 always precedes Act 2 — don't write `PLAN.md` until the grill has resolved the decision tree with the user.
- The Act-2 protocol is executed from `claudex-review/SKILL.md`, not from memory — if this file and that one ever disagree about the review loop, that one wins.
- Code only in Act 3, which starts automatically on Act-2 convergence — claudex-build's Step-0 kickoff confirmation is the one human gate before any code.
- `LOG_FILE` is the deliverable — keep the whole argument.

## What NOT to do

- Don't review already-written code — that's `/codex:review`.
- Don't skip Act 1 — the grill is half the value.
- Don't re-implement the review loop inline from this file's description — open and follow `claudex-review/SKILL.md`.
