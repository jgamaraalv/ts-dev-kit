# A01:2025 Broken Access Control

The #1 risk. 40 CWEs, 3.74% avg incidence, 1.8M+ occurrences. Includes SSRF (previously separate).

## What to look for

**Missing authorization checks:**

- API endpoints without auth middleware or role checks
- Routes accessible without login (force browsing)
- Missing ownership validation — user can access/modify another user's records by changing an ID
- POST/PUT/DELETE endpoints with no access control
- Admin endpoints accessible to regular users

**IDOR (Insecure Direct Object References):**

- Sequential/predictable IDs in URLs or request bodies (`/api/users/123`)
- No ownership check when accessing resources by ID
- Database queries using user-supplied IDs without verifying the requester owns the record

**CORS misconfiguration:**

- `Access-Control-Allow-Origin: *` on authenticated endpoints
- Reflecting the `Origin` header without validation
- Allowing credentials with wildcard origins

**CSRF:**

- State-changing operations (POST/PUT/DELETE) without CSRF tokens
- Cookie-based auth without SameSite attribute

**Path traversal:**

- File paths constructed from user input without sanitization
- `../` sequences not blocked
- Symlink following without checks

**JWT/session issues:**

- JWTs not validated (signature, expiry, audience, issuer)
- Long-lived JWTs without refresh token rotation
- Sessions not invalidated on logout
- Session IDs in URLs

**SSRF:**

- Server makes HTTP requests to user-supplied URLs
- No allowlist for internal/external URL targets
- DNS rebinding not mitigated

## Prevention checklist

- [ ] Deny by default — only grant access explicitly
- [ ] Implement access control once, reuse everywhere (middleware/decorator pattern)
- [ ] Enforce record ownership in queries (`WHERE user_id = ?` with authenticated user's ID)
- [ ] Validate JWT claims: `aud`, `iss`, `exp`, scopes
- [ ] Set short JWT expiry + refresh token pattern
- [ ] Invalidate sessions server-side on logout
- [ ] Use CSRF tokens or SameSite cookies for state-changing requests
- [ ] Restrict CORS to specific trusted origins
- [ ] Disable directory listing; remove `.git`, backups from web root
- [ ] Log and alert on access control failures
- [ ] Rate-limit API and controller access
- [ ] For SSRF: allowlist target hosts/IPs, block internal ranges (169.254.x.x, 10.x.x.x, etc.)
- [ ] Include access control tests in unit/integration test suites

## Key CWEs

| CWE | Name                                                    | Common in                      |
| --- | ------------------------------------------------------- | ------------------------------ |
| 200 | Exposure of Sensitive Information to Unauthorized Actor | API responses leaking data     |
| 284 | Improper Access Control                                 | Missing auth middleware        |
| 285 | Improper Authorization                                  | Role check bypass              |
| 352 | Cross-Site Request Forgery                              | Cookie-based auth without CSRF |
| 862 | Missing Authorization                                   | Endpoints without auth         |
| 863 | Incorrect Authorization                                 | Flawed role logic              |
| 918 | Server-Side Request Forgery                             | URL fetch from user input      |
| 639 | Authorization Bypass Through User-Controlled Key        | IDOR                           |
