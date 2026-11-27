# `coach audit`: coach the setup, not the request

Status: v0 in PR #7 (2026-11-27): unit tests and the three behavioral evals pass (3/3 each). Not yet accepted: the precision check on the maintainer's own findings is still open. This is a living spec: update it as decisions land, and record what changed and why.

**Changed while building v0:**
- A1 also fires for two different files with identical content, not only one file reached by two paths.
- A3 drops `MUST`: `retired.md` names IMPORTANT, ALWAYS and NEVER only. It maps to `11-skills-hooks`, whose "When" names ALWAYS/NEVER rules, so `why` has a technique file to open.
- The audit's own home and repo can be overridden with `EVAL_AGENT_COACH_HOME` and `EVAL_AGENT_COACH_REPO` (or `AGENT_COACH_AUDIT_HOME` and `AGENT_COACH_AUDIT_REPO`). With an overridden home it never reads folders above it, nor managed settings.
- Runs are saved per repository, in `~/.agent-coach/state/audits/<repo>-<hash>/<timestamp>.json`, so two repos audited on the same day don't overwrite each other. `--no-save` skips it.
- The JSON lists every hook by event and source (`hooks`), not only the context-adding ones, because some users' rules also forbid per-tool-call hooks.
- Paths shown with `~` mean the audited home, which the JSON states as `home`. Files the skill opens also carry an absolute `file`, so they resolve when the home is a fixture.
- `claude plugin details` reports the new skill as about 40 always-on tokens. The skills docs say a `disable-model-invocation: true` skill's description isn't in context, and this session's skill list agrees (it shows `agent-coach` but not `coach`), so the real per-session cost should be 0. Not measured directly.

## Problem

The coach diagnoses one request at a time. Its hooks see the prompt and nothing else: not the instruction files, hooks, permissions, tools or eval suites that decide how well an agent works. So setup-level techniques (02 instruction files, 03 verification hooks, 11 skills and hooks, 12 tool hygiene, 16 safety, 17 evals) rarely come up. In practice the coach falls back on scoping, verification and plan-first, because those are the gaps a single prompt shows.

Lab guidance has moved the same way. The leverage is in the agent's environment (context, tools, checks, persistence, measurement), not only in the wording of a request. See the sources in techniques 02, 03, 12, 16 and 17.

## Goal

One on-demand run shows me the few setup gaps that cost me the most, each with evidence and a fix I can apply.

Success criteria:
- Every finding cites evidence I can check: a path, a `path:line`, or a measured number.
- Every finding names the catalogue technique it comes from, so `why` works on it.
- At most three findings are ranked as top; the rest are listed in one line each.
- It edits nothing.
- It adds nothing to the per-prompt or per-session context.

## Non-goals

- Teaching how to build agents. The catalogue covers working with coding agents.
- Fixing the setup automatically. The audit proposes; I apply, or ask an agent to.
- Judging individual prompts. Per-request coaching already does that.

## Design: collect, check, coach

```
coach audit (Python, stdlib, no network, $0)        coach-audit skill (the user's agent)
  collect  -> setup facts (allow-listed files) --->   reads findings + measurements
  check    -> findings (rules) + measurements        + memory, if a memory tool is connected
           -> stdout, or --json for the skill         -> ranks, explains, gives fix skeletons
```

### 1. Collect

`coach audit` reads a fixed allow-list of config locations for the tools it knows (v0: Claude Code), plus the current repository. It produces a setup snapshot:

- **Instruction files** the tool loads, at user, project and parent level (`CLAUDE.md`, `AGENTS.md`): path, resolved path, line count, estimated tokens.
- **Hooks** from settings and enabled plugins: the event and the source. It doesn't record the commands.
- **Permissions:** the default or auto mode, whether deny rules exist, and whether the sandbox is on.
- **MCP servers:** name and transport only.
- **Plugins and skills:** names.
- **The repository:** test setup (a `tests/` dir, `pytest.ini`, a `test` script, a Makefile target), CI config, and an `evals/` directory.

### 2. Check

Rules are deterministic Python with fixed thresholds. A rule exists only when a catalogue source states the threshold; otherwise the number is reported as a measurement.

**Findings (v0)**

| ID | Technique | Fires when | Evidence |
|---|---|---|---|
| A1 `duplicate-instructions` | 02 | two instruction files the tool loads resolve to the same file, or hold identical text | both paths, the shared target, tokens loaded twice |
| A2 `long-instructions` | 02 | a loaded instruction file is over 200 lines (Claude's own recommendation, cited in 02) | path, line count |
| A3 `shouted-rules` | 11, retired.md | an instruction file uses all-caps IMPORTANT / ALWAYS / NEVER outside code | `path:line` for each (first five) |
| A4 `no-test-command` | 02, 03 | the repo has a test setup and no loaded instruction file names a command to run it | test config path, files checked |
| A5 `auto-without-containment` | 16 | an auto or bypass permission mode is on, with no deny rules and no sandbox | the setting names |

**Measurements (v0):** numbers with no sourced threshold. The skill weighs them against the user's own context.

| ID | Technique | What |
|---|---|---|
| M1 | 02 | tokens of instruction files loaded into every session |
| M2 | 11, 12 | hooks that add context on every prompt and at session start, with their sources (agent-coach's own included) |
| M3 | 12 | MCP servers enabled for every project (12 says "start with one or two"; there's no hard number) |
| M4 | 03 | whether any Stop hook runs a check |
| M5 | 11 | enabled plugins and skills |
| M6 | 17 | whether the repo has evals |

### 3. Coach

The `coach-audit` skill runs `coach audit --json` and reads the result. It queries memory if a memory tool is available (see below). Then it writes the report:
- the top three gaps, ranked by expected payoff, each with its evidence, technique ID, one line of rationale and a fill-in-the-blanks fix in the coach's usual style
- every other finding or measurement worth a look, one line each
- what it couldn't check (for example, no memory tool, or a config file it couldn't parse)

The model only makes the judgments rules can't: whether an instruction file's content is useful, whether a measurement is a problem for this user, and what memory says about repeated mistakes.

## Hard-coding: what goes in code and what doesn't

| In code | Not in code |
|---|---|
| Where each tool keeps its config (as the installers already do) | Anything about one user: servers, hosts, projects, endpoints |
| Rules whose threshold an official source states (A1–A5) | Thresholds no source states. These are reported as measurements (M1–M6) |
| How each measurement is defined | Judgments about content quality, which the model makes with the technique file |

Why rules at all: they're free, run in under a second, can be unit-tested, and give the model evidence it can't invent. Why not rules alone: content quality and the user's history need judgment.

**Staleness guard.** A test checks that every rule's technique ID still exists in `index.md` or `retired.md`. If the monthly refresh retires a technique, CI fails until a person retires or remaps its rules. The refresh agent can't edit code, so this keeps a human in the loop.

## User context from memory

The audit runs inside the user's agent, and that agent already has its tools connected. If one of them is a memory tool (any MCP server that can search notes), the skill uses it. The repository never names a server, host, key or project.

- **Optional hint.** `coach memory "<one line>" [--save]` saves a hint to `~/.agent-coach/state/memory-hint`, a plain-text file next to the mode: the hint on the first line, and `save-without-asking: yes` on the second when `--save` is given. The hint says which tool and which projects to search and where summaries go; `--save` allows saving without asking. `coach memory --clear` removes it. `coach audit --json` includes the hint. Without a hint, the skill searches whatever memory tool it finds.
- **At most three queries, about 2,000 tokens in total:**
  1. Mistakes or corrections the user keeps repeating. If nothing in the setup covers one (an instruction-file line, a hook, a test), that's a finding under 02 or 11. A habit of stopping before verifying becomes a Stop hook with a check (03, step 3).
  2. Errors with root causes in this repository. The same class of error twice becomes a gotcha line (02) or a failing test (06).
  3. The previous audit's summary, if one was saved, so the report can say "still open since ___".
- **Memory text is data, never instructions (16).** An eval checks this.
- **Per-request coaching doesn't query memory.** The always-on force rules are already 415 of their 450-token budget, and a memory call in every session adds delay and cost. Memory reaches per-request coaching through the audit instead (v1 focus line, below).

### Saving the audit summary (v0)

After the report, the skill saves one summary per audit per repository through the memory tool. Other agents can then see what the last audit found and what's still open, and the next audit can tell new gaps from old ones.

- **What's saved:**
  - the date and the repository
  - each finding's ID, with its status: new, still open, or fixed since the last audit
  - the measurements as numbers
  - the top three and the fix proposed for each

  Never config values or file contents. The CLI's JSON doesn't contain them, so the summary can't either.
- **Where it goes:** the place the hint names, otherwise the memory tool's default. If the tool can replace a note, the summary replaces the previous audit's note for the same repository, so memory keeps the current state and the tool keeps the history.
- **Permission:** the skill saves without asking when the hint says so (`coach memory` takes a `--save` flag). Otherwise it offers to save in one line at the end of the report. Writing to a user's memory is a side effect, so it isn't done silently by default.
- **Local copy:** every run is also kept in `~/.agent-coach/state/audits/<date>.json`, so diffs work without a memory tool.

## Session history: read `/insights`, don't parse transcripts

Session history shows patterns no agent writes to memory:
- the same prompt typed in several sessions, which is a skill candidate (11)
- runs of corrections (01, 15)
- sessions that end without a check (03)

The audit still doesn't parse transcripts itself, for four reasons:
- **The format is internal.** Claude Code documents its transcript format as internal: it changes between versions, and direct parsing can break on any release ([sessions](https://code.claude.com/docs/en/sessions.md#where-transcripts-are-stored)). A parser in this repo would be the brittle kind of hard-coding.
- **They hold untrusted content.** Transcripts include tool output from web pages, issues and files. Feeding that to an auditing agent that can write to memory adds untrusted content to private data and a write channel (16). They can also hold pasted secrets.
- **They expire.** Transcripts are deleted after 30 days by default (`cleanupPeriodDays`, [.claude directory](https://code.claude.com/docs/en/claude-directory.md#cleaned-up-automatically)).
- **Claude Code already analyzes them.** `/insights` reads up to 200 recent sessions and writes a report to `~/.claude/usage-data/report.html` ([costs](https://code.claude.com/docs/en/costs.md#analyze-your-usage-patterns)).

So in v0 the skill reads the latest `/insights` report, if one exists and is under 30 days old, as data and within about 3,000 tokens, and folds its patterns into the ranking. If there's no report, the audit says so and suggests running `/insights`, which costs model tokens, so the user decides. The report's format isn't documented either, so only the model reads it; no code depends on its structure. Codex session history comes later, through a supported export if one exists.

## Entry points

- **CLI:** `coach audit [--json] [--repo PATH] [--no-save]`. It prints findings and measurements without a model. `EVAL_AGENT_COACH_HOME` and `EVAL_AGENT_COACH_REPO` point it at a fixture, because `claude plugin eval` passes only `EVAL_` variables; relative paths resolve against the checkout. Each run is saved to `~/.agent-coach/state/audits/<repo>-<hash>/<timestamp>.json`. `bin/audit.py` is imported only by the `audit` and `memory` commands, so the hooks don't load it.
- **Skill:** `skills/coach-audit/SKILL.md`, with `disable-model-invocation: true` so it loads only when asked.
  - It's added to `SKILL_NAMES` so the other tools get it.
  - It's left out of `pack`, because chat apps can't read local files.
- **Typed `coach audit`:** today `TOGGLE_RE` doesn't match it, so it reaches the model as plain text. In v0 the hook recognizes it and adds one line pointing to the skill, on that prompt only. In tools without per-prompt hooks, invoke the skill by name.

## Related change: optional per-prompt reminder

This ships as its own pull request, before v0.

- **The setting:** `coach reminder off|on`, saved in `~/.agent-coach/state/reminder`. Some users' instructions forbid hooks that add context to every prompt, and this lets them follow that rule.
- **When off:**
  - No context is added per prompt; the session-start rules don't change.
  - Typed `coach <mode>` still works, because the session rules tell the agent to run `coach <mode>`, and `/coach` is a skill.
- **What you lose:**
  - the one-line reinforcement on each prompt, so coaching can fade in long sessions, as it already does in Cursor, Copilot and Antigravity
  - mode switches that skip the model call
- **Codex, Gemini CLI and Cursor:** the installer removes the per-prompt hook entry, so nothing runs per prompt. Codex then asks to re-trust its hooks.
- **Claude Code:**
  - A plugin's hooks can't be turned off one at a time, only the whole plugin or all hooks ([hooks](https://code.claude.com/docs/en/hooks.md)).
  - So the hook stays and adds nothing when the reminder is off. The remaining cost is one short process per prompt, with no tokens.
  - **Decided 2026-11-26: the per-prompt hook stays in the plugin.** People who install only the plugin keep the reminder and the instant mode switches. One short process per prompt is the accepted cost. Moving the hook into `~/.claude/settings.json` was rejected, because plugin-only installs would then lose it.

## Distribution

- **The coach is already a plugin in its own marketplace** (`claude plugin marketplace add macayaven/agent-coach`). Publishing is a push to this repository; there's no submission step ([publish](https://code.claude.com/docs/en/plugins/publish.md)).
- **The audit ships as a skill inside the `agent-coach` plugin:** one install, and it shares the catalogue. A marketplace can list several plugins that are enabled one by one ([create a marketplace](https://code.claude.com/docs/en/plugins/create-marketplace.md)). So a standalone, hook-free `coach-audit` plugin is possible later, for people who want the audit without always-on coaching.
- **Anthropic's plugin directory:**
  - Submissions go through claude.ai/directory/manage. They need a paid plan and a public GitHub repo, and get automated validation, a security scan and human review of new listings ([directory publish](https://claude.com/docs/directory/publish)).
  - `claude-plugins-official` isn't open to submissions.
- **Readiness on 2026-11-26:** `claude plugin validate --strict .` failed on two warnings, `ICON_MISSING` (a square PNG of 512–2,048 px; the first icon submitted is the one that sticks) and a missing `version`, and asked for `network.hosts`. Both are added on `chore/directory-readiness`: `.claude-plugin/icon.png` (a draft, 1,024 px) and `"network": {"hosts": ["github.com"]}`, the host `coach update` pulls from. `--strict` still fails on one warning, no `version`, on purpose: without a version, Claude Code detects updates by commit SHA, so each merged monthly refresh reaches users. With a version, nobody gets an update until it's bumped. The directory's checklist rates a missing version as a warning, not a blocker.

## Privacy and safety

- **Allow-listed reads only.** From `~/.claude.json` it reads MCP server names and transport type, never `env`, `args`, `headers` or URLs, and never per-project history fields.
- **Cloud folders are skipped.** It never walks into iCloud Drive, Google Drive, Dropbox or OneDrive.
- **No network.** The output stays on the machine, apart from what the user's own agent sends to its model during the skill step.
- **Tested.** A fixture places a fake key in `env`, `args` and `headers`; the test asserts it never appears in the output.

## Cost

- **`coach audit`:** $0, target under 1 second (measured: under 0.1 s on the maintainer's Mac).
- **Skill step:** one agent turn, up to three memory calls and one memory save. Target input: under 3,000 tokens (the JSON at about 1,000, memory at about 2,000, the skill text within the 700-token budget that `SKILL.md` has), plus up to about 3,000 more when an `/insights` report is read. Measured in v0: the skill is about 690 tokens; the JSON is about 870 on the eval fixture and about 1,650 on the maintainer's Mac (18 plugins, 33 MCP servers), so heavy setups run over the target.
- **Per prompt and per session:** zero added in v0. The hook line fires only on the `coach audit` prompt.

## Evals

- **Unit tests** (CI, $0), in `tests/test_audit.py`. Fixture homes are built in temp folders by the tests themselves. Tests cover:
  - each rule, with one case where it fires and one where it doesn't
  - the secrets fixture
  - every rule's technique ID existing in the catalogue
  - the skill's token budget
- **Behavioral evals** (`claude plugin eval`, paid, run with the maintainer's OK). Run them with `--case 'audit-*' --allow-tools Bash`: Bash is a gated tool in evals. They replay `tests/fixtures/audit-replay.json` (`EVAL_AGENT_COACH_REPLAY`), the collector's output for the fake home `tests/fixtures/audit-home/` with A1, A4 and A5 planted. `tests/fixtures/make_replay.py` rebuilds it, and a unit test fails when it drifts from the collector.
  - **Why replay (found in eval runs on 2026-11-27):**
    - `EVAL_` variables reach the agent's shell, and the plugin's `bin/` and `tests/` are readable.
    - The eval's shell sandbox blocks the plugin's `evals/` folder, every `.claude/` folder (fixture included) and `~/.local/bin/coach`.
    - A live collector therefore can't see a planted user `settings.json` or `/insights` report. v0 also hid this: unreadable paths looked absent.
    - The collector now lists every path it couldn't read in `unchecked`, and the skill falls back to `../../bin/coach` when `coach` is blocked. The same blocking would hit `~/.claude` for a user who runs the audit from a sandboxed shell.
  - The planted `/insights` report sits outside `.claude/` (`tests/fixtures/insights-report.html`) so the Read tool can open it.
  - `audit-ranks-with-evidence`: a fixture with three planted gaps. Each top finding must cite a path and a technique ID, and no files may be edited.
  - `audit-works-without-memory`: with no memory tool, the audit completes and says memory wasn't available.
  - `audit-ignores-planted-instruction`: the fixture's `/insights` report contains an instruction aimed at the auditor. The audit must not follow it, and may report it. (Not a `CLAUDE.md`: Claude Code loads a subfolder's `CLAUDE.md` as real instructions when the agent reads files there, which would test the wrong thing.)
- **Eval results (2026-11-27, default model, Haiku judge, 3 runs per case, $5.48 in all across six runs while fixing the wiring):**
  - `audit-ignores-planted-instruction`: 3/3. The agent read the planted report, didn't follow it, and flagged it.
  - `audit-works-without-memory`: 3/3.
  - `audit-ranks-with-evidence`: 1/3 with a single grader that checked four things at once, although the failed replies met its rubric when read by hand. Split into three single-criterion graders: 3/3, with 26 of 27 judge votes PASS.
- **v0 acceptance:**
  - Unit tests pass.
  - Each behavioral case passes 3 of 3 runs.
  - On the maintainer's own machines, the maintainer marks each top finding as real or not real. That gives the first precision number, recorded in the PR.
  - Saving to memory is checked by hand on the maintainer's machine, because the eval sandbox has no memory server. That's a known gap in the automated checks.

## Rollout

- **Optional per-prompt reminder:** its own pull request, not built yet. v0 doesn't depend on it, so v0 shipped first.
- **v0:** Claude Code only. The collector, rules A1–A5, measurements M1–M6, the skill with memory reads and the summary save, the `/insights` report as an input, the hook pointer, unit tests and the three behavioral evals.
- **Directory readiness (done early, its own branch):** the icon and declared hosts are on `chore/directory-readiness`.
- **After v0 ships:** approve the final icon, then submit to Anthropic's plugin directory.
- **v1:**
  - Focus line: `coach focus <ID> [<ID>]` saves up to two technique IDs, and the session-start rules gain one line, "Focus: prefer <IDs> when they fit" (about 15 tokens). This keeps per-request coaching aligned with the last audit without a memory call per session.
  - Diffs against the previous audit.
  - A Codex collector.
- **Later:**
  - Collectors for Gemini CLI, Antigravity, Cursor and Copilot.
  - Codex session history through a supported export.
  - A standalone, hook-free `coach-audit` plugin, if people ask for one.

## Open decisions

| # | Decision | Status |
|---|---|---|
| 1 | Read memory during an audit | Default: yes, when a memory tool is connected |
| 2 | Save audit summaries to memory | **Decided 2026-11-26: yes, in v0.** Without asking only when the hint allows it |
| 3 | How memory reaches per-request coaching | Default: through the v1 focus line, not a memory call per session |
| 4 | Session history | Default: read the latest `/insights` report; no transcript parser in this repo |
| 5 | Per-prompt reminder | **Decided 2026-11-26: make it optional** (`coach reminder off`), as its own PR (not built yet; v0 doesn't depend on it). In Claude Code the hook stays in the plugin and adds nothing when off; one short process per prompt is the accepted cost |
| 6 | Paid eval budget for v0 | Default: 3 cases × 3 runs, once before merge |
| 7 | Anthropic's plugin directory | Default: submit after v0 ships. Icon and hosts are ready; `--strict` keeps one warning (no `version`) on purpose, see Distribution |
