---
name: dev-pipeline
description: Use when someone asks to fix a bug, implement a feature, add functionality, resolve an issue, or build something new. Works across any project with a `.agents/` directory. Also triggers on "dev pipeline", "fix and ship", or "build and deploy".
model: claude-sonnet-4-6
effort: max
tools: [Read, Write, Edit, Bash, Glob, Grep, Agent]
---

## What This Skill Does

Project-agnostic development pipeline. Takes a task, applies Backward Design, delegates to specialist agents with project-specific context, builds, and deploys. The EA handles all orchestration — no separate orchestrator agent.

**Pipeline:** Backward Design → Delegate → QA → Build → Deploy → Verify

---

## Step 0: Detect Project

Determine the target project from `<ARGUMENTS>` or the working directory. If ambiguous, ask.

Load the project's context file:
```
projects/<project-name>/.agents/context.md
```

This file contains: tech stack, build commands, deploy commands, architecture patterns, and project-specific QA criteria. All subsequent steps use this context.

If no `.agents/` directory exists for the project, run a general pipeline without specialization and note that the project would benefit from a `.agents/context.md` file.

---

## Step 1: Backward Design

Before any implementation, apply Backward Design:

### 1. Define the Goal
What does the finished product look like? How should it function? What does success look like from the user's perspective? Be specific — "the button saves the form" not "improve the save flow."

### 2. Identify Components
What pieces are required to achieve that goal? Which layers of the stack are affected (frontend, backend, data, content)? List every component that must exist or change.

### 3. Plan the Build
How will each component be built? How do they connect to achieve the goal? What's the dependency order — what must be built first?

For **small tasks** (single-file bug fixes, copy changes): Backward Design can be a mental checklist — don't over-formalize it. State the goal, identify what changes, and proceed.

For **large tasks** (new features, multi-component work): Write a brief plan before delegating. The plan doesn't need to be a formal spec — just goal, components, and build order.

---

## Step 2: Delegate to Specialist Agents

For each component identified in Step 1, launch the appropriate agent. When building the agent prompt:

1. Start with the task description.
2. If `projects/<project-name>/.agents/<agent-name>.md` exists, append it as a project specialization block.
3. Include relevant context from the Backward Design plan (what this component must achieve, how it connects to other components).

**Available general agents** (in `agents/`):
- `ui-engineer` — Frontend components, styling, accessibility, responsive design
- `backend-engineer` — Server-side logic, APIs, database, security rules
- `qa-engineer` — Testing, auditing, accessibility compliance, spec verification
- `content-writer` — UI copy, instructional content, user-facing text
- `data-analyst` — Data queries, engagement metrics, analytics reports
- `graphics-engineer` — 3D scenes, SVG rendering, visual effects, animations
- `deployment-monitor` — Post-deploy health checks

**Project-only agents** (in `projects/<name>/.agents/`):
- `economy-designer` (Portal) — XP rates, loot tables, currency sinks, boss stats, ability effects, progression curves. **Launch this agent before backend-engineer when the task involves economy mechanics** (loot generation, shop pricing, XP formulas, combat stats). Economy-designer produces the spec; backend-engineer implements the Cloud Functions.

Check the `.agents/` directory for other project-specific agents. See `agents/ROUTING.md` for full routing guidance.

### Delegation format:
```
The user wants: [task description]

Your goal for this delegation: [specific component goal from Backward Design]

How this connects: [what other components depend on or feed into this work]

Available agents for coordination: [other agents involved in this task]

## Project Specialization
[Contents of projects/<name>/.agents/<agent-name>.md, if it exists]
```

Run agents in parallel when their tasks are independent. Stagger when there are dependencies (e.g., types/models before UI that consumes them).

---

## Step 3: QA

After all engineering agents complete, launch the **qa-engineer** with all changed files and the Backward Design goal. Include the project's QA specialization if it exists.

**If the task involved UI changes**, also include in the QA delegation:
- Which pages/routes were affected by the changes
- Paths to any standalone HTML files that were created or modified
- The note: "Visual inspection required — screenshot affected pages at 1366x768"

If QA rejects:
1. Read each bug report.
2. Route each bug to the responsible agent.
3. After fixes, re-run QA.

---

## Step 4: Build

Once QA signs off, execute the build commands from `context.md`. Both frontend and backend if applicable.

If the build fails:
1. Read errors — determine which agent's code caused them.
2. Launch the responsible agent to fix.
3. Re-build until clean.

**Never deploy broken code. Never skip the build.**

---

## Step 5: Commit and Push

```bash
cd "<project-path>"
git add <specific files that were modified>
git commit -m "<concise description>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
git push origin main
```

Stage specific files — never `git add -A` or `git add .`. Imperative mood, under 72 chars first line.

---

## Step 6: Deploy

Skip deploy if changes are purely local tooling, dev config, or documentation.

For deployable changes, delegate to the **release-engineer** agent with: the list of commits, affected deploy targets (hosting/functions/rules/indexes), confirmation that build passed and QA signed off, and the project's `.agents/release-engineer.md` specialization if it exists.

The release-engineer handles deploy ordering (indexes → rules → functions → hosting), pre-deploy gates, and rollback preparation. Do NOT deploy inline — always delegate.

---

## Step 7: Post-Deploy Verification

After release-engineer reports success, launch the **deployment-monitor** agent with the project specialization to verify production health. Include a summary of what was deployed. If deployment-monitor reports critical issues, route back to release-engineer for rollback.

---

## Step 8: Report

Provide a brief summary:
- What was changed and why (the Backward Design goal)
- Which agents contributed
- Files modified
- Build + QA status
- Deploy status
- Post-deploy health

---

## Error Handling

Use the 5-step self-correction loop (Read → Research → Patch → Retry → Log) at each pipeline stage. Max 3 retry loops per stage before escalating.

- **Build failure:** Read compiler output → identify responsible agent → launch with error context → rebuild.
- **QA rejection:** Route each defect to the responsible agent → re-run QA after fixes.
- **Deploy failure:** Check deploy logs → verify build artifacts exist → retry with narrower scope (`--only hosting` or `--only functions`).
- **Agent timeout/failure:** Retry once with a simplified prompt (reduce scope or split the task). If the agent fails twice: for simple components (copy, config, single-file changes), handle directly in the EA context. For complex components (multi-file features, 3D/SVG work), escalate to the user with what the agent attempted and where it failed — don't attempt complex engineering inline.
- **Escalate immediately:** Permission/auth failures, ambiguous requirements, changes that would affect live student data.
- **Write intermediate build/test output to `temp/`** instead of passing through context when output exceeds ~200 lines.

---

## Notes

- **EA is the orchestrator.** You coordinate directly — no separate orchestrator agent.
- **Backward Design scales.** Quick mental checklist for bugs, brief written plan for features.
- **Project context is loaded, not hardcoded.** Build/deploy commands come from `.agents/context.md`.
- **Agents get specialized at runtime.** General agent + project specialization file = project-aware specialist.
- **Autonomous execution.** The full pipeline runs without pausing for user approval unless a decision is genuinely ambiguous.
- **Build must pass.** QA sign-off + clean build are both required before deploy.
