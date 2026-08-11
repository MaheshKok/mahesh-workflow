---
name: pre-commit-qa
description: >-
  After completing code changes — run all linters, typecheckers, and tests.
  Optionally run CodeRabbit AI review. Bump version, update changelog, write
  structured commit. Applies to any project; project-specific commands go via
  AGENTS.md/CLAUDE.md or memory.
tags: [qa, lint, test, version, changelog, commit, workflow]
---

# Pre-Commit QA Workflow

After every implementation or fix, run ALL project quality checks before
considering the work complete.

## Quality tooling cadence

When adding multiple quality libraries or validators, work one library at a time: add/configure the tool, run it, fix all findings, run validation, commit that tool's changes, then move to the next tool. See `references/quality-tooling-cadence.md` for the detailed workflow and pitfalls. Do NOT skip any step.

When the user describes "Phase N branch" work, verify whether they mean separate physical Git branches or phase-scoped commits on one branch. Report that distinction explicitly before saying a phase is complete. A phase can be implemented as commits but still fail the user's "branch" wording if no separate branch objects exist.

## Trigger

- Finishing a code change (feature, fix, refactor)
- Before committing or pushing
- User says "run the linters" or "check everything"

## Steps

### 1. Run all QA checks

Run every quality gate the project defines. Common patterns:

```
prettier --check     (or format:check)
eslint               (or lint)
react-doctor         (or another framework-specific static-analysis doctor)
tsc --noEmit         (or typecheck, typecheck:ext, typecheck:webview)
<test runner>        (vitest, jest, pytest, go test, etc.)
```

If a project has React webviews/apps and React Doctor is installed or requested,
include it in the standard validation pipeline. Configure it non-interactively for
repeatable local/CI use, fail on error-level diagnostics, and treat warnings as
triage candidates rather than silently ignoring them. See
`references/react-doctor-validation.md` for setup and common fix patterns.

When improving quality gates for TypeScript + React projects, do not start by
adding many tools at once. First verify ESLint is scoped to the actual runtimes
(extension host / browser webview / scripts / tests), wire any installed but
unused plugins, then add high-signal tools in phases. See
`references/typescript-react-quality-tooling.md` for the recommended adoption
order, tool trade-offs, and pitfalls. See
`references/typescript-react-quality-tooling-phase-notes.md` for practical
phase execution notes from Dependency Cruiser and SonarJS adoption, including
host/webview protocol boundaries and strict-lint warning pitfalls.

If any check fails, fix the issue and re-run until all pass. Use auto-fix
flags when available (`prettier --write`, `eslint --fix`) before re-running.

### 2. Bump version once per branch

For projects using semantic versioning:
- **Patch** (0.7.3 to 0.7.4): bug fixes only
- **Minor** (0.7.3 to 0.8.0): new features
- **Major** (1.0.0 to 2.0.0): breaking changes

Before changing the version, compare the branch version against the target base
branch (usually `main`):

```bash
python3 - <<'PY'
import json, subprocess
working = json.load(open('package.json'))['version']
base = json.loads(subprocess.check_output(['git', 'show', 'main:package.json'], text=True))['version']
print(f'main={base}')
print(f'working={working}')
print(f'already_bumped={working != base}')
PY
```

Rules:
- If the branch version already differs from `main`, do **not** bump again.
- If starting a new feature/fix branch from `main`, bump once for that branch.
- If work was accidentally stacked on another branch, move/recreate the work on a
  fresh `main`-based branch before deciding the version bump.
- Keep the matching changelog entry scoped to the current branch only; do not carry
  changelog entries from the stacked/source branch.

Bump in the version file (`package.json`, `Cargo.toml`, `pyproject.toml`,
`setup.cfg`, etc.).

### 3. Update changelog

Add an entry following the project's existing format (Keep a Changelog is
common). Include:
- Version number and date
- Sections: Added, Changed, Fixed, Removed, Security, Tests, etc.
- Brief descriptions of each user-facing change

If the version file was bumped, treat the changelog update as mandatory and
part of the same release/version change. Do not commit a package/version bump
without the matching changelog entry. If you discover after committing that the
changelog was missed, add the changelog entry and amend the version-bump commit
when the user asks to commit, so the version bump and changelog stay together.

### 4. Write a structured commit message

Use bullet points, not one-liners. Group changes under categories.

For bugfix commits, prefer this section order:

```
fix(scope): short description

Problem:
- What was broken or confusing for the user.
- Include the concrete failure mode when useful.

Fixed:
- What changed to resolve the bug.
- Mention important command/behavior changes.

Preserved:
- Existing behavior intentionally kept unchanged.
- Include this section only when relevant.

Localized:
- Localization/catalog/translation updates.
- Include this section only when relevant.

Tests and Validation:
- Focused regression tests added or updated.
- Full validation commands that passed.
```

For features or broader changes, use the relevant categories:

```
feat: short description (vX.Y.Z)

Added:
- ...

Changed:
- ...

Fixed:
- ...
```

Reference new files, modified files, and any notable details.

### 5. Verify once more

After committing, verify `git status` is clean and the commit is as expected
(`git log --oneline -1`).

## Pitfalls

- **Skipping a step**: Every step exists because skipping it has caused
  problems before. Prettier without eslint means lint errors sneak through.
  Typecheck without tests means passing code that breaks at runtime.
- **Assuming tests still pass after formatting**: Prettier can change code
  structure; re-run tests after `prettier --write`.
- **Using stale React Doctor config names**: React Doctor reads `doctor.config.json`
  or `doctor.config.ts`; `react-doctor.config.json` is ignored/deprecated and will
  emit a warning. Keep the package script non-interactive (`react-doctor -y`) and
  the config explicit about offline/share/fail behavior.
- **Forgetting to check whether the branch is already bumped**: Version bumps
  are branch-scoped, not task-scoped. Always compare the working version with the
  base branch (`git show main:package.json` or equivalent) before bumping. If it
  already differs, leave it alone. Double-bumping because an earlier task on the
  same branch already changed the version creates misleading release numbers.
- **Stacking unrelated work on a previous feature/fix branch**: Before starting
  a new change, verify the current branch base. If the task belongs in a fresh
  branch, stash or otherwise move the work onto a `main`-based branch, then
  re-evaluate the version bump and changelog against `main`. Do not carry
  unrelated changelog entries from the previous branch.

- **Exposed credentials through tool output or config files**: When
  authenticating to external services through CLI tools, verify the
  credential does not leak into persistent state. Tokens embedded in git
  clone URLs land in `.git/config` as the origin remote — always run
  `git remote set-url origin <clean-url>` after an authenticated clone.
  Plaintext secrets in VS Code settings are syncable and world-readable —
  use `vscode.SecretStorage` instead. Credentials passed as CLI arguments
  are visible in the process list; consider environment variables or
  credential helpers.
- **Over-broad catch blocks that mask filesystem errors**: Catching all
  errors from `fs.access` and treating them as "file not found" hides
  permission errors, broken symlinks, and invalid paths. Check
  `err.code === "ENOENT"` specifically and surface everything else to the
  user before proceeding.
- **Absolute security claims in documentation**: "Tokens are
  never persisted" is false if the cleanup step can fail. Prefer
  precise language: "reset after successful clone so credentials
  are not left when cleanup succeeds."
- **Creating provider remotes without checking for existing
  origin**: When a publish/clone flow creates a remote repository
  via GitHub/GitLab API, check whether `origin` already exists
  BEFORE making the API call. If origin exists, ask the user:
  push to the existing origin (skip adding the new remote), or
  pick a different remote name. Otherwise the API-created repo
  is orphaned and the user's branch may push to an unintended
  target.

## CodeRabbit AI Review (Optional Gate)

After the standard QA pipeline passes, optionally run an automated AI code review using
the CodeRabbit CLI. This is especially useful for large or security-sensitive feature
branches.

### Quick start

```bash
coderabbit review --agent --base main
```

- `--agent` — structured JSON findings for programmatic processing
- `--base main` — compares current branch against main
- For large diffs (>1000 lines): `terminal(background=true, notify_on_complete=true, timeout=1800)`

The review outputs JSON Lines: `review_context`, `status` updates, `finding` objects
(with `severity`, `fileName`, `codegenInstructions`), and a `complete` message.

### Processing findings

1. Verify against current code (line numbers shift)
2. Categorize: Still valid → fix, Already fixed → skip, False positive → skip
3. Apply fixes minimally and surgically
4. Re-run full validation pipeline after all fixes

### Key pitfalls

- **CodeRabbit CLI buffers all output**: Zero output until review completes — use
  `background=true, notify_on_complete=true`
- **Line numbers shift** after applying fixes — always re-verify by code pattern
- **Re-review on a clean branch returns error**: Exit code 1 + "No files found for
  review" means the branch is clean, not a failure
- **Branch outruns your fixes**: On actively-developed branches, verify fixes survived
  before re-review
- **replace_all is dangerous**: Prefer targeted replacements with unique context
- **Test mocks break when switching abstraction layers**: Watch for `Number of calls: 0`
  on old spies after refactors

See `references/coderabbit-review-workflow.md` for the full workflow with all pitfalls
and edge cases.

## References

- `references/typescript-react-quality-phase-gates.md` — phase-gate rules for TypeScript/React quality-tooling initiatives: same-branch sequencing, strict-mode finding cleanup before moving phases, ESLint/Knip patterns, and React plugin compatibility notes.

- `references/coderabbit-review-workflow.md` — Full CodeRabbit CLI review workflow,
  finding processing, pitfalls, and edge cases.
- `references/coderabbit.md` — Original CodeRabbit integration notes.
- `references/credential-security.md` — Patterns for handling credentials in VS Code
  extensions and git operations without leaking them to config files, process lists,
  or syncable settings.
- `references/react-doctor-validation.md` — React Doctor setup, config naming,
  common fix patterns, suppressions, and validation loop.
- `references/typescript-react-quality-tooling.md` — phased adoption guide for
  TypeScript + React quality gates: ESLint scoping, typed linting, React hooks,
  Knip, Dependency Cruiser, SonarJS, Semgrep, and noise/peer-compatibility pitfalls.
- `references/typescript-react-quality-tooling-phase-notes.md` — practical phase
  notes for Dependency Cruiser and SonarJS adoption: neutral webview protocol
  modules, host/webview boundary fixes, strict-lint warning pitfalls, and
  library-scoped commit cadence.
- `references/typescript-react-quality-phase-verification.md` — how to verify
  phase-based quality-tooling work, including the distinction between separate
  physical branches and phase-scoped commits plus CI warning-gate checks.
