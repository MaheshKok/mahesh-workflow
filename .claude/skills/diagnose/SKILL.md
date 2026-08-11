---
name: diagnose
description: Strict read-only analysis mode. Use when the user says "dont make any change", "just tell me", "just suggest your findings", "what do you think of", or asks a question about code/config without requesting an edit. Findings and answer only, zero writes.
---

# Diagnose (read-only)

The user wants analysis, not action. This is the single most re-typed
instruction in their history — honor it strictly.

## Rules

1. ZERO writes: no Edit, no Write, no file creation, no commits, no config
   changes, no daemon restarts. Running tests or read-only shell commands to
   gather evidence is fine.
2. Answer in chat. Do NOT create a .md report file unless the user explicitly
   asks to "document" it. "Dont document just tell me" is the standing default.
3. Ground every claim in evidence: file:line references, actual command
   output, actual log lines. Never "this should work" — show why it does or
   does not.
4. If asked "what do you think" of code/uncommitted changes: give an honest
   critical assessment — defects first (severity-ordered, file:line), then
   design concerns, then what is good. No sycophancy.
5. End with a one-line offer: the concrete fix you would apply if asked.
   Do not apply it.

## Exit

Mode ends only when the user explicitly asks for a change ("fix it",
"implement it", "go ahead"). A question in their reply is not permission.
