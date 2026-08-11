---
name: design-system
description: Audit supplied design tokens, components, styles, or visual evidence and return concrete consistency, accessibility, and component findings. Use for focused design-system reviews. Do not use to research competitors, generate a full system, start a preview, run a browser audit, or modify UI code.
---

# Design-System Audit

## Required input

Need supplied token, component, stylesheet, screenshot, or review evidence and the audit target. Return `blocked` when there is no inspectable evidence.

## Return exactly

```json
{
  "status": "complete|blocked",
  "summary": "",
  "findings": [{"area": "token|component|accessibility|consistency", "evidence": "", "impact": "", "recommendation": ""}],
  "assumptions": [],
  "risks": [],
  "next_action": ""
}
```

## Rules

- Ground every finding in supplied evidence; do not invent file or line references.
- Check color, typography, spacing, component states, focus visibility, and contrast where evidence permits.
- Separate observed defects from proposed token or component changes.
- Do not browse competitors, generate assets, run a preview, or edit source files.

## Trigger checks

Trigger: "Audit these design tokens."; "Review consistency in these supplied components."; "Find accessibility gaps in this stylesheet."; "Assess this UI screenshot against our system."; "Prioritize these visual inconsistencies."

Do not trigger: "Create a new design system."; "Research competitor sites."; "Run the app and inspect every page."; "Generate a preview."; "Fix the CSS."
