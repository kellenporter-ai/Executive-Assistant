---
name: dependency-audit
description: Check for outdated packages, security vulnerabilities, and license issues in project dependencies. Use when Kellen says "check dependencies", "npm audit", "outdated packages", "security scan", "dependency audit", "are our packages up to date", or wants to verify dependency health before a release.
model: claude-haiku-4-5-20251001
effort: low
tools: [Bash, Read, Glob]
---

## Purpose

Run dependency health checks (outdated packages, security vulnerabilities) and produce a prioritized report.

## Steps

1. **Determine project from `<ARGUMENTS>`.** Default to Porter's Portal (`projects/Porters-Portal`). If a path is given, use that.

2. **Run security audit:**
   ```bash
   cd "<project-path>" && npm audit --json 2>/dev/null | head -200
   ```
   Parse the JSON output. Count vulnerabilities by severity (critical, high, moderate, low).

3. **Check for outdated packages:**
   ```bash
   cd "<project-path>" && npm outdated 2>/dev/null
   ```
   Capture the table of current vs wanted vs latest versions.

4. **Check Cloud Functions dependencies** (if applicable):
   ```bash
   cd "<project-path>/functions" && npm audit --json 2>/dev/null | head -200
   cd "<project-path>/functions" && npm outdated 2>/dev/null
   ```

5. **Report to Kellen:**

   ```markdown
   ## Dependency Audit: [project name]

   ### Security Vulnerabilities
   | Severity | Count | Action |
   |----------|-------|--------|
   | Critical | X | Fix immediately |
   | High | X | Fix this sprint |
   | Moderate | X | Review when convenient |
   | Low | X | Note only |

   **Top critical/high issues:**
   - [package@version]: [vulnerability description] → `npm audit fix` or manual update to [version]

   ### Outdated Packages
   | Package | Current | Wanted | Latest | Risk |
   |---------|---------|--------|--------|------|
   | react | 18.2.0 | 18.2.0 | 19.0.0 | Major — breaking changes likely |

   ### Recommendations
   1. [Prioritized list of what to update and in what order]
   ```

6. **For critical/high vulnerabilities**, suggest the specific fix command. If `npm audit fix` can resolve it, say so. If it requires a manual major version bump, flag the risk.

## Inputs
- Optional: project path (defaults to Porter's Portal)

## Output
- Security vulnerability report with severity counts
- Outdated packages list with risk assessment
- Prioritized fix recommendations

## Error Handling

- **npm not found:** Check if in correct directory. Try `npx` fallback.
- **No package-lock.json:** Run `npm install` first to generate it, then audit.
- **Escalate immediately:** If critical vulnerabilities affect authentication, data access, or student PII — flag prominently.
