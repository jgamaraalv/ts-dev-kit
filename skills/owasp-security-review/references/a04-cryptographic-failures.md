# A04:2025 Cryptographic Failures

32 CWEs, 3.80% avg incidence, 1.6M+ occurrences. Leads to sensitive data exposure or system compromise.

## What to look for

**Data in transit:**

- HTTP used instead of HTTPS
- Missing HSTS header
- TLS < 1.2 allowed
- Weak cipher suites (CBC mode, RC4, DES)
- Self-signed certificates accepted without validation
- Certificate chain not validated
- STARTTLS used instead of implicit TLS
- FTP, SMTP, or other unencrypted protocols for sensitive data

**Data at rest:**

- Sensitive data stored in plaintext (passwords, tokens, PII, credit cards)
- Database columns with sensitive data not encrypted
- Backups not encrypted
- Sensitive data in log files

**Password storage:**

- MD5 or SHA1 used for password hashing
- Passwords hashed without salt
- Fast hash functions (SHA-256 without key stretching) for passwords
- Missing work factor — use Argon2, scrypt, bcrypt, or PBKDF2

**Key management:**

- Hardcoded encryption keys or API keys in source code
- Keys committed to version control
- Keys not rotated
- Weak key generation (predictable seeds, insufficient entropy)
- Keys stored in plaintext files
- Same key used across environments

**Weak algorithms:**

- MD5, SHA1 for integrity/signatures
- DES, 3DES, RC4 for encryption
- RSA without OAEP padding
- ECB mode for block ciphers
- `Math.random()` or similar non-CSPRNG for security purposes

**Missing encryption:**

- Caching of responses containing sensitive data (CDN, Redis, browser)
- Sensitive data in URL query strings
- Sensitive data in cookies without encryption

## Prevention checklist

- [ ] Classify data by sensitivity; apply controls per classification
- [ ] Encrypt all data in transit with TLS >= 1.2, forward secrecy ciphers
- [ ] Enable HSTS with `includeSubDomains` and `preload`
- [ ] Encrypt sensitive data at rest
- [ ] Hash passwords with Argon2, scrypt, or bcrypt (with appropriate work factor)
- [ ] Use authenticated encryption (AES-GCM, ChaCha20-Poly1305) — never just encryption
- [ ] Generate keys with CSPRNG; store in HSM or secrets manager
- [ ] Rotate keys regularly; never hardcode keys in source
- [ ] Disable caching for responses with sensitive data
- [ ] Drop support for TLS < 1.2 and CBC ciphers
- [ ] Don't store sensitive data unnecessarily; discard when no longer needed
- [ ] Use `crypto.randomUUID()` or `crypto.getRandomValues()` (Node.js) — never `Math.random()`
- [ ] Validate server certificates and trust chains

## Key CWEs

| CWE | Name                                    | Common in                   |
| --- | --------------------------------------- | --------------------------- |
| 327 | Broken or Risky Cryptographic Algorithm | MD5, SHA1, DES usage        |
| 328 | Reversible One-Way Hash                 | Weak password hashing       |
| 330 | Use of Insufficiently Random Values     | Predictable tokens          |
| 338 | Cryptographically Weak PRNG             | Math.random() for secrets   |
| 321 | Use of Hard-coded Cryptographic Key     | Keys in source code         |
| 319 | Cleartext Transmission                  | HTTP, unencrypted protocols |
| 326 | Inadequate Encryption Strength          | Short keys, weak ciphers    |
| 916 | Password Hash With Insufficient Effort  | Fast hashing for passwords  |
