---
verified: 2026-11-22
---

# 7. Scope the task: goal, context, constraints, done-when

- **What:** state the **Goal**, **Context** (files and patterns to follow), **Constraints** and **Done when**. Describe the result, not the steps. An issue assigned to a cloud agent *is* the prompt: write it as problem + acceptance criteria + files.
- **Use when:** every non-trivial request.
- **Overkill:** spelling out steps that frontier models already know. Prescriptive micro-instructions can hurt. Decompose less than you used to.
- **Why it works:**
  - Pointing at an existing pattern beats describing one.
  - Constraints work better than checklists: "No TODOs, no partial implementations" beats "remember to finish".
  - Signal scope upward too ("be ambitious: empty and error states, keyboard nav"), with numbers where possible.
- **Sources:**
  - Claude Code best practices: https://code.claude.com/docs/en/best-practices
  - Harness design for long-running apps (2026-03-24): https://www.anthropic.com/engineering/harness-design-long-running-apps
  - Codex best practices: https://learn.chatgpt.com/guides/best-practices
  - Codex prompting: https://learn.chatgpt.com/docs/prompting
  - Cursor: towards self-driving codebases (2026-02-05): https://cursor.com/blog/self-driving-codebases
  - GitHub Copilot cloud agent best practices: https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results
