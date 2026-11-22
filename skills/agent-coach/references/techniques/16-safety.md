---
verified: 2026-11-22
---

# 16. Safety: contain the agent rather than approving every action

- **What:** sandbox with both filesystem *and* network isolation, deny rules that hold in every mode, credentials kept out of the agent's reach, and pushes allowed only to PR branches with `main` protected.
- **Use when:** autonomous modes, untrusted repos or content, anything near secrets.
- **Why it works:**
  - People approve almost all permission prompts, so approvals stop being a real check.
  - Auto modes are classifiers, not guarantees, so "never" rules belong in deny rules or hooks.
  - Prompt injection arrives through READMEs, issues and web pages. Avoid the "lethal trifecta" of private data + untrusted content + an exfiltration channel by cutting one leg.
  - Repo-local agent config is untrusted until you accept the folder.
  - Codex: start with tight sandbox and approval settings and loosen them only for trusted repos.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - How we contain Claude across products (2026-05-25): https://www.anthropic.com/engineering/how-we-contain-claude
  - How we built Claude Code auto mode (2026-03-25): https://www.anthropic.com/engineering/claude-code-auto-mode
  - Claude Code sandboxing (2025-10-20): https://www.anthropic.com/engineering/claude-code-sandboxing
  - Codex best practices: https://learn.chatgpt.com/guides/best-practices
  - Antigravity CLI best practices: https://antigravity.google/docs/cli/best-practices
  - Practitioner — Simon Willison, The lethal trifecta (2025-06-16): https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/
