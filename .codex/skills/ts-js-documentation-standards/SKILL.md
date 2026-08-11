---
name: ts-js-documentation-standards
description: Apply meaningful TSDoc/JSDoc documentation standards when working in TypeScript or JavaScript codebases.
tags:
  - typescript
  - javascript
  - tsdoc
  - jsdoc
  - documentation
  - linting
---

# TypeScript/JavaScript Documentation Standards

Use this skill whenever modifying, adding, reviewing, or planning TypeScript or JavaScript code, especially code that exports functions, classes, hooks, interfaces, types, services, commands, extension APIs, or other boundary behavior.

## Core rule

Do not introduce undocumented functions or exported boundary APIs unless the repository already has an explicit documented exclusion for that area.

Documentation must explain the function's real contract, not merely repeat its name, parameter types, or return type.

## What to document

For each new or changed function, class, method, hook, exported type, interface, enum, or module-level API, add or update TSDoc/JSDoc that captures the durable behavior a maintainer needs to know:

1. Contract: what the API guarantees and what callers may rely on.
2. Invariants: assumptions that must remain true before, during, or after execution.
3. Side effects: filesystem, network, UI, state, telemetry, logging, cache, process, command, or storage effects.
4. Failure modes: thrown errors, rejected promises, fallbacks, ignored failures, partial success, cancellation, retries.
5. Trust boundaries: user input, paths, shell commands, secrets, tokens, remotes, webview messages, extension-host/webview crossing, network responses.
6. Non-obvious lifecycle constraints: initialization order, disposal, cleanup, subscriptions, event ordering, concurrency, debouncing, cancellation.
7. Compatibility constraints: VS Code APIs, browser/webview behavior, Node runtime limitations, platform-specific behavior.

## What to avoid

Reject low-value comments that only restate TypeScript or obvious implementation details:

- Bad: `/** Handles click. */`
- Bad: `/** Returns a string. */`
- Bad: `/** The user ID parameter. */`
- Bad: `/** Creates a Foo. */` when the signature already says `createFoo()`.
- Bad: comments that drift into implementation narration instead of stable caller-facing behavior.

Prefer concise but meaningful documentation:

```ts
/**
 * Resolves a repository-relative path only after confirming it remains inside the workspace root.
 *
 * This guards command execution and file reads against path traversal from user-controlled input.
 * Throws when the normalized path escapes the trusted workspace boundary.
 */
export function resolveWorkspacePath(workspaceRoot: string, candidatePath: string): string {
  // ...
}
```

```ts
/**
 * Debounces branch search requests so the webview only renders the newest result set.
 *
 * Older in-flight requests are allowed to finish, but their results are ignored once a newer query
 * has been issued. This keeps the UI stable when users type quickly.
 */
function useDebouncedBranchSearch(query: string): BranchSearchState {
  // ...
}
```

## Repository-first workflow

1. Inspect the repository's existing documentation rules before editing:
   - README or contributor docs.
   - ESLint config for `tsdoc`, `jsdoc`, or `eslint-plugin-jsdoc` rules.
   - Existing TSDoc/JSDoc style in nearby files.
   - Any documented exclusions or ratchets.
2. Follow project-local rules over generic preferences.
3. If the repo has no explicit standard, use TSDoc for TypeScript and JSDoc for JavaScript.
4. For React components, avoid noisy presentational comments unless the component exposes non-obvious behavior, lifecycle constraints, hooks, data boundaries, or side effects.
5. For small private helpers, document when behavior is non-obvious, security-sensitive, stateful, asynchronous, or reused across boundaries. If a repository enforces all functions, comply with that ratchet.
6. When changing behavior, update existing comments in the same edit so docs do not drift.

## Lint and validation checklist

Before finishing code changes in a TypeScript/JavaScript repository:

1. Run the smallest relevant focused test or typecheck first.
2. Run the repo's documentation lint commands when available, such as:
   - `bun run lint`
   - `bun run lint:strict`
   - `npm run lint`
   - `pnpm lint`
   - `yarn lint`
   - project-specific `tsdoc`, `jsdoc`, or documentation validation scripts.
3. If documentation linting is missing and the task adds public APIs, note the risk and consider adding a scoped lint rule only if the user requested tooling changes.
4. Do not claim documentation coverage passed unless the relevant command actually ran.

## Review checklist

When reviewing TypeScript/JavaScript code, check that:

- New functions are not left undocumented where project rules require documentation.
- Exported APIs and boundary functions have meaningful comments.
- Comments mention contracts, invariants, side effects, failure modes, or trust boundaries when relevant.
- Comments do not simply restate names, parameter types, or return types.
- Documentation stayed synchronized with implementation changes.
- React/presentational code avoids comment noise unless a non-obvious contract exists.

## IntelliGit-specific note

For the IntelliGit / `pycharm-git-for-vscode` repository, follow the repository TSDoc standard and ratchet documented in `docs/tsdocs/TSDOC.md`, `README.md`, and `eslint.config.mjs`. The standard expects meaningful comments for completed source areas and avoids React presentational noise.
