#!/usr/bin/env python3
"""Web research pipeline — search, extract, convert.

Usage:
    python3 tools/web-research.py search "query" [--num 10]
    python3 tools/web-research.py extract "https://example.com/page"
    python3 tools/web-research.py convert "/path/to/file.pdf"
    python3 tools/web-research.py research "query" [--num 5] [--depth normal|deep]

All output writes to temp/web-research/ by default. Use --stdout to print directly.
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote, urlparse

EA_ROOT = Path(__file__).resolve().parent.parent
TEMP_DIR = EA_ROOT / "temp" / "web-research"
ENV_FILE = EA_ROOT / ".env"


def load_env():
    """Load API keys from .env file."""
    env = {}
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                env[key.strip()] = value.strip()
    return env


def sanitize_filename(text, max_len=80):
    """Convert text to a safe filename."""
    safe = re.sub(r"[^\w\s-]", "", text).strip()
    safe = re.sub(r"[\s]+", "_", safe)
    return safe[:max_len].rstrip("_")


def ensure_temp_dir():
    """Create output directory if needed."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)


def write_output(content, name, stdout=False):
    """Write content to temp file or stdout. Returns file path."""
    if stdout:
        print(content)
        return None
    ensure_temp_dir()
    ts = int(time.time())
    filename = f"{ts}_{sanitize_filename(name)}.md"
    filepath = TEMP_DIR / filename
    filepath.write_text(content, encoding="utf-8")
    print(filepath, file=sys.stdout)
    return filepath


# ---------------------------------------------------------------------------
# Discovery layer
# ---------------------------------------------------------------------------

def search_serper(query, num_results=10):
    """Search via Serper.dev Google SERP API."""
    import requests

    env = load_env()
    api_key = env.get("SERPER_API_KEY", "")
    if not api_key:
        return None

    resp = requests.post(
        "https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "num": num_results},
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    results = []
    for item in data.get("organic", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        })
    return results


def format_search_results(results, query):
    """Format search results as Markdown."""
    lines = [f"# Search Results: {query}\n"]
    for i, r in enumerate(results, 1):
        lines.append(f"## {i}. {r['title']}")
        lines.append(f"**URL:** {r['url']}")
        lines.append(f"{r['snippet']}\n")
    return "\n".join(lines)


def cmd_search(args):
    """Execute search command."""
    results = search_serper(args.query, args.num)
    if results is None:
        print(
            "SERPER_API_KEY not set in .env. "
            "Use WebSearch built-in tool instead, or sign up at serper.dev "
            "(2500 free queries).",
            file=sys.stderr,
        )
        sys.exit(1)
    if not results:
        print(f"No results found for: {args.query}", file=sys.stderr)
        sys.exit(1)

    content = format_search_results(results, args.query)
    write_output(content, f"search_{args.query}", stdout=args.stdout)


# ---------------------------------------------------------------------------
# Extraction layer
# ---------------------------------------------------------------------------

async def extract_crawl4ai(url):
    """Extract URL content using Crawl4AI (primary tier)."""
    try:
        from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

        browser_cfg = BrowserConfig(headless=True)
        crawl_cfg = CrawlerRunConfig()

        async with AsyncWebCrawler(config=browser_cfg) as crawler:
            result = await crawler.arun(url=url, config=crawl_cfg)
            if not result.success:
                return None
            md = result.markdown
            # markdown may be a MarkdownGenerationResult or a string
            if hasattr(md, "raw_markdown"):
                return md.raw_markdown
            return md if md else None
    except Exception as e:
        print(f"[crawl4ai] Failed: {e}", file=sys.stderr)
        return None


def extract_jina(url):
    """Extract URL content using Jina Reader API (fallback tier)."""
    import requests

    try:
        jina_url = f"https://r.jina.ai/{url}"
        resp = requests.get(
            jina_url,
            headers={"Accept": "text/markdown"},
            timeout=30,
        )
        resp.raise_for_status()
        text = resp.text.strip()
        return text if len(text) > 100 else None
    except Exception as e:
        print(f"[jina] Failed: {e}", file=sys.stderr)
        return None


def extract_bs4(url):
    """Extract URL content using BeautifulSoup (last resort)."""
    import requests
    from bs4 import BeautifulSoup

    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; research-bot)"},
            timeout=20,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script, style, nav, footer, header
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Basic cleanup: collapse blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text if len(text) > 100 else None
    except Exception as e:
        print(f"[bs4] Failed: {e}", file=sys.stderr)
        return None


def extract_url(url):
    """Try all extraction tiers: crawl4ai -> jina -> bs4."""
    # Tier 1: Crawl4AI (local, unlimited)
    print(f"[extract] Trying Crawl4AI for {url}...", file=sys.stderr)
    content = asyncio.run(extract_crawl4ai(url))
    if content:
        print("[extract] Success via Crawl4AI", file=sys.stderr)
        return content

    # Tier 2: Jina Reader (free proxy)
    print(f"[extract] Trying Jina Reader for {url}...", file=sys.stderr)
    content = extract_jina(url)
    if content:
        print("[extract] Success via Jina Reader", file=sys.stderr)
        return content

    # Tier 3: BeautifulSoup (static only)
    print(f"[extract] Trying BeautifulSoup for {url}...", file=sys.stderr)
    content = extract_bs4(url)
    if content:
        print("[extract] Success via BeautifulSoup", file=sys.stderr)
        return content

    return None


def cmd_extract(args):
    """Execute extract command."""
    content = extract_url(args.url)
    if content is None:
        print(f"All extraction methods failed for: {args.url}", file=sys.stderr)
        sys.exit(1)

    domain = urlparse(args.url).netloc
    path_slug = sanitize_filename(urlparse(args.url).path)
    name = f"{domain}_{path_slug}" if path_slug else domain
    header = f"# Extracted: {args.url}\n\n"
    write_output(header + content, name, stdout=args.stdout)


# ---------------------------------------------------------------------------
# Document conversion layer
# ---------------------------------------------------------------------------

def cmd_convert(args):
    """Convert a local document to Markdown."""
    filepath = Path(args.path).resolve()
    if not filepath.exists():
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    try:
        from markitdown import MarkItDown

        md = MarkItDown()
        result = md.convert(str(filepath))
        content = result.text_content
    except Exception as e:
        print(f"Conversion failed: {e}", file=sys.stderr)
        sys.exit(1)

    name = f"converted_{filepath.stem}"
    header = f"# Converted: {filepath.name}\n\n"
    write_output(header + content, name, stdout=args.stdout)


# ---------------------------------------------------------------------------
# Full research pipeline
# ---------------------------------------------------------------------------

def cmd_research(args):
    """Search + extract top results."""
    # Discovery
    results = search_serper(args.query, args.num)
    if results is None:
        print(
            "SERPER_API_KEY not set. For full research pipeline, either:\n"
            "  1. Add SERPER_API_KEY to .env (serper.dev, 2500 free queries)\n"
            "  2. Use the /web-research skill which can fall back to WebSearch\n",
            file=sys.stderr,
        )
        sys.exit(1)

    if not results:
        print(f"No results found for: {args.query}", file=sys.stderr)
        sys.exit(1)

    # How many to extract
    extract_count = min(args.num, len(results))
    if args.depth == "deep":
        extract_count = min(10, len(results))

    # Extract top results
    sections = [f"# Research: {args.query}\n"]
    sections.append(f"*{len(results)} results found, extracting top {extract_count}*\n")

    for i, r in enumerate(results[:extract_count], 1):
        sections.append(f"---\n## Source {i}: {r['title']}")
        sections.append(f"**URL:** {r['url']}")
        sections.append(f"**Snippet:** {r['snippet']}\n")

        content = extract_url(r["url"])
        if content:
            # Truncate very long extractions to keep output manageable
            max_chars = 5000 if args.depth == "normal" else 15000
            if len(content) > max_chars:
                content = content[:max_chars] + f"\n\n*[Truncated at {max_chars} chars]*"
            sections.append(content)
        else:
            sections.append("*Extraction failed for this URL.*")
        sections.append("")

    full_content = "\n\n".join(sections)
    write_output(full_content, f"research_{args.query}", stdout=args.stdout)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Web research pipeline — search, extract, convert.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Shared flag added to each subparser
    stdout_kw = dict(action="store_true", help="Print output to stdout instead of temp/")

    # search
    p_search = sub.add_parser("search", help="Search the web via Serper API")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--num", type=int, default=10, help="Number of results")
    p_search.add_argument("--stdout", **stdout_kw)

    # extract
    p_extract = sub.add_parser("extract", help="Extract a URL to Markdown")
    p_extract.add_argument("url", help="URL to extract")
    p_extract.add_argument("--stdout", **stdout_kw)

    # convert
    p_convert = sub.add_parser("convert", help="Convert a document to Markdown")
    p_convert.add_argument("path", help="Path to document (PDF, DOCX, PPTX, etc.)")
    p_convert.add_argument("--stdout", **stdout_kw)

    # research
    p_research = sub.add_parser("research", help="Full pipeline: search + extract")
    p_research.add_argument("query", help="Research query")
    p_research.add_argument("--num", type=int, default=5, help="Number of results to extract")
    p_research.add_argument("--depth", choices=["normal", "deep"], default="normal")
    p_research.add_argument("--stdout", **stdout_kw)

    args = parser.parse_args()

    commands = {
        "search": cmd_search,
        "extract": cmd_extract,
        "convert": cmd_convert,
        "research": cmd_research,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
