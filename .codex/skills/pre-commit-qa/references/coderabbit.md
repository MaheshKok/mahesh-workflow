# CodeRabbit CLI — AI Code Review

CodeRabbit is an AI-powered code review tool that runs locally against git diffs.
Use it as an additional QA gate before pushing, especially for large features.

## Quick Start

```bash
# Install (one-time)
# macOS: brew install coderabbit
# Or: npm install -g coderabbit
# Verify: coderabbit --help

# Authenticate (one-time)
coderabbit auth login
```

## Review Commands

```bash
# Agent mode — structured JSON findings (best for programmatic consumption)
coderabbit review --agent --base main

# Plain-text review of all local changes  
coderabbit review --plain

# Interactive full-screen UI
coderabbit review --interactive

# Show findings from the last review without re-running
coderabbit review findings

# Check installation and readiness
coderabbit doctor
```

## Usage Pattern

1. Complete your changes and pass all local QA (prettier, eslint, typecheck, tests)
2. Run `coderabbit review --agent --base main` for a second pair of AI eyes
3. Review findings and fix any issues
4. Commit and push

## Pitfalls

- **Large diffs time out in foreground mode**: For PRs with 2000+ lines changed,
  run in background with a long timeout (`terminal(background=true, timeout=1800)`)
  or use `coderabbit review --agent --base main &` with process polling.
- **Requires auth**: Run `coderabbit auth login` first. Without auth the CLI exits
  with an error.
- **Can be slow**: The review service processes diffs remotely. Expect 30s-5min
  depending on diff size and service load.
- **--base main vs --base-commit**: Use `--base main` for branch comparisons;
  `--base-commit` for comparing against a specific commit on the same branch.
