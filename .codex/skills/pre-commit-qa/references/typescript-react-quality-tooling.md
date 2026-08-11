# TypeScript + React quality-tooling adoption

Use this when improving static analysis for a TypeScript + React codebase, especially VS Code extensions with both extension-host code and browser webviews.

## Core lesson

Do not start by adding many quality tools at once. First make ESLint understand the project shape:

- Scope extension-host TypeScript separately from React/webview TypeScript.
- Use Node/VS Code globals only for extension-host and scripts.
- Use browser globals only for webview code.
- Scope test globals to tests only.
- Check for installed but unwired ESLint plugins before adding new ones.

For VS Code extensions, global browser globals are a smell: backend extension code and webview code run in different runtimes and should not share lint assumptions.

## Recommended first wave

1. `eslint-plugin-react-hooks`
   - Add immediately for React webviews.
   - `react-hooks/rules-of-hooks`: error.
   - `react-hooks/exhaustive-deps`: warning first; can be noisy for VS Code webview message/subscription patterns.

2. Type-aware `typescript-eslint`
   - Enable `recommendedTypeChecked` before reaching for more tools.
   - Highest value checks include floating promises, misused promises, unsafe async patterns, and unnecessary conditions.
   - Expect initial cleanup; stage the change if findings are numerous.

3. `knip`
   - Add report-only first.
   - Tune entry points for extension main, webview bundles, scripts, and tests before gating.
   - Best tool for unused files, exports, dependencies, and devDependencies; replaces depcheck/ts-prune for most TS repos.

4. Existing React linting
   - If `eslint-plugin-react` is installed, either wire it into flat config and verify it works with the active ESLint version, or remove it.
   - Do not leave installed lint plugins unwired; they create a false sense of coverage.
   - With `eslint-plugin-react@7.x` on bleeding-edge ESLint majors, `settings.react.version: "detect"` can fail at runtime with `contextOrFilename.getFilename is not a function`; pin the known React version in settings (for example `"18.2.0"`) and verify `bun run lint` before relying on the plugin.

## Recommended second wave

1. `dependency-cruiser`
   - Use for enforceable architecture boundaries and cycles.
   - For VS Code extensions, useful boundaries include:
     - webviews must not import `vscode`, `fs`, `path`, `child_process`, Git services, or extension-host modules.
     - extension-host code must not import React webview components.
     - Git/service layers should not import views/webview UI.
   - Prefer this over Madge for long-term enforcement.

2. `eslint-plugin-sonarjs`
   - Good for cognitive complexity and code smells.
   - Start as warnings with high thresholds; do not make complexity a hard gate on day one.
   - Tune noisy rules such as duplicate strings, especially around i18n keys and UI labels.

3. `eslint-plugin-import-x`
   - Prefer over legacy `eslint-plugin-import` for modern flat-config/TypeScript setups.
   - Let dependency-cruiser own cycles; use import-x for duplicate imports, unresolved imports, and selected import hygiene.
   - Treat import ordering as auto-fixable style, not high-value correctness.

## Later / optional tools

- `eslint-plugin-jsx-a11y`: valuable for custom webviews, but start as warnings and scope to TSX/webview files. Component libraries can cause false positives.
- `semgrep`: useful later for curated security/static rules around command execution, path handling, webview HTML/CSP, and credential leaks. Prefer custom repo-specific rules over broad noisy packs.
- `jscpd`: optional report-only duplicate-code metric. Do not gate initially.
- StrykerJS/mutation testing: useful for high-risk pure logic modules, but slow; run scheduled/manual, not in normal pre-commit validation.

## Tools to avoid or delay

- Do not add Madge if dependency-cruiser is adopted; it is mostly redundant.
- Do not add depcheck, ts-prune, or ts-unused-exports when Knip can cover the space better.
- Do not enable `eslint-plugin-unicorn` recommended wholesale; cherry-pick only a few correctness rules if needed.
- Do not jump directly to full `strictTypeChecked`/stylistic TypeScript presets in a mature repo; start with `recommendedTypeChecked` and ratchet later.
- Do not add Biome/Oxlint just for speed when the need is ecosystem-specific React/TypeScript/architecture checks and the project already uses ESLint/Prettier.

## Peer-compatibility check before installing

Before adding ESLint plugins on bleeding-edge ESLint/TypeScript versions, check peer ranges:

```bash
npm view eslint-plugin-react-hooks version peerDependencies --json
npm view eslint-plugin-sonarjs version peerDependencies --json
npm view eslint-plugin-jsx-a11y version peerDependencies --json
npm view eslint-plugin-react version peerDependencies --json
npm view eslint-plugin-import-x version peerDependencies --json
```

If a plugin does not officially list the active ESLint major, test it in a branch before making it part of the validation pipeline.

## Adoption principle

Add small focused branches:

1. ESLint scoping + React hooks + type-aware TypeScript linting.
2. Knip report/tuning, then gate after triage.
3. Dependency Cruiser architecture boundaries.
4. SonarJS code-smell warnings.
5. Accessibility/security/deep checks after the core signal is clean.

Avoid dumping many plugins into one commit: a wall of warnings teaches maintainers to ignore lint output.