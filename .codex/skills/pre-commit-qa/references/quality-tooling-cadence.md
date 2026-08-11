# Quality Tooling: One-Library-at-a-Time Commit Cadence

Use this reference when adding code-quality libraries or validators (ESLint plugins, Knip, dependency-cruiser, SonarJS, React Doctor, etc.) to a user's codebase.

## Durable workflow lesson

When a quality-improvement task introduces multiple tools, do not batch all tool installation, all findings, and all fixes into one large commit. The preferred cadence is:

1. Add exactly one tool/library.
2. Wire the smallest useful configuration and package script for that tool.
3. Run the tool in the intended strict/report mode.
4. Fix or deliberately configure every finding from that tool before moving on.
5. Run the repo's validation set after those fixes.
6. Commit that tool's install/config/fixes as its own commit.
7. Only then start the next tool/library.

## Why

Quality tools often produce broad refactors and dependency/file deletions. Per-tool commits keep reviewable boundaries clear: reviewers can tell which changes were required by Knip versus dependency-cruiser versus SonarJS, and regressions can be bisected to one validator.

## Pitfalls

- Do not say "phase complete" when only the tool was added; the phase/library is complete only after findings are fixed and validation passes.
- Do not preserve a large working tree across several quality tools unless the user explicitly asks for a combined commit.
- If a validation command listed in repository docs does not exist, state that clearly and run the closest existing validation command; do not claim the missing command passed.
- If a full validation command is blocked/denied, stop before committing. A commit should represent actually run validation, not intended validation.
