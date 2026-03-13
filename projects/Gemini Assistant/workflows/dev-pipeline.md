# Workflow: Dev Pipeline

Full development lifecycle for features and bug fixes. Orchestrates specialist agents from design through validation.

## Step 1: Research & Understand

1. **Analyze the request** — What exactly needs to change? Is this a new feature, enhancement, or bug fix?
2. **Explore the codebase** — Find relevant files, understand existing patterns and conventions.
3. **Reproduction (bugs only)** — Write a test or script that demonstrates the failure. Do not proceed until the bug is confirmed.

## Step 2: Strategy & Design

1. **Draft a plan** — Outline changes across backend, frontend, and tests.
2. **Identify agents** — Which specialists are needed? (ui-engineer, backend-engineer, etc.)
3. **Dependency mapping** — Which changes depend on others? What can run in parallel?
4. **User review** — Present the plan for confirmation before writing code.

## Step 3: Execution

For each component in the plan:

1. **Delegate to the appropriate agent** with a scoped task description.
2. **Parallel dispatch** — If tasks are independent (e.g., frontend + backend), invoke both agents in the same turn.
3. **Self-correction** — If a build or test fails, the agent must:
   - Research the error
   - Apply one fix
   - Retry
   - Max 3 correction loops, then escalate to the user

## Step 4: Quality Audit

1. **Invoke qa-engineer** with the list of changes and the original requirements.
2. QA runs tests, checks security, accessibility, and spec compliance.
3. If QA rejects, route findings back to the responsible engineering agent with fix directions.
4. Re-run QA after fixes. Max 2 QA cycles before escalating.

## Step 5: Final Validation

1. **Run full test suite** — All relevant tests must pass.
2. **Run linting/type checking** — No new violations.
3. **Documentation** — Update relevant docs if the change affects APIs, configuration, or user-facing behavior.

## Step 6: Handoff

Present the result to the user:
```
## Implementation Complete

**Goal:** [original request]
**Changes:**
- [file: description of change]
- [file: description of change]

**Tests:** [pass/fail summary]
**QA:** [pass/fail with any notes]
**Documentation:** [updated / not needed]

**Next Steps:** [deploy instructions, remaining manual steps, or follow-up items]
```

## Error Handling

- **Auth/Permission errors** — Stop and escalate immediately.
- **Ambiguous requirements** — Ask for clarification before guessing.
- **Data loss risk** — Back up files before destructive operations.
- **Max retries exceeded** — Report the failure log and ask the user for direction.
