---
verified: 2026-11-22
---

# 13. Independent review

- **What:** a reviewer that never saw the author's reasoning. Options:
  - a fresh subagent or session (`/code-review`)
  - Codex `/review` or automatic PR review
  - Cursor Bugbot
  - agent-to-agent review loops
- **Use when:** before merging anything non-trivial. Make the review check against the spec or acceptance criteria.
- **Overkill:** an evaluator pays off mainly when the task is at the edge of what the model can do. Always say "skip style": a reviewer asked to find problems always finds some, and fixing all of them adds needless abstraction. You still review the code yourself before asking colleagues to.
- **Why it works:** agents grade their own work generously. A separate, skeptical evaluator is far easier to tune.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Harness design for long-running apps (2026-03-24): https://www.anthropic.com/engineering/harness-design-long-running-apps
  - Codex best practices: https://learn.chatgpt.com/guides/best-practices
  - Harness engineering (2026-02-11): https://openai.com/index/harness-engineering/
  - Cursor: best practices for coding with agents (2026-01-09): https://cursor.com/blog/agent-best-practices
  - Practitioner — Simon Willison, Agentic Engineering Patterns: https://simonwillison.net/guides/agentic-engineering-patterns/
