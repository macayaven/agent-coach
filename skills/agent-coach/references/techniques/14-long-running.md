---
verified: 2026-11-22
---

# 14. Long-running agent harnesses

- **What:** state kept outside the context window, so a long run survives across sessions:
  - a JSON feature list where everything starts as "failing"
  - a progress file
  - an init or smoke-test script
  - one commit per feature
  - every session starts by reading progress and the git log
  - Variants: planner, generator and evaluator agents; ExecPlans; `/goal`; Stop-hook loops with iteration caps.
- **Use when:** multi-hour or unattended work. Before you leave it running, have:
  1. a definition of done
  2. a check the agent runs itself
  3. a limited access scope
  4. a stop condition (max turns or budget)
  5. a known destination for the result and a person who signs off
  - Try it on 3 items before the rest.
- **Overkill:** heavy scaffolding on current models. "Every component in a harness encodes an assumption about what the model can't do." Strip parts as models improve.
- **Why it works:** state outside the context survives compaction and new sessions, and commits make every step reversible.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Effective harnesses for long-running agents (2025-11-26): https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - Harness design for long-running apps (2026-03-24): https://www.anthropic.com/engineering/harness-design-long-running-apps
  - Building a C compiler with parallel Claudes (2026-02-05): https://www.anthropic.com/engineering/building-c-compiler
  - Codex long-running work & `/goal`: https://learn.chatgpt.com/docs/long-running-work
  - ExecPlans / PLANS.md (2025-10-07): https://developers.openai.com/cookbook/articles/codex_exec_plans
  - Cursor: best practices for coding with agents (2026-01-09): https://cursor.com/blog/agent-best-practices
