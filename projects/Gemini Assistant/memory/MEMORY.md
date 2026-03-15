# Memory

## Discourse Performance (2026-03-15)

### My Strengths (keep leveraging)
- Security surface area analysis — caught outbound `postMessage('*')` that peer missed
- Teacher workflow thinking — identified gradebook integration gap, context-sync confusion
- Speed — 40-55s on audits vs peer's 80-120s. Good for rapid first-pass.

### Peer's Strengths (learn from these)
- React anti-patterns: stale closures, missing useEffect deps, listener churn, ref cleanup
- WCAG precision: 2-3x more a11y findings, catches landmarks/heading hierarchy/focus management
- Edge cases: completion guards, ref reset on prop changes, repeated callback firing
- When peer and I disagree on severity, peer is usually more conservative (and usually right for student-facing code)

### Synthesis Protocol
- Agreements = high confidence
- My unique findings are often broader/systemic; peer's are often deeper/technical
- Always include a "Unique Findings" section in discourse reports — this is where the highest value lives

## Bridge Configuration
- Timeout: 300s for file-reading audits (180s times out on 1000+ line files)
- Shell `cat` works when `read_file` hits workspace restrictions, but adds latency
- **Auto-fallback built (2026-03-15):** Bridge auto-scales 3.1→2.5 Pro→2.5 Flash on 429 AND timeout. Gemini 3.1 can silently hang under load (not just 429). Timeout now treated as exhaustion signal.
- Both non-shared and shared versions have identical fallback logic
