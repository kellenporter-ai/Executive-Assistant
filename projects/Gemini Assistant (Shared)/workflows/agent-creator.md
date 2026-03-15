# Workflow: Agent Creator

Create, audit, or improve agent definitions in `.gemini/agents/`.

## Creating a New Agent

### Step 1: Define the Domain

1. **What tasks** will this agent handle?
2. **What tools** does it need? (read_file, write_file, shell, etc.)
3. **What should it NOT do?** (explicit boundaries)
4. **Which model tier?** (gemini-2.5-pro for complex work, gemini-2.5-flash for simple/fast tasks)

### Step 2: Check for Overlap

Read existing agents in `.gemini/agents/` and `references/agent-routing.md`:
- Does an existing agent already cover this domain?
- Would expanding an existing agent be better than creating a new one?
- Are boundaries with existing agents clear and non-overlapping?

### Step 3: Write the Agent

Create `.gemini/agents/<name>.md` following this structure:

```markdown
---
name: agent-slug
description: "Exhaustive, mutually exclusive description of when to invoke this agent. Include what it handles AND what it does NOT handle."
model: gemini-2.5-pro | gemini-2.5-flash
---

[Persona — who this agent is and what it specializes in]

## Boundaries
[What this agent does NOT do — explicit exclusions]

## Context Loading
[What to read before starting: memory, project specializations, references]

## [Domain-Specific Rules]
[Non-negotiable principles for this agent's domain]

## Workflow
[Step-by-step process for executing tasks]

## Task Report Format
[Structured output template — ensures the EA can parse results]

## Cross-cutting Notes (for /remember)
[Placeholder for discoveries relevant beyond this agent's domain]
```

### Step 4: Update Routing

Add the new agent to `references/agent-routing.md`:
- Add to the agent table
- Define boundary ownership with overlapping agents
- Add to relevant multi-agent coordination sequences

## Auditing an Existing Agent

1. **Description quality** — Is it specific enough for the EA to route correctly? Are there ambiguous triggers?
2. **Boundary clarity** — Any overlap with other agents?
3. **Tool access** — Does it have the right tools? Too many? Too few?
4. **Report format** — Does it produce structured output the EA can consume?
5. **Context loading** — Does it read the right memory and reference files?

## Improving an Agent

Based on audit findings or user feedback:
1. Refine the description for better trigger accuracy
2. Tighten or clarify boundaries
3. Add domain rules from lessons learned
4. Improve the report format for better EA consumption
