---
verified: 2026-11-22
---

# 10. Parallel agents: worktrees, background and cloud agents

- **What:** one checkout per agent.
  - Local: `claude -w`, Codex worktrees, Cursor's automatic worktrees, Antigravity subagents with a `branch` workspace.
  - Cloud: Claude cloud sessions, Codex Cloud, Cursor cloud agents, the Copilot cloud agent, Antigravity remote agents.
- **Use when:**
  - independent tasks
  - best-of-N (the same prompt across several models, then pick the best result)
  - backlog chores sent to cloud agents that return PRs
  - one large mechanical change split into units after you approve a plan (Claude `/batch`)
- **Overkill and anti-patterns:**
  - two agents editing the same files without worktrees
  - one giant shared task: in a parallel C-compiler build, all agents hit the same bug and overwrote each other's fixes
- **Why it works:** isolated checkouts stop agents from colliding. Copy local-only files into each worktree with `.worktreeinclude`, and preinstall dependencies for cloud agents.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Run agents in parallel: https://code.claude.com/docs/en/agents
  - Building a C compiler with parallel Claudes (2026-02-05): https://www.anthropic.com/engineering/building-c-compiler
  - Codex best practices: https://learn.chatgpt.com/guides/best-practices
  - Codex long-running work & `/goal`: https://learn.chatgpt.com/docs/long-running-work
  - Cursor: best practices for coding with agents (2026-01-09): https://cursor.com/blog/agent-best-practices
  - Antigravity artifact review & subagents: https://antigravity.google/docs/artifact-review, https://antigravity.google/docs/subagents
  - GitHub Copilot cloud agent best practices: https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results
