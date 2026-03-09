---
name: web-research
description: Search the web, extract URLs to Markdown, or convert documents (PDF/DOCX/PPTX). Use when Kellen says "research X", "find resources on Y", "extract this URL", "scrape this page", "convert this PDF", "look up X online", or any variation of web-based research and extraction.
model: claude-sonnet-4-6
effort: medium
tools: [Read, Bash, Write, WebSearch, WebFetch]
---

# Web Research

## Purpose
Search the web, extract page content to clean Markdown, and convert documents — using a tiered local-first pipeline that doesn't burn API credits.

## Steps

### 1. Parse Intent
Determine mode from the user's request:
- **search** — find URLs on a topic (discovery only)
- **extract** — convert a specific URL to Markdown
- **convert** — convert a local file (PDF, DOCX, PPTX) to Markdown
- **research** — full pipeline: search + extract top results + summarize

### 2. Discovery (search / research modes)

Try the Python tool first:
```bash
cd "/home/kp/Desktop/Executive Assistant" && tools/.venv/bin/python3 tools/web-research.py search "QUERY" --num 10
```

If the script reports `SERPER_API_KEY not set`, fall back to the `WebSearch` built-in tool for discovery. Present the top results and ask which to extract (unless in research mode, where you extract the top 5 automatically).

### 3. Extraction (extract / research modes)

For each URL:
```bash
cd "/home/kp/Desktop/Executive Assistant" && tools/.venv/bin/python3 tools/web-research.py extract "URL"
```

The script tries Crawl4AI (local, unlimited) → Jina Reader (free proxy) → BeautifulSoup (static). Output goes to `temp/web-research/` — the script prints the file path.

Read the output file to get the extracted content.

If all tiers fail on a URL, note it and move on to the next source.

### 4. Document Conversion (convert mode)

```bash
cd "/home/kp/Desktop/Executive Assistant" && tools/.venv/bin/python3 tools/web-research.py convert "/path/to/file.pdf"
```

Supports PDF, DOCX, PPTX, XLSX via Microsoft MarkItDown. Output goes to `temp/web-research/`.

### 5. Full Research Pipeline (research mode)

```bash
cd "/home/kp/Desktop/Executive Assistant" && tools/.venv/bin/python3 tools/web-research.py research "QUERY" --num 5 --depth normal
```

Use `--depth deep` for comprehensive research (extracts up to 10 results with longer content).

If Serper key is not set, manually orchestrate: use WebSearch for discovery, then extract each URL individually per step 3.

### 6. Synthesize and Present

After extraction:
1. Read the output file(s) from `temp/web-research/`
2. Summarize key findings across sources
3. Present a concise brief with source links
4. Note where full extractions are saved for reference

## Inputs
- A search query, URL, or file path
- Optional: depth preference (normal/deep), number of results

## Output
- Markdown files in `temp/web-research/` (persists within session, gitignored)
- Concise summary with source attribution presented to Kellen

## Error Handling

Use the 5-step self-correction loop before escalating to Kellen:

1. **Read** — Parse the error message. Identify the failing component, line, or tool.
2. **Research** — Check if this is a known pattern (search codebase, read docs, check `agents/memory/SHARED.md`).
3. **Patch** — Apply a targeted fix. Change one thing at a time.
4. **Retry** — Re-run the failed step. If it fails again with a *different* error, loop back to step 1 (max 3 loops).
5. **Log** — Whether fixed or not, note what happened. If escalating, include: error message, what you tried, and why it didn't work.

**Skill-specific error handling:**
- On Crawl4AI failure: automatic fallback to Jina → bs4 (handled in Python script)
- On Serper failure: fall back to `WebSearch` built-in tool
- On total extraction failure for a URL: skip it, note the failure, continue with other sources
- Escalation: if all URLs fail or if authentication/paywall blocks all extraction attempts

## API Keys (if applicable)
This skill requires the following keys in `.env`:
- `SERPER_API_KEY` — Google SERP API from serper.dev. 2500 free queries on signup, then $0.30-1.00/1k queries. **Optional** — skill falls back to WebSearch if not set.
