# CodeRabbit AI Review Workflow

Run automated AI code review on a feature branch using the CodeRabbit CLI.
This is an optional pre-commit gate — run after the standard QA pipeline
(linters, typecheckers, tests) and before opening a PR.

## When to Use

- After completing a feature branch and before opening a PR
- When the user asks for a code review or mentions CodeRabbit
- After applying review fixes — re-run to verify resolution

## Workflow

### 1. Run the Review

```bash
coderabbit review --agent --base main
```

- `--agent` — emits structured JSON findings for programmatic processing
- `--base main` — compares current branch against main
- For large diffs (>1000 lines), use background mode with a long timeout

The review output is JSON Lines (one JSON object per line):
- `{"type":"review_context",...}` — branch and base info
- `{"type":"status",...}` — progress updates
- `{"type":"finding","severity":"...","fileName":"...","codegenInstructions":"..."}` — findings
- `{"type":"complete","status":"review_completed","findings":N}` — completion

### 2. Process Findings

For each finding:
1. **Verify against current code** — the finding may reference lines that have shifted. Read the actual file at the referenced location.
2. **Categorize**:
   - **Still valid** — the issue exists in current code → fix it
   - **Already fixed** — a prior commit resolved it → skip with brief reason
   - **False positive** — the finding misunderstands the code → skip with brief explanation
3. **Apply fixes** — keep changes minimal and surgical
4. **Run full validation pipeline** after all fixes: prettier → eslint → typecheck → tests → build

### 3. Commit

Structure commit messages for review fixes:
```
fix: resolve CodeRabbit review findings in <area>

- Brief description of each fix
- Keep it scannable with bullet points
```

## Key Options

| Flag | Purpose |
|------|---------|
| `--agent` | Structured JSON output for agents |
| `--base <branch>` | Compare against a base branch |
| `--type all/committed/uncommitted` | Scope of changes to review |
| `--plain` | Plain-text output (non-interactive) |
| `--interactive` | Full-screen terminal UI |

## Pitfalls

- **Large diffs time out**: Use `terminal(background=true, notify_on_complete=true, timeout=1800)` for diffs over 1000 lines. The review service can take 5-10 minutes on large changes.
- **Line numbers shift**: After applying fixes, finding line numbers are stale. Always re-verify by searching for the referenced code pattern, not the line number.
- **Sequential fix commits intertwine**: If a finding says "X is undefined" and you fix it, a subsequent finding saying "Y references X incorrectly" may be stale. Re-verify each finding against the latest code state.
- **replace_all is dangerous**: When fixing function name references, `patch(replace_all=true)` can hit occurrences in other code paths. Prefer targeted replacements with unique surrounding context.
- **Stale LSP diagnostics after patches**: Trust the typechecker (`tsc --noEmit`) over inline LSP diagnostics for verifying fixes.
- **CodeRabbit CLI buffers all output**: When running `--agent`, the CLI produces ZERO output until the entire review completes. Always use `background=true, notify_on_complete=true`.
- **patch tool escape drift**: When `old_string` contains backslash-escaped quotes but the actual file uses straight quotes, the patch tool rejects. Always `read_file` first and pass the exact file content.
- **Test mocks break when switching abstraction layers**: If a fix changes which internal abstraction a codepath calls, tests that mock the OLD layer will fail silently. The mock for the OLD layer still exists — it just never gets called anymore. Check for `Number of calls: 0` on the old spy.
- **Duplicate command registrations → extract shared handler**: Extract shared logic into a standalone async function, have both registrations call it.
- **Custom rendering is fragile — prefer proven components**: When a fix involves graph rendering, wrap the existing proven component with a state-management shell over building custom canvas code.
- **jsdom canvas stub guards**: `canvas.getContext("2d")` returns a non-null stub in jsdom. Guard with `typeof ctx.save !== "function"`.
- **Branch outruns your fixes**: On actively-developed branches, other commits may land between review and fix application. Before re-review, verify fixes survived by grepping for a unique string you added.
- **Verify which view the fix applies to**: When a finding mentions "consolidate duplicate code" and the code appears in multiple views, confirm which view the user means before replacing components.
- **Re-review on a clean branch returns an error**: When the branch is tree-identical to base, CodeRabbit exits with code 1 and "No files found for review" — this means the review is clean, not a failure.
- **Don't rebuild — delegate to proven sub-components**: For compacting/simplifying a component, delegate to existing sub-components rather than building custom rendering.
- **"Unused variable" in test mock constructors**: CodeRabbit may flag test variables as unused but removing them can break mock isolation.
- **"Registration not disposed" false positive**: When CodeRabbit flags a `registerWebviewViewProvider()` as not disposed, check whether the call is already inside a `context.subscriptions.push(...)` block.
