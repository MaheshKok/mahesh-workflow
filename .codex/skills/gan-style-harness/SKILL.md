---
name: gan-style-harness
description: Create a generator-evaluator acceptance specification for a quality-sensitive application task. Use when a user needs independent implementation and evaluation criteria, iteration limits, and pass thresholds. Do not use to launch agents, start servers, run tests, or manage iterations.
---

# Generator-Evaluator Specification

## Required input

Need the product goal, acceptance criteria, target surface, and iteration budget. Return `blocked` when they are absent.

## Return exactly

```json
{
  "status": "complete|blocked",
  "summary": "",
  "findings": [{"criterion": "", "weight": 0, "evidence_required": "", "pass_condition": ""}],
  "assumptions": [],
  "risks": [],
  "next_action": ""
}
```

## Rules

- Keep the evaluator independent from the proposed implementation approach.
- Require observable evidence for every criterion.
- Set a finite iteration cap and a stop condition.
- Do not assign models, invoke tools, start an application, or execute a feedback loop.

## Trigger checks

Trigger: "Define independent quality gates for this dashboard."; "Create an evaluator rubric for this landing page."; "Set a pass threshold for this app task."; "Separate generator and reviewer acceptance criteria."; "Review this iteration budget."

Do not trigger: "Build the dashboard."; "Spawn a planner and evaluator."; "Run Playwright."; "Start the dev server."; "Keep iterating until it looks good."
