# Gemini Assistant Memory

<!-- Domain-specific knowledge: CLI quirks, model performance, discourse outcomes -->

## Bridge Performance
- **Timeout:** 180s is too short for audits of files >1000 lines. Use `--timeout 300` for audit tasks.
- Gemini reads files via `cat` in shell commands when `read_file` tool hits workspace restrictions. This works but adds latency.
- **Auto-fallback (2026-03-15):** Bridge now automatically scales down models on 429 errors AND timeouts. Tier order: 3.1-pro-preview → 2.5-pro → 2.5-flash. Exhausted models get a 15-min cooldown. Use `--status` to check availability. No need to manually specify `--model` anymore — the bridge picks the highest available.
- **Workspace override:** Bridge defaults to `projects/Gemini Assistant/` but can target any directory with `--workspace /path/to/project`. Use this for Portal audits so Gemini's `read_file` tool can access Portal files directly without `cat` workarounds.

## Discourse Patterns (from 2026-03-15 testing)

### Where Gemini Adds Unique Value
- **Security surface area** — Gemini caught outbound `postMessage('*')` data leakage that Claude missed
- **System-level thinking** — identified teacher workflow gaps (gradebook integration, context-sync vs daily-briefing confusion) that Claude's code-focused lens missed
- **Speed** — completes audits in 40-55s vs Claude's 80-120s. Good for rapid first-pass.

### Where Claude Adds Unique Value (learn from these)
- **React anti-patterns** — stale closures, missing useEffect deps, listener churn from inline callbacks in deps arrays, ref cleanup on unmount, completion guard patterns
- **WCAG precision** — cites specific criteria numbers, finds 2-3x more a11y issues, catches missing landmarks/heading hierarchy/focus management
- **Edge cases** — catches things like `allCompleteFireRef` not resetting on prop changes, `ChecklistBlock` firing `onComplete` repeatedly

### Synthesis Protocol
- Agreements = high confidence, safe to auto-fix
- When Claude and Gemini disagree on severity, Claude is usually more conservative (and usually right for student-facing code)
- Always check for Claude's "unique findings" — these are often the highest-value items
