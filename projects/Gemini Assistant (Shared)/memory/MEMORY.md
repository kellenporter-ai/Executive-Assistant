# Memory

<!-- Context-agnostic learnings from discourse sessions — applicable to any teacher's setup -->

## Discourse Patterns <!-- propagate-to-shared -->

### Cross-Model Code Review
- Running two different AI models on the same code review produces stronger results than either alone
- Model A (detailed/technical) catches framework-specific anti-patterns, performance issues, and edge cases
- Model B (broad/fast) catches security surface area, system-level gaps, and UX insights
- Synthesis: agreements = high confidence; disagreements = valuable severity calibration signal
- Every discourse session found issues neither model would catch alone

### Cross-Model Accessibility Audits <!-- propagate-to-shared -->
- The detailed model finds 2-3x more WCAG issues — use it as the thorough pass
- The fast model works as a rapid first pass and catches UX insights the detailed model misses
- Key a11y patterns both models should check: landmark roles, focus management on tab/route changes, touch target sizing, color-only information, reduced motion gates, heading hierarchy, sr-only text for icon-only status indicators

### Bridge Timeout Guidance <!-- propagate-to-shared -->
- File-reading audits on files >1000 lines need 300s timeout minimum
- Simple prompts (no file reading): 60-120s is sufficient
- Complex multi-file analysis: 300s+
