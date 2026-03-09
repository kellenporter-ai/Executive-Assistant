# Porters-Portal Lesson Block JSON Schema

This is the complete reference for all 21 block types supported by the Porters-Portal lesson editor. The JSON import accepts either a plain array of blocks or an object with a `blocks` property.

## Import Formats

**Array format (preferred for this skill):**
```json
[
  { "type": "TEXT", "content": "..." },
  { "type": "MC", "content": "...", "options": [...], "correctAnswer": 0 }
]
```

**Object format:**
```json
{
  "blocks": [
    { "type": "TEXT", "content": "..." }
  ]
}
```

## General Rules

- Every block MUST have a `type` field.
- Do NOT include `id` fields — they are auto-generated on import.
- Only include fields relevant to the specific block type.
- Blocks that don't use `content` as their primary field should still include `"content": ""` for consistency.

---

## Content Blocks

### TEXT
Plain text content.
```json
{
  "type": "TEXT",
  "content": "Your text content here"
}
```

### SECTION_HEADER
Section heading with icon and optional subtitle.
```json
{
  "type": "SECTION_HEADER",
  "icon": "emoji here",
  "title": "Section Title",
  "subtitle": "Optional subtitle"
}
```

### IMAGE
Image with caption and alt text.
```json
{
  "type": "IMAGE",
  "url": "https://example.com/image.png",
  "caption": "Figure caption",
  "alt": "Description of image"
}
```

### VIDEO
YouTube video embed.
```json
{
  "type": "VIDEO",
  "url": "https://youtube.com/watch?v=...",
  "caption": "Optional caption"
}
```

### OBJECTIVES
Learning objectives list.
```json
{
  "type": "OBJECTIVES",
  "title": "Learning Objectives",
  "items": [
    "Objective 1",
    "Objective 2",
    "Objective 3"
  ]
}
```

### DIVIDER
Horizontal separator.
```json
{
  "type": "DIVIDER",
  "content": ""
}
```

### EXTERNAL_LINK
Styled link card with button.
```json
{
  "type": "EXTERNAL_LINK",
  "title": "Resource Title",
  "url": "https://example.com",
  "content": "Description of the resource",
  "buttonLabel": "Open",
  "openInNewTab": true
}
```

### EMBED
iFrame embed (Codepen, PhET simulations, etc.).
```json
{
  "type": "EMBED",
  "url": "https://codepen.io/example",
  "caption": "Interactive example",
  "height": 500
}
```

### INFO_BOX
Callout box with variant styling.
```json
{
  "type": "INFO_BOX",
  "variant": "tip",
  "content": "Helpful information here"
}
```
Variants: `"tip"` (green), `"warning"` (amber), `"note"` (blue)

---

## Vocabulary Blocks

### VOCABULARY
Single term with definition.
```json
{
  "type": "VOCABULARY",
  "term": "Angular velocity",
  "definition": "The rate of change of angular position"
}
```

### VOCAB_LIST
Multiple terms with definitions.
```json
{
  "type": "VOCAB_LIST",
  "terms": [
    { "term": "Term 1", "definition": "Definition 1" },
    { "term": "Term 2", "definition": "Definition 2" }
  ]
}
```

---

## Activity Blocks

### ACTIVITY
Activity card with instructions.
```json
{
  "type": "ACTIVITY",
  "icon": "emoji",
  "title": "Activity Title",
  "instructions": "Detailed instructions for the activity"
}
```

### CHECKLIST
Interactive checkbox list.
```json
{
  "type": "CHECKLIST",
  "content": "Checklist Title",
  "items": [
    "Item 1",
    "Item 2",
    "Item 3"
  ]
}
```

### SORTING
Two-category drag-and-drop sorting.
```json
{
  "type": "SORTING",
  "title": "Sorting Activity Title",
  "instructions": "Sort these items into the correct categories",
  "leftLabel": "Category A",
  "rightLabel": "Category B",
  "sortItems": [
    { "text": "Item 1", "correct": "left" },
    { "text": "Item 2", "correct": "right" },
    { "text": "Item 3", "correct": "left" }
  ]
}
```

### DATA_TABLE
Editable data table for experiments.
```json
{
  "type": "DATA_TABLE",
  "title": "Table Title",
  "columns": [
    { "key": "trial", "label": "Trial", "editable": false },
    { "key": "measurement", "label": "Measurement", "unit": "m", "editable": true }
  ],
  "trials": 3
}
```

### BAR_CHART
Interactive energy/momentum bar chart with three sections: Initial, Delta (Δ), and Final. Students drag bars to represent quantities at each stage of a physical process. Embedded as an iframe tool with full drag interaction.
```json
{
  "type": "BAR_CHART",
  "title": "Chart Title",
  "height": 450
}
```
- `height` — Canvas height in pixels (default 450, student can resize 200–1000px)
- Students add bars in each section (Initial/Δ/Final) and label them with physics quantities from a dropdown
- Color-coded: Initial (green), Delta (blue), Final (red)
- Ideal for energy bar charts, momentum bar charts, and conservation law visualizations

### DRAWING
Full-featured drawing canvas for physics diagrams — force diagrams, vector drawings, free-body diagrams, motion maps, and extended-body diagrams. Includes pen, arrow, shape, and text tools with physics-specific vector labeling.
```json
{
  "type": "DRAWING",
  "title": "Draw the free-body diagram",
  "instructions": "Draw and label all forces acting on the block",
  "drawingMode": "free",
  "canvasHeight": 400
}
```
- `title` — Prompt displayed above the canvas
- `instructions` — Additional guidance text shown to the student
- `drawingMode` — `"free"` (default, general drawing), `"point_model"` (point-mass diagrams), or `"extended_body"` (extended-body diagrams)
- `canvasHeight` — Height in pixels (default 400)
- `backgroundImage` — Optional URL to a background image (e.g., a scenario diagram students draw on top of)
- **Drawing tools available to students:** pen (adjustable width), eraser, arrows with physics vector labels (force, displacement, velocity, Δv, acceleration, momentum, angular momentum, custom), shapes (circle, rectangle, line), text, select/move, undo/redo

### MATH_RESPONSE
Multi-step math work area where students show their problem-solving process. Supports natural math input that auto-converts to rendered LaTeX — students type normally (e.g., `F = ma`, `v = (2)(9.8)(5)`) and see formatted math.
```json
{
  "type": "MATH_RESPONSE",
  "title": "Show your work",
  "content": "A 5 kg block is pushed with 20 N of force. Find the acceleration.",
  "maxSteps": 10,
  "stepLabels": ["Given:", "Find:", "Step 1:", "Step 2:", "Step 3:"],
  "showLatexHelp": true
}
```
- `title` — Display title above the work area
- `content` — The problem/question text
- `maxSteps` — Maximum number of step inputs allowed (default 10)
- `stepLabels` — Suggested labels for each step (default: `["Given:", "Find:", "Step 1:", "Step 2:", "Step 3:"]`). Students can change labels.
- `showLatexHelp` — Show the symbol toolbar for Greek letters and operators (default true)
- **Auto-converts:** Greek letters (θ, Δ, ω, etc.), operators (×, ÷, ≥, ≤), trig/log functions, unit patterns (m/s², rad/s, kg, N, J, W), and fraction notation `(a)/(b)` → rendered fractions

---

## Question Blocks (Interactive, tracked for completion)

### MC (Multiple Choice)
```json
{
  "type": "MC",
  "content": "Question text here?",
  "options": [
    "Option A",
    "Option B",
    "Option C",
    "Option D"
  ],
  "correctAnswer": 1
}
```
- `correctAnswer` is 0-based index
- 2-6 options supported

### SHORT_ANSWER
```json
{
  "type": "SHORT_ANSWER",
  "content": "Question text here?",
  "acceptedAnswers": [
    "acceptable answer 1",
    "acceptable answer 2"
  ]
}
```
- Matching is case-insensitive, substring
- For open-ended questions, `acceptedAnswers` can be omitted or left as an empty array

### RANKING
Drag-to-reorder items. List items in the CORRECT order — the system scrambles them.
```json
{
  "type": "RANKING",
  "content": "Arrange these in the correct order:",
  "items": [
    "First item (correct position 1)",
    "Second item (correct position 2)",
    "Third item (correct position 3)"
  ]
}
```

### LINKED
Follow-up question linked to another block. Only shown if the referenced block is answered correctly.
```json
{
  "type": "LINKED",
  "linkedBlockId": "block_id_here",
  "content": "Follow-up question based on previous answer",
  "acceptedAnswers": [
    "answer variation 1"
  ]
}
```
Note: Since IDs are auto-generated on import, LINKED blocks are difficult to use in imported JSON. Avoid using LINKED blocks in generated lessons unless the user specifically requests them.
