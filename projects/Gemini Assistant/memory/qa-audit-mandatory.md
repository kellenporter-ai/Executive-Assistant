---
name: qa-audit-mandatory
description: Never skip the QA audit step in development workflows.
type: feedback
---

Always run the QA audit step when generating code, tools, or activities, even if other planning or design steps are skipped to save time.
**Why:** The user explicitly stated that the QA audit step is vital and must not be skipped.
**How to apply:** During any Dev Pipeline or 2D Activity workflow (or any code generation), ensure a QA review is performed before delivering the final output. Route to the qa-engineer or equivalent for this step.