# Structured commit message files

Use this when committing with a multi-section body (for example `Problem / Fixed / Preserved / Localized / Tests`).

Pattern:

1. Write the complete commit message to a temporary text file.
2. Commit with `git commit -F /tmp/message.txt` instead of many shell `-m` arguments.
3. Verify with `git log -1 --format=%B` that all headings and bullets survived exactly.
4. If a commit was already created with a malformed or truncated body, rewrite the message file and run `git commit --amend -F /tmp/message.txt` before reporting the commit.

Why:

- Long `git commit -m ... -m ...` commands are easy to damage through shell quoting, embedded newlines, or wrapper truncation.
- A file-based message preserves the user's preferred structured format and makes verification straightforward.

Minimal command shape:

```bash
cat > /tmp/commit-msg.txt <<'MSG'
feat: concise subject

Problem:
...

Fixed:
...

Preserved:
...

Localized:
...

Tests:
...
MSG

git commit -F /tmp/commit-msg.txt
git log -1 --format=%B
```
