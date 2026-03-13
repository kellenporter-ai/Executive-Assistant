# Workflow: Slide Deck

Generate polished, presentation-ready HTML slide decks using Reveal.js.

## Step 1: Gather Content

1. **Source material** — What content should the slides cover? (topic, file, URL, lesson plan, etc.)
2. **Audience** — Who will see this presentation? (students, colleagues, stakeholders)
3. **Slide count** — How many slides? (default: 15-25)
4. **Style** — Formal, casual, visual-heavy, text-light?

If the user provides a file or URL, extract/read it first.

## Step 2: Outline

Draft a slide-by-slide outline:
```
1. Title Slide — [title, subtitle, author]
2. Overview — [key points]
3-N. Content slides — [one concept per slide]
N+1. Summary / Takeaways
N+2. Q&A / Discussion
```

Present the outline for user approval before building.

## Step 3: Build

Generate a self-contained HTML file using Reveal.js:

### Technical Requirements
- **Viewport:** 1280x720 — all content must fit without scrolling
- **CDN:** Load Reveal.js from CDN (no local dependencies)
- **Self-contained:** Single HTML file with all styles inline
- **Typography:** h1: 2.2em, h2: 1.6em, body: 0.8-0.9em
- **Section padding:** 20px 30px max
- **Transitions:** Smooth, consistent (slide or fade)

### Design Guidelines
- One concept per slide — never overload
- Use visual hierarchy (size, color, position) to guide attention
- Dark backgrounds with light text for projection readability
- Minimal text — bullet points, not paragraphs
- Use speaker notes for detailed content (`<aside class="notes">`)

### For image-heavy decks
- Side-by-side layouts (image left, text right) prevent vertical overflow
- Dense content should be split across multiple slides
- Encode images as base64 `data:` URIs for self-contained files

## Step 4: Validate

1. Open the HTML file and verify:
   - All slides render within 1280x720 without scrolling
   - Navigation works (arrow keys, space bar)
   - No broken images or missing resources
   - Speaker notes are present where needed
2. Fix any issues found.

## Step 5: Deliver

Save to the user's requested location or `assets/Presentations/`.

Report: slide count, estimated presentation time (1-2 min per slide), and any speaker notes included.
