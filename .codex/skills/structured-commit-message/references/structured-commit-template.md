# Structured Commit Message Template

This user prefers structured commit bodies with these sections:

```
<type>(<scope>): <short title under 72 chars>

=== Problem ===
<what was broken or missing, phrased as a condition or behavior>

=== Fixed ===
- <bullet list of bug-fix changes, each describing a specific fix>

=== Added ===
- <bullet list of new features, capabilities, or data that didn't exist before>
- <separate from Fixed — don't mix fixes and new additions>

=== Preserved ===
- <behaviors/features kept intact, to reassure reviewers>

=== Tests ===
- <specific test names or file references>
- <validation commands run and their results>
```

## Section semantics

| Section | Purpose | When to omit |
|---------|---------|-------------|
| Problem | What was wrong — a condition or behavior, not a wishlist | Never |
| Fixed | Bug-fix changes: what was corrected | Omit if no bugs were fixed |
| Added | New capabilities, features, data, tests — things that didn't exist | Omit if no new additions |
| Preserved | What was intentionally kept unchanged | Omit if nothing notable was preserved |
| Tests | Evidence: test names, count, validation results, lint results | Never |

**Rule:** Feature-heavy commits (new dashboard, new metrics, new tests) use
Problem + Added (and optionally Fixed if there were bugs too). Bug-fix commits
use Problem + Fixed. Pure refactors use only Problem + Fixed + Preserved.

The `=== Section Name ===` headers help reviewers scan quickly — keep them.

## Examples

### Feature-heavy commit (Problem + Added + Tests)

```
feat: add live dashboard, agent/session metadata, and metrics persistence

=== Problem ===
The proxy had no visual interface. Agent, session, and provider metadata
were missing from metrics and the savings ledger.

=== Added ===
- Live dashboard at /dashboard with per-request table, agent/session panels
- identify_agent(), identify_session(), identify_provider() classifiers
- Metrics.bootstrap() replays savings.jsonl on startup for persistence
- provider/agent/session fields in savings ledger JSONL entries
- Cache-Control headers on /dashboard endpoint

=== Tests ===
- tests/unit/test_identify_provider.py: 15 tests
- tests/unit/test_metrics_persistence.py: 5 tests
- tests/unit/test_agent_session.py: 11 tests (from prior commit)
- Full suite: 471 passed; lint clean; format clean
```

### Bug-fix commit (Problem + Fixed + Tests)

```
fix: reset currentBranchHasUpstreamCache on repo switch

Problem: currentBranchHasUpstreamCache wasn't cleared in setRepositoryRootUri,
so postWorkingTreeSnapshot + onDidChangeVisibility could replay stale upstream
state from the previous repo.

Fixed: Reset currentBranchHasUpstreamCache = false alongside other
repository-scoped caches when the repository root changes.

Tests:
- format:check, lint, typecheck, build pass
- All 525 tests pass
```

```
feat(commit-panel): hide empty Changes section, add drag-to-track highlight and count badge

Problem: Changes section was always visible even when empty. Unversioned file
drag-to-track had no visual feedback on the drop target or cursor.

Fixed:
- Hide Changes section when no tracked or unversioned files exist
- Highlight Changes section header with blue outline on drag-over
- Show file count badge on drag cursor for multi-file drags
- Add drag enter/leave counter tracking for reliable highlight toggling

Preserved:
- Existing single-file drag-to-track behavior
- All checkbox/section toggle semantics

Tests:
- 4 new selective commit tests (view-providers.integration.test.ts)
- All 529 tests pass
- format:check, lint, typecheck, build pass
```

```
refactor(tests): reorganize test directory into domain-categorized hierarchy

Problem: The tests/ directory had a flat layout — all unit, integration,
webview, and helper files mixed under tests/unit/. Files like gitops.test.ts
bundled multiple domains into a single file. Helpers lived under tests/unit/utils/
alongside actual tests. Setup files and fixtures had no dedicated home.

Fixed:
- Restructure tests/ into unit/, webview/unit/, integration/, helpers/,
  fixtures/, and setup/ directories
- Split monolithic tests/unit/gitops.test.ts into domain-specific files
  under tests/unit/git/gitops/: branch, commits, errors, remotes, status
- Move helpers from tests/unit/utils/ to tests/helpers/
- Create tests/setup/ with vitest.setup.ts, jsdom.setup.ts, vscode.mock.ts
- Add fixture .gitkeep placeholders under tests/fixtures/{git,localization,webviews}/
- Update vitest.config.ts include pattern to tests/**/* instead of tests/unit/**/*

Preserved:
- All test content, assertions, and imports unchanged (pure file moves/splits)
- vscode.mock.ts content preserved from its prior location inside the deleted gitops.test.ts
- Existing vitest.config.jsdom.ts config unchanged

Tests:
- All 532 tests pass (35 files, 0 failures)
- format:check, lint, typecheck, architecture:check, react-doctor, build all pass
```
