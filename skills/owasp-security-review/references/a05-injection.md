# A05:2025 Injection

- [What to look for](#what-to-look-for)
- [Prevention checklist](#prevention-checklist)
- [Code patterns](#code-patterns)
- [Key CWEs](#key-cwes)

37 CWEs, 3.08% avg incidence, 1.4M+ occurrences, 62K+ CVEs. Includes XSS (30K+ CVEs) and SQLi (14K+ CVEs).

## What to look for

**SQL Injection:**

- String concatenation in SQL queries: `"SELECT * FROM users WHERE id = " + userId`
- Template literals in SQL: `` `SELECT * FROM users WHERE id = ${userId}` ``
- ORM raw queries with user input interpolated
- Stored procedures that concatenate user input
- Missing parameterized queries / prepared statements

**Cross-Site Scripting (XSS):**

- User input rendered in HTML without encoding/escaping
- `dangerouslySetInnerHTML` in React with unsanitized content
- `innerHTML`, `outerHTML`, `document.write()` with user input
- URL parameters reflected in page without encoding
- Missing Content-Security-Policy header
- SVG or HTML file uploads served inline

**Command Injection:**

- Shell commands built via string concatenation with user input
- Using `exec()` instead of `execFile()` with argument arrays in Node.js
- User input passed to `eval()`, `Function()`, `setTimeout(string)`
- Template engines with unescaped user input (SSTI)

**NoSQL Injection:**

- MongoDB queries with user-controlled operators (`$gt`, `$ne`, `$where`)
- JSON body parsed directly into query filters without validation

**Other injection types:**

- LDAP queries with unescaped user input
- XPath queries with string concatenation
- Header injection (CRLF in user-controlled header values)
- Log injection (unescaped user input in log messages)
- Expression Language injection (Spring EL, OGNL)

**LLM Prompt Injection:**

- User input passed directly into LLM prompts without sanitization
- See OWASP LLM Top 10 for detailed guidance

## Prevention checklist

- [ ] Use parameterized queries / prepared statements for ALL database access
- [ ] Use ORM methods properly — avoid raw query interpolation
- [ ] Context-aware output encoding (HTML, JS, URL, CSS contexts)
- [ ] In React: avoid `dangerouslySetInnerHTML`; if necessary, sanitize with DOMPurify
- [ ] Set `Content-Security-Policy` header to restrict inline scripts
- [ ] Use `execFile()` with argument arrays instead of shell string interpolation
- [ ] Never use `eval()` or `Function()` with user input
- [ ] Validate and sanitize all input server-side (allowlist preferred over denylist)
- [ ] For file uploads: validate MIME type, don't serve inline, use Content-Disposition: attachment
- [ ] Encode user input in log messages to prevent log injection
- [ ] Use SAST/DAST tools in CI/CD to catch injection flaws early

## Code patterns

**Bad — SQL string concatenation (Node.js):**

```js
db.query(`SELECT * FROM users WHERE email = '${req.body.email}'`);
```

**Good — Parameterized query:**

```js
db.query("SELECT * FROM users WHERE email = $1", [req.body.email]);
```

**Bad — Shell command with string interpolation:**

```js
// DANGEROUS: allows command injection
const cmd = "convert " + req.query.filename + " output.png";
```

**Good — Argument array (no shell):**

```js
// SAFE: arguments passed as array, not interpreted by shell
execFile("convert", [req.query.filename, "output.png"]);
```

## Key CWEs

| CWE | Name                                 | Common in            |
| --- | ------------------------------------ | -------------------- |
| 79  | Cross-site Scripting (XSS)           | Web frontends        |
| 89  | SQL Injection                        | Database queries     |
| 78  | OS Command Injection                 | Shell commands       |
| 94  | Code Injection                       | eval(), dynamic code |
| 77  | Command Injection                    | Subprocess calls     |
| 20  | Improper Input Validation            | All input handling   |
| 116 | Improper Encoding/Escaping of Output | Template rendering   |
