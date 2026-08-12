#!/usr/bin/env python3
"""Inject compaction-preservation instructions into Claude Code PreCompact hooks."""

import json
import sys

# Consume hook input so Claude Code can pipe the standard hook payload safely.
try:
    if not sys.stdin.isatty():
        json.load(sys.stdin)
except Exception:
    # The instruction is static; malformed/empty hook input should not block compaction.
    pass

additional_context = 'When compacting, you MUST preserve:\n1. All rules and constraints from CLAUDE.md and system prompt — copy them verbatim\n2. Current task context and progress\n3. File paths that were modified\n4. Specific error messages and their solutions\n5. User corrections and preferences stated during the session\n\nYou MAY summarize:\n- Tool call outputs (keep conclusions, drop raw output)\n- File contents that were read (keep what was learned, drop the text)\n- Exploratory steps that led nowhere'

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "PreCompact",
        "additionalContext": additional_context,
    }
}))
