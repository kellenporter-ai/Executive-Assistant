# Workflow: Dev Pipeline

Full development lifecycle for features and bug fixes. Orchestrates specialist agents from design through validation.

## Step 1: Backward Design (Phase 1)

1. **Analyze the request** — Define the end goals (evidence of success) and architectural constraints first.
2. **Success Criteria Mapping** — Identify what "Pass" looks like before writing code.
3. **Redesign Loop Detection** — If this is a re-entry from a QA failure, analyze why the initial design failed before starting Step 2.

## Step 2: Delegate/Plan (Phase 2)

1. **Task Decomposition** — Decompose into discrete tasks and identify parallel batches (independent tasks).
2. **Identify agents** — Which specialists are needed? (ui-engineer, backend-engineer, etc.)
3. **Dependency mapping** — Which changes depend on others? What can run in parallel?
4. **User review** — Present the plan for confirmation before writing code.

## Step 3: Build & QA (Phase 3)

For each component in the plan:

1. **Delegate (Build)** — Dispatch sub-agents in YOLO mode. Use native parallel dispatch for independent tasks by emitting contiguous tool calls in a single turn.
2. **Hard Gate Verification** — Every build must be followed by an automated verification (linters/tests) and a `qa-engineer` audit.
3. **Self-Correction (Redesign Loop)** — If a build or test fails, the agent must:
   - Research the error
   - Apply one fix
   - Retry (Max 3 correction loops)
   - If failures persist, escalate to Step 1 (Backward Design) to re-evaluate the strategy.

## Step 4: Deploy & Complete (Phase 4)

1. **Final Validation** — Run full project-wide test suite and build.
2. **Handoff** — Present the result to the user.
3. **Session Archival** — Finalize the `session-log.md` and log the action.

**7. Log Action** — Record the final project outcome (success/fail) to the local database:
```bash
python3 tools/system/log_action.py --agent "Manager" --action "Implementation Handoff" --category "Projects" --status "success"
```

- **Auth/Permission errors** — Stop and escalate immediately.
- **Ambiguous requirements** — Ask for clarification before guessing.
- **Data loss risk** — Back up files before destructive operations.
- **Max retries exceeded** — Report the failure log and ask the user for direction.
