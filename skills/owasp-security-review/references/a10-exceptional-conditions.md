# A10:2025 Mishandling of Exceptional Conditions

- [What to look for](#what-to-look-for)
- [Prevention checklist](#prevention-checklist)
- [Code patterns](#code-patterns)
- [Key CWEs](#key-cwes)

New category for 2025. 24 CWEs, 2.95% avg incidence, 769K+ occurrences.

## What to look for

**Failing open:**

- Error conditions that grant access instead of denying it
- Try/catch blocks that silently continue on auth/authz errors
- Default case in permission checks grants access
- Missing `else` or `default` clause assumes success
- Transaction failures that leave partial state (not rolled back)

**Information leakage via errors:**

- Stack traces exposed in HTTP responses
- Database error messages revealing schema/query details
- Internal file paths exposed in error messages
- Technology/version information in error responses
- Different error responses for different failure modes (enables enumeration)

**Unchecked return values:**

- Function return values ignored (especially security-critical functions)
- Promise rejections not handled (unhandledRejection)
- Null/undefined not checked before use
- Database query results assumed to always return data

**Resource leaks on error:**

- File handles not closed in error paths
- Database connections not released on exception
- Memory not freed after error conditions
- Locks not released in exceptional paths

**Missing error handling:**

- No global exception handler / error middleware
- Empty catch blocks (`catch (e) {}`)
- Generic catch-all that swallows specific errors
- No error boundary in React (uncaught render errors crash the app)
- Missing `finally` blocks for cleanup

**Rate limiting and resource exhaustion:**

- No limits on request size, file upload size, query complexity
- No timeouts on external service calls
- No circuit breakers for failing dependencies
- Unlimited concurrent operations lead to resource exhaustion

## Prevention checklist

- [ ] Implement a global exception handler / error middleware
- [ ] Fail closed — deny access on any error in auth/authz paths
- [ ] Roll back entire transactions on failure; never leave partial state
- [ ] Return generic error messages to users; log detailed errors server-side
- [ ] Use consistent error response format across the application
- [ ] Check all return values from security-critical functions
- [ ] Handle all Promise rejections (`.catch()` or `try/catch` with `await`)
- [ ] Clean up resources in `finally` blocks (connections, file handles, locks)
- [ ] Never use empty catch blocks — at minimum, log the error
- [ ] Add error boundaries in React for graceful UI degradation
- [ ] Set rate limits, request size limits, and timeouts everywhere
- [ ] Add circuit breakers for external service calls
- [ ] Centralize error handling — one pattern across the entire application
- [ ] Aggregate repeated identical errors into statistics above a threshold
- [ ] Test error paths: stress testing, fault injection, chaos engineering

## Code patterns

**Bad — Failing open:**

```js
let isAdmin = false;
try {
  isAdmin = await checkAdminRole(userId);
} catch (e) {
  // silently continue — isAdmin stays false... or does it?
}
// If checkAdminRole throws after setting isAdmin = true...
```

**Good — Failing closed:**

```js
let isAdmin;
try {
  isAdmin = await checkAdminRole(userId);
} catch (e) {
  logger.error("Admin check failed", { userId, error: e });
  throw new ForbiddenError("Access denied");
}
```

**Bad — Empty catch:**

```js
try {
  await riskyOperation();
} catch (e) {}
```

**Good — Log and handle:**

```js
try {
  await riskyOperation();
} catch (e) {
  logger.error("riskyOperation failed", { error: e });
  throw new InternalError("Operation failed");
}
```

## Key CWEs

| CWE | Name                                              | Common in                |
| --- | ------------------------------------------------- | ------------------------ |
| 209 | Error Message Containing Sensitive Info           | API error responses      |
| 636 | Not Failing Securely (Failing Open)               | Auth error paths         |
| 248 | Uncaught Exception                                | Missing try/catch        |
| 252 | Unchecked Return Value                            | Ignored function results |
| 476 | NULL Pointer Dereference                          | Missing null checks      |
| 754 | Improper Check for Unusual Conditions             | Edge cases not handled   |
| 755 | Improper Handling of Exceptional Conditions       | Generic catch-all        |
| 703 | Improper Check/Handling of Exceptional Conditions | Missing error handling   |
