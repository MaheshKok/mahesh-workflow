---
name: safety-guard
description: Assess the risk of a proposed operation and return required safeguards, evidence, and an explicit next action. Use before destructive commands, migrations, production changes, or external communication. Do not use to intercept tools, enforce permissions, or execute the operation.
---

# Operation Risk Assessment

## Required input

Need the proposed operation, target environment, rollback or recovery path, and approval owner. Return `blocked` if any is missing.

## Return exactly

```json
{
  "status": "complete|blocked",
  "summary": "",
  "findings": [{"risk": "", "safeguard": "", "evidence_required": ""}],
  "assumptions": [],
  "risks": [],
  "next_action": ""
}
```

## Rules

- Prefer a read-only or reversible alternative when it meets the goal.
- Require target confirmation and backup evidence before irreversible work.
- Treat missing rollback, owner, or environment as blocking.
- Do not claim to block a tool call or enforce permissions; the installed hook only warns.

## Trigger checks

Trigger: "Assess this production migration."; "Can we safely delete this bucket?"; "Review this force-push plan."; "What safeguards are needed before publishing?"; "Assess this customer-email send."

Do not trigger: "Run the migration."; "Block all destructive commands."; "Freeze this directory."; "Send the email."; "Install a security product."
