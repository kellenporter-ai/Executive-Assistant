# Workflow: Lesson Plan

Generate structured lesson plans for any subject and grade level. Adapts to the teacher's preferred instructional framework or defaults to backward design.

**Output formats:** Structured markdown (default) or printable HTML
**Output location:** `assets/LessonPlans/<subject>/`

## Step 1: Gather Requirements

Determine from the user's request:

- **Subject and topic** — What is being taught? (e.g., "cellular respiration", "the Civil War", "solving systems of equations")
- **Grade level** — What level are the students?
- **Class duration** — How long is the period? (default: 50 minutes)
- **Source material** (optional) — File paths to PDFs, textbook excerpts, or activity guides to convert into a lesson

If source material is provided, read each file to understand the content, existing structure, and pedagogical approach.

### Framework Detection

If the user specifies a framework, use it:

| Framework | Structure |
|-----------|-----------|
| **ISLE** | Preparation → Observation → Model Development → Hypothesis Testing → Application |
| **5E** | Engage → Explore → Explain → Elaborate → Evaluate |
| **Direct Instruction** | Objective → Input → Model → Guided Practice → Independent Practice → Check |
| **Workshop Model** | Mini-lesson → Work Time → Share/Debrief |
| **Inquiry-Based** | Question → Investigate → Analyze → Conclude → Reflect |

If no framework is specified, use **backward design**: define the goal, determine evidence of learning, then plan activities that build toward that evidence.

## Step 2: Analyze Content

### Topic Mode (no source file)
1. Identify key concepts, vocabulary, and common misconceptions.
2. Determine which framework phases are appropriate (not every topic needs every phase).
3. Plan what activities, examples, and representations students will work with.

### Resource Mode (source file provided)
1. Read the entire resource.
2. Identify the pedagogical structure already present (many resources already follow a framework).
3. Map existing sections to the chosen framework's phases.
4. Note which activities are hands-on/physical and need adaptation for the classroom context.

## Step 3: Design the Lesson

Plan the lesson before generating output:

### Activity Design Principles

- **Students do, not read.** For every chunk of content, include an activity where students interact with the material.
- **Concrete before abstract.** Start with examples, observations, or scenarios before introducing formal definitions or formulas.
- **Multiple representations.** Use diagrams, data tables, graphs, and verbal explanations — not just text.
- **Check for understanding.** Include formative checks (quick questions, think-pair-share prompts, exit tickets) throughout, not just at the end.
- **Pacing.** A 50-minute lesson typically has 3-5 distinct segments. More than 6 segments feels rushed; fewer than 3 feels unfocused.

### Activity Types

Match activities to the learning goal:

| Goal | Activity Types |
|------|---------------|
| Activate prior knowledge | Quick poll, brainstorm, KWL chart, warm-up problem |
| Build new understanding | Guided observation, data collection, reading with annotation, demonstration |
| Practice skills | Worked examples, problem sets, sorting/matching tasks |
| Deepen thinking | Discussion prompts, peer critique, compare/contrast, what-if scenarios |
| Assess understanding | Exit ticket, quiz, self-assessment, reflection prompt |

## Step 4: Generate the Lesson Plan

### Markdown Mode (default)

Output a structured lesson plan:

```markdown
# [Lesson Title]

**Subject:** [subject] | **Grade:** [grade] | **Duration:** [time]
**Framework:** [framework used]

## Learning Objectives
By the end of this lesson, students will be able to:
1. [objective 1]
2. [objective 2]
3. [objective 3]

## Materials Needed
- [material 1]
- [material 2]

## Lesson Sequence

### [Phase/Segment 1 Name] (X min)
**Purpose:** [what this segment accomplishes]

**Teacher Does:**
- [instruction or facilitation action]

**Students Do:**
- [student activity]

**Key Questions:**
- [questions to ask during this segment]

### [Phase/Segment 2 Name] (X min)
...

## Assessment / Exit Ticket
[How you'll check for understanding at the end]

## Differentiation
- **Support:** [scaffolds for struggling students]
- **Extension:** [challenges for advanced students]

## Notes
[Anything the teacher should know — common misconceptions, timing tips, material prep]
```

### HTML Mode

Generate a self-contained HTML file with:
- Clean, readable layout optimized for screen and print
- Collapsible sections for each lesson phase
- Print-friendly `@media print` styles (white background, compact layout)
- Dark theme for screen viewing
- Teacher notes in highlighted callout boxes

Save to `assets/LessonPlans/<subject>/[topic-slug]-lesson.html`.

## Step 5: Self-Review

Before presenting, verify:
- Timing across all segments sums to the class duration (within 5 minutes)
- Each learning objective is addressed by at least one activity
- No more than 2 consecutive text-heavy segments without an interactive element
- Vocabulary is defined when first introduced, not in a disconnected list

## Step 6: Present to User

After generating, provide a summary:
- Lesson title and framework used
- Number of segments and total time
- Learning objectives
- Activity types included
- Any notes about content needing manual review (e.g., placeholder materials, activities that need physical supplies)

Ask if the user wants changes before finalizing.

## Step 7: Save

Save the file and report the path.

## Error Handling

Use the self-correction loop (max 3 attempts). Escalate if:
- Subject matter is outside your knowledge (ask user for source material)
- Time constraints make the lesson infeasible (suggest splitting into two lessons)
- The user's framework choice doesn't fit the content (explain why and suggest alternatives)

## Notes

- **Scope matters.** A single lesson should cover 1-3 related concepts, not an entire unit. If the topic is too broad, suggest breaking it into multiple lessons.
- **Scientific/factual accuracy is critical.** Do not include incorrect information.
- **Respect the teacher's expertise.** Present the plan as a starting point — the teacher knows their students best.
- **Vocabulary.** Define key terms when they first appear, not in a separate list disconnected from context.
- **Timing is a guide.** Include minute estimates per segment, but note that actual pacing depends on the class.
