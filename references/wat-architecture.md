# WAT Architecture Mapping

## What is WAT?

WAT (Workflow, Agent, Tool) is an architectural pattern for agentic AI systems that decomposes automation into three decoupled layers: semantic instructions (Markdown SOPs), cognitive orchestration (LLM agents), and deterministic execution (tools/integrations). By separating *what to do* from *who reasons about it* from *how it gets done*, the system stays maintainable, cost-efficient, and resilient to failures.

---

## Terminology Mapping

| WAT Layer | Our Term | Location | Role |
|---|---|---|---|
| **Workflow** | Skill | `.claude/skills/<name>/SKILL.md` | Markdown SOPs that define objectives, steps, inputs, outputs, and error handling |
| **Agent (Manager)** | Executive Assistant | `CLAUDE.md` + `context/` | Central orchestrator — routes tasks, makes decisions, delegates to sub-agents |
| **Agent (Sub)** | Agents | `agents/*.md` + project overrides in `.agents/` | Specialized executors — scoped to a domain, don't make strategic decisions |
| **Tool** | Tools / MCP | `tools/`, Claude Code built-ins, MCP servers | Deterministic scripts and integrations that interact with external systems |
| **State / Memory** | Context + Memory | `context/`, `decisions/`, `~/.claude/.../memory/` | Distributed knowledge that gets injected into the agent at runtime |

---

## Orchestration Flow

```
User Request
     │
     ▼
┌─────────────┐
│  Executive   │  ← CLAUDE.md + context/ loaded at init
│  Assistant   │  ← Stateless; reconstructs state each session
│  (Manager)   │
└──────┬──────┘
       │ routes to appropriate skill
       ▼
┌─────────────┐
│    Skill     │  ← Markdown SOP with steps, inputs, outputs
│  (Workflow)  │  ← Constrains the agent's behavior for this task
└──────┬──────┘
       │ delegates execution
       ▼
┌─────────────┐
│   Agents    │  ← Specialized sub-agents (ui-engineer, qa-engineer, etc.)
│   (Subs)    │  ← Scoped context, execute and report back
└──────┬──────┘
       │ invoke as needed
       ▼
┌─────────────┐
│    Tools    │  ← local-agent.py, grade-assistant.py, MCP servers
│ (Execution) │  ← Deterministic, single-responsibility, error-reporting
└─────────────┘
       │
       ▼
    Output → User / File / Database / Deployment
```

---

## Design Principles (from WAT, applied here)

### 1. Decoupling
Each layer is independently modifiable. Changing a skill's steps doesn't require touching agent definitions or tool scripts. Updating a tool's API integration doesn't change any workflow logic.

### 2. Stateless Agents with Context Injection
The EA and sub-agents are stateless between sessions. Intelligence is reconstructed via `CLAUDE.md`, `context/` files, `decisions/` log, and persistent memory files. No hidden state lives inside the model.

### 3. Hierarchical Delegation
The EA (Manager Agent) doesn't do everything — it routes to specialized sub-agents. Each sub-agent operates with scoped context relevant to its domain, reducing token waste and improving accuracy.

### 4. Cost-Aware Model Routing
- **Opus 4.6** — deep reasoning, complex orchestration, architectural decisions
- **Sonnet 4.6** — utility skills (sign-off, remember, context-sync, daily-briefing)
- **Haiku 4.5** — simple, fast tasks
- **Local Ollama (qwen3:14b)** — drafting, summarization, boilerplate (saves API tokens)

### 5. Error as Context, Not Fatal
When a tool fails, the error is fed back into the agent's reasoning loop as actionable context. The agent evaluates the error and decides: retry, fall back to an alternative, or escalate to Kellen. Skills define error-handling directives to constrain this behavior.

### 6. Version-Controlled Workflows
All skills, agent definitions, and context files are Git-tracked. Changes are reviewable, reversible, and auditable through the decision log.

---

## What We Intentionally Skip (and why)

| WAT Feature | Why We Skip It |
|---|---|
| **Inbox-to-project pipeline** | Kellen's priorities are teaching automation and Portal dev, not enterprise email triage. Can revisit later. |
| **P.A.R.A. auto-classification** | No automated ingestion system to classify. Manual priority management via `current_priorities.md` works for current scale. |
| **Always-on webhooks** | Requires external infra (n8n, Make.com). Adds complexity without matching current needs. |
| **External orchestration platforms** | Claude Code's built-in skill/agent system handles orchestration natively. No need for a separate platform. |
| **MCP servers (Gmail, Slack, Zapier)** | Deferred until there's a concrete use case. Google Calendar MCP is the most likely first addition. |
