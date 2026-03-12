---
name: perf-audit
description: Run a performance audit on Porter's Portal or any web project — bundle size analysis, render profiling, query performance, and Core Web Vitals check. Use when Kellen says "perf audit", "check performance", "bundle size", "why is it slow", "Chromebook performance", "check load times", or wants to verify performance budgets are met.
model: claude-sonnet-4-6
effort: high
tools: [Read, Glob, Grep, Bash, Agent]
---

## Purpose

Measure, analyze, and report on application performance by delegating to the performance-engineer agent. Produces a metrics report with actionable optimization recommendations.

## Steps

1. **Determine scope from `<ARGUMENTS>`:**
   - Full audit (default): bundle + queries + render patterns
   - Bundle only: "just check bundle size"
   - Query only: "audit Firestore queries"
   - Specific page: "the grading page is slow"
   - If no project specified, default to Porter's Portal (`projects/Porters-Portal`).

2. **Collect baseline metrics.** Run these measurements before delegating:

   ```bash
   # Bundle analysis
   cd "<project-path>" && npm run build 2>&1 | tail -20
   ls -la dist/assets/*.js 2>/dev/null | sort -k5 -n -r | head -20
   du -sh dist/ 2>/dev/null
   ```

   Write output to `temp/perf-audit-baseline.txt` if it exceeds 50 lines.

3. **Run bundle history comparison** (for bundle scope or full audits):
   ```bash
   cd "/home/kp/Desktop/Executive Assistant" && python3 tools/bundle-tracker.py --project "<project-path>"
   ```
   This compares current chunk sizes against `temp/bundle-history.json` (previous builds). Flags >10% chunk growth or >5% total growth. Include any regressions in the delegation below.

4. **Delegate to performance-engineer.** Launch the agent with:

   ```
   Run a performance audit on [project].

   ## Scope
   [full / bundle / query / specific page]

   ## Baseline Metrics
   [paste build output and chunk sizes]

   ## Performance Budgets
   | Metric | Budget |
   |--------|--------|
   | Initial bundle (gzipped) | < 250 KB |
   | Largest Contentful Paint | < 2.5s |
   | Time to Interactive | < 3.5s |
   | Cloud Function cold start | < 3s |
   | Firestore query response | < 500ms |

   ## Target Environment
   Chromebook, 1366x768, Chrome stable, school WiFi (~10 Mbps)

   ## What to Check
   - Bundle: chunk sizes, lazy loading coverage, manual chunk config
   - Queries: N+1 patterns, missing .limit(), missing indexes, listener count
   - Render: unnecessary re-renders, missing memoization, virtualization gaps
   - Memory: listener cleanup, subscription leaks, growing state

   Analyze the codebase and report findings. For any optimizations you can implement directly (memoization, lazy imports, query limits), go ahead and make the changes. For architectural changes, report recommendations only.
   ```

5. **Review results.** Read the performance-engineer's report. Verify:
   - Metrics are measured, not estimated
   - Recommendations match the target environment (Chromebook, not desktop)
   - Any code changes made are minimal and targeted

6. **If code was changed**, run the build to verify:
   ```bash
   cd "<project-path>" && npm run build 2>&1
   ```

7. **Report to Kellen:**

   ```markdown
   ## Performance Audit Results

   **Project:** [name]
   **Scope:** [full / bundle / query / page]

   ### Metrics
   | Metric | Current | Budget | Status |
   |--------|---------|--------|--------|
   | Bundle (gzipped) | X KB | 250 KB | PASS/FAIL |
   | ... | ... | ... | ... |

   ### Issues Found
   | Priority | Issue | Impact | Fix |
   |----------|-------|--------|-----|
   | HIGH | ... | ... | ... |

   ### Changes Made (if any)
   - [file]: [what changed, before/after metric]

   ### Remaining Opportunities
   - [Deferred items for future rounds]
   ```

## Inputs
- Optional: project path (defaults to Porter's Portal)
- Optional: scope (full / bundle / query / page name)

## Output
- Metrics report with pass/fail against budgets
- Actionable optimization recommendations
- Any direct fixes already applied

## Error Handling

Use the 5-step self-correction loop before escalating.

- **Build failure:** Check for pre-existing build errors vs. errors introduced by perf changes. If perf-engineer broke the build, revert and report.
- **No dist/ directory:** Project hasn't been built yet. Run build first, then measure.
- **Escalate immediately:** If a proposed optimization would change user-visible behavior or data handling, confirm with Kellen before applying.
