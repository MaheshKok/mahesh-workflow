---
name: harness-sync
description: Audit and repair the agent tooling stack — MCP servers, plugins, skills, hooks — for Claude Code CLI, Claude Code Desktop, Codex, and Hermes. Use when the user asks "is X mcp available / initialized / indexed", "why didnt you use serena", "install this plugin everywhere", or when hooks/gates misbehave.
---

# Harness Sync

The user runs four agent environments (Claude Code CLI, Claude Code Desktop,
Codex CLI/Desktop, Hermes) sharing one tool stack: serena, codebase-memory,
lean-ctx, caveman, ponytail, claude-mem, plus per-repo skills. Config drift
between them is a recurring time sink.

## Config locations

- Claude Code: `~/.claude/settings.json` (hooks, permissions, plugins),
  `~/.claude/skills/`, `~/.claude/CLAUDE.md`, per-repo `.claude/`.
- MCP registrations: `claude mcp list` (CLI), Claude Desktop config for
  desktop, `~/.codex/` for Codex, `~/.hermes/` for Hermes.
- lean-ctx: `~/.local/share/lean-ctx/config.toml` (shell allowlist, path
  jail). Needs client restart after edits.
- codebase-memory: index per repo with ABSOLUTE path, never `.`.

## Audit procedure

1. Enumerate what the CURRENT session actually exposes (tool list /
   ToolSearch), not what config files claim. A registered server that is not
   exposed is the most common failure.
2. For codebase-memory: `list_projects` + `index_status` for the current
   repo; re-index if missing or stale.
3. For serena: confirm the project is activated and `initial_instructions`
   ran.
4. Check hook health: a PreToolUse gate that references a tool name not
   present in the session (for example a plugin-namespaced name when the
   plain server is loaded) will deadlock the session. Verify every matcher
   in `settings.json` hooks against real tool names.
5. Report a table: component, expected, actual, fix.

## Rules

- Distinguish "not configured" from "not exposed in this session" — do not
  claim misconfiguration until a fresh client check also fails.
- Config edits for other environments (Codex, Hermes, Desktop) require the
  app to be quit first when it holds the file; say so before editing.
- After any fix, verify by re-running the failing operation, not by re-reading
  the config.
