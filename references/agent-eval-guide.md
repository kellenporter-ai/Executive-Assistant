# Agent Eval & Benchmark Guide

Reference for deep evaluation, benchmarking, and description optimization of agents created with the `agent-creator` skill. For basic agent creation/editing, see `.claude/skills/agent-creator/SKILL.md`.

---

## Eval Infrastructure Overview

Workspace layout: `agent-creator-workspace/iteration-N/eval-<ID>/`

The skill-creator plugin provides reusable tooling:
- **Base path**: `/home/kp/.claude/plugins/cache/claude-plugins-official/skill-creator/205b6e0b3036/skills/skill-creator/`
- `eval-viewer/generate_review.py` — HTML review viewer
- `scripts/aggregate_benchmark.py` — Benchmark aggregation
- `agents/comparator.md` — Blind A/B comparison (advanced use)
- `assets/eval_review.html` — Trigger eval review template

---

## Running and Evaluating Test Cases

### Step 1: Spawn All Runs

For each test case, spawn two subagents in the same turn:

**With-agent run:** Launch the agent using the Agent tool with the test prompt. Have it save outputs to the workspace.

```
Execute this task using the agent defined at <path-to-agent.md>:
- Task: <eval prompt>
- Context files: <eval files if any>
- Save outputs to: <workspace>/iteration-N/eval-<ID>/with_agent/outputs/
```

**Baseline run:** Same prompt, but without the agent — just a general-purpose subagent with no specialized instructions.

When **improving** an existing agent, snapshot the original first (`cp <agent.md> <workspace>/agent-snapshot.md`) and use the snapshot as baseline.

Write an `eval_metadata.json` for each test case:

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name",
  "prompt": "The task prompt",
  "assertions": []
}
```

### Step 2: Draft Assertions While Runs Are In Progress

Good assertions for agents focus on:

- **Behavioral boundaries**: "The agent did not modify files outside its domain"
- **Output format compliance**: "The agent produced a structured sign-off report"
- **Protocol adherence**: "The agent followed the delegation protocol with all required fields"
- **Quality indicators**: "The output addresses all requirements from the prompt"
- **Boundary respect**: "The agent reported backend needs rather than implementing them itself"

Update `eval_metadata.json` and `evals/evals.json` with the assertions.

### Step 3: Capture Timing Data

When each subagent completes, save `total_tokens` and `duration_ms` from the notification to `timing.json` in the run directory.

### Step 4: Grade, Aggregate, and Review

1. **Grade each run** — read `agents/grader.md` and evaluate each assertion against the outputs. Save to `grading.json`. Use `text`, `passed`, and `evidence` fields.

2. **Aggregate into benchmark**:
   ```bash
   python -m scripts.aggregate_benchmark <workspace>/iteration-N --skill-name <agent-name>
   ```
   (Run from the skill-creator directory.)

3. **Analyst pass** — read benchmark data and surface patterns. See `agents/analyzer.md`.

4. **Launch the viewer**:
   ```bash
   nohup python /home/kp/.claude/plugins/cache/claude-plugins-official/skill-creator/205b6e0b3036/skills/skill-creator/eval-viewer/generate_review.py \
     <workspace>/iteration-N \
     --skill-name "<agent-name>" \
     --benchmark <workspace>/iteration-N/benchmark.json \
     > /dev/null 2>&1 &
   VIEWER_PID=$!
   ```
   For iteration 2+, add `--previous-workspace <workspace>/iteration-<N-1>`.

5. **Tell the user** the viewer is open and explain what they'll see.

### Step 5: Read Feedback

When the user says they're done reviewing, read `feedback.json`. Empty feedback = looks good. Focus improvements on test cases with specific complaints.

Kill the viewer when done: `kill $VIEWER_PID 2>/dev/null`

---

## The Iteration Loop

1. Apply improvements to the agent `.md` file
2. Rerun all test cases into `iteration-<N+1>/`
3. Launch the viewer with `--previous-workspace` pointing at the previous iteration
4. Wait for user review
5. Read feedback, improve, repeat

Keep going until:
- The user is happy
- All feedback is empty
- You're not making meaningful progress

---

## Description Optimization

After the agent is working well, optimize its description for triggering accuracy.

### Step 1: Generate Trigger Eval Queries

Create 20 eval queries — a mix of should-trigger and should-not-trigger. Save as JSON:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

Queries must be realistic — specific tasks with file paths, personal context, details.

**Should-trigger queries (8-10):** Different phrasings of tasks this agent handles. Include cases where the user doesn't name the agent explicitly. Include edge cases where this agent competes with another but should win.

**Should-not-trigger queries (8-10):** Near-misses that share keywords but actually need a different agent or no agent at all.

### Step 2: Review with User

1. Read template from the skill-creator's `assets/eval_review.html`
2. Replace `__EVAL_DATA_PLACEHOLDER__` with the JSON array, `__SKILL_NAME_PLACEHOLDER__` with agent name, `__SKILL_DESCRIPTION_PLACEHOLDER__` with current description
3. Write to `/tmp/eval_review_<agent-name>.html` and open it
4. User edits and exports — check `~/Downloads/eval_set.json`

### Step 3: Run the Optimization Loop

```bash
python -m scripts.run_loop \
  --eval-set <path-to-trigger-eval.json> \
  --skill-path <path-to-agent-dir> \
  --model <model-id> \
  --max-iterations 5 \
  --verbose
```

Run from the skill-creator scripts directory. Periodically check progress.

### Step 4: Apply the Result

Take `best_description` from the output and update the agent's frontmatter. Show before/after and report scores.

---

## Eval JSON Schemas

Test cases are saved to `evals/evals.json`:

```json
{
  "agent_name": "example-agent",
  "evals": [
    {
      "id": 1,
      "prompt": "Realistic task prompt the user would say",
      "expected_output": "Description of what success looks like",
      "context_files": [],
      "expectations": []
    }
  ]
}
```

See `references/schemas.md` for the full schema.

---

## Other Reference Files

- `references/agent-patterns.md` — Standard patterns, boilerplate blocks, and conventions
- `references/schemas.md` — JSON schemas for evals.json, grading.json, benchmark.json
- `agents/grader.md` — How to evaluate assertions against agent outputs
- `agents/analyzer.md` — How to analyze benchmark results and surface patterns
