# Workflow: Study Guide

Generate condensed, student-facing study guides from existing content. Distills lessons, notes, or question banks into focused review materials with practice problems and worked solutions.

**Output formats:** Printable HTML (default) or structured markdown
**Output location:** `assets/StudyGuides/<subject>/`

## Step 1: Identify Source Material

The user will specify content in one of these ways:

- **By topic:** "Study guide for photosynthesis" → generate from domain knowledge
- **By file path:** "Study guide from this PDF" → read and distill the document
- **By unit:** "Study guide for Unit 3" → pull from available materials

When given a file path, read it in full. Use the content to determine scope, depth, and terminology.

## Step 2: Confirm Scope

Ask the user:
1. **Subject and level** — What subject and grade level is this for?
2. **Scope** — Full unit review or targeted concept review?
3. **Format** — Printable HTML (default) or markdown?
4. **Include practice problems?** (default: yes, 8-12 problems with worked solutions)
5. **Concise mode?** — If the user says "keep it short", "just the basics", "condensed version", "quick review", or "don't go overboard", switch to concise mode (see below). When in doubt, ask: "Would you like the full study guide or a condensed version?"

## Step 3: Structure the Study Guide

Every study guide follows this structure, adapted to the content:

### A. Header
- Title: "Study Guide: [Topic/Unit]"
- What's covered, what's not
- Estimated study time

### B. Key Concepts (3-8)
Each concept gets:
- A clear, jargon-free explanation (2-3 sentences max)
- A concrete example or analogy
- Common misconception to avoid (when relevant)

### C. Vocabulary
- Essential terms with plain-language definitions
- Grouped by relationship, not alphabetical

### D. Key Frameworks & Relationships (when applicable)
Adapt this section to the subject:
- **STEM:** Equations with variable definitions, when to use each formula, unit reminders
- **Humanities:** Analytical frameworks, timelines, key models, cause-and-effect chains
- **Arts:** Techniques, terminology, compositional principles, style vocabulary
- **Languages:** Grammatical structures, conjugation patterns, usage rules

### E. Visual Summary (when appropriate)
- Diagrams, charts, or visual references students should study or practice sketching
- Reference key activities, projects, or experiences from the course

### F. Practice Activities with Worked Examples
- 8-12 exercises spanning difficulty:
  - 3-4 recall/understand (easy)
  - 3-4 apply/analyze (medium)
  - 2-4 evaluate/create (hard)
- Each includes a **full worked example showing reasoning**, not just the answer
- Adapt to the subject: problem-solving for STEM, passage analysis for English, source evaluation for History, technique application for Arts
- Convert MC questions into free-response format for deeper practice

### G. Self-Check
- 5-8 quick true/false, fill-in-the-blank, or "explain in one sentence" questions
- Answers at the bottom of the document

### Concise Mode

When triggered, apply these constraints:
- **Target: 15-20 sections max.** Hard cap at 25.
- Skip the self-check section
- Reduce practice problems to 3-4 (one per difficulty tier)
- Combine vocabulary into a single compact list
- Use 1-2 sentence concept explanations
- Omit the visual summary
- Keep worked solutions but make them shorter (key steps only)

## Step 4: Generate Output

### HTML Mode (default)

Generate a single self-contained HTML file with:

```css
/* Dark theme for screen */
:root {
    --bg: #1a1a2e;
    --panel-bg: rgba(25, 25, 50, 0.9);
    --text: #e8e4f4;
    --muted: #8a85a8;
    --accent: #60a5fa;
    --border: rgba(100, 100, 200, 0.2);
}
/* Print overrides — white background for paper */
@media print {
    :root { --bg: #fff; --panel-bg: #fff; --text: #000; --muted: #666; --border: #ccc; }
    body { font-size: 11pt; }
    .no-print { display: none; }
    .answers-section { page-break-before: always; }
}
```

Requirements:
- **Self-contained** — All styles inline, no external dependencies
- **Print-optimized** — Students will print these. White background, readable font size, no wasted space
- **Responsive** — Works on screen (1366x768 through 1920x1080) and prints well on letter/A4
- **Collapsible solutions** — Worked solutions in `<details><summary>` elements so students can attempt problems before checking
- **Math notation** — When applicable, use plain Unicode (e.g., F = ma) rather than LaTeX. Keeps the file self-contained and readable when printed.

### Markdown Mode

Output clean markdown with clear section headers, formatted tables, and code blocks for formulas.

## Step 5: Deliver

Save to `assets/StudyGuides/<subject>/[topic-slug]-study-guide.[html|md]`.

Report: topic covered, section count, number of practice problems, estimated study time.

## Writing Guidelines

These guides are for **students**. Write accordingly:

- **Plain language first.** Define jargon before using it.
- **Short paragraphs.** 2-3 sentences max per concept.
- **Active voice.** "Gravity pulls objects toward Earth" not "Objects are pulled toward Earth by gravity."
- **Concrete examples.** Every abstract concept gets a real-world example.
- **Worked solutions show thinking.** Don't just show steps — narrate the reasoning. "First, identify what we know and what we're solving for..."
- **Encourage, don't intimidate.** "This is a tricky concept — here's how to think about it."

## Error Handling

Use the self-correction loop (max 3 attempts):
- **Source file not found:** Ask the user for the correct path.
- **Topic too broad:** Suggest narrowing scope or splitting into multiple guides.
- **Escalate:** If the content requires domain expertise you lack, ask the user for source material rather than guessing.
