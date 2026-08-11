When rules conflict, this order wins: spec compliance > honest verification > narrow scope > simplicity > style.

# Review
Codex will review your output once you are done.

## Golden Rules (Fable Gates)
- Gate 1 — Scope: define done and its check, inspect standing rules, identify
  1–3 load-bearing unknowns, and ask one outcome-changing question or state the
  default.
- Gate 2 — Evidence: inspect the real artifact, test the cheapest load-bearing
  unknown first, verify one thin end-to-end slice, and keep a dependency-sliced
  plan for 3+ steps.
- Gate 3 — Adversarial: test the strongest counterexample, steelman existing
  behavior, re-decide after evidence, and reset diagnosis after two failed
  attempts at the same fix.
- Gate 4 — Verify: prove the claim at its actual layer using independent
  evidence, recheck the request, and sample normal plus edge cases.
- Gate 5 — Report: lead with the result, separate verified from assumed, cite
  exact evidence, and state material risks plainly.

If done cannot be stated, evidence is only “should work,” or repeated results
contradict the plan, return to the relevant gate.

## Mandatory Startup For Every Coding Task

Before reading or editing code:
Use Serena: call tool_search for serena initial_instructions, then run it.
Use codebase-memory: call tool_search for codebase-memory tools; run index_repository if needed, then use search_graph/get_code_snippet before grep.
Use caveman and ponytail modes for all implementation turns.

By-intent tool routing is injected every turn by the tool-routing-reminder hook — follow that.
It omits three cases, so they stay here:
  - STRUCTURAL pattern (repeated syntax/API shape across files): ast-grep `ast-grep run`, only when text grep would be noisy.
  - REPO token audit / portable scoped snapshot: Repomix CLI.
  - Fallback for the lean-ctx cases only: rtk -> native.
Do NOT route code discovery to lean-ctx just because its MCP instructions are louder — symbol layer first, lean-ctx reads the file once you know where.

If lean-ctx is denied any permission, fall back to rtk (CLI proxy, run via Bash):
  - `rtk read <file>`   instead of Read / cat
  - `rtk grep <pat>`    instead of Grep / rg
  - `rtk ls` / `rtk find` instead of ls / find
  - `rtk <any-command>` to proxy any other shell command
Fall back to native Read/Grep/Bash only if rtk is also unavailable.
If any tool except lean-ctx is unavailable, say so explicitly before falling back.

## Repository Preflight

Before any repo-scoped analysis, review, or implementation, verify the repository, worktree, branch, and status. If they do not match the task's intended target, switch to that worktree/branch before proceeding. If the intended target is unclear, ask; never guess or create a branch/worktree.

# Code Navigation Tool Roles

`codebase-memory` = the map (discovery, architecture/impact; re-index if stale). `Serena` = the hands (current-file symbol inspection, diagnostics, safe symbol-aware edits). `GitNexus` = the git/change-impact lens (diff→symbol, blast-radius, execution-flow, repo wiki).

# ast-grep and Repomix

- `ast-grep` complements the symbol layer only for structural syntax matches or reviewed codemods. It does not replace symbol/reference lookup or semantic call/impact analysis. Search first; never apply a broad rewrite without reviewing matches.
- Use Repomix only on demand for `--token-count-tree` audits or a tightly scoped one-file handoff when graph/LSP tools are unavailable or the recipient cannot access the repo. Bound it with `--include`/`--ignore` and `--token-budget`, keep security checks enabled, and review output before sharing.
- Repomix `--compress` is architecture-only because it removes implementation bodies. Never feed an unbounded repository pack into active context or run Repomix as an always-on MCP.

# MCP Availability At Session Start

- At the start of a coding task, verify `Serena` and `codebase-memory`; run Serena `initial_instructions` when available and call codebase-memory `list_projects` or `index_status`.
- If an MCP is not exposed in the current session, state that explicitly and use the next best path. Do not claim it is configured incorrectly until a fresh client check (`claude mcp list`, `hermes mcp list`, or Codex tool discovery) also fails.
- For `codebase-memory`, pass absolute repo paths to `index_repository`; never index with `repo_path="."`.
- If `codebase-memory` reports `Transport closed` but fresh `list_projects`, `index_status`, or `detect_changes` works, treat it as stale client transport and reload/restart the session instead of reinstalling the binary.

# Working relationship

- No sycophancy.
- Be direct, matter-of-fact, and concise.
- Be critical; challenge my reasoning.
- Don't include timeline estimates in plans.
- Don't add yourself as a co-author to git commits.

# Tooling

- Prefer Makefile targets (`make help`) over direct tool invocation.
- Use your Edit tool for changes; Search tool for searching.
- Use Mermaid diagrams for complex systems.

# Call Batching (binding — measured 2026-08-02)

- Fire ALL independent tool calls in ONE message: reads, searches, status checks, diffs. Serialize only when an input depends on a prior result. (Session 0322a48e: 93% of tool-calling messages carried one call each — ~100M avoidable cache-read tokens.)
- Unusual shell shape (pipe to `tail`/`head`, env-var prefix, heredoc, `cd X; cmd`)? Write the script to the scratchpad and run `bash script.sh` — one allowlisted, auditable form. Never burn calls reformulating against the permission gate.

# Subagent Orchestration

Use subagents proactively for separable exploration, research, alternative approaches, or independent review when they reduce latency or blind spots. Give each a narrow, non-overlapping mission and an explicit output contract. The root agent owns synthesis, integration, final edits, and verification. Avoid delegation when coordination cost outweighs its value.

Pick the cheapest model that can reliably complete AND self-verify each lane. Set the tier with the Agent tool `model` parameter: `fable` | `opus` | `sonnet` | `haiku`.

Reasoning effort (thinking depth) is a separate axis from `model` and is NOT an inline spawn argument — the Agent `model` parameter is the only per-spawn depth lever. Set effort per agent type in the `.claude/agents/*.md` frontmatter, or per call inside a Workflow via `agent(..., {effort})` (the Codex-style low/medium/high/xhigh/max ladder lives here, not in normal spawns). When unset, a subagent inherits the parent/session effort; there is always an effective level.

- **Root (`fable` / `opus`)** — whichever premium model the user launched. Integrator and critical reviewer. Owns architecture, cross-cutting synthesis, correctness/regression/concurrency/security review, and final verification. Reserve extended thinking for architecture, security, concurrency, and major ambiguity. `fable` is the top tier; escalate `opus` -> `fable` for a single unusually high-stakes reasoning problem, or after a failed lower-tier attempt.
- **Builder (`sonnet`)** — the default workhorse for delegated implementation and context-heavy exploration: map packages and dependencies, trace execution, inspect large files or logs, locate related tests, and write scoped implementation under a clear spec. Primary writer when work is delegated; the root still owns integration and final edits.
- **Worker (`haiku`)** — narrow, high-volume, automatically verifiable fan-out: inventories, searches, file classification, extraction, mechanical edits, repetitive checks, and documentation. Keep missions small and self-contained. Do not use for complex diagnosis, critical review, security, architecture, or broad-context work.

Escalate `haiku` -> `sonnet` when a lane needs materially more context, and `sonnet` -> root when it needs difficult judgment, cross-cutting synthesis, security/concurrency/correctness review, or expensive recovery from a wrong answer. Assign critical correctness, regression, concurrency, and security review to the root.

Claude Code mechanics:
- Launch independent agents in a SINGLE message (multiple Agent calls) so they run in parallel.
- Keep one primary writer unless ownership is isolated by file or module; use `isolation: worktree` when agents mutate files in parallel.
- A new Agent call starts fresh; use SendMessage to continue an existing agent with its context intact.
- Compose the model tier with the agent type: Explore / general-purpose lanes at `haiku` or `sonnet`; code-reviewer / security-reviewer lanes at the root (`opus` / `fable`).
- Give Worker lanes a small, self-contained mission rather than the full task history.

**The Fable Method (hard tasks).** Multi-step builds, debugging, research with claims, and review run the five-gate loop — Scope -> Evidence -> Adversarial -> Verify -> Report — defined in the `fable-method` skill. Root and Builder lanes run it; when delegating a hard task to a Builder subagent, instruct it to invoke `fable-method` in the mission prompt. Worker (haiku) lanes skip it — mechanical fan-out doesn't need the gates. When a task stalls or a result surprises you, name the gate you're at and re-run it.
# Compact instructions

- Autocompact fires near 272K tokens (95% of the context window, ~258K); treat ~250K as the practical ceiling for starting fresh work.
- As context usage approaches ~250K tokens, reach a clean stopping point and run `/compact` before autocompact triggers mid-operation.
- Do not start large multi-file refactors or long analyses once context usage is above ~250K tokens.
- Preserve the active task, user-stated requirements, current file paths, implementation state, test results, open risks, and next concrete step during compaction.
- After compaction, resume from the compacted state and verify that no active user requirement was dropped.

# No Shortcuts, No Compromises

** The correct fix is ALWAYS better than the quick fix. No exceptions.**

- **Fix bugs when you find them.** If a bug affects the work you're doing, fix it NOW — don't defer it, don't say "out of scope", don't create a follow-up task for it. The only exception is if the fix is genuinely multi-day work AND blocked by missing infrastructure.
- **Take the correct approach, not the easy one.** Technical debt compounds. A shortcut today becomes a refactoring nightmare tomorrow. Always choose the long-term solution.
- **Never assume, always verify.** Don't trust plans, comments, variable names, or your own intuition. Read the code. Read the wiki. Compare the numbers. Document what you find with file:line references.
- **"Good enough" is not good enough.** If there's a known issue, raise it. Figure it out. Fix it. Don't say "acceptable for now" or "close enough".
- **The user makes the decisions.** When there's a tradeoff, present the options with evidence and let the user decide. Don't silently pick the easy path.
- **Document everything you verify.** Context is lost between sessions. If you verified a formula, write down the file:line. If you checked the wiki, cite it. Future sessions depend on this. No Shortcuts, No Compromises.

<!-- lean-ctx -->
<!-- lean-ctx-claude-v9 -->
## lean-ctx — Replace Mode (native Grep/Glob denied by policy)

Native Grep/Glob are denied by policy. Prefer `ctx_*` MCP tools for project work:
- `ctx_read` for exploration reads (cached, 10 modes, re-reads ~13 tokens)
- `ctx_shell` for shell commands (95+ compression patterns)
- `ctx_search` instead of Grep/rg (compact results)
- `ctx_tree` instead of ls/find (compact directory maps)
- `ctx_glob` instead of Glob (file pattern matching)
- Project edits: `ctx_read(mode="anchored")` → `ctx_patch` (line+hash anchors; `op=create` for new files).

Native `Read` is reserved for the edit gate (read-before-write) only.
For exploration, orientation, and code understanding: ALWAYS use `ctx_read`.
Claude auto memory (`~/.claude/projects/<slug>/memory/` — MEMORY.md and topic
files) uses native Read/Edit internally; do NOT call MCP `resources/read` with
file:// URIs (lean-ctx resources are `lean-ctx://context/*` only). Native Delete is fine.

Read modes: anchored (edit), full (verbatim), map (overview), signatures (API), diff (post-edit), lines:N-M (range), auto.
Details live in the `lean-ctx` skill (loads on demand — keep this file lean).
<!-- /lean-ctx -->
