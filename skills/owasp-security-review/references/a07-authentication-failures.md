# A07:2025 Authentication Failures

36 CWEs, 2.92% avg incidence, 1.1M+ occurrences.

## What to look for

**Credential attacks not mitigated:**

- No rate limiting on login attempts
- No account lockout or progressive delays after failed attempts
- No detection of credential stuffing or password spray attacks
- No CAPTCHA or bot protection on login forms

**Weak password policies:**

- No minimum password length (NIST recommends >= 8 chars, allow up to 64+)
- Forcing complexity rules instead of checking against breached password lists
- Forced periodic password rotation (counterproductive per NIST 800-63b)
- Not checking passwords against known breached lists (haveibeenpwned.com)
- Allowing commonly used passwords ("password", "123456", "admin")

**Missing MFA:**

- No multi-factor authentication option
- MFA easily bypassed via fallback mechanisms
- SMS-only MFA without stronger alternatives (TOTP, WebAuthn)

**Session management issues:**

- Session ID not regenerated after login (session fixation)
- Session ID in URL or hidden fields
- Sessions not invalidated on logout
- No idle timeout or absolute timeout
- SSO logout doesn't invalidate all sessions (missing SLO)

**Hardcoded credentials:**

- Default passwords in code or config
- API keys or service account credentials in source code
- Test/admin accounts with known passwords in production

**Account enumeration:**

- Different error messages for "user not found" vs "wrong password"
- Registration form reveals if an email is already registered
- Password reset reveals if an email exists
- Timing differences between existing/non-existing users

**JWT issues:**

- Missing signature validation
- `alg: none` accepted
- Weak signing keys
- No `aud` or `iss` claim validation
- Token not checked for expiry

## Prevention checklist

- [ ] Implement MFA for all users; enforce for admin accounts
- [ ] Rate-limit login attempts with progressive delays
- [ ] Check passwords against top 10K worst passwords + breached credential lists
- [ ] Follow NIST 800-63b: min 8 chars, allow 64+, no forced rotation, no complexity rules
- [ ] Use the same error message for all login failures ("Invalid credentials")
- [ ] Regenerate session ID after successful login
- [ ] Invalidate sessions server-side on logout; set idle + absolute timeouts
- [ ] Never hardcode credentials; use secrets managers
- [ ] Remove default accounts or force password change on first login
- [ ] Validate JWT claims: `aud`, `iss`, `exp`, `nbf`; reject `alg: none`
- [ ] Use well-tested auth libraries/frameworks instead of custom implementations
- [ ] Log all authentication failures; alert on patterns (stuffing, brute force)

## Key CWEs

| CWE | Name                                            | Common in               |
| --- | ----------------------------------------------- | ----------------------- |
| 287 | Improper Authentication                         | Custom auth logic       |
| 307 | Improper Restriction of Excessive Auth Attempts | Missing rate limiting   |
| 384 | Session Fixation                                | Session not regenerated |
| 521 | Weak Password Requirements                      | Poor password policy    |
| 798 | Use of Hard-coded Credentials                   | Creds in source code    |
| 613 | Insufficient Session Expiration                 | Long-lived sessions     |
| 306 | Missing Authentication for Critical Function    | Unprotected endpoints   |
| 640 | Weak Password Recovery Mechanism                | Security questions      |
