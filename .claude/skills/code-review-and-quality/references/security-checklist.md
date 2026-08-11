# Security Review Checklist

Depth for the security axis of the `code-review` skill. Treat every item as a check against the change under review; each failed check is a finding (usually `Critical` or `Required`). The sections below map the OWASP Top 10 onto concrete, per-diff checks — plus a final list of what *not* to flag.

## Injection
- SQL: all queries parameterized / prepared; no string concatenation of user input. ORM raw queries escape their arguments.
- NoSQL: operators from user input rejected (`$where`, `$gt`-style injection).
- OS command: no shell interpolation of user input; pass argument arrays (`execFile`), not `sh -c "... $input"`.
- Template / SSTI: user input is never evaluated as a template.
- Path traversal: file paths from input are normalized and confined to an allowed root (`../` escapes blocked).
- XXE: XML parsers have external-entity and DTD resolution disabled before parsing untrusted documents.

## Cross-site scripting (XSS)
- Output encoded for its context (HTML body, attribute, JS, URL).
- No `dangerouslySetInnerHTML` / `innerHTML` with unsanitized input; sanitize with a vetted library (DOMPurify), or use `textContent`.
- A Content-Security-Policy is set for HTML responses; framework auto-escaping is not bypassed.

## Authentication / authorization
- Every protected endpoint checks authentication AND authorization — not just "logged in", but "allowed to do this".
- Object-level access (IDOR): the caller may access the specific record id, not merely reach the route.
- Auth logic fails closed: a thrown error must deny, never fall through to allow.
- Passwords compared with a constant-time hash verify (`bcrypt.compare`), never `==` on plaintext or on a raw digest.
- JWT: signature verified with a pinned algorithm (reject `alg: none` and HS/RS confusion); `exp`/`aud`/`iss` validated; signing keys come from a secret store, not source.

## Secrets
- No API keys, passwords, tokens, or private keys in source, logs, or fixtures.
- Secrets come from env vars or a secret manager; required ones validated at startup.
- Nothing secret is echoed into error messages or client responses.

## Untrusted data at boundaries
- All external input (request bodies, query params, headers, webhooks, uploads, third-party API responses, config files) validated against a schema before use in logic or rendering.
- File uploads: type, size, and content validated; stored outside the web root; never executed.
- Deserialization: no unsafe `pickle` / `yaml.load` / native deserialization of untrusted bytes.

## SSRF
- Server-side fetches to user-supplied URLs are allow-listed; cloud metadata endpoints (`169.254.169.254`) and internal ranges blocked.

## Transport & crypto
- TLS for data in transit; no `verify=false` / disabled cert checks.
- Passwords hashed with a slow KDF (bcrypt / scrypt / argon2), never MD5 / SHA-1.
- No home-rolled crypto — use the platform library. Security-sensitive randomness uses a CSPRNG, not `Math.random`.
- Sensitive data encrypted at rest where required; encryption keys managed, not hardcoded.

## Security headers & misconfiguration
- Security headers set for HTML/API responses: HSTS, `X-Content-Type-Options: nosniff`, frame protection (`frame-ancestors` / `X-Frame-Options`), `Referrer-Policy`.
- Cookies: `HttpOnly`, `Secure`, and `SameSite` set on session/auth cookies.
- CORS is not `Access-Control-Allow-Origin: *` combined with credentials; origins are allow-listed.
- Debug/verbose mode off in production paths; default or sample credentials changed; admin/diagnostic routes not publicly reachable.

## CSRF
- State-changing browser endpoints protected (anti-CSRF token or SameSite cookies).

## Race conditions & state integrity
- Check-then-act on shared state (balances, quotas, stock, uniqueness) is done under a row lock (`SELECT ... FOR UPDATE`), an atomic update, or a unique constraint — not a read followed by a separate write. A balance/limit check without a lock is a TOCTOU/double-spend finding.
- Money and other exactly-once operations carry an idempotency key so a retry can't apply twice.

## Logging, errors & rate limiting
- Errors don't leak stack traces, queries, or internal paths to clients.
- Security-relevant events (authentication failures, access-control denials, input-validation rejections) are logged for detection.
- Logs are free of secrets, tokens, full card/PII data — sanitized before write.
- Authentication, and expensive or enumeration-prone endpoints, are rate-limited.

## Dependencies / supply chain
- A new dependency is justified against stdlib / existing utilities; actively maintained; license compatible.
- `npm audit` (or equivalent) is clean, or findings are triaged.
- Version bumps reviewed against the changelog, isolated per package, with the lockfile diff reviewed and committed. A bulk "bump deps" with no changelog review is a finding.
- Watch for typosquatting and recently-compromised maintainers on newly added packages.

## Common false positives — verify context before flagging
- Placeholder values in `.env.example` / sample config — not real secrets.
- Clearly-marked test credentials in test files.
- Keys that are intentionally public (publishable API keys designed for client exposure).
- SHA-256 / MD5 used as a **checksum or cache key**, not as a password hash — only flag when it's guarding a credential.
- A missing check that a higher layer (gateway, middleware, framework default) already enforces — confirm it's actually absent in the request path before reporting.
