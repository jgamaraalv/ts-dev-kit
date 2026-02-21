# A09:2025 Security Logging & Alerting Failures

5 CWEs, 3.91% avg incidence. Underrepresented in data but critical for incident detection.

## What to look for

**Missing audit logs:**

- Login attempts (successful AND failed) not logged
- Access control failures not logged
- High-value transactions not logged
- Admin actions not logged
- Password changes/resets not logged
- Input validation failures not logged

**Insufficient log context:**

- Logs missing timestamp, user ID, IP address, action performed
- Logs missing request ID for correlation
- Error logs without stack traces (in backend logs, not user-facing)
- No distinction between security events and operational events

**Log integrity issues:**

- Logs stored only locally (no centralized log management)
- Logs not protected from tampering (mutable storage)
- No backup of log files
- Log retention too short for forensic analysis

**Log injection vulnerabilities:**

- User input written to logs without encoding/escaping
- Newlines in user input can forge log entries
- Special characters that manipulate log viewers (ANSI escape codes)

**Sensitive data in logs:**

- Passwords, tokens, API keys logged in plaintext
- Credit card numbers, SSNs, or PII in log entries
- Session IDs logged
- Request bodies with sensitive fields logged without redaction

**Missing alerting:**

- No alerts on repeated failed login attempts
- No alerts on access control violations
- No alerts on unusual patterns (geographic anomalies, time-based anomalies)
- DAST/pentest scans don't trigger alerts
- No incident response plan or playbook
- Alert fatigue from too many false positives

## Prevention checklist

- [ ] Log all authentication events (login, logout, failed attempts, MFA events)
- [ ] Log all access control failures with user context
- [ ] Log all input validation failures
- [ ] Include: timestamp, user ID, IP, action, resource, outcome in every log entry
- [ ] Encode/escape user input in log messages (prevent log injection)
- [ ] Never log passwords, tokens, credit cards, or other secrets
- [ ] Redact sensitive fields before logging (mask PII)
- [ ] Send logs to centralized, append-only log management (ELK, Datadog, etc.)
- [ ] Protect log integrity — use append-only storage, monitor for tampering
- [ ] Set up alerting for: repeated auth failures, access control violations, unusual patterns
- [ ] Create and test incident response playbooks
- [ ] Set appropriate log retention (regulatory requirements vary)
- [ ] Use structured logging (JSON) for machine-parseable log entries
- [ ] Add honeytokens to detect unauthorized access with near-zero false positives

## Key CWEs

| CWE | Name                                      | Common in                |
| --- | ----------------------------------------- | ------------------------ |
| 778 | Insufficient Logging                      | Missing audit trail      |
| 532 | Sensitive Information in Log File         | Logging passwords/tokens |
| 117 | Improper Output Neutralization for Logs   | Log injection            |
| 223 | Omission of Security-relevant Information | Incomplete logs          |
