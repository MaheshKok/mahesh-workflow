# TypeScript/React quality-tooling phase notes

Use these notes when adding quality libraries to a VS Code extension or similar TypeScript + React webview project.

## Dependency Cruiser phase

Goal: enforce architecture boundaries without forcing unrelated refactors.

Recommended first rules:
- `no-circular` for circular imports.
- `not-to-unresolvable` for broken imports.
- project-specific source boundaries, especially extension-host code vs browser/webview UI code.

Boundary pattern that worked well:
- Extension-host/view provider code must not import React app/component modules directly.
- Shared message contracts used by both host and webview should live in a neutral protocol directory, e.g. `src/webviews/protocol`, not under `src/webviews/react`.
- If a service directly orchestrates view providers, it belongs near the views layer rather than in a generic services layer. This avoids service -> views dependency inversions.

Implementation loop:
1. Add dependency-cruiser and an `architecture:check` script.
2. Configure a small strict rule set first; do not import a huge recommended rule set blindly.
3. Run the check and fix boundary findings by moving shared types/protocols to neutral modules instead of adding suppressions.
4. Run `typecheck` immediately after moves to catch stale relative imports.
5. Run full validation and commit the Dependency Cruiser phase separately.

## SonarJS phase

Goal: introduce high-signal code-smell coverage without turning the first pass into a large behavior refactor.

Recommended first rules:
- `sonarjs/cognitive-complexity` as a warning with a deliberately high baseline threshold for existing large handlers.
- Small, high-signal readability rules such as duplicated/identical branches and conditions, collapsible ifs, inverted boolean checks, nested switch, redundant boolean, and single-boolean-return preferences.

Important pitfall with `lint:strict`:
- If strict lint uses `--max-warnings=0`, warning-level SonarJS findings still fail the gate.
- Either clean up every warning before committing or set the first cognitive-complexity threshold high enough that only future regressions are surfaced.
- Do not enable full recommended SonarJS rules in the same pass unless the user explicitly wants a broad cleanup.

Implementation loop:
1. Verify plugin peer compatibility with the installed ESLint major.
2. Add the plugin to the existing runtime-scoped ESLint config rather than flattening environment-specific globals.
3. Run `lint:strict` immediately to see the true first-pass finding set.
4. Prefer configuration/threshold staging over broad inline suppressions for baseline complexity.
5. Run the full validation sequence and commit the SonarJS phase separately.

## Commit cadence reminder

For quality-tooling initiatives, keep commits library-scoped:
- add/configure one tool;
- run it;
- fix or stage all findings for that tool;
- run full validation;
- commit;
- only then move to the next library.

Do not batch recommendations from multiple tools into one commit.