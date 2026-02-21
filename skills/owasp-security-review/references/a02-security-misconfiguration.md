# A02:2025 Security Misconfiguration

Moved from #5 to #2. 16 CWEs, 3.00% avg incidence, 719K+ occurrences.

## What to look for

**Default and unchanged credentials:**

- Default admin accounts still active
- Default passwords in config files or environment variables
- Database connections using default credentials

**Verbose error messages:**

- Stack traces exposed to end users
- Database error details in API responses
- Framework/library version info in error pages
- Missing custom error pages (default 404/500 pages)

**Unnecessary features enabled:**

- Debug mode enabled in production (`DEBUG=true`, `NODE_ENV=development`)
- Unused ports/services running
- Sample/test endpoints deployed to production
- Admin console publicly accessible
- Directory listing enabled

**Missing security headers:**

- No `Strict-Transport-Security` (HSTS)
- No `Content-Security-Policy` (CSP)
- No `X-Content-Type-Options: nosniff`
- No `X-Frame-Options` or `Content-Security-Policy: frame-ancestors`
- No `Referrer-Policy`
- No `Permissions-Policy`

**XXE (XML External Entity):**

- XML parsers with external entity processing enabled
- DTD processing not disabled
- SOAP services accepting XML without entity restrictions

**Cloud/infra misconfig:**

- S3 buckets or cloud storage publicly accessible
- Overly permissive IAM roles
- Security groups allowing 0.0.0.0/0 ingress
- Secrets/keys hardcoded or in plaintext config

**Cookie security:**

- Missing `Secure` flag on cookies in HTTPS
- Missing `HttpOnly` flag on session cookies
- Missing or incorrect `SameSite` attribute
- Sensitive data stored in cookies in cleartext

## Prevention checklist

- [ ] Automate environment hardening — identical config for dev/QA/prod (only credentials differ)
- [ ] Remove all unused features, frameworks, sample apps, documentation
- [ ] Set `NODE_ENV=production` (or equivalent) in production
- [ ] Implement custom error pages; never expose stack traces
- [ ] Add all security headers (HSTS, CSP, X-Content-Type-Options, X-Frame-Options, Referrer-Policy)
- [ ] Set cookie flags: `Secure`, `HttpOnly`, `SameSite=Strict` or `Lax`
- [ ] Disable XML external entity processing and DTDs
- [ ] Review cloud storage permissions (S3, GCS, Azure Blob)
- [ ] Use identity federation and short-lived credentials instead of static keys
- [ ] Automate configuration verification across all environments
- [ ] Disable directory listing on web servers

## Key CWEs

| CWE  | Name                               | Common in                |
| ---- | ---------------------------------- | ------------------------ |
| 16   | Configuration                      | Broad misconfiguration   |
| 611  | Improper Restriction of XXE        | XML parsers              |
| 489  | Active Debug Code                  | Debug mode in production |
| 1004 | Sensitive Cookie Without HttpOnly  | Session cookies          |
| 614  | Sensitive Cookie Without Secure    | HTTPS cookies            |
| 942  | Permissive Cross-domain Policy     | CORS/crossdomain.xml     |
| 526  | Exposure via Environment Variables | Leaked env vars          |
