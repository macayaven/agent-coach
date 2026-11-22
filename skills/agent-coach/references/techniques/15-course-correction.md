---
verified: 2026-11-22
---

# 15. Course correction

- **What:** watch the first minute and stop drift early.
  - Claude Code: `Esc` stops and keeps the work; `/rewind` restores code and/or conversation (but not files that Bash commands changed).
  - Codex: Enter steers the current turn, Tab queues a message, `/fork` branches.
  - Antigravity: `Esc`, `/rewind`, `/fork`.
  - Cursor: revert, refine the plan, rerun.
  - If you revert the agent's edit yourself, tell it.
- **Use when:** the agent drifts from the plan or repeats a mistake. After two failed corrections, rewind or clear instead.
- **Why it works:** fixing early is cheap, and a long trail of corrections pollutes the context.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Codex best practices: https://learn.chatgpt.com/guides/best-practices
  - Codex prompting: https://learn.chatgpt.com/docs/prompting
  - Antigravity CLI best practices: https://antigravity.google/docs/cli/best-practices
  - Cursor: best practices for coding with agents (2026-01-09): https://cursor.com/blog/agent-best-practices
