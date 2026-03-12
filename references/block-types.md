# Lesson Block Types Reference

Reference for `/study-guide`, `/create-assessment`, `/lesson-plan`, and `/generate-questions` skills.

**Source:** `projects/Porters-Portal/types.ts` (lines 61-124)

## BlockType Union (22 types)

### Display/Informational (8)
| Type | Purpose | Key Fields |
|------|---------|------------|
| `TEXT` | Rich text content | `content` (string, supports LaTeX via `$...$`) |
| `SECTION_HEADER` | Section divider | `content` (header text) |
| `INFO_BOX` | Callout/highlight box | `content`, `infoBoxType` ('info' \| 'warning' \| 'tip' \| 'example') |
| `IMAGE` | Image display | `url`, `content` (caption) |
| `VIDEO` | Video embed | `url`, `content` (caption) |
| `DIVIDER` | Visual separator | (no extra fields) |
| `EXTERNAL_LINK` | Clickable link | `url`, `content` (link text) |
| `EMBED` | iframe embed | `url`, `content` (caption) |

### Reference/Knowledge (3)
| Type | Purpose | Key Fields |
|------|---------|------------|
| `VOCABULARY` | Single vocab term | `content` (term), `definition` (string) |
| `VOCAB_LIST` | Multiple vocab terms | `vocabItems` ({term, definition}[]) |
| `OBJECTIVES` | Learning objectives | `objectiveItems` (string[]) |

### Interactive/Assessment (11)
| Type | Purpose | Key Fields |
|------|---------|------------|
| `MC` | Multiple choice | `content` (question), `options` (string[]), `correctAnswer` (number, 0-indexed), `explanation` (string, optional) |
| `SHORT_ANSWER` | Free text response | `content` (prompt), `acceptedAnswers` (string[], optional) |
| `CHECKLIST` | Checkbox list | `content` (instructions), `checklistItems` ({text, correct}[]) |
| `SORTING` | Two-category sort | `content` (instructions), `sortItems` ({text, correct: 'left'\|'right'}[]), `leftLabel`, `rightLabel` |
| `RANKING` | Ordered ranking | `content` (instructions), `rankItems` (string[] in correct order) |
| `LINKED` | Matching pairs | `content` (instructions), `linkedPairs` ({left, right}[]) |
| `DATA_TABLE` | Data entry table | `content` (instructions), `columns` ({key, label, unit?, editable?}[]), `trials` (number) |
| `BAR_CHART` | Bar chart builder | `content` (instructions), `barCount`, `initialLabel`, `deltaLabel`, `finalLabel`, `height` |
| `DRAWING` | Drawing canvas | `content` (instructions), `drawingMode` ('free' \| 'point_model' \| 'extended_body'), `canvasHeight`, `backgroundImage` |
| `MATH_RESPONSE` | Math steps | `content` (instructions), `stepLabels` (string[]), `maxSteps`, `showLatexHelp` |
| `ACTIVITY` | External HTML activity | `url` (path to HTML file), `content` (instructions) |

## LessonBlock Interface

```typescript
interface LessonBlock {
  type: BlockType;        // Required — one of the 22 types above
  content: string;        // Required — primary text content
  url?: string;           // For IMAGE, VIDEO, EMBED, EXTERNAL_LINK, ACTIVITY
  explanation?: string;   // For MC — shown after answering

  // MC
  options?: string[];
  correctAnswer?: number; // 0-indexed

  // SHORT_ANSWER
  acceptedAnswers?: string[];

  // CHECKLIST
  checklistItems?: { text: string; correct: boolean }[];

  // SORTING
  sortItems?: { text: string; correct: 'left' | 'right' }[];
  leftLabel?: string;
  rightLabel?: string;

  // RANKING
  rankItems?: string[];   // Correct order

  // LINKED
  linkedPairs?: { left: string; right: string }[];

  // DATA_TABLE
  columns?: { key: string; label: string; unit?: string; editable?: boolean }[];
  trials?: number;

  // BAR_CHART
  barCount?: number;
  initialLabel?: string;
  deltaLabel?: string;
  finalLabel?: string;
  height?: number;

  // DRAWING
  drawingMode?: 'free' | 'point_model' | 'extended_body';
  canvasHeight?: number;
  backgroundImage?: string;

  // MATH_RESPONSE
  stepLabels?: string[];
  maxSteps?: number;
  showLatexHelp?: boolean;

  // VOCABULARY
  definition?: string;

  // VOCAB_LIST
  vocabItems?: { term: string; definition: string }[];

  // OBJECTIVES
  objectiveItems?: string[];

  // INFO_BOX
  infoBoxType?: 'info' | 'warning' | 'tip' | 'example';
}
```

## Interactive Block Types List

The following types are treated as interactive (student-gradeable):
```
MC, SHORT_ANSWER, CHECKLIST, SORTING, RANKING, LINKED, DRAWING, MATH_RESPONSE
```

Note: DATA_TABLE and BAR_CHART are interactive but may not appear in this list in all contexts.

## JSON Import Rules

- **No `id` fields** — IDs are auto-generated on import
- **Placeholder URLs:** Use `"url": "PLACEHOLDER: [description]"` format
- **LaTeX in TEXT blocks:** Use `$...$` for inline math
- **MC explanation field:** Shown to students after they answer. Skills (`lesson-plan`, `create-assessment`) can set this field.
- **ACTIVITY type:** The `url` points to a standalone HTML file (typically in `assets/Simulations/`)

## Common Skill Usage

### study-guide
Primarily uses: SECTION_HEADER, TEXT, INFO_BOX, VOCAB_LIST, SHORT_ANSWER, MC

### create-assessment
Primarily uses: SHORT_ANSWER, MC, DRAWING, MATH_RESPONSE, DATA_TABLE, BAR_CHART, SORTING, RANKING

### lesson-plan
Uses all types. Structure: OBJECTIVES -> SECTION_HEADER -> content blocks -> interactive blocks per section.

### generate-questions
Generates: MC, SHORT_ANSWER for boss battles, dungeon rooms, and review questions.
