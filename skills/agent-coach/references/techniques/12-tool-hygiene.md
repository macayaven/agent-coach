---
verified: 2026-11-22
---

# 12. Tool hygiene: CLI first, few tools, good tool design

- **What:**
  - Using tools: prefer a CLI (`gh`, or point the agent at `--help`), and use MCP for systems without one. Add tools only when they unlock a real workflow; start with one or two, and turn off unused servers.
  - Building tools: a few consolidated, high-impact tools, namespaced names, meaningful token-efficient responses, actionable errors, and evaluation with agents running realistic tasks.
- **Overkill:** connecting a dozen servers "just in case". Idle tool definitions still cost context.
- **Why it works:** fewer, clearer tools mean less context spent and fewer wrong calls. Lint errors that carry remediation text teach the agent while it works.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Writing effective tools for agents (2025-09-11): https://www.anthropic.com/engineering/writing-tools-for-agents
  - Code execution with MCP (2025-11-04): https://www.anthropic.com/engineering/code-execution-with-mcp
  - Codex best practices: https://learn.chatgpt.com/guides/best-practices
  - Harness engineering (2026-02-11): https://openai.com/index/harness-engineering/
