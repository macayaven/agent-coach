# Agent Coach

Agent Coach teaches you to work with AI coding agents the way top AI labs and tool makers currently recommend. It sits inside the coding agents you already use and coaches you on every request.

It has three modes:

| Mode | What happens on each request |
|---|---|
| `force` (default) | The agent holds off, names the one to three techniques your request was missing, and gives you a fill-in-the-blanks skeleton to redo it. When you resubmit, it grades the redo and then does the work. |
| `suggest` | The agent does the work as asked, then adds a short **Coach** note with the techniques and a better version of your request. |
| `off` | No coaching. |

In any mode, say `why` to get the full rationale for a technique, with its sources. In force mode, pure questions and tiny edits go straight through, and `coach skip` or `urgent` bypasses coaching for one request.

The techniques come from a sourced [playbook](skills/agent-coach/references/playbook.md) that is refreshed every month (see [Keeping it current](#keeping-it-current)).

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

Chat apps can't run the installer. Do it by hand, once per app:

1. Run `coach pack`, then upload `dist/agent-coach-skill.zip` as a skill (claude.ai: Customize → Skills; Gemini: Customize → Skills; ChatGPT desktop: Skills).
2. Add this line to the app's custom instructions:
   `Use the agent-coach skill on every request. Mode: force, unless I say "coach suggest" or "coach off".`

If the app has no skill upload, create a project, add `SKILL.md` and `playbook.md` from the zip as project files, and put the same line in the project's instructions.

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

Practices change quickly, so the playbook carries a `reviewed:` date and each technique carries a `verified:` date.

- **Monthly refresh.** A GitHub Action (`.github/workflows/refresh-playbook.yml`) has an agent re-read the official sources in [`sources.md`](skills/agent-coach/references/sources.md), update the playbook following [`REFRESH.md`](skills/agent-coach/references/REFRESH.md), and open a pull request. You review and merge it. To enable it, add an `ANTHROPIC_API_KEY` secret to the repository (or switch the workflow to `claude_code_oauth_token`), and allow GitHub Actions to create pull requests.
- **Getting the update.** Run `coach update` on each machine. It pulls the repository and refreshes every installed tool.
- **Staleness warning.** If the playbook is more than 60 days old, the coach tells you once per session to update.

## Test it

```bash
python3 -m unittest discover -s tests        # installer, hooks, mode logic
claude plugin eval . --runs 1 --ablation none   # behavior in Claude Code (makes real model calls)
```

The eval suite in `evals/` checks that force mode asks for a redo, suggest mode does the task and adds a note, plain questions are answered directly, and off stays quiet.

## Limits

- Coaching is an instruction to the model, reinforced by hooks where the tool has them. It isn't a hard lock: the model can occasionally skip it, and you can always say `coach skip`.
- Cursor, VS Code Copilot and Antigravity can't add context to each prompt, so the rules arrive once per session. In a very long session the coaching can fade; start a new chat.
- If both Codex and VS Code Copilot are installed, Copilot may list the skills twice, because it can read `~/.agents/skills` as well as `~/.copilot/skills`.
- Developed and tested on Linux. macOS should behave the same. Windows is untested; there, skills are copied instead of symlinked and `coach` isn't put on PATH.

## Layout

```
skills/agent-coach/SKILL.md              the coaching rules (single source for every tool)
skills/agent-coach/references/           playbook, sources, refresh procedure
skills/coach/SKILL.md                    /coach command
hooks/                                   per-prompt and session-start hook
bin/coach                                CLI: modes, install, update, pack
bin/adapters.py                          per-tool installers
.claude-plugin/                          Claude Code plugin and marketplace manifests
evals/, tests/                           behavioral evals and unit tests
```
