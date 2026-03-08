---
name: skill-name-here
description: Describe exactly when and why this skill should be used.
model: claude-sonnet-4-6
effort: high          # low | medium | high | max — cognitive effort directive (optional, default: high)
tools: []             # authorized tools/agents for this skill (optional)
---

# Skill Name

## Purpose
What this skill does in one sentence.

## Steps
1. First step
2. Second step
3. ...

## Inputs
- What information is needed to run this skill

## Output
- What the skill produces

## Error Handling
- On [failure type]: [recovery action]
- Escalation: [when to surface to Kellen vs. retry]

## API Keys (if applicable)
This skill requires the following keys in `.env`:
- `API_KEY_NAME` — where to get it and what it's for
