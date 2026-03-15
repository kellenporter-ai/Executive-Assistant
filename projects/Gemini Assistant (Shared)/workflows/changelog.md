# Workflow: Changelog

Generate a changelog from recent git history.

## Step 1: Determine Scope

Ask (or infer) the time range:
- Since last tag? `git describe --tags --abbrev=0`
- Since a specific date?
- Last N commits?

Default: since last tag, or last 2 weeks if no tags exist.

## Step 2: Gather Commits

```bash
git log --oneline --no-merges [range]
```

For multi-repo workspaces, gather from each project repo too.

## Step 3: Categorize

Group commits into categories:
- **Added** — New features or capabilities
- **Changed** — Modifications to existing features
- **Fixed** — Bug fixes
- **Removed** — Removed features or deprecated code
- **Security** — Security-related changes
- **Performance** — Optimization changes

## Step 4: Generate

```markdown
# Changelog

## [version or date range]

### Added
- [description] ([commit hash])

### Changed
- [description] ([commit hash])

### Fixed
- [description] ([commit hash])

### Removed
- [description] ([commit hash])
```

## Step 5: Deliver

Save to `CHANGELOG.md` in the project root (append to existing) or present inline.

Delegate to the technical-writer agent if the changelog needs polish or expanded descriptions.
