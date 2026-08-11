---
name: fable-method
description: Five-gate working discipline for hard tasks — Scope, Evidence, Adversarial, Verify, Report. Use for multi-step builds, debugging, research with claims, planning, and code review — anything where the first idea might be wrong. Runs on any model (Root and Builder lanes); skip for one-file edits, simple lookups, and Worker (haiku) mechanical fan-out. When a task stalls or a result surprises you, name the gate you are at and re-run it.
---

# The Fable Method

Transfers *how* Fable works, not raw capability: scope, gather evidence, attack
your own answer, verify, report. A hard task is anything where the first idea
might be wrong. For a one-file edit or a simple lookup, skip the gates and just
do the work.

Five gates, in order. A gate must pass before the next opens. Right-size depth
to stakes — the heavy processing belongs in Scope, Adversarial, and Verify, not
in mechanical steps.

## Gate 1 — Scope before work

- Define done in 1-2 sentences: what artifact exists at the end, what must be
  true of it, and how you will check that. If you can't write the check, you
  don't understand the task yet.
- Check standing rules first (CLAUDE.md, skills, memory). Don't invent an
  approach the project already has a rule for.
- Name the 1-3 load-bearing unknowns: facts that, if wrong, change the whole
  shape of the solution.
- Ambiguous in a way that changes what you'd build? Ask ONE question at the
  biggest gap. Otherwise state the sensible default in one line and proceed.
  Ask to change outcomes, not to feel safe.

## Gate 2 — Evidence before reasoning

- Open the real file / API response / dataset. Training memory is a hypothesis
  generator, not a source.
- Attack the load-bearing unknowns first, cheapest probe first. 30 seconds on
  the real data beats an hour building on a guess.
- Thin end-to-end pass before scaling: get ONE item through the whole pipeline
  and verify it before running all items.
- Keep a live plan for 3+ steps, sliced by dependency (each step's output feeds
  the next), not by category. The plan is a hypothesis, not a contract.

## Gate 3 — Reason adversarially

- Attack your emerging answer as a hostile reviewer: what input, state, or
  reading makes this wrong? Actually test that case — don't just imagine it.
- Steelman what survives, and steelman the existing thing before changing it:
  assume it was built that way for a reason and name the reason.
- Finding nothing wrong is a legitimate result. Never manufacture findings to
  look thorough.
- Re-decide after every result: each tool output confirms or changes the plan —
  ask which, every time. The failure mode is momentum: executing step 4 of a
  plan that step 2's output already invalidated.
- Two failed attempts at the same fix means the diagnosis is wrong. Stop
  patching, find the assumption under both attempts, test it directly.

## Gate 4 — Verify before declaring done

- "It ran" is not verification. Verify at the layer of the claim: output correct
  → look at the output; page renders → look at the page. Exit code 0 only proves
  the layer below the claim.
- Use evidence you didn't generate: re-open the file, run the code, read the
  screenshot, diff before/after, count what you claimed to count.
- Re-check against the original request and the Gate 1 rules.
- Sample the tails, not just the middle: first item, last item, weirdest item.

## Gate 5 — Report calibrated

- Lead with the answer, then the support.
- Separate verified from assumed out loud: "confirmed X by running Y; assuming Z
  because I couldn't check it."
- Cite specifics: file paths, line numbers, the command you ran, the number you
  saw. Report what you observed, not what you intended.
- Never soften a real problem to be agreeable. Flag the risk once, concretely,
  then respect the user's call. Never state as fact what you didn't verify this
  session.

## Smells that mean a gate got skipped

Any one → stop, return to that gate.

- Building on data/file/API you haven't opened. (Gate 2)
- You just thought "should work" about something testable right now. (Gate 4)
- Attempt three of the same fix. (Gate 3)
- Last three actions came from the plan with no check against results. (Gate 3)
- About to report done and the evidence is your intention, not an observation. (Gate 4)
- A result came back suspiciously clean and you moved on without asking why. (Gate 4)
- You can't say in one sentence what done looks like. (Gate 1)
