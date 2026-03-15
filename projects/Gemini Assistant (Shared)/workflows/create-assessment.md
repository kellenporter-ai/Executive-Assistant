# Workflow: Create Assessment

Generate assessments with mixed question types and matching rubrics for any subject and grade level. Every assessment includes a rubric that aligns to the stated learning objectives.

**Output formats:** Standalone HTML (default) or structured markdown
**Output location:** `assets/Assessments/<subject>/`

## Step 1: Gather Requirements

Determine from the user's request:

- **Subject and topic** — What is being assessed? (e.g., "photosynthesis", "the French Revolution", "quadratic equations")
- **Grade level** — Elementary, middle school, high school, AP/college?
- **Assessment purpose** — Formative (check understanding), summative (end-of-unit), or diagnostic (pre-assessment)?
- **Source material** (optional) — File paths to PDFs, documents, or notes that define scope
- **Output format** — HTML (default) or markdown?

If source material is provided, read each file to understand scope, depth, and terminology.

If the request is clear enough to infer subject, grade, and scope, present your plan and proceed. Only block on confirmation when genuinely ambiguous.

## Step 2: Delegate Design to Assessment-Designer

Launch the **assessment-designer** agent with:

```
Design an assessment architecture for:
- Subject: [subject]
- Topic: [topic]
- Grade level: [grade]
- Purpose: [formative/summative/diagnostic]
- Source content summary: [key concepts from source material, if any]

Deliverables:
1. Learning objectives (3-6) the assessment will measure
2. Item types and count per objective (alignment matrix)
3. Cognitive demand distribution across Bloom's taxonomy
4. Rubric tier structure with skill statements
5. Difficulty calibration plan
```

Review the assessment-designer's output. Confirm with the user if the scope, objectives, or item types need adjustment.

## Step 3: Design Questions

You (the orchestrator) now design the specific questions based on the assessment-designer's architecture. The assessment-designer provided the structure; you write the actual items.

### Question Types (choose what fits the content)

- **Free response / short answer** — Students explain, defend, predict, or analyze. Primary question type — require reasoning, not just answers.
- **Multiple choice** — Use sparingly. Distractors must be plausible and educational.
- **Drawing / visual representation** — Students sketch, label, annotate, or construct visual representations (diagrams, maps, storyboards, compositions).
- **Math / show-your-work** — Multi-step problem solving with labeled steps.
- **Data tables** — Students record, organize, or interpret quantitative data.
- **Sorting / classification** — Students categorize items into groups.
- **Ranking / ordering** — Students arrange items by a criterion.
- **Interactive elements** (HTML mode only) — Canvas-based drag-and-drop, graphing, or simulations when they genuinely add value.

### Design Principles

- **Free response emphasis.** Prefer constructed responses over selected responses. Assessments should require students to explain, defend, and reason — not just select answers.
- **One concept per question.** Each question should target one specific skill or understanding.
- **Accessible entry point.** Start with questions most students can attempt, then increase complexity.
- **No trick questions.** Questions should be challenging because the content is demanding, not because the wording is confusing.

## Step 4: Generate the Assessment

### HTML Mode (default)

Generate a single self-contained HTML file:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>[Assessment Title]</title>
    <style>/* All CSS inline */</style>
</head>
<body>
    <div id="assessment-container"><!-- Assessment content --></div>
    <script>/* Assessment logic */</script>
</body>
</html>
```

#### Requirements
- **Self-contained** — All CSS and JS inline. No external dependencies.
- **Responsive** — Must work at 1366x768 (Chromebook) through 1920x1080 (desktop).
- **Clean layout** — Questions flow vertically. Numbered clearly. Ample whitespace.
- **Print support** — Include `@media print` styles (white background, black text, hide interactive elements, format for paper).
- **Accessibility** — Keyboard navigable, sufficient contrast, ARIA labels on interactive elements.
- **Text areas** — Auto-expanding height for free response questions.
- **Progress indicator** — Show how many questions have been answered.
- **Submit button** — Displays confirmation message.

#### Dark theme (screen) + Light theme (print)
```css
:root {
    --bg: #1a1a2e;
    --panel-bg: rgba(25, 25, 50, 0.9);
    --text: #e8e4f4;
    --muted: #8a85a8;
    --accent: #60a5fa;
    --border: rgba(100, 100, 200, 0.2);
}
@media print {
    :root { --bg: #fff; --panel-bg: #fff; --text: #000; --muted: #666; --border: #ccc; }
    body { font-size: 11pt; }
    .no-print { display: none; }
}
```

#### Rubric Inclusion
Include the rubric as a collapsible section at the top:
```html
<details class="rubric-panel">
    <summary>View Rubric</summary>
    <!-- Rubric table here -->
</details>
```

### Markdown Mode

Output the assessment as structured markdown with clear sections:
- Header with title, subject, grade level
- Learning objectives
- Questions with numbering and type labels
- Rubric as a markdown table

## Step 5: Generate the Rubric

Every assessment gets a rubric. No exceptions.

### Rubric Structure

Default to four tiers unless the user specifies otherwise. Adjust tier count (3, 5, or 6) if the subject or grading system requires it.

| Tier | Label | Description |
|------|-------|-------------|
| 4 | **Mastery** | Demonstrates thorough, accurate understanding with clear reasoning |
| 3 | **Proficient** | Demonstrates solid understanding with minor gaps |
| 2 | **Developing** | Shows partial understanding with significant gaps |
| 1 | **Beginning** | Shows minimal understanding or major misconceptions |

Alternative labels are fine if the school uses different conventions (e.g., Exceeds/Meets/Approaching/Below, or Exemplary/Competent/Emerging/Incomplete).

### Rubric Rules

1. **Answer neutrality is mandatory.** Tier descriptions must assess quality and structure without revealing the correct answer. If a student can read the Developing tier and reconstruct the answer without doing the work, the rubric is too specific.
2. **Observable criteria.** Each tier must describe what student work looks like in specific, measurable terms. "Some understanding" is too vague — what does that look like on paper?
3. **Self-contained tiers.** Each tier should be understandable on its own without reading other tiers.
4. **Content-specific.** Reference the actual concepts, representations, and reasoning being assessed. Never use generic criteria.
5. **Skill statements.** Write each assessed skill as an "I am able to..." statement.

### Rubric Output

- **HTML mode:** Embed as a collapsible `<details>` section in the HTML file.
- **Markdown mode:** Output as a formatted markdown table after the questions.

## Step 6: QA Audit

Before delivering, launch the **qa-engineer** agent to audit:

- Rubric answer neutrality (can a student reverse-engineer answers from tier descriptions?)
- Cognitive demand distribution (Bloom's coverage)
- Question clarity and accessibility for the target grade level
- For HTML: accessibility, print styles, responsive behavior

If QA finds issues, fix them. Route rubric/structural problems to **assessment-designer**, wording problems to **content-writer**. Re-run QA after fixes.

## Step 7: Deliver

Save the file to `assets/Assessments/<subject>/[topic-slug]-assessment.[html|md]`.

Report to the user:
- Assessment title, subject, and grade level
- Number of questions and types used
- Learning objectives assessed
- Rubric skill statements
- QA status
- File path
- Any notes about content needing manual review

## Error Handling

Use the self-correction loop (max 3 attempts):
1. **Detect** — Identify what failed (structural issues, rubric violations, HTML rendering)
2. **Research** — Re-read the assessment-designer's architecture and rubric conventions
3. **Fix** — Patch the specific issue
4. **Retry** — Regenerate the affected section
5. **Escalate** — If 3 attempts fail, report what was tried and ask the user for guidance

**Escalate immediately:** Scientific accuracy questions, ambiguous grading criteria, when source material is contradictory.

## Notes

- **Scientific/factual accuracy is critical.** Do not fabricate inaccurate content.
- **Rubric is mandatory.** Every assessment gets one.
- **Teacher-graded.** These assessments collect student responses; the teacher evaluates them using the rubric.
- **No external assets.** HTML files must be fully self-contained.
- **Respect the user's pedagogical framework.** If they specify a framework (ISLE, 5E, direct instruction, etc.), align the assessment to it. If they don't specify, use backward design principles.
