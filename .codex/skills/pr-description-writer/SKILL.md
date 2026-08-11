---
name: pr-description-writer
description: Generate reviewer-friendly GitHub Pull Request descriptions from repository context, changed files, diffs or diff summaries, commit logs, test commands and outputs, and user-provided motivation. Use when asked to draft, write, improve, or format a PR description, pull request body, merge request description, or reviewer summary.
---

# PR Description Writer

## Core Contract

Write a GitHub Pull Request description that is specific, evidence-based, and reviewer-friendly. Treat the provided repository context, changed files, diff, commit log, test output, and user motivation as the source of truth.

Do not claim behavior, test results, motivations, or implementation details that are not supported by the provided inputs or local inspection. If no code or documentation changed, state that no PR is needed.

## Workflow

1. Read the provided context before drafting:
   - Repository context
   - Changed files
   - Git diff or diff summary
   - Commit log
   - Test commands and outputs
   - User-provided motivation

2. Separate facts from inference:
   - Use diffs and file contents for what changed.
   - Use commit messages only as supporting context; do not let them override the diff.
   - Use test output to classify checks as passed, failed, or environmentally limited.
   - Mark unknowns as notes or risks instead of filling gaps with generic language.

3. Keep the PR description scoped:
   - Mention meaningful behavior, workflow, documentation, data, CI/CD, dependency, or output-file changes.
   - Avoid implementation trivia unless it affects review, risk, or user behavior.
   - Prefer concrete nouns and changed surfaces over vague phrases like "improved functionality."

## Required Output Format

Return exactly these top-level sections unless the user explicitly asks for a shorter format:

```markdown
### Title

<Concise PR title in imperative or descriptive style.>

### Motivation

<Explain why the change is needed. Mention the user problem, bug, workflow need, or product reason.>

### Summary

- <3-7 bullets. Each bullet describes a meaningful code, documentation, workflow, data, CI/CD, dependency, or output-file change.>

### Detailed Changes

#### Code

- <Code changes, or "None.">

#### Tests

- <Test changes, or "None.">

#### Documentation

- <Documentation changes, or "None.">

#### CI/CD

- <CI/CD changes, or "None.">

#### Dependencies

- <Dependency changes, or "None.">

#### Data/output files

- <Data or generated-output changes, or "None.">

### Testing

- Unit/regression tests: <Specific tests added or updated, including file/test names when useful; write "None added" if no tests changed.>
- Feature/bug verification: <How the feature or bug fix was exercised from a user's perspective or with focused test cases.>
- Validation summary: <Brief overall validation result, grouped as a suite; do not list every lint/type/build command by default.>
- Limitations: <Failed checks, skipped checks, environmental blockers, or known warnings; write "None." only when supported.>

### Risks / Notes

- <Risks, limitations, follow-ups, or reviewer attention points.>
```

## Testing Section Rules

The Testing section should explain evidence, not dump the validation transcript.

- Prioritize unit, integration, or regression tests added/updated for this PR. Name the test file and the behavior covered when known.
- Describe how the feature or bug fix was exercised from the user/workflow perspective.
- Summarize broad validation suites compactly, for example: "Full project validation passed: format, lint, typecheck, build, localization, tests, packaging." Do not list every command by default.
- Include exact command names only when they materially help the reviewer reproduce a focused check, explain a failure, or document an environmental limitation.
- If no tests were added, say so explicitly and explain what verification was performed instead.
- Do not hide failed checks, skipped checks, known warnings, or environmental blockers. Include them under Limitations with enough context for reviewers to assess risk.
- Do not claim tests passed unless outputs confirm success.

If no verification was performed, write:

```markdown
- Unit/regression tests: None added.
- Feature/bug verification: Not run - <reason>.
- Validation summary: Not run - <reason>.
- Limitations: <risk created by lack of verification>.
```

## Quality Rules

- Be specific, not generic.
- Do not hide failed checks or warnings.
- Do not claim tests passed unless outputs confirm success.
- Do not turn environmental limitations into passing results.
- Do not include long code snippets unless they are necessary for reviewer understanding.
- Keep the title concise and actionable.
- Keep the summary to 3-7 bullets.
- Include "None." for Detailed Changes areas with no relevant changes.
- Use reviewer-oriented language: explain what changed, why it matters, and where reviewers should focus.
