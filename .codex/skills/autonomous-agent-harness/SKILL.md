---
name: autonomous-agent-harness
description: Assess whether a persistent autonomous-agent harness is justified and return a bounded operating specification covering authority, state, observability, and shutdown. Use for architecture decisions about autonomous systems. Do not use to install, schedule, dispatch, or operate agents.
---

# Autonomous Harness Assessment

## Required input

Need the operating objective, available runtime capabilities, allowed authority, and incident owner. Return `blocked` if any is unknown.

## Return exactly

```json
{
  "status": "complete|blocked",
  "summary": "",
  "findings": [{"area": "authority|state|observability|shutdown", "recommendation": "", "evidence": ""}],
  "assumptions": [],
  "risks": [],
  "next_action": ""
}
```

## Rules

- Prefer no harness when a bounded manual or one-shot workflow meets the goal.
- Require explicit write, spend, and external-communication authority.
- Define state ownership, telemetry, human escalation, and a shutdown path.
- Do not create automations, queues, memory stores, integrations, or background work.

## Trigger checks

Trigger: "Do we need an autonomous harness for deploy monitoring?"; "Assess this persistent-agent proposal."; "Define authority for a monitoring agent."; "Review this agent shutdown design."; "What telemetry does an autonomous service need?"

Do not trigger: "Schedule a daily report."; "Build an AutoGPT clone."; "Send these emails."; "Create a task queue."; "Run a browser bot."
