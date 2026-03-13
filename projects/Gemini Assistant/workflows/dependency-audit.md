# Workflow: Dependency Audit

Check for outdated packages, security vulnerabilities, and license issues.

## Step 1: Detect Package Manager

Look for:
- `package.json` → npm/yarn/pnpm
- `requirements.txt` / `pyproject.toml` → pip/poetry
- `Cargo.toml` → cargo
- `go.mod` → go modules

## Step 2: Security Audit

Run the appropriate audit command:
```bash
# Node.js
npm audit --audit-level=moderate

# Python
pip-audit  # or safety check

# Rust
cargo audit

# Go
govulncheck ./...
```

## Step 3: Check for Outdated

```bash
# Node.js
npm outdated

# Python
pip list --outdated

# Rust
cargo outdated
```

## Step 4: Report

```
## Dependency Audit

### Security Vulnerabilities
| Package | Severity | Description | Fix |
|---------|----------|-------------|-----|
| [name] | [critical/high/moderate/low] | [description] | [upgrade to version X] |

### Outdated Packages
| Package | Current | Latest | Type |
|---------|---------|--------|------|
| [name] | [version] | [version] | [major/minor/patch] |

### Recommendations
1. [Critical: upgrade X immediately due to CVE-YYYY-NNNN]
2. [Moderate: batch-update minor versions]
3. [Low: major version upgrades to evaluate]
```

## Step 5: Fix (with permission)

If the user wants to fix:
- **Patch/minor updates** — Safe to batch: `npm update` or equivalent
- **Major updates** — One at a time, with testing between each
- **Security fixes** — Prioritize by severity

Always run tests after dependency changes.
