---
verified: 2026-11-22
---

# 1. Context hygiene

- **What:** keep each session to one coherent task, and reset when it degrades.
- **Use when:** switching to an unrelated task (`/clear`). After two failed corrections, clear the session and write one better prompt instead of a third correction. Compact at milestones with a focus (`/compact <focus>`). In Codex, use one chat per outcome and fork only when the work really branches. In Cursor, start fresh when the agent repeats mistakes.
- **Overkill:** budgeting tokens aggressively. Large windows plus automatic compaction make running out rare. Reset for focus and cost, not out of fear.
- **Why it works:** recall degrades as context grows ("context rot", a finite attention budget). Failed attempts stay in the history and get re-read on every turn, and every turn re-sends the history, which costs money.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Effective context engineering for AI agents (2025-09-29): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents
  - Codex best practices: https://learn.chatgpt.com/guides/best-practices
  - Cursor: best practices for coding with agents (2026-01-09): https://cursor.com/blog/agent-best-practices
  - Antigravity CLI best practices: https://antigravity.google/docs/cli/best-practices
