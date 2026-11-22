---
verified: 2026-11-22
---

# 2. Lean repo instruction files (AGENTS.md / CLAUDE.md / GEMINI.md)

- **What:** record only what the agent can't discover by reading the repo:
  - exact test, typecheck and lint commands, including how to run a single test
  - code that is misleading
  - decisions made outside the repo
  - anything you've had to correct twice
- **Use when:** setting up a repo for agents, or after the agent makes the same mistake twice. Ask it for a retrospective and add the lesson.
- **Overkill:** prose about architecture, style guides (use a linter), rare edge cases. Keep the file short: Claude recommends under 200 lines. OpenAI's harness team uses about 100 lines as a table of contents pointing into docs/. *Labs disagree on layout:* Codex lists important directories as useful content, while Anthropic says to leave layout out. The middle ground is a short map with pointers.
- **Why it works:** the file is loaded into every session, so each line costs attention. "Too much guidance becomes non-guidance," and a long file goes stale.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - CLAUDE.md, AGENTS.md & memory: https://code.claude.com/docs/en/memory
  - Codex best practices: https://learn.chatgpt.com/guides/best-practices
  - AGENTS.md in Codex: https://learn.chatgpt.com/docs/agent-configuration/agents-md
  - Harness engineering (2026-02-11): https://openai.com/index/harness-engineering/
  - GitHub Copilot cloud agent best practices: https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results
  - Antigravity CLI best practices: https://antigravity.google/docs/cli/best-practices
