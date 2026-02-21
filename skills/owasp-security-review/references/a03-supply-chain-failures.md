# A03:2025 Software Supply Chain Failures

Expanded from "Vulnerable and Outdated Components". 6 CWEs, 5.72% avg incidence. Highest average exploit (8.17) and impact (5.23) scores.

## What to look for

**Vulnerable dependencies:**

- Outdated packages with known CVEs (check `package.json`, `requirements.txt`, `Gemfile`, etc.)
- No lock file (`yarn.lock`, `package-lock.json`) — versions unpinned
- Lock file not committed to version control
- No automated vulnerability scanning (Dependabot, Snyk, npm audit, etc.)
- Transitive dependencies with known vulnerabilities

**Untrusted sources:**

- Packages installed from unofficial registries or URLs
- Git dependencies pointing to forks or unknown repos
- Unsigned packages or missing integrity hashes
- `.npmrc` or pip config pointing to non-standard registries

**Build pipeline risks:**

- CI/CD pipelines without integrity checks
- Build scripts that `curl | bash` from external URLs
- No separation of duties (same person writes and deploys code)
- Secrets in CI config files or build logs
- Missing branch protection rules
- No signed commits or artifact signing

**Unmaintained components:**

- Dependencies with no updates in 2+ years
- Libraries with known EOL (end of life) status
- No alternative available for deprecated packages

**Post-install scripts:**

- npm `postinstall` scripts that execute arbitrary code
- pip `setup.py` with network calls or system commands

## Prevention checklist

- [ ] Generate and maintain an SBOM (Software Bill of Materials) — use CycloneDX or SPDX
- [ ] Track all direct AND transitive dependencies
- [ ] Run `npm audit` / `yarn audit` / `pip-audit` in CI
- [ ] Enable Dependabot, Renovate, or similar for automated dependency updates
- [ ] Pin dependency versions; use lock files; commit lock files
- [ ] Only use packages from trusted registries with verified publishers
- [ ] Prefer signed packages; verify checksums
- [ ] Review and approve dependency updates before merging
- [ ] Remove unused dependencies to reduce attack surface
- [ ] Harden CI/CD: enable MFA, lock down IAM, separate duties, sign builds
- [ ] Use staged rollouts for dependency updates
- [ ] Monitor CVE databases: NVD, OSV, GitHub Advisory Database
- [ ] Audit npm postinstall scripts before adding new dependencies

## Key CWEs

| CWE  | Name                                             | Common in           |
| ---- | ------------------------------------------------ | ------------------- |
| 1104 | Use of Unmaintained Third Party Components       | Abandoned libraries |
| 1395 | Dependency on Vulnerable Third-Party Component   | Known CVEs          |
| 1329 | Reliance on Component That is Not Updateable     | Locked-in versions  |
| 1357 | Reliance on Insufficiently Trustworthy Component | Unverified sources  |
