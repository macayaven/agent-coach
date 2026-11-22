---
verified: 2026-11-22
---

# 5. Spec-driven development

- **What:** a durable spec, then a plan, tasks, implementation and convergence. Examples are GitHub Spec Kit's `/speckit-*` steps and Codex ExecPlans (a living PLANS.md with Progress and Decision Log sections).
- **Use when:** greenfield features, work spanning several sessions or agents, handoffs, unattended runs.
- **Overkill:** bug fixes and small changes. Spec Kit phases are "independent entry points, not mandatory phases". Cursor warns that frozen specs age badly and prefers a living plan.
- **Why it works:** one artifact defines "done" for the builder, the reviewer and the next session, so any session can restart from the file alone.
- **Sources:**
  - GitHub Spec Kit: https://github.com/github/spec-kit
  - ExecPlans / PLANS.md (2025-10-07): https://developers.openai.com/cookbook/articles/codex_exec_plans
  - Cursor: dynamic planning agents (2026-01-30): https://cursor.com/blog/dynamic-planning-agents
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
