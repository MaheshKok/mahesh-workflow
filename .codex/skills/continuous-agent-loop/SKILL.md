---
name: continuous-agent-loop
description: Design a bounded autonomous-workflow specification with explicit stages, quality gates, stop conditions, and recovery steps. Use when a user needs to choose or review a repeatable agent loop. Do not use to schedule work, spawn agents, modify CI, or run a loop.
---

# Bounded Workflow Specification

## Required input

Need a goal, the permitted actions, a completion signal, and a failure boundary. Return `blocked` when any is missing.

## Return exactly

```json
{
  "status": "complete|blocked",
  "summary": "",
  "findings": [{"stage": "", "entry": "", "exit": "", "quality_gate": ""}],
  "assumptions": [],
  "risks": [],
  "next_action": ""
}
```

## Rules

- Specify a finite loop only: plan, execute, verify, recover or stop.
- Give each stage one measurable exit condition.
- Define a retry limit and an escalation condition.
- Do not create schedules, start agents, run commands, open PRs, or change files.

## Trigger checks

Trigger: "Design a verification loop for nightly dependency checks."; "What stop condition should this agent workflow have?"; "Review this proposed retry cycle."; "Specify recovery after a failed quality gate."; "Choose stages for a repeatable review workflow."

Do not trigger: "Run this every night."; "Start three agents."; "Fix CI now."; "Set up a cron."; "Implement this feature."
