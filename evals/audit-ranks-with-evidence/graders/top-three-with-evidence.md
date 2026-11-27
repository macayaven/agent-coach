---
type: llm
weight: 2
---

Look only at the reply's top-ranked gaps (its "Top 3" section or equivalent).
PASS if there are at most three, and each one names a technique ID in the form `NN-name` (for example `16-safety`) and cites concrete evidence: a file path, a `path:line` or a number.
FAIL if there are more than three, or if any of them has no technique ID or no evidence.
