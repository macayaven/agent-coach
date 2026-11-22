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

## Settings these protections depend on

Several protections are repository settings, not files, so they don't travel with a clone or fork. The owner applies them once, under the repository's **Settings**:

1. **Rules → Rulesets → New ruleset → Import a ruleset.** Choose `.github/rulesets/protect-main.json`. If the import is refused, create a branch ruleset for the default branch by hand: restrict deletions, block force pushes, and require a pull request before merging with zero required approvals.
2. **Actions → General → Workflow permissions.** Select read-only permissions, and tick "Allow GitHub Actions to create and approve pull requests" so the refresh can open its pull request.
3. **Secrets and variables → Actions.** Add the `ANTHROPIC_API_KEY` secret.
4. **Advanced Security.** Turn on private vulnerability reporting, and confirm secret scanning and push protection are on.

## If you fork or install someone else's copy

Read `hooks/coach_hook.py`, `bin/` and `skills/agent-coach/SKILL.md` first. They are short.

## Reporting a problem

Use **Report a vulnerability** on the repository's Security tab. Please don't open a public issue for a security problem.
