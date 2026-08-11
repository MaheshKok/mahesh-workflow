---
name: structured-commit-message
description: Write the user's preferred structured Git commit messages and commit message files. Use when asked to draft, improve, amend, or create a commit message; when committing changes; or when the user asks for a structured commit message, commit body, or git commit -F message.
---

# Structured Commit Message

## Workflow

1. Inspect the actual change before writing: staged diff, unstaged diff if relevant, changed files, and available test evidence.
2. Read `references/structured-commit-template.md` before drafting the message.
3. Read `references/structured-commit-message-files.md` before creating or amending a commit with a multi-section body.
4. Use a concise Conventional Commit-style subject: `<type>(<scope>): <short title under 72 chars>`.
5. Use the `=== Problem ===`, `=== Fixed ===`, `=== Added ===`, `=== Preserved ===`, and `=== Tests ===` section style from the reference.
6. Keep `Problem` and `Tests` in every structured commit body. Omit optional sections only when they do not apply.
7. Do not claim tests, verification, behavior, or motivation that is not supported by local evidence or user-provided facts.

## Commit Execution

For multi-section commits, write the full message to a temporary file and run `git commit -F <file>`. After committing or amending, verify with `git log -1 --format=%B` that the headings and bullets survived exactly.

## Quality Bar

Prefer specific bullets over generic summaries. Mention preserved behavior only when it helps reviewers understand risk. Do not add co-author trailers unless the user explicitly asks.
