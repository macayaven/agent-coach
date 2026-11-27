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

`coach install` sets up every supported tool it finds on your machine. To pick tools yourself, name them: `coach install claude codex cursor`.

The coach keeps to files of its own. It adds hooks to each tool's hook settings and, where a tool has no hooks, a rules file that belongs to it. It never writes its rules into `AGENTS.md`, `CLAUDE.md` or `GEMINI.md`, so instruction files you maintain or link from elsewhere stay untouched. The first time it edits a settings file, it keeps the original beside it as `<name>.agent-coach.bak`. `coach uninstall` removes everything it added.

| Tool | What gets installed | How coaching reaches each request |
|---|---|---|
| Claude Code (CLI, desktop app, IDE extensions) | A Claude Code plugin: hooks and skills | A hook on every prompt |
| Codex (CLI, IDE extension, ChatGPT desktop app) | Two hooks in `~/.codex/hooks.json`, skills in `~/.agents/skills` | A hook on every prompt, once you trust the hooks: run `/hooks` in Codex |
| Gemini CLI | Two hooks in `~/.gemini/settings.json`, a `/coach` command, skills in `~/.agents/skills` | A hook on every prompt |
| Antigravity (app, IDE, `agy` CLI) | Its own rules file, `~/.gemini/config/rules/agent-coach.md`, and skills in `~/.gemini/config/skills` | Always-on rules, read when a session starts |
| Cursor (IDE, `agent` CLI) | Two hooks in `~/.cursor/hooks.json`, skills in `~/.agents/skills` | Rules injected when a chat starts |
| VS Code with GitHub Copilot | A marked block in `~/.copilot/copilot-instructions.md`, or its own file under `~/.copilot/instructions/` if that file is a link; skills in `~/.copilot/skills` | Always-on instructions |

Hooks run through a small launcher, `~/.agent-coach/bin/coach-hook`, which finds a working Python 3 each time. They keep working after a Python upgrade.

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

### Turn off the per-prompt reminder

In Claude Code, Codex and Gemini CLI, a hook adds a one-line mode reminder to every prompt, so coaching doesn't fade in long sessions. If your own rules forbid hooks that add context to every prompt, turn it off:

```
coach reminder off     # or: coach reminder on
```

- **Codex, Gemini CLI, Cursor:** the installer removes the coach's per-prompt hook entry, so nothing runs per prompt. Codex asks you to trust its hooks again.
- **Claude Code:** a plugin's hooks can't be turned off one at a time, so the hook still runs and adds nothing. The cost is one short process per prompt, with no tokens.
- **What you lose:** the reminder itself. Where the per-prompt hook is gone, typed `coach <mode>` reaches the agent, which applies it and runs `coach <mode>` to save it.

The session-start rules don't change.

## Audit your setup

Per-request coaching only sees the prompt. `coach audit` looks at the setup your agent works in: the instruction files it loads, hooks, permissions, MCP servers, plugins, and whether the repo has tests and evals. v0 covers Claude Code.

```
coach audit            # findings and measurements, no model, no network, edits nothing
coach audit --json     # the same, for the coach-audit skill
```

For a ranked report with fixes, ask your agent: type `coach audit` in a chat, or `/agent-coach:coach-audit` in Claude Code. The `coach-audit` skill runs the command, reads your memory tool if one is connected, reads your latest `/insights` report if it's under 30 days old, and gives you the top three gaps, each with evidence, a technique ID and a fill-in-the-blanks fix.

- **Rules and measurements.** A rule fires only where a catalogue source states the threshold: the same instruction file loaded twice, an instruction file over 200 lines, all-caps IMPORTANT/ALWAYS/NEVER, tests with no test command in any instruction file, and `auto` or `bypassPermissions` with no deny rules or sandbox. Everything else (instruction tokens, context hooks, MCP servers, Stop hooks, plugins and skills, evals) is reported as a number for the skill to weigh.
- **Privacy.** It reads a fixed list of config files and outputs MCP servers by name and transport, hooks by event and source, and settings by key name. It never outputs environment variables, arguments, headers, URLs or hook commands.
- **History.** Each run is saved in `~/.agent-coach/state/audits/`, so the next one marks findings as new, still open or fixed.
- **Memory.** `coach memory "hybrid-memory: search core and this repo's project"` tells the skill which memory tool and projects to search; add `--save` to let it save the audit summary without asking. Without a hint, it uses whatever memory tool the agent has, and offers to save.

## Keeping it current

Practices change quickly, so the technique index carries a `reviewed:` date and each technique file carries a `verified:` date.

- **Monthly refresh.** A GitHub Action (`.github/workflows/refresh-techniques.yml`) has an agent re-read the official sources in [`sources.md`](skills/agent-coach/references/sources.md) and update the techniques following [`REFRESH.md`](skills/agent-coach/references/REFRESH.md). A second job, which runs no agent, checks the result, runs the tests and opens a pull request. You review and merge it.
- **Enabling it.** The refresh calls the Claude API, so it needs a sign-in and credit. See [Set up the monthly refresh](#set-up-the-monthly-refresh).
- **Getting the update.** Run `coach update` on each machine. It pulls the repository and refreshes every installed tool.
- **Staleness warning.** If the techniques were last reviewed more than 60 days ago, the coach tells you once per session to update.

## Set up the monthly refresh

**Sign-in without a stored key (preferred).** In the Claude Console, open Settings → Workload identity → Connect workload → GitHub Actions and create a rule for this repository:

| Field | Value |
|---|---|
| GitHub organization | the repository's owner |
| Repository | the repository's name |
| Branch / ref | `refs/heads/main` |
| CEL condition | leave empty |
| Workspaces | exactly one |

Then add the IDs the Console gives you as repository variables (Settings → Secrets and variables → Actions → Variables): `ANTHROPIC_FEDERATION_RULE_ID`, `ANTHROPIC_ORGANIZATION_ID`, `ANTHROPIC_SERVICE_ACCOUNT_ID` and `ANTHROPIC_WORKSPACE_ID`. Don't add the sample workflow the Console shows.

Run "Refresh techniques" once by hand from the Actions tab. If the sign-in is refused, the Console's Workload identity history shows the reason and the values the run sent. Two refusals are common:

- **`match_subject_prefix`.** GitHub can issue the subject in a newer format that includes numeric IDs, such as `repo:<owner>@<id>/<repo>@<id>:ref:refs/heads/main`. Copy the `sub` value from the history entry into the rule's subject.
- **`match_claim_value_mismatch`.** The wizard's "Only push" option adds a condition that the event is `push`, but the refresh is started by schedule or by hand. Remove the `event_name` condition from the rule.

**Sign-in with a key (alternative).** Add an `ANTHROPIC_API_KEY` repository secret from a dedicated key with a low spend limit. It is used only while the variables above are not set.

**Credit.** The Console organization needs API credit. The monthly API credits included in some Claude plans work, once they are linked to that organization: the workflow runs the agent with `claude -p` directly because those credits don't cover the Claude Code GitHub Action.

**Model.** The refresh uses Claude Code's default model. To choose another, set the repository variable `REFRESH_MODEL` to a model ID.

If a run fails, its log states why in the "Show why the agent failed" step.

## Context cost

The coach loads as little as it can, and only when it's needed. Figures are estimates in tokens (about four characters each); run `coach doctor` to see the current ones.

| When | Tokens | What loads |
|---|---|---|
| Start of each session | about 410 in `force`, 290 in `suggest` | The rules for the current mode only |
| Each prompt (Claude Code, Codex, Gemini CLI) | under 20; 0 with `coach reminder off` | A one-line mode reminder |
| First coached request in a session | about 1,150 | The technique index: when each technique applies, and its redo skeleton |
| Each time you ask `why` | up to about 470 | The one technique file with the rationale and sources |
| Mode `off` | 0 with hooks; about 70 in tools that use an instruction file | A stub that says how to turn the coach back on |
| `coach audit`, only when you ask | about 700 for the skill and 1,000 to 2,000 for the command's output | The `coach-audit` skill, then up to about 2,000 from memory and 3,000 from an `/insights` report |

The unit tests enforce these budgets, so a refresh can't quietly make the coach heavier. An eval case also checks that a normal coaching turn reads the index and no technique files.

## Test it

```bash
python3 -m unittest discover -s tests        # installer, hooks, mode logic, context budgets
bash tests/test_accept_refresh.sh            # the script that vets the monthly refresh
bash tests/test_run_refresh_agent.sh         # how the refresh agent's sign-in is handled
claude plugin eval . --runs 3 --ablation none   # behavior in Claude Code (makes real model calls)
claude plugin eval . --runs 3 --ablation none --case 'audit-*' --allow-tools Bash   # the audit cases need the shell
```

CI runs the first three on every pull request.

The eval suite in `evals/` checks that force mode asks for a redo without loading technique files, suggest mode does the task and adds a note, plain questions are answered directly, and off stays quiet. The `audit-*` cases replay a recorded audit of a fake home in `tests/fixtures/` and check that the report ranks at most three gaps with evidence, works without a memory tool, and ignores an instruction planted in the `/insights` report. They replay instead of collecting because the eval sandbox can't read `.claude/` folders; the unit tests cover the collector.

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
- `coach audit` reads Claude Code's config files. A sandboxed shell may not be allowed to: the `claude plugin eval` sandbox blocks every `.claude/` folder, `~/.claude` included, and Claude Code's own sandbox may too. The audit then lists the files it couldn't read instead of treating them as missing. Run it in your own terminal for a full result.
- Developed and tested on Linux. macOS should behave the same. Windows is untested; there, skills are copied instead of symlinked and `coach` isn't put on PATH.

## Layout

```
skills/agent-coach/SKILL.md                the coaching rules (single source for every tool)
skills/agent-coach/references/index.md     technique index, read once per coached session
skills/agent-coach/references/techniques/  one file per technique, read only on `why`
skills/agent-coach/references/             also: retired practices, sources, refresh procedure
skills/coach/SKILL.md                      /coach command
skills/coach-audit/SKILL.md                coach audit: ranks the setup gaps and proposes fixes
hooks/                                     per-prompt and session-start hook
bin/coach                                  CLI: modes, install, update, pack, doctor, audit
bin/audit.py                               the audit's collector, rules and measurements
bin/adapters.py                            per-tool installers
.claude-plugin/                            Claude Code plugin and marketplace manifests
.github/workflows/                         CI and the monthly refresh
.github/rulesets/protect-main.json         the branch protection applied to main
evals/, tests/                             behavioral evals and tests
```

See [CONTRIBUTING.md](CONTRIBUTING.md) to change the coach and [SECURITY.md](SECURITY.md) for how the repository is protected.
