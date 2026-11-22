---
verified: 2026-11-22
---

# 6. Test-first with agents

- **What:** red/green TDD. Write the tests, confirm they fail, commit them, then implement without editing the tests.
- **Use when:** clear inputs and outputs, reproducing a bug, refactors.
- **Overkill:** spikes and visual design. Use screenshots or an evaluator instead.
- **Why it works:**
  - A test seen failing first proves it exercises the new code, and test-first guards against unneeded code.
  - Saying explicitly that you're doing TDD stops the agent from writing mock implementations.
  - Forbidding edits to the tests stops the agent from "passing" by weakening them.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Effective harnesses for long-running agents (2025-11-26): https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents
  - Cursor: best practices for coding with agents (2026-01-09): https://cursor.com/blog/agent-best-practices
  - Practitioner — Simon Willison, Agentic Engineering Patterns: https://simonwillison.net/guides/agentic-engineering-patterns/
