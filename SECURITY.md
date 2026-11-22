# Security

## Why this repository needs care

Installing Agent Coach gives this repository real reach into your tools:

- Its rules are loaded into your coding agents as instructions.
- Its hook, a Python script, runs on your machine on every prompt in Claude Code, Codex and Gemini CLI.
- If you use the cloud setup script, each new Claude Code web session clones `main` and runs code from it.

So anyone who can change `main` can change what your agents are told and what runs on your machine. Treat write access to this repository like access to your shell.

## How `main` is protected

- **Pull requests only.** A ruleset blocks direct pushes, force pushes and deletion of `main`. Its definition is in [`.github/rulesets/protect-main.json`](.github/rulesets/protect-main.json).
- **Tests on every pull request.** CI runs the unit tests, including the context-size budgets.
- **Pinned actions.** Workflows use actions pinned to exact commits, and Dependabot proposes updates once a month.
- **Secret scanning and push protection** are enabled in the repository settings.

## How the monthly refresh is contained

The refresh agent reads web pages, and a page could try to manipulate it. The workflow limits what a manipulated agent could do:

- The agent's job holds the API key, but it can't write to the repository, can't run shell commands, and can fetch only from the listed source domains.
- A separate job opens the pull request. It runs no agent and never sees the API key. It accepts only small Markdown files under `skills/agent-coach/references/` and runs the tests first.
- A person reviews and merges the pull request. Read the changes to `index.md` closely, because agents treat that file as instructions.

One risk remains: a manipulated agent could try to leak the API key to one of the allowed domains. Use a dedicated API key with a low spend limit for the `ANTHROPIC_API_KEY` secret, so a leak is cheap and easy to revoke.

## If you fork or install someone else's copy

Read `hooks/coach_hook.py`, `bin/` and `skills/agent-coach/SKILL.md` first. They are short.

## Reporting a problem

Use **Report a vulnerability** on the repository's Security tab. Please don't open a public issue for a security problem.
