---
description: With no memory tool connected, coach audit still completes and says memory wasn't available.
max_turns: 14
allowed_tools: [Bash, Read, Glob, Grep, Skill]
env:
  EVAL_AGENT_COACH_MODE: force
  EVAL_AGENT_COACH_HOME: evals/fixtures/audit-home
  EVAL_AGENT_COACH_REPO: evals/fixtures/audit-home/work/app
---

coach audit
