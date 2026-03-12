# Agent Patterns & Conventions

Reference for the `/agent-creator` skill. Standard patterns for writing and maintaining Claude Code sub-agents.

## File Structure

```yaml
---
name: kebab-case-identifier
description: "Detailed description with 3-4 concrete triggering examples using arrows"
model: claude-sonnet-4-6    # or claude-haiku-4-5-20251001, claude-opus-4-6
---
```

Optional: `color` field (purple, pink, red, blue, green, orange, yellow).

## Description Field (Triggering)

The description is the **primary triggering mechanism**. Write it to match real user language:

- Include 3-4 concrete examples: `"Fix auth bug → launch backend-engineer"`
- Err on the side of being pushy — undertriggering is more common than overtriggering
- Use natural language, not formal specs
- Include negative triggers ("do NOT trigger when...")

## Body Section Order

1. **Boundaries** — what the agent IS and IS NOT responsible for
2. **Context Loading** — load project specialization + `agents/memory/SHARED.md`
3. **Domain Rules** — non-negotiable standards (security, a11y, data integrity)
4. **Workflow/Protocol** — numbered steps describing methodology
5. **Report Format** — exact Markdown template for output

## Boundary Pattern

Every agent must explicitly define:

```markdown
## What I Do
- [Single domain responsibility]

## What I Don't Do (delegate back)
- [Adjacent domain] → report to EA, don't solve
- [Another domain] → note dependency, don't implement
```

**Key principle:** Agents report dependencies, they don't solve them.
- `backend-engineer` reports "data contracts needed" — doesn't touch UI
- `ui-engineer` reports "API shape I need" — doesn't write Cloud Functions
- `qa-engineer` reports bugs to responsible agent — doesn't fix code
- `content-writer` produces content — doesn't integrate into codebase
- `data-analyst` produces recommendations — doesn't implement changes

## Memory System

### Mandatory Pre-reads
```markdown
1. Read `agents/memory/SHARED.md` (cross-cutting knowledge)
2. Read `agents/memory/<agent-name>/MEMORY.md` (domain knowledge)
3. If project-specific: read `projects/<name>/.agents/<agent-name>.md`
```

### What to Save
- Patterns discovered during work that aren't in code comments
- Bugs or quirks that would bite future work
- Corrections to wrong assumptions in existing memory

### What NOT to Save
- Code patterns visible in the source (just read the file)
- One-time task details
- Anything already in SHARED.md

### Cross-cutting Discoveries
Note any findings relevant to other agents in the report footer:
```markdown
## Cross-cutting Notes (for /remember)
- [Discovery relevant to other agents]
```

## Tool Access by Role

| Role | Tools |
|------|-------|
| Engineering (backend, ui, graphics) | Read, Write, Edit, Glob, Grep, Bash |
| Quality (qa) | Read, Write, Edit, Glob, Grep, Bash |
| Analysis (data-analyst) | Read, Glob, Grep, Bash |
| Content (content-writer) | Read, Glob, Grep |
| Local LLM | Ollama API (localhost:11434) |

## Model Selection

| Complexity | Model | Use For |
|-----------|-------|---------|
| High | claude-opus-4-6 | Complex orchestration, architectural decisions |
| Medium | claude-sonnet-4-6 | Engineering, QA, most skills |
| Low | claude-haiku-4-5-20251001 | Content writing, data formatting, simple analysis |
| Local | ollama:qwen3:14b | Drafting, summarizing, boilerplate |

## Error Escalation

Severity levels:
- **Critical:** Always blocks — escalate immediately
- **High:** Usually blocks — escalate with suggested fix
- **Medium:** May block — EA can defer
- **Low:** Note only — include in report

**Skip self-correction for:**
- Auth/permission failures (can't self-fix credentials)
- Ambiguous requirements (need human decision)
- Data loss risk (destructive operations)

## Report Format Template

```markdown
# [Agent Name] Report

## Summary
[1-2 sentence overview]

## Changes Made
- [File]: [what changed and why]

## Issues Found
| Severity | Issue | Location | Recommendation |
|----------|-------|----------|----------------|
| HIGH | ... | file:line | ... |

## Dependencies / Blockers
- [What other agents need to know or do]

## Cross-cutting Notes (for /remember)
- [Discoveries relevant beyond this agent's domain]
```

## Sizing Guidelines

- **Specialists:** < 200 lines
- **Orchestrators:** < 250 lines
- Focus > length. A 100-line agent with clear protocols beats a 300-line agent with vague instructions.

## Project Specializations

Portal-specific agents live in `projects/Porters-Portal/.agents/<agent-name>.md`:
- No frontmatter needed (inherits from general agent)
- Contains project-specific constraints, file paths, conventions
- Loaded by the general agent as additional context

## Cross-referencing

- Use paths relative to EA root: `agents/memory/SHARED.md`
- For code: `projects/Porters-Portal/src/components/Foo.tsx:42`
- Link related agents: "See also: backend-engineer for API contracts"
- Link memory: "Documented in agents/memory/qa-engineer/MEMORY.md"
