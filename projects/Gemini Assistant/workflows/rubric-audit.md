# Workflow: Rubric Audit

Validate rubric quality and assessment design by delegating to the assessment-designer agent. Reports findings with severity ratings and specific fixes.

## Step 1: Identify Target

Determine what's being audited from the user's request:

- A rubric (markdown table, document, or file)
- An assessment with embedded rubrics
- A question bank
- Pasted rubric text in the conversation

If no target is specified, ask what to audit.

## Step 2: Read the Target

Load the rubric or assessment content. If a file path is given, read it. If the user pasted content, use it directly.

## Step 3: Delegate to Assessment-Designer

Launch the **assessment-designer** agent with:

```
Audit the following assessment/rubric for quality issues.

## Audit Checklist
- [ ] Answer neutrality: Can a student reconstruct the correct answer from tier descriptions alone?
- [ ] Tier distinctness: Are all tiers clearly differentiated with concrete criteria?
- [ ] Observable criteria: Are descriptors measurable, not vague? ("shows understanding" is vague — what does it look like?)
- [ ] Cognitive demand alignment: Do higher tiers require genuinely deeper thinking, not just "more" of the same?
- [ ] MC length bias: Are correct answers consistently longer than distractors?
- [ ] Bias check: Does language or context inadvertently advantage certain student groups? (cultural references, gendered scenarios, socioeconomic assumptions, reading level vs. target grade)
- [ ] Clarity: Is language accessible for the target grade level, including ELL students?
- [ ] No answer leakage: No specific equations, values, or procedures appear in rubric text
- [ ] Objective alignment: Does each rubric criterion map to a stated learning objective? Are any objectives unassessed?
- [ ] Tier realism: Is the top tier achievable by a strong student (not superhuman)? Is the bottom tier distinguishable from "no submission"?
- [ ] Coverage: Does the rubric address every scorable element of the assessment?

## Content to Audit
[paste content here]
```

## Step 4: Review Findings

Read the assessment-designer's report. For each violation:

1. **Confirm it's real** — not a false positive.
2. **Rate severity:**
   - **CRITICAL** — Correct answer is leaked in rubric text. Students can reverse-engineer the answer.
   - **HIGH** — Tiers are ambiguous or indistinguishable. Grading will be inconsistent.
   - **MEDIUM** — Wording issues, minor clarity problems, slight bias.
   - **LOW** — Style preferences, formatting, non-critical improvements.

## Step 5: Report

Present findings in this format:

```markdown
## Rubric Audit Results

**Target:** [file name or description]
**Status:** PASS / NEEDS REVISION (X issues)

### Issues Found
| # | Severity | Issue | Location | Suggested Fix |
|---|----------|-------|----------|---------------|
| 1 | CRITICAL | Developing tier reveals the answer | Q3, Tier 2 | Rewrite to describe reasoning quality, not content |

### What Passed
- [Checklist items that were clean]

### Recommended Next Steps
- [Specific actions to fix each issue]
```

## Error Handling

- **File not found:** Ask the user for the correct path.
- **Ambiguous format:** If content isn't recognizable as a rubric or assessment, ask what should be audited.
- **Escalate immediately:** If the rubric is for a live assessment students are currently taking — flag this before suggesting changes.
