# Workflow: Web Research

Search the web, extract content from URLs, and convert documents. Use when the user asks to research a topic, extract a URL, or convert a file.

## Capabilities

1. **Search** — Find information on a topic using web search.
2. **Extract** — Pull content from a URL and convert to Markdown.
3. **Convert** — Transform PDF/DOCX/PPTX files to Markdown.

## Step 1: Determine Action

Based on the user's request:
- "Research X", "Find info about Y" → **Search** then **Extract** top results
- "Extract this URL", "Scrape this page" → **Extract** the specific URL
- "Convert this PDF" → **Convert** the specific file

## Step 2: Execute

### Search
Use the available search tools (Google Search, web_search, or equivalent) to find relevant results. Summarize the top 5-10 results with titles, URLs, and brief descriptions.

### Extract
Fetch the URL content. Clean and convert to well-structured Markdown:
- Preserve headings, lists, code blocks, and tables
- Remove navigation, ads, and boilerplate
- Save long extractions to `temp/web-research/` (gitignored)

### Convert
For document files (PDF, DOCX, PPTX):
- Use available conversion tools (markitdown, pandoc, or built-in)
- Save output to `temp/web-research/`
- Report the output path and a brief summary

## Step 3: Synthesize

If the user asked for research (not just extraction):
1. Read through extracted content
2. Synthesize key findings into a concise summary
3. Cite sources with URLs
4. Highlight areas of consensus and disagreement
5. Note gaps in the available information

## Output

```
## Research: [topic]

### Key Findings
- [finding with source citation]
- [finding with source citation]

### Sources
1. [Title](URL) — [brief description]
2. [Title](URL) — [brief description]

### Gaps / Further Research Needed
- [areas where information was incomplete or contradictory]
```

For extractions, just deliver the Markdown content or report the saved file path.
