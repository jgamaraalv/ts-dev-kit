# A08:2025 Software or Data Integrity Failures

14 CWEs, 2.75% avg incidence, 501K+ occurrences. Focuses on trust boundaries and integrity verification.

## What to look for

**Insecure deserialization:**

- Deserializing data from untrusted sources (user input, cookies, APIs)
- Java `ObjectInputStream` on untrusted data
- Python: using unsafe deserialization (e.g., `pickle`) on untrusted data — use JSON instead
- PHP `unserialize()` on user input
- Node.js YAML deserialization of untrusted data
- JSON with type coercion enabling prototype pollution

**Untrusted code inclusion:**

- Scripts loaded from third-party CDNs without Subresource Integrity (SRI) hashes
- `<script src="...">` without `integrity` attribute
- Dynamic import of modules from user-controlled paths
- iframes loading content from untrusted domains

**Unsigned updates:**

- Auto-update mechanisms that don't verify signatures
- Firmware/software updates downloaded over HTTP
- Package installations without checksum verification
- Docker images pulled without digest verification

**CI/CD integrity:**

- Build artifacts not signed or verified
- Pipeline pulls code/artifacts from untrusted sources
- No separation between build and deploy permissions
- Build environment not isolated

**Cookie/data integrity:**

- Cookies used for authorization decisions without server-side validation
- Client-side data (hidden fields, local storage) trusted for security decisions
- API responses cached and reused without revalidation

**Prototype pollution (JavaScript):**

- Recursive merge of user input into objects
- `Object.assign()` or lodash `_.merge()` with untrusted data
- `__proto__`, `constructor`, `prototype` not filtered from input

## Prevention checklist

- [ ] Use digital signatures to verify software/data integrity
- [ ] Add Subresource Integrity (SRI) hashes to all CDN scripts/styles
- [ ] Verify checksums/signatures for all downloaded packages and updates
- [ ] Use trusted, vetted package registries; consider internal mirrors
- [ ] Implement code review for all changes before deployment
- [ ] Ensure CI/CD has proper segregation, access control, and audit logging
- [ ] Never deserialize untrusted data with unsafe serializers; use JSON with schema validation
- [ ] Validate all serialized data with integrity checks before processing
- [ ] Filter `__proto__`, `constructor`, `prototype` from user input in JavaScript
- [ ] Pin Docker image versions by digest, not just tag
- [ ] Sign build artifacts and verify before deployment

## Key CWEs

| CWE | Name                                                            | Common in             |
| --- | --------------------------------------------------------------- | --------------------- |
| 502 | Deserialization of Untrusted Data                               | API payloads, cookies |
| 829 | Inclusion of Functionality from Untrusted Sphere                | CDN scripts           |
| 494 | Download of Code Without Integrity Check                        | Auto-updates          |
| 345 | Insufficient Verification of Data Authenticity                  | Unsigned artifacts    |
| 915 | Improperly Controlled Modification of Dynamic Object Attributes | Prototype pollution   |
| 565 | Reliance on Cookies without Validation                          | Auth cookies          |
