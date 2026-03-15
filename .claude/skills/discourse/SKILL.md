---
name: discourse
description: "Run parallel Claude + Gemini analysis on the same task, then synthesize results for a stronger outcome. Use when you want discourse QA, a second opinion, cross-model synthesis, or independent verification. Triggers on: 'discourse QA', 'run discourse', 'get both perspectives', 'cross-model review', 'Gemini and Claude both review this'."
model: claude-sonnet-4-6
effort: max
tools: [Read, Write, Edit, Bash, Glob, Grep, Agent]
---

## What This Skill Does

Orchestrates parallel work between a Claude Code agent and the Gemini system on the same task, then synthesizes their independent findings into a stronger combined result. Different models have different blind spots — discourse exploits this for better outcomes.

**Protocol:** Parallel Analysis → Collection → Synthesis → Merged Report

---

## When to Use Discourse

**High value:**
- QA audits (most valuable — different models catch different bugs)
- Architecture reviews (two perspectives before committing)
- Security audits (different threat models, different catches)
- Content review (wording, neutrality, pedagogical framing)

**Not worth the overhead:**
- Trivial fixes (typos, config changes, single-line edits)
- Tasks where the answer is unambiguous
- Pure implementation tasks (just have one system do it)

---

## Step 1: Parallel Phase

Launch both agents simultaneously using the Agent tool. Each works independently — do NOT share one system's findings with the other before both complete.

### Claude Agent
Launch the appropriate Claude Code agent (e.g., `qa-engineer`) with the task:
```
[Standard delegation prompt for the Claude agent]
```

### Gemini Agent
Launch `gemini-assistant` with the same task, targeting the equivalent Gemini agent:
```
The user wants: [task description]

Your goal: [same goal as Claude agent — independent analysis]

Target Gemini agent: [equivalent agent name, e.g., qa-engineer]

Important: This is a discourse task. Your analysis will be compared with a Claude Code agent's independent analysis. Focus on thoroughness and flag anything you think is a unique finding.

[Include relevant file paths, context, and requirements]
```

**Launch both in a single message using parallel Agent tool calls.**

---

## Step 2: Collection Phase

Wait for both agents to return their Task Reports. Extract:
- **Claude findings:** list of issues, verdicts, recommendations
- **Gemini findings:** list of issues, verdicts, recommendations, unique findings

---

## Step 3: Synthesis Phase

Compare the two reports and categorize every finding:

### Agreements (High Confidence)
Findings that both systems flagged independently. These go directly into the final report — if two different models found the same issue, it's almost certainly real.

### Disagreements (Needs Resolution)
Findings where the two systems contradict each other. For each disagreement:
1. Review the specific evidence from both sides
2. If one is clearly correct based on the code/spec, resolve it
3. If genuinely ambiguous, escalate to the user with both perspectives

### Unique Findings (Additions)
Findings that only one system caught. Include all of them in the final report with provenance tags:
- `[Claude]` — found only by Claude
- `[Gemini]` — found only by Gemini

---

## Step 4: Merged Report

Produce a single synthesized report:

```markdown
## Discourse Report: [Task Name]

### Method
Parallel analysis by Claude [agent-name] and Gemini [agent-name].

### Verdict: [APPROVED / REJECTED]

### Agreements (Both Systems)
[Findings both flagged — highest confidence]

### Unique Findings
#### Found by Claude
[Findings only Claude caught]

#### Found by Gemini
[Findings only Gemini caught]

### Disagreements (Resolved)
[Any contradictions and how they were resolved]

### Combined Recommendations
[Merged action items from both perspectives]

### Cross-cutting Notes (for /remember)
- [Patterns about what each system catches well]
- [Discourse outcomes worth remembering]
```

---

## Step 5: Memory

After synthesis, check if any cross-cutting learnings emerged:
- Patterns about what Claude catches vs. what Gemini catches
- Discourse outcomes that were notably better than single-system
- Context-agnostic findings to propagate to the Shared version

If present, note them for the `/remember` skill to consolidate.

---

## Notes

- **Independence is critical.** Never share one system's findings with the other before both complete — that defeats the purpose of discourse.
- **Provenance tags matter.** The EA and future agents need to know which system found what, to calibrate trust and improve routing.
- **Discourse is opt-in.** The dev-pipeline defaults to single-system QA. Discourse is for complex, high-stakes, or explicitly requested tasks.
- **Gemini has full file access.** It can read code, run commands, and edit files — it's not limited to just analyzing what you send it.
