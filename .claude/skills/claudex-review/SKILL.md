---
name: claudex-review
description: Claude×Codex collaboration — the REVIEW half (Act 2). A standalone adversarial PLAN-review loop where Claude (builder) and OpenAI Codex (read-only critic, gpt-5.6-sol) tag-team an implementation plan before any code is written. Use when you ALREADY have a plan or a clear idea and just want the cross-model stress-test — no requirements interview first. Claude drafts/loads the plan into PLAN.md, Codex reviews it in a read-only sandbox and returns VERDICT:APPROVED or VERDICT:REVISE, Claude revises and re-submits to the same Codex session while it stays resumable (fresh-reseeded past the context ceiling) until APPROVED or a MAX_ROUNDS cap. Human approves the converged plan before code. Use when the user says "/claudex-review", "codex review my plan", "have Codex review my plan", "argue this plan with Codex", "adversarial plan review", "make Claude and Codex argue over the plan", or is about to build something high-stakes (auth, schema, concurrency, migrations, payments) and wants a second-model sanity check on the PLAN before implementation. For a guided requirements interview BEFORE the review use /claudex-grill. NOT for reviewing already-written CODE (that is the Codex plugin's /codex:review) and NOT for trivial changes.
---

# Claudex-Review — Adversarial Plan-Review Loop

Two models, one plan, a bounded argument. **Claude is the builder and orchestrator. Codex is a read-only critic** that can read the repo and the plan but cannot touch a single file. They communicate strictly through `PLAN.md` + a Codex session that persists across rounds while it stays resumable (fresh-reseeded past the context ceiling). The human enters at exactly two points: kickoff and final sign-off.

This is a **deliberate, high-stakes tool** — reach for it on auth, data models, concurrency, migrations, payments, anything expensive to get wrong. Skip it for obvious/cheap work.

> This file is the **canonical Act-2 engine**. `claudex-grill` and `claudex-grill-docs` execute it by reference with small overrides — edit the protocol HERE, never re-copy it into the siblings.

## Models (edit here)

| Role | Var | Default | Effort |
|------|-----|---------|--------|
| Adversarial plan review / architect | `REVIEW_MODEL` | `gpt-5.6-sol` | `REVIEW_EFFORT` = `xhigh`, every round |

- `sol` is the top-judgment tier from `~/.codex/AGENTS.md` (Sol = review/architecture/acceptance). Claude authored the plan; Codex-Sol attacks it. The cross-provider split is the point — a model does not catch its own blind spots.
- Pinned via `-m "$REVIEW_MODEL" -c model_reasoning_effort="$REVIEW_EFFORT"`.
- If your Codex can't resolve `sol`, set `REVIEW_MODEL` to your live default. A bad model fails loudly on Round 1 (no `thread.started` line) — switch and rerun, never retry blind.
- **Effort fallback (mirror of the model fallback):** if the CLI rejects an effort value as an invalid `model_reasoning_effort` enum, drop one rung (`xhigh`→`high`→`medium`), log the downgrade in `LOG_FILE`, and rerun. Never retry blind at the rejected value. Fallback only goes DOWN — never "recover" by climbing.
- **Never set `ultra`. It is not a tier.** Wire-captured on codex-cli 0.144.1 against a local sink: `ultra` exits 0, prints `turn.completed`, empty stderr, and the rollout records `"reasoning_effort":"ultra"` — but the request body says `{"effort":"max"}`. The CLI rewrites it before it leaves the machine, and `ultra` is absent from the API's own enum. Every round this skill previously dispatched at `ultra` was silently a `max` round costing ~4× `xhigh`, logged under a label that never shipped.
- **Why `xhigh` and not `max`.** Measured on a real build campaign: two `max` rounds, same repo, same reviewer — the round that spent 76% more reasoning turns and 2.7× the transcript was the one **rejected** on 7 findings. Extra effort optimizes harder against whatever objective the prompt states; it does not repair a mis-stated one. The lever is the precision gate below, not the dial. Raising a round above `xhigh` needs an explicit user instruction for that round, logged in `LOG_FILE`.
- Optional `MODEL_PROVIDER`: if set, append `-c model_provider="<id>"`. Unset by default.
- **Precision gate (binding — applies to EVERY round).** A reviewer spends its budget on whatever the prompt leaves undefined. Given room it invents scope: speculative redesigns, findings nobody asked for, very long runtimes, no gain in defect quality. This was always the real failure mode — it was misattributed to `ultra` when the tier was never what caused it. So **precision is the price of dispatching at all** — a round may only be launched if its prompt states ALL of the following explicitly:
  1. **Exact target** — the file plus the section headings or line ranges to attack, and what to skim or skip. Never "review the plan".
  2. **Explicit non-goals** — what is out of scope, named. Carry the plan's `Out of scope` section into the prompt verbatim.
  3. **Settled items** — the disposition ledger (REJECTED / ACCEPTED-RISK with reasons), with the standing order not to re-raise them absent a new defect.
  4. **Output contract** — the exact finding format, the severity rubric, and the verdict line (the Round-1 prompt below already carries these; no round may drop them).
  5. **A no-redesign clause** — report defects in the plan as written; do not propose an alternative architecture unless a listed defect makes the current one unworkable.
  6. **A bound** — most severe first, and a cap on how many findings to return, so it stops rather than padding.
  **If any of the six cannot be stated concretely, the round is not ready to launch.** Narrow the target or sharpen the ask first, and log why it was delayed. An underspecified round is worse than no round — that is the whole finding, not a style preference, and no amount of effort substitutes for it.
- **No per-round effort schedule — every round is `xhigh`.** The old schedule spent the most on round 1 and on deadlock tie-breaks. Both of those spends were `ultra`, which means both were silently `max`, which means the schedule was paying ~4× on exactly the rounds it claimed were special without any evidence the depth changed a verdict. What makes round 1 the strongest pass is that it is a full from-scratch attack with the six precision items stated — not the dial. Escalate the *prompt* (tighter target, harder non-goals, explicit disposition ledger), never the effort.

## Codex CLI mechanics (verified codex-cli 0.144.1)

- Non-interactive runner is `codex exec`. Pass the prompt as an arg **with `< /dev/null`** — `codex exec` reads stdin *in addition to* the prompt arg, so under a non-TTY driver (the Bash tool, CI) it hangs forever waiting on stdin EOF without the redirect.
- `--json` streams events; parse `{"type":"thread.started","thread_id":"…"}` → `SID`. The critique is written to the `-o <file>` — read that, do not parse the stream for content.
- **Unique files every round:** `OUT=$(mktemp /tmp/claudex-verdict.XXXXXX); STREAM=$(mktemp /tmp/claudex-stream.XXXXXX); ERR=$(mktemp /tmp/claudex-err.XXXXXX)`. Never reuse fixed paths — a stale file from a crashed prior run or a concurrent invocation reads as a fresh verdict.
- Resume the SAME session with `codex exec resume "$SID" …` so Codex remembers its prior critiques. **Resume does NOT accept `-s`** — force read-only with `-c sandbox_mode="read-only"`, or Codex inherits `config.toml` (possibly a writable default) and could edit files mid-loop. This is the single most important safety line.
- **Stderr goes to `$ERR`, not `/dev/null`**, and the codex exit code is captured from the pipeline: append `; RC=${PIPESTATUS[0]}` after every codex pipeline. **Success = `RC` 0 + non-empty `-o` file + a `thread.started` line** (`mktemp` pre-creates the file, so existence alone proves nothing; a run can emit partial output then die nonzero). On failure, show the tail of `$ERR` — never discard it.
- **Timeout:** every codex call runs with `timeout: 600000` on the Bash tool (the default 2-min tool timeout kills real reviews). If the ceiling trips, treat it as a failed run — stop, don't retry blind. A big-plan round can legitimately need >10 min — run it with `run_in_background: true` and judge it by the liveness watch below, never by wall-clock alone. For any background round, arm ONE heartbeat watcher (`python3 ~/.claude/skills/claudex-build/helpers.py watch "$R" 600` via Bash `run_in_background`) and then leave the run alone — **wakeup budget ≤3 per round** (the run's own exit notification, at most one watcher alert, one corroboration pass); no main-loop polling of the rollout or stream between notifications, and TaskStop the watcher when the run's own exit arrives. Measured on a real multi-phase session: unbudgeted monitoring produced 112 notification wakeups ≈ half of all main-thread API calls.
- **Liveness watch (hung vs slow):** process liveness lies — a healthy run blocked on the API stream and a wedged one both sit at ~0% CPU, and the `--json` stream is legitimately quiet for long stretches (few event types). The ONLY trustworthy progress signal is the session rollout, `R=$(ls ~/.codex/sessions/<yyyy>/<mm>/<dd>/rollout-*"$SID".jsonl)`: healthy = `ls -l "$R"` mtime keeps advancing and `grep -c '"last_token_usage"' "$R"` grows between checks. **Hung = rollout mtime frozen > ~10 min AND the token-event count flat** (measured hang on a build run: 55 min frozen at launch size, zero token events, process alive at 0.0% CPU, no stderr error). Recovery: kill the codex process, then re-issue the SAME round — the critic is read-only and a zero-token hang leaves its session state unchanged, so Round 1 relaunches fresh and rounds ≥2 `resume "$SID"` with the same round prompt (prior critiques intact; log the incident in `LOG_FILE`). If the re-issued round hangs again, reseed a fresh session from `PLAN.md` + the disposition ledger (the session-hygiene path). The startup stderr `failed to load models cache` is cosmetic — it appears in successful runs too; never diagnose a hang from it.
- **Token telemetry (peak, not last):** after each round:
  ```bash
  W=$(grep -o '"model_context_window":[0-9]*' "$STREAM" | tail -1 | cut -d: -f2)
  grep -o '"last_token_usage":{"input_tokens":[0-9]*' "$STREAM" | awk -F: -v w="${W:-258400}" \
    'BEGIN{p=0}{l=$NF+0; if(l>p)p=l} END{printf "PEAK=%d LAST=%d PCT=%d%% NONRESUMABLE=%s\n", p, l, p*100/w, (p*100/w>85 || l*2<p) ? "yes" : "no"}'
  ```
  Judge the session by **PEAK, not the final event** — the last event lies after an auto-compaction (measured on a real session: peak 235,087/258,400 = 91%, final event 31,110). `NONRESUMABLE=yes` (peak > 85% of window, or LAST < half of PEAK = compaction) is binding. Log the whole line in the round header in `LOG_FILE`. If the stream carries no usage events (`PEAK=0`), run the same commands on the rollout under `~/.codex/sessions/<date>/` keyed by `SID`; if neither source has events, treat the session as `NONRESUMABLE=yes` — absent telemetry fails closed, never open.

## Session hygiene (context ceiling)

A resumed critic session degrades before it fails: measured on a real run, a long-lived resumed thread reached 85% of its context window, and review quality is the first casualty. Rules:

- If the telemetry above flags the session non-resumable (**peak > ~85%** of the model context window, or compaction detected), do NOT resume again. Start a **fresh session** re-seeded from disk: `PLAN_FILE` + the disposition ledger (see the loop) carry the entire review state — nothing of value lives only in the old session.
- A fresh reseed does not reset `ROUND` or `MAX_ROUNDS`; log `SID(old) → SID(new)` in `LOG_FILE`.

## Prerequisites (verify once, fast)

- `codex --version` ≥ 0.130. `codex login` done (ChatGPT account or API key). Auth/model error → surface it, don't silently retry.
- **Echo the active review model before Round 1** so the user can confirm: state `REVIEW_MODEL` + `REVIEW_EFFORT` with the resolved tunables. If the user objects, stop before burning a round.
- Run from the target repo's root.

## Tunables (read from args, else default)

| Var | Default | Meaning |
|-----|---------|---------|
| `MAX_ROUNDS` | `5` | Hard cap on review rounds. The loop ALWAYS terminates here. |
| `REVIEW_MODEL` / `REVIEW_EFFORT` | `gpt-5.6-sol` / `xhigh` | See Models. Flat every round — no schedule, never `ultra`. Above `xhigh` only on an explicit per-round user instruction, logged. |
| `PLAN_FILE` | `PLAN.md` | Where the evolving plan lives (repo root). |
| `LOG_FILE` | `PLAN-REVIEW-LOG.md` | Append-only transcript of the argument. The artifact. |

If invoked with e.g. `rounds=3`, use that for `MAX_ROUNDS`. Echo resolved values before starting. Everywhere below, `PLAN.md` stands for the resolved `PLAN_FILE` — substitute it in every prompt and command.

## Flow

### Step 0 — Kickoff (human gate #1)

The invocation is the kickoff. Confirm scope in one line: what is being planned. Snapshot `git status -sb` now — the later plan-checkpoint commit may only auto-commit paths that were clean at this kickoff. If the user gave no task, ask for it (one question). Then proceed — no round-by-round approval; that comes at the end.

### Step 1 — Claude plans

Do real planning: read the relevant code, think through the approach, surface decisions and tradeoffs. Then write the plan to `PLAN_FILE`:

```markdown
# Plan: <task>
_Round 0 — initial draft by Claude_
## Goal
<one paragraph>
## Approach
<numbered steps, concrete>
## Key decisions & tradeoffs
<the contestable choices — name them explicitly so Codex has something to bite>
## Risks / open questions
<what you're unsure about>
## Out of scope
<bounds>
```

Initialize `LOG_FILE`:

```markdown
# Plan Review Log: <task>
Started <local time if known, else "session start">. MAX_ROUNDS=<n>. Reviewer: <REVIEW_MODEL>/<REVIEW_EFFORT>.
```

Show the user the plan inline; say you're sending it to Codex for adversarial review.

### Step 2 — The loop

Maintain `ROUND` (start 1), `SID` (empty until round 1 returns), and the **disposition ledger** — per prior finding: FIXED / REJECTED / ACCEPTED-RISK with one line of reasoning each, built during triage and fed back to Codex every round.

**The Round-1 review prompt** (write to a temp file: `RP1=$(mktemp)`; adjust the task line):

> You are an adversarial reviewer for an implementation plan. Be skeptical and specific — your job is to find what breaks, not to be agreeable. Read the plan at `PLAN.md` and any repo files you need (you are read-only). Verify the plan's claims against the actual code where possible. Identify concrete flaws: security holes, race conditions, missing edge cases, schema conflicts, wrong assumptions, observability gaps, simpler alternatives.
> Report findings as a numbered list, most severe first, one finding per line, in EXACTLY this format:
> `N. [CRITICAL|REQUIRED|MINOR] <file or plan section> — <defect in one sentence>. Fix: <one-line fix>.`
> Severity: CRITICAL = data loss, corruption, security hole, race condition. REQUIRED = the plan is wrong or incomplete and must change before implementation. MINOR = worth improving; must not block implementation.
> Do NOT modify any files. End your reply with EXACTLY one line: `VERDICT: APPROVED` or `VERDICT: REVISE`. REVISE requires at least one CRITICAL or REQUIRED finding — MINOR findings alone never justify REVISE.

**Round 1** (creates the session — capture `SID`):

```bash
OUT=$(mktemp /tmp/claudex-verdict.XXXXXX); STREAM=$(mktemp /tmp/claudex-stream.XXXXXX); ERR=$(mktemp /tmp/claudex-err.XXXXXX)
codex exec -m "$REVIEW_MODEL" -c model_reasoning_effort="$REVIEW_EFFORT" -s read-only \
  --json -o "$OUT" "$(cat "$RP1")" \
  < /dev/null 2>"$ERR" | tee "$STREAM" | grep '"type":"thread.started"'; RC=${PIPESTATUS[0]}
```

Parse `thread_id` → `SID`; stamp `SID: <thread_id>` under the `LOG_FILE` header (cross-references the session rollouts for later token audits). Critique in `$OUT`. `RC` nonzero, empty `$OUT`, or no `thread.started` = failed run — show the tail of `$ERR`, stop, tell the user.

**Rounds 2..MAX** — build a per-round prompt file `RP` from this template (this is the drift guard: Codex must see what changed and what was already adjudicated):

```
Round <n> re-review of PLAN.md.
CHANGED SECTIONS since your last review: <list them — re-read these in full; skim the rest>.
DISPOSITION ledger (cumulative — every prior finding, stable numbering):
  #<k> FIXED — <how, one line>
  #<k> REJECTED — <reason, one line>
  #<k> ACCEPTED-RISK — <reason, one line>
Do not re-raise REJECTED or ACCEPTED-RISK items unless my revision created a NEW defect around them.
Same finding format and severity rules as Round 1 ([CRITICAL|REQUIRED|MINOR], numbered, one line each).
End with EXACTLY one line: VERDICT: APPROVED or VERDICT: REVISE (MINOR findings alone never justify REVISE).
```

On the **final round** (`ROUND` == `MAX_ROUNDS`) append: `FINAL ROUND before human arbitration — a full-document sweep is permitted, but REVISE only for CRITICAL or REQUIRED defects.`

```bash
OUT=$(mktemp /tmp/claudex-verdict.XXXXXX); STREAM=$(mktemp /tmp/claudex-stream.XXXXXX); ERR=$(mktemp /tmp/claudex-err.XXXXXX)
codex exec resume "$SID" -c model="$REVIEW_MODEL" -c model_reasoning_effort="$REVIEW_EFFORT" \
  -c sandbox_mode="read-only" --json -o "$OUT" "$(cat "$RP")" \
  < /dev/null 2>"$ERR" | tee "$STREAM" >/dev/null; RC=${PIPESTATUS[0]}
```

**Each round, after Codex returns:**

1. Read `$OUT`. Append to `LOG_FILE`: `## Round <n> — Codex (<REVIEW_MODEL>, effort <REVIEW_EFFORT>)` + the full critique (+ the `peak/window` telemetry line).
2. Parse the verdict from the **last non-empty line only** (a substring match anywhere in the critique can hit quoted or negated text):
   ```bash
   VERDICT=$(awk 'NF{last=$0} END{print last}' "$OUT" | grep -oiE '^[[:space:]]*VERDICT:[[:space:]]*(APPROVED|REVISE)[[:space:]]*$')
   ```
   The anchors are load-bearing: an unanchored match accepts a last line like `VERDICT: REVISE (but actually no blockers)` or `NO VERDICT: APPROVED`. Trailing commentary on the verdict line = no match → the corrective-resume path below.
   No match → ONE corrective resume: `Reply with exactly one line: VERDICT: APPROVED or VERDICT: REVISE.` Session hygiene gates corrective resumes too — `NONRESUMABLE=yes` → skip the corrective call and treat as REVISE. Still no match → treat as REVISE and log the anomaly. Never guess APPROVED from prose.
3. **Consistency check (contract enforcement):**
   - `APPROVED` while the critique lists a `[CRITICAL]` or `[REQUIRED]` finding → contract violation: ONE corrective resume asking Codex to reconcile (fix the severity tags or the verdict). Still inconsistent → treat as REVISE on the listed findings, log the anomaly.
   - `REVISE` with only `[MINOR]` findings → contract violation the other way: treat as **APPROVED-with-notes**, log it, break.
4. `VERDICT: APPROVED` (consistent) → break to Step 3 (converged).
5. `VERDICT: REVISE` → Claude triages **each finding individually** (Claude is final arbiter — Codex advises, does not command): FIXED (revise `PLAN_FILE`), REJECTED (with reason), or ACCEPTED-RISK (with reason). Append `### Claude's response` to `LOG_FILE` (per-finding disposition). The triage IS the next round's disposition ledger. Increment `ROUND`.
6. Check session hygiene (context ceiling) before resuming. If `ROUND > MAX_ROUNDS` → break to Step 3 (deadlock).

### Step 3 — Resolution (human gate #2)

**If APPROVED:** Present the final `PLAN_FILE`, a 3-bullet summary of what the argument improved, and the round count. Ask: *"Plan survived N rounds of Codex. Implement it now — Codex builds it (`/claudex-build`), Claude builds it, or stop here?"* Only on a yes is code written. **No code is written during the loop.** If the user picks Codex, first commit the plan artifacts (`PLAN_FILE`, `LOG_FILE`, and any Act-1 doc updates such as `CONTEXT.md`/`docs/adr/` — `docs: plan checkpoint — <task>`) under claudex-build's post-commit gate policy (formatter mutation → restage once; hook check failure → fix and retry; still impossible → surface it, don't hang), confirm the tree is clean, then invoke `claudex-build` with `SPEC_FILE=PLAN.md` and the same `LOG_FILE` — roles flip (Codex writes, Claude reviews the diff) and the build rounds append to the same log.

**If MAX_ROUNDS hit without APPROVED (deadlock):** Do NOT pretend it converged. List each point Codex still flags + Claude's counter-position; hand it to the human to break the tie. A flagged disagreement beats a false "approved."

## Hard rules

- Codex is read-only EVERY round — `-s read-only` first call, `-c sandbox_mode="read-only"` every resume. It never writes.
- The loop ALWAYS terminates at `MAX_ROUNDS`. No unbounded recursion.
- Claude is the final arbiter on every REVISE — triage is per-finding (FIXED / REJECTED / ACCEPTED-RISK, reason logged) and the triage is fed back to Codex next round. Don't cave to Codex on everything (defeats the cross-model check) and don't ignore it (defeats the point).
- REJECTED and ACCEPTED-RISK items are settled — a re-raised settled item with no new defect is noise; note it in the log and move on.
- Verdicts must be consistent with severities — enforce the contract with one corrective resume, then fail toward the severity evidence, never toward APPROVED.
- Session hygiene beats sentiment: past ~85% peak (or any compaction), reseed a fresh session from `PLAN.md` + the ledger.
- Every round requires a precise prompt — all six items of the precision gate stated explicitly, or the round does not launch and the delay is logged. Never dispatch against an open-ended ask. Every round runs `xhigh`; **never set `ultra`** — the CLI rewrites it to `max` before the request leaves the machine, so it only buys ~4× the tokens and a log line that lies about what ran.
- Code only after human gate #2.
- `LOG_FILE` is the deliverable — keep the whole argument.

## What NOT to do

- Don't use this to review existing code — that's `/codex:review`.
- Don't resume with `--last` — capture and echo the explicit `SID` (a missing/garbage id can silently resume the wrong session).
- Don't parse the JSONL stream for the critique — read the `-o` file.
- Don't reuse fixed `-o`/stream/err paths across rounds — `mktemp` every time, and check `$OUT` is non-empty (existence proves nothing).
- Don't judge a session by its last token event — compaction makes it lie; use the peak.
- Don't diagnose a hang from `ps`/CPU or a quiet stream — rollout mtime + token events only (see the liveness watch).
- Don't let Codex edit files. Read-only, always.
- Don't skip the log — the argument transcript is the most valuable artifact.
