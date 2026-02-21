# A06:2025 Insecure Design

39 CWEs, 1.86% avg incidence. Focuses on design and architecture flaws — not implementation bugs.

## What to look for

**Missing threat modeling:**

- No documented threat model for the application
- Security requirements not part of user stories
- No abuse/misuse cases defined
- Business logic not validated against adversarial use

**Business logic flaws:**

- No rate limiting on high-value operations (purchases, transfers, account creation)
- Price/quantity manipulation possible via client-side values
- Multi-step workflows that can be skipped or replayed
- State transitions not validated (e.g., order status jumps from "pending" to "shipped")
- Race conditions in concurrent operations (double-spend, TOCTOU)

**Missing security controls by design:**

- Client-side-only enforcement of security rules
- No server-side validation of business rules
- Trust boundary violations (trusting client-sent data as authoritative)
- No separation of concerns between public/private/admin functionality
- Insufficient tenant isolation in multi-tenant systems

**Credential handling:**

- Unprotected storage of credentials
- Knowledge-based recovery ("security questions")
- Credentials sent via insecure channels

**File upload issues:**

- No file type validation (server-side)
- Dangerous file types accepted (.exe, .php, .jsp)
- File content not inspected (MIME type spoofing)
- Uploaded files stored in web-accessible directories
- No file size limits

**Insufficient compartmentalization:**

- Monolithic permissions (all-or-nothing access)
- No network segmentation between tiers
- Single failure point brings down entire system

## Prevention checklist

- [ ] Perform threat modeling for critical flows (auth, payments, data access)
- [ ] Define security requirements in user stories
- [ ] Write misuse cases alongside use cases
- [ ] Validate all business logic server-side — never trust the client
- [ ] Rate-limit high-value operations
- [ ] Validate state transitions (only allow legal state changes)
- [ ] Implement proper tenant isolation in multi-tenant systems
- [ ] Segregate application tiers on network level
- [ ] Validate file uploads: type, size, content; store outside web root
- [ ] Use secure design patterns from OWASP library
- [ ] Test critical flows for race conditions
- [ ] Replace security questions with secure recovery methods (email/SMS link)

## Key CWEs

| CWE | Name                                            | Common in              |
| --- | ----------------------------------------------- | ---------------------- |
| 434 | Unrestricted Upload of File with Dangerous Type | File uploads           |
| 269 | Improper Privilege Management                   | Role systems           |
| 501 | Trust Boundary Violation                        | Client/server boundary |
| 522 | Insufficiently Protected Credentials            | Password storage       |
| 362 | Race Condition                                  | Concurrent operations  |
| 602 | Client-Side Enforcement of Server-Side Security | Frontend-only checks   |
| 799 | Improper Control of Interaction Frequency       | Missing rate limiting  |
| 841 | Improper Enforcement of Behavioral Workflow     | Skippable steps        |
