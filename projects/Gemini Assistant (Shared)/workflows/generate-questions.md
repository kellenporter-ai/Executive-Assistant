# Workflow: Generate Questions

Generate large question banks from source material or topics. Outputs validated JSON files with built-in quality checks for answer bias, duplicate detection, and cognitive demand distribution.

**Output location:** `assets/Questions/<subject>/`

## Step 1: Parse Input

Determine from the user's request:

- **Topic** (required) — What subject matter should the questions cover?
- **Source material** (optional) — File path to a PDF, document, or notes. If provided, ground ALL questions in the source material.
- **Subject and level** — What subject and grade level? (e.g., "AP Biology", "8th grade math", "Intro to CS")
- **Question count** — How many? (default: 50-100. User can request more.)

If only a topic is given, use domain knowledge to generate questions.

## Step 2: Confirm Scope

Ask the user:
1. **Subject and level** — Confirm the subject and grade level, or infer from context.
2. **Question format** — Multiple choice (default), short answer, or mixed?
3. **Difficulty distribution** — Even split across tiers, or weighted toward a specific level?

Default to multiple choice with even Bloom's distribution if the user doesn't specify.

## Step 3: Generate Questions Using Subagents

For efficiency with large banks, delegate to **content-writer** subagents in parallel — one per difficulty tier.

### Difficulty Tiers (Bloom's Taxonomy)

| Tier | Bloom's Levels | Difficulty | Question Characteristics |
|------|---------------|------------|-------------------------|
| 1 | Remember & Understand | Easy | Recall facts, define terms, identify concepts, recognize patterns |
| 2 | Apply & Analyze | Medium | Use knowledge in new situations, compare/contrast, interpret data or texts, analyze relationships |
| 3 | Evaluate & Create | Hard | Justify positions, critique arguments, synthesize across sources, design solutions, propose interpretations |

### Subagent Prompt Template

For each tier, spawn a content-writer with:

```
You are an expert educational assessment writer. Generate [count] multiple-choice questions on the topic: "[topic]".

Subject/Level: [subject]
Difficulty: [tier description]
Bloom's Level: [bloom's levels for this tier]

[If source material provided: Base ALL questions on this content: (paste key content)]

Requirements:
- 4 answer options per question
- Distractors must be plausible and educational — never use joke answers
- Vary question stems (standard, "which of the following", "what would happen if", scenario-based, data/text interpretation)
- No negative stems ("Which is NOT...") unless clearly marked. No "all/none of the above."
- Stems should be complete enough to attempt answering without reading the options
- Each question must have: id, stem, options (array of 4 strings), correctAnswer (0-based index), difficulty ("EASY"/"MEDIUM"/"HARD")

Output ONLY a valid JSON array. No markdown fences, no commentary. End cleanly with ].

Example format:
[
  {
    "id": "t1q001",
    "stem": "What is the primary function of mitochondria?",
    "options": ["Energy production", "Protein synthesis", "Cell division", "Waste removal"],
    "correctAnswer": 0,
    "difficulty": "EASY"
  }
]

ID prefix: [t1q / t2q / t3q based on tier]
```

### Short Answer Format (if requested)

```json
{
  "id": "sa001",
  "stem": "Explain why...",
  "sampleAnswer": "A strong response would include...",
  "difficulty": "MEDIUM",
  "type": "short_answer"
}
```

## Step 4: Collect and Validate

After all subagents complete:

1. **Parse each result** as JSON. If invalid, attempt auto-fix (trailing commas, truncated arrays — close with `]`).
2. **Merge** all tier arrays into a single array.
3. **Count** questions per tier. Report if significantly under target.
4. **Deduplicate** — scan for duplicate or near-duplicate stems. Remove duplicates.
5. **Validate IDs** — ensure no duplicates. Reassign sequential IDs if needed.

### Answer Position Shuffle (MANDATORY for MC)

LLMs heavily bias the correct answer toward position A/B (~80-90% of the time). After merging:

For each question:
1. Store the correct answer **text**: `correctText = options[correctAnswer]`
2. Shuffle the `options` array (Fisher-Yates)
3. Update `correctAnswer` to the new index of `correctText`

After shuffling, verify distribution: count how many times the correct answer lands at each position (0, 1, 2, 3). Each should be ~25%. If any position exceeds 35%, re-shuffle that subset.

### Answer Length Bias Check (MANDATORY for MC)

Check whether correct answers are consistently longer than distractors. For each question, compare the character length of the correct answer to the average distractor length. If the correct answer is longest in more than 40% of questions, flag it. Fix by rewriting options so all four are similar in length and specificity — if the correct answer is detailed, make distractors equally detailed; if distractors are concise, make the correct answer equally concise. Do not pad distractors with filler.

## Step 5: Write Output

Save to: `assets/Questions/<subject>/[topic-slug]-questions.json`

The file contains a single JSON array of question objects.

After writing, report:

```
Questions generated:
- Tier 1 (Easy): [count]
- Tier 2 (Medium): [count]
- Tier 3 (Hard): [count]
- Total: [total] questions

Answer position distribution: A=[x]% B=[x]% C=[x]% D=[x]%
Length bias check: [PASS/corrected X questions]
Duplicates removed: [count]
File: [path]
```

## Error Handling

Use the self-correction loop (max 3 attempts):

- **Subagent returns invalid JSON:** Attempt auto-fix. If unfixable, re-spawn with a smaller batch.
- **Question count under target:** Re-spawn underperforming subagents. If source material is too narrow, note it and suggest broadening.
- **Shuffle fails:** Verify question format matches schema. Re-run shuffle on failing subset.
- **Duplicate detection:** Remove dupes, reassign IDs, note count in summary.
- **Escalate immediately:** Factual accuracy concerns, ambiguous topic scope, contradictory source material.

## Notes

- **Factual accuracy is critical.** Do not fabricate incorrect information. If unsure about a fact, omit the question.
- **Distractors must be plausible.** Every wrong answer should represent a common misconception or reasonable error, not an obviously wrong choice.
- **Ground in source when provided.** If the user gave source material, questions must be answerable from that material.
- **ALWAYS shuffle answer positions.** Never skip this step. LLM bias is real and consistent.
- **ALWAYS check answer length bias.** Correct answers that are consistently longest is a testable pattern students will exploit.
- **Output is pure JSON** — no markdown fences in the output file.
- **Large banks go through temp/.** Write intermediate batches to `temp/` before merging to avoid context bloat.
