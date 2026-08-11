---
name: claudex-build
description: Claude×Codex collaboration — the BUILD half (Act 3). Hand a frozen spec (PLAN.md or any locked plan) to OpenAI Codex to IMPLEMENT with write access, while Claude stays the spec-writer and reviewer — the role-flip of /claudex-review. Codex (gpt-5.6-luna at xhigh reasoning effort) builds from the spec, Claude reads the full diff like a contributor PR, runs the proof test itself, and iterates fixes up to MAX_FIX_ROUNDS in a FRESH Codex session every round — both fix rounds at xhigh, never max, never ultra — before taking over and finishing directly. Each accepted phase is committed by Claude automatically — the human enters at kickoff and gets a final report; there are no mid-run approval gates. Use when the user says "/claudex-build", "have codex build this", "codex implement the plan", "hand the plan to codex", "delegate the build to codex", or right after a plan survives /claudex-grill, /claudex-grill-docs, or /claudex-review and they choose Codex for implementation. Also for standalone delegation: refactors, mechanical migrations, bug fixes with a known repro, test/coverage writing — anything that reads as a work order. NOT for tiny edits (~<20 lines — delegation overhead loses), NOT for design work (if writing the spec forces decisions, that is /claudex-grill first), NOT for reviewing existing code (the Codex plugin's /codex:review), and NOT for anything needing Claude-session tools (MCP, secrets, browser). Kept separate from build-review.js (that one is Sonnet-builds-in-harness; this is Codex-builds-via-CLI).
---

# Claudex-Build — Codex Types, Claude Verifies, Claude Commits

The build half of the Claude×Codex loop and the role-flip of `/claudex-review`: there, Claude builds the plan and Codex critiques it read-only. Here, **Codex is the builder with write access; Claude is the spec-writer, reviewer, and committer.** Codex implements a frozen spec end-to-end; Claude judges the diff like a contributor PR, runs the proof itself, iterates bounded fixes, then **commits the accepted phase and moves on — no human approval mid-run.** The human enters at kickoff and receives a final report when everything is done.

Adapted from Peter Steinberger's `codex-first` pattern and the `grill-me-codex` skills (chaseai), rebuilt on this house's verified Codex mechanics (codex-cli 0.144.1).

**Spec quality decides success.** Codex starts with zero session context — everything it needs is in the prompt. A plan that survived `/claudex-grill` or `/claudex-review` already is a frozen spec; that is the ideal input.

## Models (edit here)

| Role | Var | Default | Effort |
|------|-----|---------|--------|
| Implement (launch) | `BUILD_MODEL` | `gpt-5.6-luna` | `BUILD_EFFORT` = `xhigh` |
| Fix rounds | `FIX_EFFORT` | — | `xhigh` on both rounds. After fix round 2, Claude takes over and finishes directly. |

- Pinned via `-m "$BUILD_MODEL" -c model_reasoning_effort="$BUILD_EFFORT"`.
- **`xhigh` is this skill's only effort. `max` exists on the wire and is deliberately not used.** The ladder is `xhigh` → `xhigh` → **Claude takeover**: no escalation on fix rounds, and no escalation to `max` ever. Two reasons, both measured, not stylistic:
  - **Cost.** `max` runs ~4× the tokens of `xhigh` for the same work order.
  - **It did not buy correctness.** Two `max` rounds on the same repo, same reviewer, same campaign: round 1 PEAK 244,332 (94%) accepted with one correction; round 2 PEAK 244,499 (94%), **76% more reasoning turns and 2.7× the transcript — and rejected on 7 findings**, five of them the same failure (deleting the semantic distinction being measured instead of raising it). More effort optimizes harder against whatever objective the prompt states; it does not repair a mis-stated one.
  What actually moved outcomes was **spec quality and Root review**, never the tier. So control diff sprawl and wrong-objective failures through the *prompt* (the SCOPE DISCIPLINE block in Step 4A and explicit FORBIDDEN rules), never by moving the effort.
- **`gpt-5.6-luna` at `xhigh` is the only build model+effort this skill uses.** There is no substitute tier and no silent fallback to another model: if your Codex can't resolve `luna`, that is an environment fault to fix and report, not a reason to build on something else — a round that quietly ran on a different model or effort produces a diff you cannot compare against any other round. A bad model fails loudly on Round 1 (no `thread.started` line, model/auth error); fix the resolution and rerun the SAME model, never retry blind and never swap the tier. Raising a round to `max` requires an explicit user instruction for that round, logged in `LOG_FILE` — it is never the orchestrator's own recovery move.

**`model_reasoning_effort` enum facts (verified codex-cli 0.144.1, wire-captured against a local sink):**

- Luna accepts `none | low | medium | high | xhigh | max`. `minimal` is rejected by the API for this model (`unsupported_value`), though the CLI forwards it.
- **`ultra` is a silent client-side rewrite to `max`.** The run exits 0, prints `turn.completed`, writes an empty stderr, and the session rollout still records `"reasoning_effort":"ultra"` — but the intercepted request body says `{"effort":"max"}`. Terra clamps identically. `ultra` is absent from the API's own enum entirely. So asking for `ultra` never bought anything above `max`; it only removed your ability to tell. Never set it — not because it is too much, but because it is not real.
- **The CLI performs no local validation of this setting.** A garbage value (`banana`) is forwarded verbatim and rejected server-side. So a typo costs an API round-trip and a failed turn, not a fast local error — which is why the value is pinned in one place here rather than typed per round.
- **Effort fallback:** a rejection arrives as a server-side 400 naming the supported values, not a config-parse error. On rejection, drop one rung (`xhigh`→`high`→`medium`), log the downgrade in `LOG_FILE`, and rerun. Fallback only ever goes DOWN — never "recover" by climbing to `max`, and never "fall back" to `ultra`, which is `max` wearing a different name.
- Optional `MODEL_PROVIDER`: if set, append `-c model_provider="<id>"`. Unset by default.

## Codex CLI mechanics (verified codex-cli 0.144.1)

- Non-interactive runner is `codex exec --disable multi_agent` for this skill. The flag is mandatory on every build, fix, continuation, and interrupted-round resume so the delegated writer cannot recursively orchestrate. Feed the prompt via stdin (`- <"$FILE"`) so it gets immediate EOF — `codex exec` reads stdin *in addition to* any prompt arg, so under a non-TTY driver (the Bash tool, CI) a bare arg hangs forever waiting on stdin EOF.
- `--json` streams events; parse `{"type":"thread.started","thread_id":"…"}` → `SID`. Codex's final report is written to the `-o <file>` — read that file, do not parse the stream for content.
- **Unique files every round:** `OUT=$(mktemp /tmp/claudex-build.XXXXXX); STREAM=$(mktemp /tmp/claudex-stream.XXXXXX); ERR=$(mktemp /tmp/claudex-err.XXXXXX)`. Never reuse fixed paths — a stale file from a crashed prior run reads as a fresh report.
- **`codex exec resume --disable multi_agent "$SID"` is NOT part of this skill's round loop** — every round (build, fix, continuation) launches a new session. Resume survives for exactly one purpose: continuing a single round that was interrupted mid-flight (the hang-recovery path below, where the rollout shows real token events). Resume only a SID whose initial work order began with the exact Step-1 receipt. It is never the vehicle for handing review findings back. If you use it there: **resume does NOT accept `-s`** — force the sandbox with `-c sandbox_mode="…"`, re-assert `-c model=… -c model_reasoning_effort=…`, and resend the complete Step-1 delegated-writer receipt block for determinism. Missing or malformed receipt is a protocol error: stop and relaunch fresh with the complete receipt.
- Write access (this skill): `-c sandbox_mode="$SANDBOX" -c approval_policy="never"` on both `exec` and `resume`. `SANDBOX` tunable, default `danger-full-access` (handles installs/tests/out-of-repo). `workspace-write` is safer but blocks network + out-of-repo writes.
- **Stderr goes to `$ERR`, not `/dev/null`**, and the codex exit code is captured from the pipeline: append `; RC=${PIPESTATUS[0]}` after every codex pipeline. **Success = `RC` 0 + non-empty `-o` file + a `thread.started` line** (`mktemp` pre-creates the file, so existence alone proves nothing; a run can emit partial output then die nonzero). On failure, show the tail of `$ERR` — never discard it.
- **Timeout:** every codex call runs with `timeout: 600000` on the Bash tool (the default 2-min tool timeout kills real builds). Spec clearly >10 min (multi-file feature, migration, image generation) → launch with `run_in_background: true` and read the `-o` file when it exits. Don't kill a quiet background run early — Codex builds are legitimately slow; quiet ≠ hung — decide from the liveness watch below, never from the stream or `ps`.
- **Liveness watch (hung vs slow):** process liveness lies — a healthy run blocked on the API stream and a wedged one both sit at ~0% CPU, and the `--json` stream is legitimately quiet for long stretches (few event types). The ONLY trustworthy progress signal is the session rollout, `R=$(ls ~/.codex/sessions/<yyyy>/<mm>/<dd>/rollout-*"$SID".jsonl)`: healthy = `ls -l "$R"` mtime keeps advancing and `grep -c '"last_token_usage"' "$R"` grows between checks. **Hung = rollout mtime frozen > ~10 min AND the token-event count flat** (measured hang: 55 min frozen at launch size, zero token events, process alive at 0.0% CPU, no stderr error). Recovery: kill the codex process (TaskStop on the background task), then — zero token events ever produced → relaunch FRESH with the same prompt file (nothing to save; log `SID(old) → SID(new)` in `LOG_FILE`); token events > 0 → resume only a SID whose initial work order carried delegated mode, using `codex exec resume --disable multi_agent "$SID"` with a stdin work order beginning with the complete five-line receipt block from Step 1, followed by "continue where you left off." Missing or malformed receipt is a protocol error: stop and relaunch fresh with the complete receipt. The rollout preserves the partial build; if the resumed run re-hangs, go fresh. The startup stderr `failed to load models cache` is cosmetic — it appears in successful runs too; never diagnose a hang from it.
- **Automated heartbeat (every background run):** don't rely on remembering to check — arm a watcher right after capturing `SID`. Use a **Bash `run_in_background` python3 script file**, NOT the Monitor tool and NOT inline shell: shell-hook wrappers (e.g. lean-ctx) block builtins/`$(…)` at arm time (exit 126) and kill Monitor-wrapped commands at a ~120s runtime cap mid-sleep, while Bash background tasks run unhooked for hours (the codex run itself lives there). Script contract: every `STALE` seconds sample the rollout's mtime age, byte size, and `"last_token_usage"` count; a sample is *frozen* only if age > `STALE` AND size flat AND token count flat; **alert only after 2 consecutive frozen samples**, by printing one line and exiting nonzero — the task-exit notification is the alert delivery. Self-expire (~3h) so a forgotten watcher can't alert on a finished run. TaskStop the watcher when the build's own exit notification arrives.
  Arm it with `python3 ~/.claude/skills/claudex-build/helpers.py watch "$R" 600` via Bash `run_in_background` (implements exactly this contract: 2 consecutive frozen samples → one line + exit 1; 3h self-expiry). `STALE=600` is deliberately conservative for `xhigh`, this skill's only effort: reasoning stretches between tool calls are long enough that a quiet rollout is normal, and 2 consecutive frozen samples means ~20 min of genuine silence before anything alerts. Do not lower it to "catch hangs sooner" — a false alert costs a main-loop wakeup out of a budget of three, while a real hang is still caught within ~20 min. A long quiet stretch alone still proves nothing — CPU and silence are lying signals; corroborate below.
  **A heartbeat alert is a trigger to corroborate, never an automatic kill.** Declare hung and kill ONLY when independent signals agree: (1) rollout mtime frozen past the effort threshold across 2+ consecutive checks; (2) rollout byte size flat; (3) token-event count flat; (4) no worktree file mtimes advancing (a building codex edits files; `find <repo> -newer <marker> | head`); (5) the codex process's cumulative CPU TIME (`ps -o time`) not advancing between two samples — identify the PID by full command line (`pgrep -fl 'codex exec'`), never by loose grep (unrelated processes match "codex"); (6) `$ERR` has no fatal error and no exit notification arrived (crash ≠ hang — a crash already notifies on its own). Init-hang signature additionally: zero token events ever + rollout frozen at launch size. Any single signal alone — CPU% above all — proves nothing.
- **Wakeup budget (binding): ≤3 main-loop wakeups per background round** — (1) the build task's own exit notification, (2) at most one watcher alert, (3) the one corroboration pass that alert triggers. Between notifications the orchestrator does NOT touch the run: no foreground rollout `ls`/`grep`, no extra background probe tasks, no timer loops — the armed watcher is the only process watching, and it already encodes the sampling policy. A watcher alert triggers exactly one corroboration pass (the six-signal check above), then kill-or-rearm; re-arm at most once per round. TaskStop the watcher the moment the build's own exit notification arrives — a stopped watcher never fires again. Measured cost of ignoring this: a real multi-phase run burned 112 notification wakeups ≈ half of all its main-thread API calls, each replaying ~150K of cached context — monitoring, not building.
- **Token telemetry (peak, not last):** after each round run `python3 ~/.claude/skills/claudex-build/helpers.py telemetry "$STREAM" "$R"` (second arg optional: the session rollout, consulted when the stream carries no usage events) → `PEAK= LAST= PCT= NONRESUMABLE=`. Judge by **PEAK, not the final event** — a compacted session reports a tiny LAST while its PEAK hit 91% (measured: 235,087/258,400, final event 31,110). The helper encodes the policy and its output is **binding**: `NONRESUMABLE=yes` on peak > 85% of window, on compaction (LAST < half of PEAK), or on zero usage events in both sources — absent telemetry fails closed, never open. Log the whole line in the round header in `LOG_FILE`.

## Session lifecycle (resume vs fresh — decides quality)

Measured on a real multi-phase build: a session resumed ~26× climbed to 85% of the model's context window and under-delivered the same wiring across three consecutive rounds; a fresh session re-seeded from the spec finished the next phase in one round. Rules:

- **Every Codex round is a FRESH session — build, fix, and continuation alike. Nothing in this skill resumes.** The spec, the reviewer's findings, and the working tree are the state, and all three live on disk. Log `SID(prev) → SID(new)` in `LOG_FILE` each round so the chain stays auditable.
- **Why fix rounds go fresh too** (the non-obvious one): a resumed builder re-reads its own rejected reasoning sitting next to the correction, and drifts back toward the design the review just rejected — the same "restate the bounds verbatim or it drifts" failure the fix prompt was already compensating for. A fresh session sees only the defect list and the current bytes, so there is nothing to drift back to. It also restarts context at zero every round instead of compounding toward the ceiling.
- **What freshness costs, and how to pay it:** a fresh session knows nothing about the build it is fixing. That cost is real and is paid in the work order, not in the session — every fix prompt must be self-contained (Step 4A). A fix list that reads as "also fix the thing we discussed" is a broken work order.
- Because nothing resumes, `NONRESUMABLE` telemetry no longer gates routing. Keep logging the telemetry line — it is still how a phase that is too big gets caught (see the sizing rule below) — but it never decides resume-vs-fresh, because that decision is already made.
- **Size work packages for the ceiling.** Even a fresh full-phase session peaked at 91% on a real run — a phase that big is two phases. Slice at one integration seam + its focused tests, targeting a **predicted peak of 45–50%** — predictions drift up, never down (measured: a package sized as "fits under 60%" peaked at 89%, burned 3M tokens, and delivered zero commits). Predicted >50% → split in the work order before launching, not after the session bloats; splitting is cheap (measured: three small packages averaged ~51% fewer tokens per accepted commit than one monolith).
- **The ORCHESTRATOR session is sized too, not just Codex's.** A real multi-phase run held one Claude session for 15 h and auto-compacted 3× (~100–190K of cache re-write each, plus summary-fidelity risk mid-phase); a later run that ignored the ceiling compacted **23×** (0322a48e). For multi-phase builds the default answer is **Phase-lane mode (next section)** — the in-root ceiling below applies to classic mode and to the conductor as fallback. Classic in-root rule: prefer **1–2 phases per orchestrator session** when choosing how to slice the spec — but that is a sizing heuristic, not a stop condition. **Compaction never halts the run.** Do not stop at a phase boundary because an auto-compact fired or is imminent; launch the next phase anyway. What makes that safe is that the spec, `LOG_FILE`, and the committed tree ARE the state — the same doctrine as Codex freshness — so keep `LOG_FILE` current at every phase commit (`BASE_HEAD`, resolved tunables + `SEAL_MODE` state, the per-phase table, one line per committed phase). A compacted orchestrator re-reads that from disk and continues. The run ends when every phase is committed, or on a HALT.

## Phase-lane mode (default for ≥2 phases)

One session running every phase in-root is the measured disease: 23 auto-compactions over a ~15-phase run, summary-fidelity loss mid-build, plan files re-read after every compact. The architectural fix: the user-facing session is a thin **CONDUCTOR**; each phase executes in a **fresh phase-lane subagent** that dies at its phase commit. Fresh-per-phase is the Codex freshness doctrine applied to Claude's own side — the spec, `LOG_FILE`, and the committed tree are the state. Mode selection: ≥2 phases and the Agent tool available → phase-lane mode; single phase, or no Agent tool → classic in-root.

**Conductor contract:**
- Runs Step 0 gates and tunables resolution ONCE at kickoff; owns the phase table and the final report; is the ONLY place `AskUserQuestion` may fire.
- Per phase: spawn the lane — Agent tool, `general-purpose`, `model: opus` (the lane is the acting phase-root; root tier is mandatory, `fable` on the same escalation triggers as root) — then wait on the lane's completion notification. No polling lanes; the lane-completion notification is the conductor's only wakeup, same doctrine as Codex-round watchers.
- The lane prompt is a POINTER work order, self-contained in one screen: invoke the `claudex-build` skill; execute ONLY Phase `<n>` per Steps 2–5 in phase-lane mode; `SPEC_FILE`, `LOG_FILE`, resolved tunables, `SEAL_MODE` state, `BASE_HEAD=<hash>`. Never inline the spec, prior phases, or history — the lane reads them from disk (measured: a 28.6K inline handoff was pure waste).
- On lane return, AUDIT — never re-review: (1) `git log -1` hash equals the lane's claimed commit and HEAD moved by exactly that commit; (2) `LOG_FILE` tail shows the phase's round entry with evidence body and seal state; (3) tree clean. Budget ≤5 tool calls, batched. Any mismatch between lane claim and repo/log state = protocol violation → **HALT the run and report the user**; never launch the next lane over a mismatch.
- Conductor keeps nothing in context but the phase table and one summary line per phase (~60K ceiling). If the conductor compacts anyway, it does NOT stop: `LOG_FILE` plus the committed tree are the state, so it re-reads the phase table from disk and spawns the next lane.

**Phase-lane contract (acting phase-root):**
- Executes Steps 2–5 for its ONE phase verbatim: Codex launch, watcher + wakeup budget, gate-verifier lanes (fresh per phase, SendMessage reuse for fix re-checks), fix/continuation routing through `helpers.py`, root-tier diff spot-reads, seal write, phase acceptance, and the phase commit. Every root invariant binds to the lane for its phase — it spot-reads the diff, owns the verdict, never self-certifies takeover bytes, logs evidence per round in `LOG_FILE`.
- Returns ≤10 lines, nothing else: `PHASE <n>: ACCEPTED <commit-hash>` or `HALT: <reason>`; rounds used (build/fix/continuation/takeover); PEAK/PCT telemetry; seal state; exact proof command + counts. Detail lives in `LOG_FILE`, not the return value.
- Never asks the user anything: a decision the work order cannot answer = `HALT: needs-human — <the question>`, surfaced by the conductor.
- Lanes are strictly sequential — never two alive at once (single-writer rule). A new phase is a NEW lane; never SendMessage a finished phase's lane back to life for new work (fix re-checks WITHIN the phase use the lane's own verifier, not a resurrected lane).
- First-run note: if background-task notifications prove unreliable inside a lane's loop, the lane's armed watcher/Monitor is the fallback wait mechanism (same six-signal corroboration); the conductor's involvement never grows beyond the completion notification.

## Prerequisites (verify once, fast)

- `codex --version` ≥ 0.130. `codex login` done (ChatGPT account or API key both fine). Auth/model error → surface it, don't silently retry.
- **Echo the active build model at kickoff** so the user can confirm: state `BUILD_MODEL` + `BUILD_EFFORT` + `SANDBOX` before launching. If the user objects, stop.
- **Codex has a native image-generation tool** in `codex exec` sessions (ChatGPT-account backed, no API key). Specs may include "generate these image assets yourself" steps — name exact paths, dimensions, style in the contract.
- Run from the target repo's root (`exec` and `resume` then need no `-C`; `resume` doesn't support `-C` anyway).

## Tunables (read from args, else default)

| Var | Default | Meaning |
|-----|---------|---------|
| `SPEC_FILE` | `PLAN.md` | The frozen spec Codex implements. |
| `BUILD_MODEL` / `BUILD_EFFORT` | `gpt-5.6-luna` / `xhigh` | See Models. Fix ladder is fixed: `xhigh` → `xhigh` → takeover. `max` only on an explicit per-round user instruction. |
| `SANDBOX` | `danger-full-access` | Codex write sandbox. |
| `MAX_FIX_ROUNDS` | `2` (fixed) | Not tunable — the ladder defines exactly two fix rounds, both at `xhigh`; then Claude takes over and finishes directly. |
| `LOG_FILE` | `PLAN-REVIEW-LOG.md` | Append-only build transcript. If it exists (a grill/review ran), append `## Act 3 — Build`; else create it. |
| `PROOF_CMD` | from spec | Exact broad test/verify command that counts as phase-acceptance proof. If the spec lacks one, ask the user ONE question to get it before launching. |
| `GATES_FILE` | `.claudex-gates.json` | Deterministic gate manifest: `[{"name","cmd","timeout_s"?,"stage"?}]`, `stage` ∈ `round`/`accept` (omitted = both stages). Missing → `verify.py` derives a single accept-stage gate from `PROOF_CMD`. |
| `SEAL_MODE` | `shadow` | Acceptance fast-path mode. `shadow`: seal written and checked, result LOGGED, final verifier still runs — collects the go/no-go datum. `enforce`: `SEAL: INTACT` skips the fresh final verifier. Flip to `enforce` only after ≥1 full shadow build logs zero final-verifier findings in hash-unchanged files. |

Echo resolved values before starting.

## Step 0 — Gates (before any Codex launch)

1. **Spec gate.** `SPEC_FILE` must exist and read as a work order (goal, concrete steps, bounds). No spec → offer `/claudex-grill` (interview first) or `/claudex-review` (have a plan, want it stress-tested). If the user insists on building from a rough idea, write the spec WITH them first — that is design, and design stays with Claude.
2. **Clean-tree gate.** `git status -sb`. One exception: if the ONLY dirty paths are plan artifacts handed over by a just-finished grill/review — `SPEC_FILE`, `LOG_FILE`, and Act-1 doc updates (`CONTEXT.md`, `CONTEXT-MAP.md`, `docs/adr/`) — commit them yourself as `docs: plan checkpoint — <task>` and proceed — but ONLY if those paths were clean when the grill/review started (the wrapper snapshots `git status -sb` at its kickoff); pre-existing dirt in them may be the user's own edits: stop and ask (the automatic handoff must not stall on its own artifacts). Any other dirt → STOP and ask the user to commit or stash. Non-negotiable: Codex writes with full access, and a dirty tree means its diff can't be isolated or cleanly reverted.
3. **Baseline:** `BASE_HEAD=$(git rev-parse HEAD)` — recorded in `LOG_FILE`. Every review below diffs against it, and HEAD moving off it mid-round is a hard failure. Also pin the governing protocol bytes: append the output of `python3 ~/.claude/skills/claudex-build/helpers.py sha` to `LOG_FILE` (audits can then tell exactly which skill+helper version ran).
   Resolve the gate manifest now: `GATES_FILE` (default `.claudex-gates.json`) present → echo its gate names into `LOG_FILE`; absent → `verify.py` derives a single accept-stage gate from `PROOF_CMD` — log that fallback. No manifest AND no `PROOF_CMD` is a Step-0 stop (the gates runner fails closed, exit 2).
4. Confirm scope in one line, then go. **This is the only human gate in this skill** — after it, the phase loop (build → verify → fix → commit → next phase) runs unattended until the final report.

## Step 1 — The build prompt (contract, via temp file)

Never inline-quote the prompt — write it to a temp file. Fill this contract completely; when chained from a grill/review skill, derive it from the plan's sections. The DELIVERABLES checklist is the under-delivery guard: on a real build, a phase whose "done" was implicit shipped partial wiring three rounds running — an enumerated checklist with a per-item self-report ends that.

```bash
P=$(mktemp)
cat >"$P" <<'EOF'
EXECUTION_MODE: delegated-writer-v1
OUTER_ORCHESTRATOR: claudex-build
OUTER_PLAN_REVIEW: complete
OUTER_INDEPENDENT_VERIFIER: Claude
INNER_ROLE: implementation-writer

GOAL: <one paragraph — what done looks like>
SPEC: Read ONLY the section of <SPEC_FILE> for this phase (name the heading
or line range) plus its global constraints section. Do not read the whole
plan history. The spec is frozen and already reviewed. Implement it exactly.
If a step is impossible as written, implement the closest faithful version
and report the deviation — do not redesign.
DELIVERABLES (the definition of done — every item, no partial credit):
  1. <concrete artifact/behavior — e.g. "X wired into Y at activation">
  2. <…one line per item, exhaustive; derive from the spec's steps>
KEY PATHS: <files/dirs Codex will touch or must read first>
CONSTRAINTS: <"don't touch X", style rules, deps that must not change>
NON-GOALS: <explicitly out of scope — from the plan's Out of scope section>
GIT: Do NOT run git commit, push, tag, stash, rebase, or checkout — do not
move HEAD or any ref. Leave ALL changes uncommitted in the working tree.
Committing is the reviewer's job, not yours.
CHECKS: Run the focused tests for the modules you changed (new/RED-GREEN
tests for new behavior). Do NOT run the full suite — the reviewer runs the
broad proof at acceptance.
WRITER MODE: Follow only Delegated writer mode in
~/.agents/skills/codex-subagent-driven-development/SKILL.md. The outer
Claude workflow already owns planning challenge, independent verification,
broad proof, acceptance, Gate 5, and commit. Do not spawn subagents, invoke
another Codex process, re-plan, independently accept, run broad proof, or
commit. Record a non-destructive baseline; map every deliverable to a
public-behavior check; new behavior gets focused RED for the intended
reason, then minimum GREEN; run focused checks and writer self-verification;
log any documented exception explicitly.
OUTPUT: End with a report — for EACH numbered deliverable, one line
`<n>. DONE — <file:evidence>` or `<n>. NOT-DONE — <why>`; then files changed
(one line each: path + what/why); then for each check: the command, exit
code, pass/fail counts, and duration — include full output ONLY for
failures; then any deviations from the spec with reasons. A deliverable
without evidence counts as NOT-DONE. End with `SUBAGENTS_SPAWNED: 0`.
EOF
```

## Step 2 — Launch Codex (fresh session, capture SID)

```bash
OUT=$(mktemp /tmp/claudex-build.XXXXXX); STREAM=$(mktemp /tmp/claudex-stream.XXXXXX); ERR=$(mktemp /tmp/claudex-err.XXXXXX)
codex exec --disable multi_agent -m "$BUILD_MODEL" -c model_reasoning_effort="$BUILD_EFFORT" \
  -c sandbox_mode="$SANDBOX" -c approval_policy="never" \
  --json -o "$OUT" - <"$P" 2>"$ERR" | tee "$STREAM" | grep '"type":"thread.started"'; RC=${PIPESTATUS[0]}
```

- Parse `thread_id` from the `thread.started` line → `SID`; stamp `SID: <thread_id>` under the round header in `LOG_FILE` (cross-references the session rollouts for later token audits). Codex's report lands in `$OUT`.
- **Success = `RC` 0 + non-empty `$OUT` + a `thread.started` line.** Anything else → failed run — show the tail of `$ERR`, stop, tell the user.
- **Heads-up on completion (required):** when a background Codex run finishes, the FIRST line of your next message must be a loud standalone banner — `🔔 CODEX FINISHED — <what> (exit ok/fail) — verifying now` — BEFORE any verification output. The user is not watching tool calls.

## Step 3 — Verify (Claude owns the verdict; lanes do the legwork)

Codex's report is advisory. Judgment is never delegated — verification legwork always is: a gate-disciplined verifier subagent returns compressed, structured evidence so root context stays lean across phases (inline collection is what forces compactions on long runs; measured on a real run, verification evidence also silently degraded to solo diff reads when it wasn't a subagent's explicit job).

1. **HEAD gate first (inline, before spawning anything):** `git rev-parse HEAD` must equal `BASE_HEAD` (for the current phase). Moved → Codex violated the GIT clause: hard-stop the round, inspect `git reflog`, restore, and treat it as a failed round.
   Then **gates, deterministically, zero model tokens:** `python3 ~/.claude/skills/claudex-build/verify.py gates --base "$BASE_HEAD" --stage round` (Bash, timeout 600000). It runs every `GATES_FILE` gate for the stage plus the gate-gaming scan (`.only`/`.skip`/lint- and type-silencing/test-file deletions in the diff), writes `verdict.json` + per-gate logs under `$(git rev-parse --git-dir)/claudex-verify/` (inside `.git` — never tracked, invisible to the clean-tree gates), and prints `GATES: GREEN|RED warn=<n>`. A RED gate's log tail is the interpretation input — a model reads the excerpt, it never re-witnesses the run.
2. **Phase verifier — ONE fresh read-only subagent (`general-purpose`, model `opus`), spawned per phase (single-writer intact; the only writer exception is the fixup lane in Step 4C, which runs alone, after the verdict).** Escalate to `fable` when any trigger holds: high-risk domain (auth, schema, concurrency, migrations, payments); the `opus` verdict returns inconclusive or self-contradictory; or verifier and root disagree on a CRITICAL. Mission input: the phase's spec slice, Codex's report verbatim, `BASE_HEAD`, and an **explicit file list** — the diff's files plus named callers — with the bound stated in the mission: verify within the listed files and their direct callers, no repo-wide exploration, target ≤30 tool calls, and report the actual count in the Gate-5 report. The mission instructs it to invoke the `fable-method` skill and work Gates 1–5:
   - deliverables audit — per-item DONE/NOT-DONE vs the diff, file:line evidence for every DONE claim;
   - the gate verdict consumed, not re-derived — mission input includes the `verdict.json` path; manifest gates are settled facts and the verifier is FORBIDDEN from re-running them (re-witnessing was measured at 321 subagent Bash calls in one run). Every `warn` entry must be explicitly adjudicated (gamed vs benign) in its report;
   - focused tests it devises for the changed area (not manifest gates) — exact command, exit code, pass/fail counts, failing names, raw tail on failure;
   - impact walk — changed symbols → callers (symbol tools), affected-test locations, `git status -sb` + untracked via `git ls-files --others --exclude-standard`, each new file read;
   - **candidate** findings with file:line;
   - a Gate-5 report — result first, **verified separated from assumed**, exact evidence cited, material risks plain, ending `VERDICT: ACCEPT` or `VERDICT: REVISE` with reasons.
   **Fix rounds re-use the SAME verifier via SendMessage** (fix diff + its own prior findings — its context is the asset); spawn a replacement only if it drifts or bloats. **A fresh verifier spawn for a fix-round or delta re-check is a logged policy violation**, same class as an off-ladder effort — measured: three fresh `opus` verifiers on one phase cold-read 2–7M cache tokens EACH re-deriving context the first one already held. The fresh spawn is reserved for Step 5's final verifier, where killing anchoring is the point.
3. **Root judges on the verifier's report — the report is input, never the decision.** Root spot-reads `git diff HEAD` where the stakes concentrate: the spec-fidelity core of the phase, everything the verifier flagged, anything in a high-risk domain — never trusting the report alone (the Fable acceptance rule). Confirm or reject every candidate finding. Evidence-free DONE is a **defect**; a NOT-DONE is **not** — it routes to continuation (Step 4B). Reviewer-scale trivia is neither — route it to a fixup lane (Step 4C); it never burns a Codex fix round. Root also restates the HEAD gate itself, with hashes, in the log — `BASE_HEAD <hash> == HEAD <hash>, checked by root` — Codex's self-report never counts. Verdict, severities, and the defect list are root's alone. On an ACCEPT verdict root immediately snapshots what was accepted: `python3 ~/.claude/skills/claudex-build/verify.py seal write --base "$BASE_HEAD"` — the seal (per-file blob hashes + verdict digest + open-warn count) is what Step 5 diffs against; any bytes written after it (fixups, takeover, hooks) surface there as `DELTA`.
4. **Proof ladder:** after a fix round, SendMessage the phase verifier for a scoped re-check of exactly the fix diff (Gates 2/4 on the delta). The broad `PROOF_CMD` is an accept-stage gate in `GATES_FILE` and runs once, at **phase acceptance** (Step 5), via `verify.py gates --stage accept` — no lane, no model witness; the contract is objective: exit code + failing names + raw tail on failure, and non-zero exit = not accepted, no interpretation. **Log the exact command string with the counts** (drifting proof commands make runs unauditable). A failing proof is never waved off as flake until the failing test's NAME is captured and logged — rerun only after it's named. Codex's pasted output never counts as proof.
5. Append to `LOG_FILE` under `## Act 3 — Build`: `### Round <n> — Codex build (BUILD_MODEL/effort)` + SID + the telemetry line + **the verifier's Gate-5 report (verbatim or tightly condensed, its VERDICT line intact — it IS the round's evidence body)** + `### Claude's verdict` with root's hash-restated HEAD gate and per-finding dispositions. Every round logs these or says explicitly why one is absent — a verdict entry with no evidence body is itself a protocol violation (measured: 7 of 8 later-phase verify steps on a real run recorded no evidence trail).

## Step 4 — Fix loop (bounded, no escalation) vs continuation (fresh) vs fixups (lanes)

Four follow-up states — route each finding to exactly one:

- **Defect in completed work** → FIX round (A).
- **NOT-DONE deliverable** → continuation (B) — unfinished work is not a defect; pushing it into a fix round is how real runs ended up burning top-tier fix prompts on leftovers.
- **Next phase / work package** → fresh session (B).
- **Reviewer-scale trivia** → fixup lane (C) — never a Codex round.

**A. FIX round** — route the mechanics through the helper: `python3 ~/.claude/skills/claudex-build/helpers.py route fix <round#>` → `EFFORT=… MODE=fresh`, or `TAKEOVER` when rounds are exhausted. **The helper's output is binding** — both fix rounds run at `xhigh` (no escalation; the tier was never the lever — see Models), and `MODE` is always `fresh`. Real runs broke the prose ladder under context pressure (resuming past an 89% peak, continuations miscounted as fix rounds) — the helper exists so a route it didn't emit is a logged policy violation, not an option.

**A fix round launches a NEW session (Step 2's command), never a resume.** Write the fix list to a temp file (`$P2`) as a **standalone work order** — the session receiving it has no memory of the build, so everything it needs is in this file or nowhere:

- begin with the exact delegated-writer receipt block from Step 1, including the standalone `EXECUTION_MODE: delegated-writer-v1` line; missing or malformed receipt is a protocol error — do not launch, or stop and relaunch with a complete receipt;
- every defect: exact file:line, what is wrong, and the expected corrected behavior — never "the issue we discussed" or "your earlier approach";
- the **GIT clause, CONSTRAINTS, and NON-GOALS verbatim** from the build prompt (not summarized — a fresh builder has never seen them);
- KEY PATHS it must read first, including the files it wrote in the round being corrected;
- the per-defect check that proves the fix, and the instruction to report a diff size per item so scope creep is visible;
- a scope clause: fix exactly these items, report-don't-fix anything else discovered.

Counts against `MAX_FIX_ROUNDS`. Capture the new `SID` and log `SID(prev) → SID(fix<n>)`.

```bash
OUT=$(mktemp /tmp/claudex-build.XXXXXX); STREAM=$(mktemp /tmp/claudex-stream.XXXXXX); ERR=$(mktemp /tmp/claudex-err.XXXXXX)
codex exec --disable multi_agent -m "$BUILD_MODEL" -c model_reasoning_effort="$FIX_EFFORT" \
  -c sandbox_mode="$SANDBOX" -c approval_policy="never" \
  --json -o "$OUT" - <"$P2" 2>"$ERR" | tee "$STREAM" | grep '"type":"thread.started"'; RC=${PIPESTATUS[0]}
```

**Freshness changes the vehicle, not the budget** — a fix round costs one of the two `MAX_FIX_ROUNDS` regardless. And it does not change the effort: both fix rounds run `xhigh` in their own new sessions.

**B. CONTINUATION** — remaining NOT-DONE deliverables or the next phase. Route check first: `python3 ~/.claude/skills/claudex-build/helpers.py route continuation <n>` → `EFFORT=base MODE=fresh` (base = `BUILD_EFFORT`), or `TAKEOVER` past the cap — binding, same as fix routing: a continuation NEVER resumes, never runs at fix-ladder effort, and never counts as a fix round. Launch a **fresh session** (Step 2) at base `BUILD_EFFORT`. Its work order must begin with the exact delegated-writer receipt block from Step 1; missing or malformed receipt is a protocol error — do not launch, or stop and relaunch with a complete receipt. The remaining work order is distilled, not cumulative: the immutable global contract (CONSTRAINTS/NON-GOALS/GIT, ~10 lines) + the current phase slice of the spec + one line per already-done phase — never the full spec history or prior phases' details. Include the current phase's DONE/NOT-DONE ledger — the uncommitted diff already contains the DONE items; say so, so they are not redone. Does not count as a fix round. Never mix continuation work into a fix prompt. **Continuation cap:** at most 2 continuations per phase, and a continuation that completes zero new deliverables ends delegation — Claude takes over the remainder (this bounds the NOT-DONE loop).

**C. REVIEWER FIXUPS (delegated legwork)** — mechanical, localized findings with zero design judgment: lint/format violations, missing JSDoc, unused imports/vars, typos, guard clauses ≤ ~10 lines in one file. Anything touching behavior, API shape, or more than one file of logic is a DEFECT → route A, never here.

- **Threshold:** fewer than ~3 items or < ~10 total lines → root fixes directly, no lane (delegation overhead loses — same logic as the ~20-line rule). Above that, delegate.
- **Model:** `haiku` when every item states the exact edit (file:line + required change); `sonnet` when an item needs local reading to write (e.g. a JSDoc line describing the symbol). One lane, one message — the fixup lane is THE writer while it runs; no verifier or other lane, no root edit concurrently.
- **Contract:** the prompt is an exact fix list — per item: file:line, the problem, the expected change, and the per-item check (e.g. the lint rule that must go quiet). Touch ONLY listed files. Return a per-file diff summary + check output.
- **Budget (binding): ≤20 tool calls for the whole lane, one focused check per item.** The per-item check named in the fix list is the ONLY verification a fixup lane runs — no mutation testing, no RED-GREEN ceremony, no new test scaffolding beyond a check the list itself names, no full-suite runs (the accept-stage gates re-prove the phase anyway). An item that turns out to need a new test file, design thought, or more than one file of logic → return it `OUT-OF-SCOPE` untouched; root re-routes it (fix round or root-direct). The lane reports its tool-call count; exceeding the budget is a logged policy violation. Measured: a "3 MINORs" lane ran 91 calls / 96K output tokens doing unrequested TDD-and-mutation ceremony — the largest single agent in its entire run.
- **Safety snapshot:** `git diff HEAD > $(mktemp)` before launching — the tree carries Codex's uncommitted work, so a misbehaving lane cannot be blanket-reverted. Out-of-bounds output → restore touched files from the snapshot, root fixes directly.
- **Root re-review:** lane claims are advisory like Codex's — root re-reads the lane's diff and re-runs the focused check before Step 5. Log in `LOG_FILE` as `reviewer fixups (delegated: <model>)` + the item list.
- Fixups never count against `MAX_FIX_ROUNDS` and never carry NOT-DONE work.

Re-verify (Step 3) after each round. After `MAX_FIX_ROUNDS` fix rounds with defects still open: **Claude takes over** — fix the remainder directly and log the takeover. Takeover edits are behavior root wrote, and root never self-certifies (the Fable root-as-writer rule): the mandatory **final pre-commit verifier (Step 5.2)** receives the takeover diff explicitly flagged, and the phase cannot commit on root's own proofs alone. Then proceed to Step 5 as normal. Ping-ponging trivia through delegation burns more than it saves.

## Step 5 — Phase acceptance & auto-commit (no human gate)

Acceptance sequence, in order:

1. **Finish the log first:** write the phase's remaining `LOG_FILE` entries now, BEFORE committing — the log rides in the phase commit. After the commit, do not touch tracked files until the next phase starts.
2. **Gates, then seal, then only as much verifier as the delta earns.**
   a. `verify.py gates --base "$BASE_HEAD" --stage accept` — the manifest includes `PROOF_CMD`, so this IS the broad proof. RED → each failure is a **defect**: name it from the gate log, route through the fix ladder if rounds remain, else Claude-takeover; re-run to green (naming every failure first — no unnamed flakes), no model re-witnessing. Gate runs can mutate files (snapshots, lockfiles) — re-check `git status -sb` and review anything new before proceeding.
   b. `verify.py seal check --base "$BASE_HEAD"` routes the pre-commit review:
      - **`SEAL: INTACT`** — nothing changed since the round verifier's accepted review. `SEAL_MODE=enforce`: skip the fresh final verifier and go to commit — the sealed round verdict is the pre-commit evidence. `SEAL_MODE=shadow` (default): run the full final verifier (c) anyway and log `SHADOW: findings in hash-unchanged files = <n>` — that number is the go/no-go for flipping to `enforce`.
      - **`SEAL: DELTA <files>`** — re-review scope is exactly the listed files **plus their callers** (impact walk — byte-identity never certifies a dependent). SendMessage the phase verifier for the scoped delta (its context is the asset); if it is gone, a fresh `sonnet` verifier takes the delta — a hash-scoped re-read is Builder-shaped work. EXCEPTION: takeover and hook-fix bytes always land here and always get verifier eyes at `opus` (`fable` on the Step-3 triggers) — root never self-certifies, seal or no seal.
      - **`SEAL: MALFORMED` or `SEALED-RED`** — fail closed: full final verifier (c), exactly as before the seal existed.
   c. **Full final verifier (shadow mode, MALFORMED, or Step-3 escalation triggers):** a **fresh** read-only subagent (`general-purpose`, model `opus`; `fable` on the Step-3 triggers), NEVER the round verifier reused (the fresh spawn exists to kill anchoring). Input: the phase's spec slice, every round's findings + dispositions, the takeover diff if any (explicitly flagged), the `verdict.json` path (gates are settled facts — it must not re-run them), and the final `git diff HEAD`. It runs **Gates 4–5 only** — independently verify the final bytes at their actual layer, sample normal + edge cases, report verified-vs-assumed — ending `VERDICT: OK` or `VERDICT: FINDINGS <list>`. FINDINGS → root fixes directly, SendMessage the same final verifier for ONE re-check; a finding still open after that is a defect — resolve it or abort the phase per Step 4; never commit past an unresolved CRITICAL. Root fixes here change bytes → the seal shows DELTA: re-run 2a + 2b before commit.
3. **Commit (Claude, never Codex):** stage the phase's changes + `LOG_FILE`, commit as `<type>: <description>` (house format, no attribution). Keep the hash in orchestrator state for the final report — never append it to a tracked file post-commit (that leaves the next phase starting dirty and the last hash forever uncommitted).
4. **Post-commit gate:** `git status -sb` must be clean and `git rev-parse HEAD` must have advanced past `BASE_HEAD`. Any bytes changed after the proof — formatter mutations or hook-driven fixes (defects: fix ladder if rounds remain, else Claude fixes directly) — go back through the Step 3 change review and a green Step 5.2 proof before ONE retry commit; what lands must be exactly what was reviewed and proved. Hooks still failing or mutating after that cycle → abort the remaining phases and produce the final report early with the exact state — an unattended run ends with a report, never a mid-run question.
5. Re-capture `BASE_HEAD=$(git rev-parse HEAD)`. **Classic in-root mode:** run `/compact` now, before launching the next phase — proactive, cheaper than an uncontrolled mid-phase auto-compact; `LOG_FILE` + the committed tree are the state, so nothing is lost. (Phase-lane mode needs no extra compact here — each lane already dies at its phase commit, which is the same reset.) Then launch the next phase fresh (Step 2) — or, after the last phase, produce the **final report**: per-phase table (rounds, fix rounds, takeovers, commit hash, PEAK/PCT), deliverables ledger, proof output tail, spec deviations.

**Pushes, releases, and GitHub mutations remain user-driven** — never push; the pre-push security review still applies when the user pushes.

## Hard rules

- Clean tree before launch (plan-checkpoint exception only); `BASE_HEAD` recorded; HEAD unchanged after every Codex round; tree clean again after every phase commit.
- The work order always carries the GIT clause (no commit/push/tag/HEAD moves) and the DELIVERABLES checklist; every report is audited item-by-item.
- Claude never skips the change review — `git diff HEAD` + untracked enumeration, every round. Codex claims are advisory until Claude has read the changes and (at acceptance) run the broad proof itself.
- Fix ladder: `xhigh` → `xhigh` → Claude takes over. **No escalation — a rejected round is a spec failure, not an effort failure (measured: `max` burned 76% more turns on the same task and was rejected on 7 findings).** `max` only on an explicit per-round user instruction, logged. Fresh-fix fallback keeps the same effort and budget.
- NOT-DONE work routes to a fresh continuation, never into a fix round; max 2 continuations per phase, and a zero-progress continuation → takeover.
- Reviewer fixups: mechanical-only, one writer lane at a time, snapshot before launch, root re-reads the diff — design-touching findings go to the Codex ladder, never the fixup lane. Lane budget ≤20 tool calls, per-item named checks only; anything bigger comes back `OUT-OF-SCOPE`.
- Background-run wakeup budget: ≤3 main-loop wakeups per round (exit notification, one watcher alert, one corroboration pass); the armed watcher is the only watcher — no main-loop polling between notifications.
- Batch independent orchestrator tool calls (reads, greps, status checks, log appends) into a single message — the round-trip context is the cost unit, not the tool call. Measured on a real run: 93% of tool-calling messages carried exactly one call ≈ ~100M avoidable cache-read tokens.
- Phase-lane mode is the default for ≥2 phases: conductor spawns one fresh `opus` lane per phase; the lane is the acting phase-root and every root invariant binds to it; lanes run strictly sequentially; the conductor audits (commit hash, log evidence, seal, clean tree — ≤5 batched calls) and never accepts a phase on the lane's claim without that audit; audit mismatch = HALT, never the next lane. `AskUserQuestion` is conductor-only — lanes return `HALT: needs-human` instead.
- The orchestrator does NOT stop at phase boundaries. Compaction is not a halt condition — a compacted session resumes from `LOG_FILE` + the committed tree and launches the next phase. The run ends only when every phase is committed, or on a HALT. Keep `LOG_FILE` current at each phase commit; that is what makes running through a compact safe.
- Phase verification runs through the fable-method gate verifier (`opus`; `fable` on defined triggers): fresh per phase, SAME one re-used via SendMessage for fix rounds and delta re-checks. Pre-commit routes through the seal: INTACT commits on the sealed round verdict in `enforce` mode (shadow mode still runs the final verifier and logs the comparison); DELTA earns a scoped delta review; MALFORMED or takeover bytes earn the full fresh final verifier — fail closed. Root spot-reads the diff and owns the verdict — a verifier report alone never accepts a phase.
- Deterministic gates run ONLY through `verify.py gates` — no model witnesses a gate run, no verifier re-runs a green manifest gate, RED is interpreted from the gate log tail. `verdict.json` and `seal.json` are machine-written; hand-editing them is a protocol violation. Every warn entry is adjudicated by name before acceptance.
- Claude-as-writer never self-certifies: takeover and hook-fix edits are flagged to the final verifier; the phase never commits on root's own proofs alone.
- Log discipline is binding: per round — SID, telemetry line, evidence body (verifier report), root's hash-restated HEAD gate, exact proof command string; a proof failure is named before any rerun.
- **Every round is a fresh Codex session — build, fix, and continuation.** Nothing in the round loop resumes; resume exists only to continue a single interrupted round. Every prompt is therefore a self-contained work order, and `SID(prev) → SID(new)` is logged each round.
- Commits: Claude-side only, automatic at phase acceptance, only on green broad proof, hashes kept out of tracked files. Codex never commits. Pushes are user-driven only.
- `LOG_FILE` is the deliverable — with a preceding grill/review it tells the whole story: grilled → reviewed → built → verified → committed.

## What NOT to do

- Don't build without a spec — that is designing by delegation, and it fails. Route to `/claudex-grill` or `/claudex-review` first.
- Don't use for ~<20-line single-obvious-change edits — just make the edit.
- Don't spawn a fixup lane for 1–2 trivial items — fix them inline; and don't smuggle behavior changes into a fixup list.
- Don't resume with `--last` — capture and use the explicit `SID` (parallel sessions make `--last` grab the wrong thread). Echo the id into the command visibly before running: a missing/garbage id can silently fall back to the most recent session instead of erroring — a wrong-target resume looks exactly like a successful one.
- Don't resume a session because it "keeps context" — not for new work, and not for fix rounds either. Measured result: quality degrades and rounds multiply; a resumed builder also drifts back toward the design the review just rejected. Distill and go fresh, every time.
- Don't write a fix prompt that references the conversation ("your earlier approach", "the issue we discussed", "as noted above"). The session reading it is new and has never seen any of that — such a prompt is a broken work order, not a terse one.
- Don't judge a session by its last token event — compaction makes it lie; use the peak line's `NONRESUMABLE` flag.
- Don't poll a background codex run from the main loop — no rollout `ls`/`grep` between notifications, no extra probe tasks; the armed watcher is the only watcher (wakeup budget: ≤3 per round).
- Don't hand a fixup lane anything that needs a new test file or design thought, and don't let it "improve" beyond the list — ≤20 tool calls, named checks only, everything else returns `OUT-OF-SCOPE` to root.
- Don't parse the JSONL stream for the report — read the `-o` file.
- Don't reuse fixed `-o`/stream/err paths across rounds — `mktemp` every time; success needs `RC` 0 AND non-empty `$OUT` (existence proves nothing).
- Don't append the fresh commit's hash to tracked files — orchestrator state + final report only.
- Don't let any model re-run a green manifest gate — the verdict file is the fact; re-witnessing is the measured 321-Bash-call tax this design exists to kill. RED is interpreted from the gate log tail only.
- Don't flip `SEAL_MODE=enforce` without at least one full shadow build logging zero final-verifier findings in hash-unchanged files — and drop back to `shadow` after any protocol change (the Step-0 SHA lines tell you when the protocol changed).
- Don't let Codex commit — and don't push, tag, or touch remotes yourself; commits stay local, pushes belong to the user.
