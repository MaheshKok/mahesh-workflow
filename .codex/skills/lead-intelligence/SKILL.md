---
name: lead-intelligence
description: Rank user-supplied leads and prepare consent-safe outreach drafts using supplied relationship evidence. Use for qualification, prioritization, warm-path assessment, or message drafting from an existing lead list. Do not use to discover people, scrape profiles, enrich data, send messages, or automate outreach.
---

# Lead Ranking and Drafting

## Required input

Need a supplied lead list, objective, ranking criteria, and relationship evidence for any claimed warm path. Return `blocked` when the list, objective, or ranking criteria is missing. Treat a claimed warm path without relationship evidence as unavailable.

## Return exactly

```json
{
  "status": "complete|blocked",
  "summary": "",
  "findings": [{"lead": "", "rank": 0, "rationale": "", "recommended_channel": "", "draft": ""}],
  "assumptions": [],
  "risks": [],
  "next_action": ""
}
```

## Rules

- Rank only supplied records; state missing evidence instead of inferring it.
- Do not use sensitive traits or unverifiable relationship claims; treat missing consent or relationship evidence as a risk.
- Draft messages for user review only; never send or create invites.
- Do not browse, scrape, enrich, automate, or coordinate other agents.

## Trigger checks

Trigger: "Rank these supplied investor leads."; "Choose a channel for these warm introductions."; "Draft a reviewed follow-up for this lead."; "Assess these user-provided relationship notes."; "Prioritize this account list against our criteria."

Do not trigger: "Find new investors."; "Scrape LinkedIn."; "Enrich these records."; "Send these DMs."; "Run a prospecting campaign."
