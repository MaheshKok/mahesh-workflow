---
name: prove-it
description: Verify a change works by actually running the system end-to-end, not by reading code or trusting tests alone. Use when the user says "actually run it", "verify it works", "do not assume", "test the entire flow", or after claiming something works. Produces evidence, not assertions.
---

# Prove It (verify by running)

The user has repeatedly caught sessions claiming "the API runs perfectly"
without running it. Claims require execution evidence.

## Procedure

1. Identify the real entry point: the service, CLI, extension, or daemon —
   not a synthetic one-off script. If a FastAPI app has an endpoint, start
   the app and hit the endpoint; do not import the function and call it
   directly (explicit prior user correction).
2. Start the system the way a user would (`make run`, `uvicorn`, launch
   config). Long-running processes: run in background, then probe.
3. Drive one real flow end-to-end with real data: real request, real file,
   real ingestion. Capture actual output.
4. Check the observable side effects: HTTP status and body, log lines, DB
   rows, dashboard numbers, `cache_hit` flags — whatever the change claims
   to affect. Before/after comparison where possible.
5. For ai-calls-router specifically: restart the daemon if code changed
   (config is hot-reloaded, code is not), make live calls, then check
   `acr.log` and the savings/metrics output. The debug-routing project skill
   has the details.
6. Report: what was run (exact commands), what was observed (pasted output),
   verdict. If anything failed, say so plainly with the output — never soften
   a failure.

## Rules

- Tests passing is necessary, not sufficient. This skill is about the live
  path.
- Never fabricate or paraphrase output. Paste it.
- Clean up what you started (kill background processes) unless the user wants
  it left running.
