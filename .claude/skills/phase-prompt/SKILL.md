---
name: phase-prompt
description: Generate a comprehensive, self-contained LLM implementation prompt for the next phase of a plan. Use when the user says "give me llm prompt for phase N / next phase", "comprehensive prompt for an llm", or wants a goal handed to another agent. Reads the plan doc, verifies prior-phase state, emits one copy-pasteable prompt.
---

# Phase Prompt Generator

You produce ONE self-contained prompt that a fresh LLM session (Codex, Hermes,
another Claude) can execute with zero access to this conversation.

## Procedure

1. Locate the plan. Look in `docs/plans/`, `docs/`, or ask which file. Read the
   phase list and identify the next unimplemented phase (check git log and code,
   do not trust the plan's checkboxes).
2. Verify the previous phase actually landed before prompting the next one. If
   it did not, say so and stop — do not write a prompt built on missing work.
3. Write the prompt using the template at `~/.claude/templates/phase-llm-prompt.md`.
4. Output the prompt in a single fenced block, nothing else after it.

## Hard requirements for the generated prompt

- Self-contained: repo path, branch, exact file paths, current state summary.
  The receiving LLM has NOT seen this conversation.
- Scope-fenced: list what is in scope and explicitly what is NOT (later phases).
- Test mandate: comprehensive unit tests are part of the phase, not optional.
  Name the test dir and the existing pattern file to imitate.
- Gate mandate: name the exact command that must pass (`make qa`, `npm test`,
  `bun run build`) before the phase counts as done.
- Commit mandate: commit the changes before finishing, conventional format,
  no AI attribution, never commit `.claude/` or `CLAUDE.md`.
- Verification handshake: end the prompt with "report what was implemented,
  what was tested, and any deviations from this prompt" so the user can run
  /verify-phase afterwards.
