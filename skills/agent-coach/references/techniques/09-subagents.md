---
verified: 2026-11-22
---

# 9. Subagents for isolation, not for a better answer

- **What:** delegate bounded jobs to a subagent with its own context:
  - independent parallel work
  - noisy output (full test runs, wide searches) that you want summarized
  - unbiased review
  - restricted roles, such as a read-only reviewer
- **Overkill:** handing off the same task for a "better answer". It's the same model, it gathers the context again, and it multiplies tokens.
- **Why it works:** it keeps the main thread's context clean, and summaries come back instead of raw logs. Use a cheaper model for simple jobs, and check spend with `/usage`.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Codex best practices: https://learn.chatgpt.com/guides/best-practices
  - Codex prompting: https://learn.chatgpt.com/docs/prompting
