---
name: rubric-audit
description: Audit rubrics and assessment designs for answer neutrality, tier quality, difficulty calibration, and ISLE alignment. Use when Kellen says "audit this rubric", "check my assessment", "review these tiers", "is this rubric neutral", "validate my questions", or wants quality assurance on assessment content before deploying to students.
model: claude-sonnet-4-6
effort: medium
tools: [Read, Glob, Grep, Agent]
---

## Purpose

Validate rubric quality and assessment design by delegating to the assessment-designer agent, then reporting findings with specific fixes.

## Steps

1. **Identify the target.** Determine what's being audited from `<ARGUMENTS>`:
   - A rubric file (JSON or markdown)
   - An assessment JSON (lesson blocks with rubrics)
   - A question bank file
   - A design doc produced by assessment-designer
   - If no file specified, ask Kellen what to audit.

2. **Read the target file(s).** Load the rubric/assessment content. If it's a Portal assignment, check `assets/` or `temp/` for the relevant files.

3. **Read references.** Load these before delegating:
   - `references/rubric-format.md` — rubric conventions and answer neutrality rules
   - `references/block-types.md` — available block types and their grading behavior

4. **Delegate to assessment-designer.** Launch the assessment-designer agent with this prompt structure:

   ```
   Audit the following assessment/rubric for quality issues.

   ## Audit Checklist
   - [ ] Answer neutrality: Can a student reconstruct the answer from tier descriptions?
   - [ ] Tier distinctness: Are all 5 tiers (Beginning → Mastery) clearly differentiated?
   - [ ] Observable criteria: Are descriptors measurable, not vague?
   - [ ] ISLE alignment: Do higher tiers require deeper ISLE engagement?
   - [ ] Difficulty calibration: Is tier distribution appropriate for the assessment type?
   - [ ] MC length bias: Are correct answers consistently longer than distractors?
   - [ ] ELL accessibility: Is language clear for non-native English speakers?
   - [ ] No specific answers leaked: No equations, values, or model procedures in rubric text

   ## Content to Audit
   [paste content here]

   ## Reference Standards
   [paste rubric-format.md conventions]
   ```

5. **Review findings.** Read the assessment-designer's report. For each violation:
   - Confirm it's a real issue (not a false positive)
   - Rate severity: CRITICAL (answer leaked), HIGH (tier ambiguity), MEDIUM (wording), LOW (style)

6. **Report to Kellen.** Present findings in this format:

   ```markdown
   ## Rubric Audit Results

   **Target:** [file name]
   **Status:** PASS / NEEDS REVISION (X issues)

   ### Issues Found
   | # | Severity | Issue | Location | Fix |
   |---|----------|-------|----------|-----|
   | 1 | CRITICAL | ... | Q3, Tier 2 | ... |

   ### What Passed
   - [Checklist items that were clean]

   ### Recommended Next Steps
   - [Specific actions to fix issues]
   ```

## Inputs
- Path to rubric, assessment JSON, question bank, or design doc
- Optional: specific concerns to focus on ("check answer neutrality only")

## Output
- Structured audit report with severity-rated findings and specific fixes

## Error Handling

Use the 5-step self-correction loop before escalating.

- **File not found:** Ask Kellen for the correct path. Check `assets/`, `temp/`, and `projects/Porters-Portal/` common locations.
- **Ambiguous format:** If the file isn't recognizable as a rubric or assessment, ask Kellen to clarify what they want audited.
- **Escalate immediately:** If the rubric is for a live assessment students are currently taking — flag this before making any changes.
