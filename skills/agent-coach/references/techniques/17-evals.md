---
verified: 2026-11-22
---

# 17. Measure: evals for prompts, skills and agent workflows

- **What:**
  - Start with 20–50 tasks taken from real failures, with unambiguous success criteria and reference solutions.
  - Grade outcomes, not the order of tool calls, and read the transcripts.
  - Track pass@k (any success in k tries) versus pass^k (all k succeed).
  - Capability evals graduate into a regression suite. Re-check your setup on every new model.
- **Use when:** changing a prompt, skill, instruction file or harness, or choosing between models or approaches.
- **Overkill:** one-off tasks. For individuals, a 3-item trial and `/usage` are often enough.
- **Why it works:** "it seems better" is noise. Agents are non-deterministic, so judge on several runs and on transcripts.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Harness design for long-running apps (2026-03-24): https://www.anthropic.com/engineering/harness-design-long-running-apps
  - Demystifying evals for AI agents (2026-01-09): https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents
  - Harness engineering (2026-02-11): https://openai.com/index/harness-engineering/
