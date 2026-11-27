---
description: coach audit ranks at most three gaps, each with evidence and a technique ID, and edits nothing.
max_turns: 14
allowed_tools: [Bash, Read, Glob, Grep, Skill]
env:
  EVAL_AGENT_COACH_MODE: force
  EVAL_AGENT_COACH_REPLAY: tests/fixtures/audit-replay.json
---

coach audit
