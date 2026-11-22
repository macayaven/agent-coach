---
verified: 2026-11-22
---

# 3. Give the agent a way to verify its work

- **What:** a pass/fail check the agent runs and reads itself. Examples: tests, build exit code, types, lint, a diff against a fixture, a screenshot compared with the mockup, driving the browser like a user.
- **Use when:** almost always. All five vendors rank this first.
- **Overkill:** exploratory questions ("what would you improve?").
- **Why it works:** agents stop when the work *looks* done, and a check lets them close the loop themselves. Ask for evidence (the command and its output) rather than a claim like "tests pass".
- **Escalation, weakest to strongest:**
  1. Ask for the check in the prompt.
  2. A goal mode (`/goal` in Claude Code and Codex), where a checker re-evaluates the condition after every turn.
  3. A Stop hook that blocks finishing until the check passes.
  4. A fresh reviewer (13).
  - For UIs, use browser automation (Copilot ships the Playwright MCP server; OpenAI exposes DevTools, logs and metrics per worktree).
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Effective harnesses for long-running agents (2025-11-26): https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - Codex best practices: https://learn.chatgpt.com/guides/best-practices
  - Codex long-running work & `/goal`: https://learn.chatgpt.com/docs/long-running-work
  - Harness engineering (2026-02-11): https://openai.com/index/harness-engineering/
  - Antigravity CLI best practices: https://antigravity.google/docs/cli/best-practices
  - Cursor: best practices for coding with agents (2026-01-09): https://cursor.com/blog/agent-best-practices
  - GitHub Copilot cloud agent best practices: https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results
