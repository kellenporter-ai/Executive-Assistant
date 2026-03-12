# Rubric Format Reference

Reference for `/create-assessment`, `/grade-assistant`, and `/game-balance` skills.

**Source:** `projects/Porters-Portal/types.ts` (lines 370-439)

## ISLE SAAR Mapping (5-Level Scale)

| Tier Index | Label | Percentage | SAAR Score | Description |
|-----------|-------|------------|------------|-------------|
| 0 | Missing | 0% | 0 | No evidence of the skill |
| 1 | Emerging | 25% | 1 | Inadequate representation |
| 2 | Approaching | 50% | 2 | Needs improvement |
| 3 | Developing | 75% | 3 | Adequate representation |
| 4 | Refining | 100% | — | Exceeds expectations (portal extension) |

## Rubric Structure (Assignment)

```typescript
interface Rubric {
  title: string;
  questions: RubricQuestion[];
  rawMarkdown: string;       // Original markdown source
}

interface RubricQuestion {
  id: string;                // e.g., "q1", "q2"
  questionLabel: string;     // e.g., "Question 1: Force Analysis"
  skills: RubricSkill[];
}

interface RubricSkill {
  id: string;                // e.g., "s1", "s2"
  skillText: string;         // e.g., "Identify all forces acting on the system"
  tiers: RubricTier[];       // Always 5 tiers (Missing → Refining)
}

interface RubricTier {
  label: RubricTierLabel;    // 'Missing' | 'Emerging' | 'Approaching' | 'Developing' | 'Refining'
  percentage: number;        // 0, 25, 50, 75, 100
  descriptor: string;        // What performance looks like at this level
}
```

## Grade Structure (Submission)

```typescript
interface RubricGrade {
  grades: Record<string, Record<string, RubricSkillGrade>>;
  // grades[questionId][skillId] = { selectedTier, percentage }
  overallPercentage: number;
  gradedAt: string;          // ISO timestamp
  gradedBy: string;          // Teacher UID
  teacherFeedback?: string;  // Free-text comment shown to student
}

interface RubricSkillGrade {
  selectedTier: number;      // 0-4 (NOT "tier" — always "selectedTier")
  percentage: number;        // Matching percentage from tier
}
```

## AI Suggested Grade Structure

```typescript
interface AISuggestedGrade {
  grades: Record<string, Record<string, AISuggestedSkillGrade>>;
  overallPercentage: number;
  suggestedAt: string;
  model: string;             // e.g., "qwen3:14b"
  status: 'pending_review' | 'accepted' | 'partially_accepted' | 'rejected';
}

interface AISuggestedSkillGrade {
  suggestedTier: number;     // 0-4 (NOT "selectedTier" — always "suggestedTier")
  percentage: number;
  confidence: number;        // 0-1
  rationale: string;         // Why this tier was chosen
}
```

## Key Gotchas

1. **`selectedTier` vs `suggestedTier`** — Teacher grades use `selectedTier`, AI suggestions use `suggestedTier`. Never mix them.
2. **Tier is 0-indexed** — 0 = Missing, 4 = Refining. Not 1-5.
3. **`teacherFeedback`** — Optional string on `RubricGrade`, displayed to students in a purple callout in ResourceViewer.
4. **AI grades are `pending_review`** — Teacher must accept/reject before grade is final (human-in-the-loop).
5. **Grade path** — `submission.rubricGrade.grades[questionId][skillId].selectedTier`

## Rubric Markdown Format (for `/create-assessment`)

When generating rubrics in markdown (stored as `rawMarkdown`), use this structure:

```markdown
# Assessment Title

## Question 1: [Question Label]

### Skill: [Skill description]

| Level | Description |
|-------|-------------|
| Missing (0%) | [No evidence description] |
| Emerging (25%) | [Inadequate description] |
| Approaching (50%) | [Needs improvement description] |
| Developing (75%) | [Adequate description] |
| Refining (100%) | [Exceeds expectations description] |

### Skill: [Next skill...]
...
```

Each skill descriptor should be specific and observable — describe what the student's work looks like at that tier, not generic statements.
