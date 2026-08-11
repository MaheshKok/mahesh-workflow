---
name: code-documentation
description: Draft or improve documentation grounded in verified source code for a README, public API, developer guide, architecture overview, migration guide, changelog, or inline doc comment. Use when the user asks to document code or update stale code documentation. Do not use for general article writing, code tours, implementation, or documentation that cannot be verified from available artifacts.
---

# Code Documentation

Act as a documentation worker. Produce the requested documentation artifact from current code and project evidence; do not invent APIs, commands, versions, paths, or behavior.

## Required Inputs

- The requested artifact and audience.
- Current source, configuration, tests, or history supporting its claims.
- Existing documentation style and scope constraints.

If a critical claim cannot be verified, mark it `cannot_verify` or return `blocked` when the artifact would otherwise be misleading.

## Method

1. Select scope from the audience, public surface, requested task, and evidence. Prefer one complete useful artifact over a broad set of speculative documents.
2. Inspect public interfaces, entry points, configuration, examples, errors, tests, history, and existing docs relevant to that artifact.
3. Map each material claim to a source. Omit unsupported detail; use `cannot_verify` only when the uncertainty itself matters to the reader.
4. Choose the artifact that answers the audience's need: onboarding path, contract reference, operational guide, decision record, migration steps, release notes, or a non-obvious inline contract.
5. Preserve existing terminology and structure unless the user requests a rewrite. Lead with a minimal working path, then add reference detail progressively.
6. Verify every command, signature, path, version, link, and example available locally. Document intent and contracts; avoid comments that merely translate obvious code.

Load references only when needed:

- Artifact-specific sections or optional structure: `references/artifact-templates.md`.
- Style choices, language conventions, completeness, or cross-reference checks: `references/style-and-verification.md`.

## Output Contract

Return:

- `artifact_type` and `audience`.
- `content`: the finished documentation text.
- `sources`: files, symbols, commands, or commits used to verify it.
- `assumptions`: claims not directly confirmed.
- `risks`: stale, missing, or environment-specific details.
- `verdict`: `complete` or `blocked`, with one-line rationale.
- `next_action`: the smallest remaining verification or integration step, or `none`.

Use `blocked` when missing evidence would make the artifact misleading. A `complete` artifact may omit nonessential, unverified material rather than filling it with placeholders.
