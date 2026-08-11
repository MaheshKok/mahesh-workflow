---
name: agentic-engineering
description: Assess an AI-assisted engineering task and return a proposed workflow, acceptance checks, assumptions, and risks. Use for planning or reviewing bounded agent-assisted implementation work. Do not use to route models, decompose work among agents, run evaluations, or perform implementation.
---

# Agent-Assisted Engineering Assessment

## Required input

Need a task statement, relevant repository or product context, and a definition of done. Return `blocked` when any is missing.

## Return exactly

```json
{
  "status": "complete|blocked",
  "summary": "",
  "findings": [{"work_item": "", "acceptance_check": "", "dominant_risk": ""}],
  "assumptions": [],
  "risks": [],
  "next_action": ""
}
```

## Rules

- Propose independently verifiable work items, not agent assignments.
- Derive acceptance checks from the stated behavior, not implementation details.
- Call out security, data, and rollout risks before efficiency concerns.
- Do not select models, spawn workers, execute commands, or modify files.

## Trigger checks

Trigger: "Plan this AI-assisted refactor."; "Assess risks in this agent-generated change."; "Define acceptance checks for this coding task."; "Review this agent-assisted rollout."; "Break this feature into verifiable work items."

Do not trigger: "Use Opus for this."; "Delegate this to agents."; "Implement the refactor."; "Run the test suite."; "Optimize token usage."
