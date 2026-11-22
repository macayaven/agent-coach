---
verified: 2026-11-22
---

# 4. Explore → plan → implement → verify (plan mode)

- **What:** read-only research and a plan you can review, before any edits. Where to find it:
  - Claude Code: Shift+Tab or `/plan`
  - Codex: `/plan`
  - Cursor: Shift+Tab (plans are saved to `.cursor/plans/`)
  - Antigravity: Planning mode, which produces an implementation-plan artifact
  - Copilot: research → plan → iterate on a branch
- **Use when:** multi-file changes, ambiguous requests, unfamiliar code, several valid approaches.
- **Overkill:** one-line diffs and routine tasks. Anthropic notes that a plain first prompt in a fresh session already does the right thing in most cases. Plan mode is a tool, not a ritual.
- **Why it works:** a plan is cheap to fix. When the output misses, revert and refine the plan rather than patching with follow-ups. Keep plans at the level of the product and its deliverables: wrong granular detail cascades.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Harness design for long-running apps (2026-03-24): https://www.anthropic.com/engineering/harness-design-long-running-apps
  - Cursor: best practices for coding with agents (2026-01-09): https://cursor.com/blog/agent-best-practices
  - Cursor: dynamic planning agents (2026-01-30): https://cursor.com/blog/dynamic-planning-agents
  - Antigravity CLI best practices: https://antigravity.google/docs/cli/best-practices
  - Antigravity artifact review & subagents: https://antigravity.google/docs/artifact-review, https://antigravity.google/docs/subagents
  - GitHub Copilot cloud agent best practices: https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results
