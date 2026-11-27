---
description: With no memory tool connected, coach audit still completes and says memory wasn't available.
max_turns: 14
allowed_tools: [Bash, Read, Glob, Grep, Skill]
env:
  EVAL_AGENT_COACH_MODE: force
  EVAL_AGENT_COACH_REPLAY: tests/fixtures/audit-replay.json
---

coach audit
