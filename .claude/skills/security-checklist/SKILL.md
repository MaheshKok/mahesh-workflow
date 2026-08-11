---
name: security-checklist
description: Pre-commit security checklist and secret-management rules — no hardcoded secrets, validate all user input, parameterized queries (SQLi), sanitized HTML (XSS), CSRF, authz checks, rate limiting, non-leaky error messages. Use before any commit and whenever writing or reviewing code that handles user input, authentication/authorization, API endpoints, secrets, or sensitive data. (Distinct from the built-in /security-review branch scanner — this is the standing checklist.)
---

# Security Guidelines

## Mandatory Security Checks

Before ANY commit:
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] CSRF protection enabled
- [ ] Authentication/authorization verified
- [ ] Rate limiting on all endpoints
- [ ] Error messages don't leak sensitive data

## Secret Management

- NEVER hardcode secrets in source code
- ALWAYS use environment variables or a secret manager
- Validate that required secrets are present at startup
- Rotate any secrets that may have been exposed

## Security Response Protocol

If security issue found:
1. STOP immediately
2. Use **security-reviewer** agent
3. Fix CRITICAL issues before continuing
4. Rotate any exposed secrets
5. Review entire codebase for similar issues
