# Agent Coach

Agent Coach teaches you to work with AI coding agents the way top AI labs and tool makers currently recommend. It sits inside the coding agents you already use and coaches you on every request.

It has three modes:

| Mode | What happens on each request |
|---|---|
| `force` (default) | The agent holds off, names the one to three techniques your request was missing, and gives you a fill-in-the-blanks skeleton to redo it. When you resubmit, it grades the redo and then does the work. |
| `suggest` | The agent does the work as asked, then adds a short **Coach** note with the techniques and a better version of your request. |
| `off` | No coaching. |

In any mode, say `why` to get the full rationale for a technique, with its sources. In force mode, pure questions and tiny edits go straight through, and `coach skip` or `urgent` bypasses coaching for one request.

The techniques come from a sourced [catalogue](skills/agent-coach/references/index.md) that is refreshed every month (see [Keeping it current](#keeping-it-current)). The coach is built to stay cheap in context (see [Context cost](#context-cost)).

## Install

You need Python 3.8+ and git.

```bash
git clone https://github.com/macayaven/agent-coach ~/agent-coach
~/agent-coach/bin/coach install
```

`coach install` sets up every supported tool it finds on your machine. To pick tools yourself, name them: `coach install claude codex cursor`. Every config file it edits is backed up first as `<name>.agent-coach.bak`, and `coach uninstall` removes everything it added.

| Tool | What gets installed | How coaching reaches each request |
|---|---|---|
| Claude Code (CLI, desktop app, IDE extensions) | A Claude Code plugin: hooks and skills | A hook on every prompt |
| Codex (CLI, IDE extension, ChatGPT desktop app) | A block in `~/.codex/AGENTS.md`, a hook in `~/.codex/hooks.json`, skills in `~/.agents/skills` | A hook on every prompt, once you trust it: run `/hooks` in Codex |
| Antigravity (app, IDE, `agy` CLI) | A block in `~/.gemini/GEMINI.md`, skills in `~/.gemini/config/skills` | Always-on instructions, read when a session starts |
| Gemini CLI | The same `GEMINI.md` block, a hook in `~/.gemini/settings.json`, a `/coach` command | A hook on every prompt |
| Cursor (IDE, `agent` CLI) | Hooks in `~/.cursor/hooks.json`, skills in `~/.agents/skills` | Rules injected when a chat starts |
| VS Code with GitHub Copilot | A block in `~/.copilot/copilot-instructions.md`, skills in `~/.copilot/skills` | Always-on instructions |

Restart each tool after installing.

If you only use Claude Code, you can skip the clone and install the plugin directly:

```bash
claude plugin marketplace add macayaven/agent-coach
claude plugin install agent-coach@agent-coach
```

### Claude Code on the web

Cloud sessions don't load plugins from your machine. Add this to your cloud environment's **Setup script** instead, so every session starts with the coaching rules:

```bash
git clone --depth 1 https://github.com/macayaven/agent-coach /opt/agent-coach
mkdir -p ~/.claude && python3 /opt/agent-coach/bin/coach render >> ~/.claude/CLAUDE.md
```

### Chat apps (claude.ai, ChatGPT, Gemini)

Chat apps can't run the installer, and nothing outside the app can change their settings. Do it by hand, once per app:

1. Run `coach pack`, then upload `dist/agent-coach-skill.zip` as a skill:
   - claude.ai: Customize → Skills → + → Upload (code execution must be on)
   - Gemini: Customize → Skills → Create → upload
   - ChatGPT desktop app: Skills
2. Add this line to the app's custom instructions (claude.ai: Settings → Instructions; ChatGPT: Settings → Personalization; Gemini: Settings → Personal context):
   `For requests about code or working with AI agents, use the agent-coach skill. Mode: force, unless I say "coach suggest" or "coach off".`

The line limits coaching to coding work, because custom instructions apply to every chat you have in that app. Change `force` to `suggest` if being asked to redo requests gets in the way there.

If the app has no skill upload, create a project, add `SKILL.md` and `references/index.md` from the zip as project files, and put the same line in the project's instructions.

## Switch modes

Type one of these in any chat, or in a terminal:

```
coach force
coach suggest
coach off
coach status
```

The mode is saved once for all tools, in `~/.agent-coach/state/mode`.

- **Claude Code, Codex, Gemini CLI:** the hook handles the command instantly, without calling the model. `/coach off` also works.
- **Other tools:** the agent applies the new mode for the current session and runs `coach <mode>` to save it. New sessions read the saved mode.

## Keeping it current

Practices change quickly, so the technique index carries a `reviewed:` date and each technique file carries a `verified:` date.

- **Monthly refresh.** A GitHub Action (`.github/workflows/refresh-techniques.yml`) has an agent re-read the official sources in [`sources.md`](skills/agent-coach/references/sources.md) and update the techniques following [`REFRESH.md`](skills/agent-coach/references/REFRESH.md). A second job, which runs no agent, checks the result, runs the tests and opens a pull request. You review and merge it.
- **Enabling it.** Add a repository secret named `ANTHROPIC_API_KEY` under Settings → Secrets and variables → Actions. Use a dedicated API key with a low spend limit. Then run the workflow once by hand from the Actions tab to check it works.
- **Getting the update.** Run `coach update` on each machine. It pulls the repository and refreshes every installed tool.
- **Staleness warning.** If the techniques were last reviewed more than 60 days ago, the coach tells you once per session to update.

## Context cost

The coach loads as little as it can, and only when it's needed. Figures are estimates in tokens (about four characters each); run `coach doctor` to see the current ones.

| When | Tokens | What loads |
|---|---|---|
| Start of each session | about 410 in `force`, 290 in `suggest` | The rules for the current mode only |
| Each prompt (Claude Code, Codex, Gemini CLI) | under 20 | A one-line mode reminder |
| First coached request in a session | about 1,150 | The technique index: when each technique applies, and its redo skeleton |
| Each time you ask `why` | up to about 470 | The one technique file with the rationale and sources |
| Mode `off` | 0 with hooks; about 70 in tools that use an instruction file | A stub that says how to turn the coach back on |

The unit tests enforce these budgets, so a refresh can't quietly make the coach heavier. An eval case also checks that a normal coaching turn reads the index and no technique files.

## Test it

```bash
python3 -m unittest discover -s tests        # installer, hooks, mode logic, context budgets
bash tests/test_accept_refresh.sh            # the script that vets the monthly refresh
claude plugin eval . --runs 3 --ablation none   # behavior in Claude Code (makes real model calls)
```

CI runs the first two on every pull request.

The eval suite in `evals/` checks that force mode asks for a redo without loading technique files, suggest mode does the task and adds a note, plain questions are answered directly, and off stays quiet.

## How it works

1. **One set of rules.** `skills/agent-coach/SKILL.md` holds the rules for all three modes. Everything else is built from it.
2. **One saved mode.** `coach <mode>` writes the mode to `~/.agent-coach/state/mode`. Every tool reads it from there.
3. **Delivery per tool.** `coach install` gives each tool the strongest mechanism it supports:
   - a hook that adds the current mode's rules at session start and a one-line reminder on each prompt, or
   - a managed block in the tool's global instruction file, rewritten whenever the mode changes.
4. **Techniques on demand.** The agent reads the short index the first time it coaches in a session, and one technique file only when you ask `why`.

## Security

Installing Agent Coach lets this repository put instructions into your agents and run a small Python hook on your machine. `main` is therefore protected: changes arrive only through pull requests, CI runs on each one, and the monthly refresh agent is isolated from both the repository and the shell. [SECURITY.md](SECURITY.md) has the details and what to check before using a fork.

## Limits

- Coaching is an instruction to the model, reinforced by hooks where the tool has them. It isn't a hard lock: the model can occasionally skip it, and you can always say `coach skip`.
- Cursor, VS Code Copilot and Antigravity can't add context to each prompt, so the rules arrive once per session. In a very long session the coaching can fade; start a new chat.
- If both Codex and VS Code Copilot are installed, Copilot may list the skills twice, because it can read `~/.agents/skills` as well as `~/.copilot/skills`.
- Developed and tested on Linux. macOS should behave the same. Windows is untested; there, skills are copied instead of symlinked and `coach` isn't put on PATH.

## Layout

```
skills/agent-coach/SKILL.md                the coaching rules (single source for every tool)
skills/agent-coach/references/index.md     technique index, read once per coached session
skills/agent-coach/references/techniques/  one file per technique, read only on `why`
skills/agent-coach/references/             also: retired practices, sources, refresh procedure
skills/coach/SKILL.md                      /coach command
hooks/                                     per-prompt and session-start hook
bin/coach                                  CLI: modes, install, update, pack, doctor
bin/adapters.py                            per-tool installers
.claude-plugin/                            Claude Code plugin and marketplace manifests
.github/workflows/                         CI and the monthly refresh
.github/rulesets/protect-main.json         the branch protection applied to main
evals/, tests/                             behavioral evals and tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md) to change the coach and [SECURITY.md](SECURITY.md) for how the repository is protected.
