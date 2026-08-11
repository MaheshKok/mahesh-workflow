# Security Review Checklist

Use this reference for security-sensitive diffs. Verify context before reporting a finding.

## Injection and untrusted input

- Parameterize SQL and NoSQL queries; reject user-controlled operators.
- Pass command arguments as arrays; never interpolate untrusted input into a shell.
- Normalize user-controlled paths and confine them to an allowed root.
- Disable XML external entities and unsafe deserialization for untrusted data.
- Validate request bodies, query parameters, headers, webhooks, uploads, third-party responses, and configuration before use.

## Browser and API security

- Encode output for its HTML, attribute, JavaScript, or URL context.
- Sanitize any unavoidable raw HTML with a vetted library.
- Protect state-changing browser endpoints against CSRF.
- Set secure cookie flags and restrictive CORS/security headers where applicable.
- Rate-limit authentication, expensive, and enumeration-prone endpoints.

## Authentication and authorization

- Check both authentication and permission for the specific action and object.
- Fail closed when authentication or policy evaluation errors.
- Validate JWT signature, pinned algorithm, expiry, audience, and issuer.
- Use constant-time password-hash verification and secure session handling.

## Secrets, transport, and crypto

- Keep credentials and private keys out of source, logs, fixtures, and client errors.
- Load required secrets from an approved secret store and validate them at startup.
- Require TLS; never disable certificate verification.
- Use platform cryptography and a CSPRNG; never invent crypto.

## State integrity

- Protect check-then-write operations with atomic updates, locks, or constraints.
- Use idempotency keys for money and other exactly-once operations.
- Preserve transaction boundaries, rollback behavior, and consistent lock ordering.

## Dependencies

- Justify new dependencies against stdlib and installed packages.
- Review provenance, maintenance, license, advisory status, and lockfile changes.
- Treat bulk version bumps and unexplained transitive changes as review risks.

## Common false positives

- Placeholder values in sample configuration are not real secrets.
- Public client keys are not secret merely because they look token-like.
- Hashes used as checksums or cache keys are not password hashing.
- Do not report a missing check until confirming a gateway, middleware, framework, or database constraint does not already enforce it.
