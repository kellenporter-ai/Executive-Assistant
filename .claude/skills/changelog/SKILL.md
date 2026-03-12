---
name: changelog
description: Generate a changelog or release notes from recent git history. Use when Kellen says "changelog", "release notes", "what shipped", "what changed since last deploy", "generate changelog", "document recent changes", or wants a summary of code changes formatted for documentation.
model: claude-sonnet-4-6
effort: medium
tools: [Read, Glob, Grep, Bash, Agent]
---

## Purpose

Generate structured changelogs from git history by delegating formatting and categorization to the technical-writer agent.

## Steps

1. **Determine scope from `<ARGUMENTS>`:**
   - Date range: "since Monday", "last 2 weeks", "since v1.2"
   - Commit range: "since abc1234", "between abc1234..def5678"
   - Project: specific repo or all repos
   - If no range specified, default to commits since the last changelog or last 7 days.

2. **Collect git history.** Pull commit logs for the target range:

   ```bash
   # EA repo
   cd "/home/kp/Desktop/Executive Assistant"
   echo "=== Executive Assistant ==="
   git log --oneline --since="<date>" --no-merges

   # Portal repo
   cd "/home/kp/Desktop/Executive Assistant/projects/Porters-Portal"
   echo "=== Porter's Portal ==="
   git log --oneline --since="<date>" --no-merges
   ```

   For detailed changelogs, also pull file change stats:
   ```bash
   git log --stat --since="<date>" --no-merges
   ```

3. **Delegate to technical-writer.** Launch the agent with:

   ```
   Generate a changelog from the following git history.

   ## Format
   Group changes by category:
   - **Added** — new features, new files, new capabilities
   - **Changed** — modifications to existing behavior, refactors, improvements
   - **Fixed** — bug fixes, corrections
   - **Removed** — deleted features, removed code
   - **Security** — security-related changes
   - **Performance** — optimization changes

   Each entry: one line, past tense, reference the component/area affected.
   Skip: merge commits, version bumps, formatting-only changes.

   For entries that affect students or teachers, add a [Student-facing] or [Admin-facing] tag.

   ## Git History
   [paste commit log here]

   ## Output Location
   Write the changelog to: [target file path]
   ```

4. **Review output.** Read the technical-writer's changelog. Verify:
   - Categories are correct (a bug fix isn't listed under "Added")
   - Student-facing changes are tagged
   - No internal implementation details exposed if this is for external consumption

5. **Save the changelog.**
   - For ongoing documentation: append to `decisions/changelog.md` (or create if it doesn't exist)
   - For a specific release: save to `temp/changelog-<date>.md`
   - Ask Kellen if the destination isn't clear.

6. **Report to Kellen** with a brief summary of what was generated and where it was saved.

## Inputs
- Optional: date range or commit range
- Optional: target project (EA, Portal, or both)
- Optional: audience (internal dev notes vs. external release notes)

## Output
- Categorized changelog in markdown format
- Saved to appropriate location

## Error Handling

Use the 5-step self-correction loop before escalating.

- **No commits in range:** Report "No changes found in the specified range" and suggest expanding the date range.
- **Ambiguous date:** Parse natural language dates ("last Monday" → calculate actual date). If truly ambiguous, ask Kellen.
- **Escalate immediately:** If the changelog is for external/public release, confirm with Kellen before publishing anywhere.
