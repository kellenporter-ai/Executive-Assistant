---
name: strict-forensic-search-logic
description: Forensic database searches must require exact allele and physical marker matches
type: project
---

National Forensic Database (NFD) queries in simulations should require exact input for alleles and hair characteristics (Medullary Index) to return a match.
**Why:** To prevent "guessing" or accidental discovery of the mastermind without precise analysis.
**How to apply:** Implement strict comparison logic (e.g., `userAlleles === correctAlleles`) and include multiple red herrings (10+ entries) with partial matches to test student precision.
