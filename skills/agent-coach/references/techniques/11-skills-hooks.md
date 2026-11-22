---
verified: 2026-11-22
---

# 11. Skills, commands and hooks: advisory vs deterministic

- **What:**
  - **Skills:** on-demand procedures. Only the name and description sit in context until the skill is used.
  - **Commands:** user-invoked prompts.
  - **Hooks:** scripts the harness *always* runs at lifecycle points.
- **Use when:**
  - Make a skill when you've reused or corrected the same prompt twice. Set `disable-model-invocation: true` on skills with side effects.
  - Use hooks or deny rules for zero-exception rules (format after every edit; never touch migrations/).
  - Schedule a skill only after it works reliably by hand.
  - Codex custom prompts are deprecated in favor of skills.
- **Overkill:** hooks for preferences ("prefer named exports"). `prompt`- or `agent`-type hooks call a model, so they aren't deterministic.
- **Why it works:** an instruction-file line is advice the model may decide doesn't apply. A hook always runs.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Codex best practices: https://learn.chatgpt.com/guides/best-practices
