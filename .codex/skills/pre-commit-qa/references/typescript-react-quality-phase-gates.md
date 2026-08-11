# TypeScript/React quality-tooling phase gates

Use this reference when adding code-quality libraries or architecture tools to the IntelliGit / VS Code extension codebase.

## Branching rule for phased tooling initiatives

When the user describes multiple phases as one library/tooling-improvement initiative and names an existing branch for that initiative, keep every phase on that same branch. Do not create a fresh branch per phase unless the user explicitly asks for separate branches.

Example: if the branch is `chore/react-doctor-validation` and the user says it is dedicated to adding libraries to improve the codebase, Phase 1 ESLint/Knip, Phase 2 dependency-cruiser, and Phase 3 SonarJS should all continue on that branch.

## Phase completion gate

A phase is not complete merely because the tool was installed and configured. Before moving to the next phase:

1. Run the new tool in strict/failing mode, not only report-only mode.
2. Fix actionable findings from that phase.
3. Remove dead code/dependencies when findings are real.
4. Convert internal-only exported helpers/types to non-exported declarations when Knip reports unused exports.
5. Re-run the strict command until findings are clean, or document a deliberate scoped ignore with rationale.
6. Run the relevant validation set before starting the next phase.

For this repo, useful strict/report pairs are:

- ESLint regular: `bun run lint`
- ESLint zero-warning gate: `bun run lint:strict` or `eslint src scripts --max-warnings=0`
- Knip report-only: `bun run deps:check` using `knip --no-exit-code`
- Knip strict: `bun run deps:check:strict` using `knip`

## React/ESLint 10 compatibility note

`eslint-plugin-react` can execute under ESLint 10, but `settings.react.version: "detect"` may fail in this repo/toolchain. Prefer explicitly pinning the React version in ESLint settings, e.g. `settings: { react: { version: "18.2.0" } }`, after verifying the installed React version.

## Knip cleanup patterns seen in this repo

When strict Knip reports findings:

- Unused direct dev dependencies: remove them if no script/import/reference needs them; do not keep transitive implementation packages just because a meta-package uses them internally.
- Unused files: verify they are not extension entry points, webview bundle entries, generated assets, or test fixtures before deleting.
- Unused exported functions/types: if only used within the same file, remove `export`; if truly dead, delete them.
- Barrel files can hide stale exports. Trim barrels to only what downstream modules actually import.
- Type-only API shapes should remain exported only when consumed across module boundaries or by generated/public protocols.

## Safety

Do not advance to the next tool/library phase while the previous phase still has known strict-mode findings. The user expects every phase to end by implementing/fixing the findings it reveals.