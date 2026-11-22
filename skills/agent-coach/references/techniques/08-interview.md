---
verified: 2026-11-22
---

# 8. Have the agent interview you

- **What:** before building, the agent asks you questions, multiple-choice where possible, until it can write a goal with measurable success criteria. Antigravity builds this in as `/grill-me`: one question at a time, each with a recommended answer, and the agent reads the code instead of asking what the code can answer. Combine it with `/plan` if you want a written plan too.
- **Use when:** fuzzy requirements, decisions you haven't made yet, design trade-offs, or risky refactors where compatibility and testing expectations need agreeing first.
- **Overkill:** well-specified tasks.
- **Why it works:** it brings out the decisions you haven't pinned down, and you supply what the agent can't read from the code. Plan modes increasingly ask questions on their own.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Codex best practices: https://learn.chatgpt.com/guides/best-practices
  - Codex long-running work & `/goal`: https://learn.chatgpt.com/docs/long-running-work
  - Cursor: dynamic planning agents (2026-01-30): https://cursor.com/blog/dynamic-planning-agents
  - Plan mode in Gemini CLI (2026-03-11): https://developers.googleblog.com/plan-mode-now-available-in-gemini-cli/
  - Antigravity `/grill-me`: https://antigravity.google/docs/commands/grill-me
