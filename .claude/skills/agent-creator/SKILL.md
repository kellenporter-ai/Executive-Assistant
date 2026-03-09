---
name: agent-creator
description: "Create, audit, and improve Claude Code agents (subagent .md files). Use this skill whenever the user mentions creating a new agent, writing an agent prompt, auditing agent performance, improving an agent's instructions, optimizing agent triggering, reviewing agent descriptions, benchmarking agent quality, or iterating on agent behavior. Also trigger when the user says things like 'make me an agent for X', 'this agent isn't working well', 'audit the QA agent', 'improve the orchestrator', 'my agent keeps doing Y wrong', 'add a new agent to the team', or 'the agent description needs work'. Even if they don't say 'agent' explicitly but describe wanting a specialized autonomous worker that handles a category of tasks, this skill applies."
model: claude-sonnet-4-6
effort: high
tools: [Read, Write, Edit, Glob, Grep, Bash]
---

# Agent Creator

Create new agents, audit existing agents, and iteratively improve them.

## What Are Agents?

Agents are specialized autonomous workers defined as Markdown files in `.claude/agents/`. Each has:

- **YAML frontmatter**: `name`, `description`, `model`, `color`, `memory` fields
- **Markdown body**: Detailed instructions, protocols, and guidelines
- **Persistent memory**: A directory at `.claude/agent-memory/<agent-name>/` with a `MEMORY.md` file auto-loaded into the agent's system prompt

The `description` field is the primary triggering mechanism — it determines when Claude invokes the agent. The body only loads when the agent is actually launched. Agents are invoked via the `Agent` tool with `subagent_type` matching the agent's `name`.

## The Process

1. **Capture intent** — understand what the agent should do
2. **Write** a draft `.md` file
3. **Test** by spawning the agent on realistic prompts
4. **Evaluate** results and iterate
5. **Optimize** the description for accurate triggering

Figure out where the user is in this process and help them progress. If they say "just vibe with me", skip the formal evaluation machinery.

## Reasoning Protocol

This is an analytical skill — use structured reasoning before writing or modifying agents:

1. **Define the Problem** — What capability gap does this agent fill? What failure mode are we fixing? What does success look like?
2. **Research** — Read existing agents in `agents/` for patterns and conventions. Check for overlap with existing agents. Review `agents/memory/SHARED.md` for cross-cutting knowledge.
3. **Analyze** — Map the agent's responsibilities against the team. Identify boundary risks (scope creep, overlap with other agents).
4. **Synthesize** — Draft the agent definition with clear identity, boundaries, protocols, and output format.
5. **Conclude** — Test with realistic prompts, evaluate results, iterate.

For audits and improvements, the same protocol applies: define what's wrong → research the current behavior → analyze root causes → synthesize fixes → test.

---

## Creating an Agent

### Capture Intent

Key questions to answer:

1. **Role**: What is this agent responsible for?
2. **Boundaries**: What should it NOT do?
3. **Triggering**: When should it be launched? What user phrases indicate it's needed?
4. **Model**: Opus for orchestrators/complex reasoning, Sonnet for most specialist work.
5. **Team fit**: Does it interact with other agents? Who delegates to/from it?
6. **Output format**: What does successful completion look like?

Before writing, read existing agents in `.claude/agents/` to match style and conventions. Check `.claude/agent-memory/` to understand the memory system.

### Agent File Structure

```markdown
---
name: agent-name
description: "Detailed description with 3-4 concrete triggering examples. Err on the side of being 'pushy' — undertriggering is more common than overtriggering."
color: green
memory: project
---

# Agent body follows...
```

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Kebab-case identifier (e.g., `data-pipeline-engineer`) |
| `description` | Yes | Triggering description with examples |
| `model` | Yes | `opus` or `sonnet` |
| `color` | Yes | `purple`, `pink`, `red`, `blue`, `green`, `orange`, `yellow` |
| `memory` | Yes | `project` (shared) or `user` (personal) |

### Writing Quality Guidelines

1. **Establish identity and boundaries first.** Open with what the agent does and does NOT do.
2. **Define protocols, not just instructions.** Named protocols with numbered steps beat vague guidance.
3. **Explain the why.** Models follow reasoning better than mandates. Reserve emphatic language for genuine non-negotiables.
4. **Define output formats explicitly.** Show exact templates for reports, sign-offs, delegations.
5. **Include a self-check workflow.** The agent should verify its own work before reporting completion.
6. **Address the memory system.** Include instructions about what to save/not save to persistent memory (see `references/agent-patterns.md`).
7. **Keep it focused.** Under 200 lines for specialists, up to 250 for orchestrators. Create reference files for overflow.

### Test the Agent

Come up with 2-3 realistic test prompts — tasks a real user would delegate. Share with the user for review, then run them.

## Auditing an Existing Agent

Perform a systematic review across four dimensions:

- **Structure**: All frontmatter fields present, 3-4 triggering examples in description, appropriate body length
- **Instruction quality**: Clear identity/boundaries, named protocols, explains "why", explicit output formats, self-check step, memory instructions
- **Team integration**: No significant overlap with other agents, clear delegation paths and handoffs, error escalation path
- **Triggering accuracy**: Description captures correct usage, no obvious false-positives or false-negatives, realistic examples

Run 2-3 test prompts to verify boundaries, protocol adherence, output format, and edge case handling. Present findings as a structured report.

## Improving an Agent

### How to Think About Improvements

1. **Generalize from feedback.** Fix underlying causes, not specific symptoms.
2. **Keep the prompt lean.** Trim instructions that cause unproductive behavior.
3. **Explain the why.** Reframe ALWAYS/NEVER with reasoning.
4. **Watch for boundary violations.** Scope creep is the most common failure mode.
5. **Check protocol adherence.** If the agent skips steps, either remove them or clarify them.
6. **Look at handoff quality.** Ensure output integrates well with the next workflow step.

### Iteration Loop

1. Apply improvements to the agent `.md` file
2. Rerun test cases
3. Review results with user
4. Repeat until satisfied

## Deep Eval, Benchmarking & Description Optimization

For formal evaluation infrastructure — benchmark scripts, grader configs, eval viewers, assertion frameworks, description optimization loops, and A/B comparison — see **`references/agent-eval-guide.md`**.

## Reference Files

- `references/agent-eval-guide.md` — Full eval/benchmark/optimization infrastructure
- `references/agent-patterns.md` — Standard patterns and conventions for agent files
- `references/schemas.md` — JSON schemas for evals.json, grading.json, benchmark.json
- `agents/grader.md` — Assertion evaluation against agent outputs
- `agents/analyzer.md` — Benchmark result analysis
