---
reviewed: 2026-11-22
scope: Programming with AI coding agents (Claude Code, Codex, Antigravity, Cursor, Copilot)
---

# Agentic programming playbook

This is how top AI labs and coding-agent makers currently recommend working with coding agents. Each technique lists when to use it, when it's overkill, why it works, and a **redo skeleton**: the fill-in-the-blanks structure the coach gives the user in force mode. Source keys like [A1] are in the Sources section at the end. Labs sometimes disagree; where they do, the entry says so.

## Diagnose a request fast

Match what's missing from the user's request to the technique that fixes it. Choose the one to three with the most leverage; don't list everything.

| Symptom in the request | Technique |
|---|---|
| No way to tell when it's done or correct | 3 Verification |
| Vague goal, or the user hasn't decided the scope | 8 Interview, 7 Scoping |
| Multi-file, unfamiliar code, or several valid approaches | 4 Plan first |
| A bug fix or behavior with clear inputs and outputs | 6 Test-first |
| Big feature, several sessions, or a handoff | 5 Spec, 14 Long-running harness |
| No pointers to files, patterns or constraints | 7 Scoping |
| Third correction in a row, or a session mixing unrelated tasks | 1 Context hygiene, 15 Course correction |
| Several independent tasks bundled into one request | 10 Parallel agents |
| Noisy output (full test runs, wide searches) or a need for unbiased review | 9 Subagents, 13 Independent review |
| The same prompt typed again, or an "ALWAYS/NEVER" rule | 11 Skills, commands & hooks |
| Wants to connect many tools "just in case" | 12 Tool hygiene |
| Unattended or autonomous run, external content, secrets nearby | 16 Safety, 14 Harness |
| "It seems better" with no measurement | 17 Evals |

## Techniques

### 1. Context hygiene
`verified: 2026-11-22`
- **What:** keep each session to one coherent task, and reset when it degrades.
- **Use when:** switching to an unrelated task (`/clear`). After two failed corrections, clear the session and write one better prompt instead of a third correction. Compact at milestones with a focus (`/compact <focus>`). In Codex, use one chat per outcome and fork only when the work really branches. In Cursor, start fresh when the agent repeats mistakes.
- **Overkill:** budgeting tokens aggressively. Large windows plus automatic compaction make running out rare. Reset for focus and cost, not out of fear.
- **Why it works:** recall degrades as context grows ("context rot", a finite attention budget). Failed attempts stay in the history and get re-read on every turn, and every turn re-sends the history, which costs money.
- **Redo skeleton:** `/clear` → "Fix ___ in ___ without changing ___. The last attempt did ___; don't. Done = ___."
- **Sources:** [A1] [A4] [O1] [C1] [G1]

### 2. Lean repo instruction files (AGENTS.md / CLAUDE.md / GEMINI.md)
`verified: 2026-11-22`
- **What:** record only what the agent can't discover by reading the repo:
  - exact test, typecheck and lint commands, including how to run a single test
  - code that is misleading
  - decisions made outside the repo
  - anything you've had to correct twice
- **Use when:** setting up a repo for agents, or after the agent makes the same mistake twice. Ask it for a retrospective and add the lesson.
- **Overkill:** prose about architecture, style guides (use a linter), rare edge cases. Keep the file short: Claude recommends under 200 lines. OpenAI's harness team uses about 100 lines as a table of contents pointing into docs/. *Labs disagree on layout:* Codex lists important directories as useful content, while Anthropic says to leave layout out. The middle ground is a short map with pointers.
- **Why it works:** the file is loaded into every session, so each line costs attention. "Too much guidance becomes non-guidance," and a long file goes stale.
- **Redo skeleton:** "Commands: test `___`, one test `___`, typecheck `___`. Gotchas: ___ (looks like ___, but actually ___)."
- **Sources:** [A1] [A2] [O1] [O4] [O5] [H1] [G1]

### 3. Give the agent a way to verify its work
`verified: 2026-11-22`
- **What:** a pass/fail check the agent runs and reads itself. Examples: tests, build exit code, types, lint, a diff against a fixture, a screenshot compared with the mockup, driving the browser like a user.
- **Use when:** almost always. All five vendors rank this first.
- **Overkill:** exploratory questions ("what would you improve?").
- **Why it works:** agents stop when the work *looks* done, and a check lets them close the loop themselves. Ask for evidence (the command and its output) rather than a claim like "tests pass".
- **Escalation, weakest to strongest:**
  1. Ask for the check in the prompt.
  2. A goal mode (`/goal` in Claude Code and Codex), where a checker re-evaluates the condition after every turn.
  3. A Stop hook that blocks finishing until the check passes.
  4. A fresh reviewer (13).
  - For UIs, use browser automation (Copilot ships the Playwright MCP server; OpenAI exposes DevTools, logs and metrics per worktree).
- **Redo skeleton:** "___. Done when `___` passes, ___ is clean, and you've shown me ___ (command and output, or a screenshot)."
- **Sources:** [A1] [A6] [O1] [O2] [O5] [G1] [C1] [H1]

### 4. Explore → plan → implement → verify (plan mode)
`verified: 2026-11-22`
- **What:** read-only research and a plan you can review, before any edits. Where to find it:
  - Claude Code: Shift+Tab or `/plan`
  - Codex: `/plan`
  - Cursor: Shift+Tab (plans are saved to `.cursor/plans/`)
  - Antigravity: Planning mode, which produces an implementation-plan artifact
  - Copilot: research → plan → iterate on a branch
- **Use when:** multi-file changes, ambiguous requests, unfamiliar code, several valid approaches.
- **Overkill:** one-line diffs and routine tasks. Anthropic notes that a plain first prompt in a fresh session already does the right thing in most cases. Plan mode is a tool, not a ritual.
- **Why it works:** a plan is cheap to fix. When the output misses, revert and refine the plan rather than patching with follow-ups. Keep plans at the level of the product and its deliverables: wrong granular detail cascades.
- **Redo skeleton:** "Explore how ___ works (read only). Write a plan to ___, covering files touched, risks and how we'll verify. Don't edit until I approve."
- **Sources:** [A1] [A7] [C1] [C2] [G1] [G2] [H1]

### 5. Spec-driven development
`verified: 2026-11-22`
- **What:** a durable spec, then a plan, tasks, implementation and convergence. Examples are GitHub Spec Kit's `/speckit-*` steps and Codex ExecPlans (a living PLANS.md with Progress and Decision Log sections).
- **Use when:** greenfield features, work spanning several sessions or agents, handoffs, unattended runs.
- **Overkill:** bug fixes and small changes. Spec Kit phases are "independent entry points, not mandatory phases". Cursor warns that frozen specs age badly and prefers a living plan.
- **Why it works:** one artifact defines "done" for the builder, the reviewer and the next session, so any session can restart from the file alone.
- **Redo skeleton:** "Interview me until you could write SPEC.md (goal, users, requirements, non-goals, acceptance tests), then stop." Then, in a fresh session: "Implement SPEC.md; every requirement gets a test."
- **Sources:** [H2] [O6] [C2] [A1]

### 6. Test-first with agents
`verified: 2026-11-22`
- **What:** red/green TDD. Write the tests, confirm they fail, commit them, then implement without editing the tests.
- **Use when:** clear inputs and outputs, reproducing a bug, refactors.
- **Overkill:** spikes and visual design. Use screenshots or an evaluator instead.
- **Why it works:**
  - A test seen failing first proves it exercises the new code, and test-first guards against unneeded code.
  - Saying explicitly that you're doing TDD stops the agent from writing mock implementations.
  - Forbidding edits to the tests stops the agent from "passing" by weakening them.
- **Redo skeleton:** "Users report ___ when ___. Look at ___. Write a failing test that reproduces it, run it to show it fails, then fix it. Don't modify the test."
- **Sources:** [A1] [A6] [C1] [P1]

### 7. Scope the task: goal, context, constraints, done-when
`verified: 2026-11-22`
- **What:** state the **Goal**, **Context** (files and patterns to follow), **Constraints** and **Done when**. Describe the result, not the steps. An issue assigned to a cloud agent *is* the prompt: write it as problem + acceptance criteria + files.
- **Use when:** every non-trivial request.
- **Overkill:** spelling out steps that frontier models already know. Prescriptive micro-instructions can hurt. Decompose less than you used to.
- **Why it works:**
  - Pointing at an existing pattern beats describing one.
  - Constraints work better than checklists: "No TODOs, no partial implementations" beats "remember to finish".
  - Signal scope upward too ("be ambitious: empty and error states, keyboard nav"), with numbers where possible.
- **Redo skeleton:** "Goal: ___. Follow the pattern in ___. Constraints: ___ (no new libraries? don't touch ___?). Done when: ___."
- **Sources:** [A1] [A7] [O1] [O3] [C3] [H1]

### 8. Have the agent interview you
`verified: 2026-11-22`
- **What:** before building, the agent asks you questions, multiple-choice where possible, until it can write a goal with measurable success criteria.
- **Use when:** fuzzy requirements, or decisions you haven't made yet.
- **Overkill:** well-specified tasks.
- **Why it works:** it brings out the decisions you haven't pinned down, and you supply what the agent can't read from the code. Plan modes increasingly ask questions on their own.
- **Redo skeleton:** "I haven't decided ___. Interview me (multiple choice where possible) until you can write a goal with measurable success criteria. No code yet."
- **Sources:** [A1] [O1] [O2] [C2] [G4]

### 9. Subagents for isolation, not for a better answer
`verified: 2026-11-22`
- **What:** delegate bounded jobs to a subagent with its own context:
  - independent parallel work
  - noisy output (full test runs, wide searches) that you want summarized
  - unbiased review
  - restricted roles, such as a read-only reviewer
- **Overkill:** handing off the same task for a "better answer". It's the same model, it gathers the context again, and it multiplies tokens.
- **Why it works:** it keeps the main thread's context clean, and summaries come back instead of raw logs. Use a cheaper model for simple jobs, and check spend with `/usage`.
- **Redo skeleton:** "In a subagent, ___ and return only ___ (e.g., failing test names and the first error line of each)."
- **Sources:** [A1] [O1] [O3]

### 10. Parallel agents: worktrees, background and cloud agents
`verified: 2026-11-22`
- **What:** one checkout per agent.
  - Local: `claude -w`, Codex worktrees, Cursor's automatic worktrees, Antigravity subagents with a `branch` workspace.
  - Cloud: Claude cloud sessions, Codex Cloud, Cursor cloud agents, the Copilot cloud agent, Antigravity remote agents.
- **Use when:**
  - independent tasks
  - best-of-N (the same prompt across several models, then pick the best result)
  - backlog chores sent to cloud agents that return PRs
  - one large mechanical change split into units after you approve a plan (Claude `/batch`)
- **Overkill and anti-patterns:**
  - two agents editing the same files without worktrees
  - one giant shared task: in a parallel C-compiler build, all agents hit the same bug and overwrote each other's fixes
- **Why it works:** isolated checkouts stop agents from colliding. Copy local-only files into each worktree with `.worktreeinclude`, and preinstall dependencies for cloud agents.
- **Redo skeleton:** "Split into independent tasks: (1) ___ (2) ___ (3) ___. Run each in its own worktree or cloud task; each one opens a PR with its own verification."
- **Sources:** [A1] [A3] [A12] [O1] [O2] [C1] [G2] [H1]

### 11. Skills, commands and hooks: advisory vs deterministic
`verified: 2026-11-22`
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
- **Redo skeleton:** "Turn ___ into a skill named ___ (when to use it: ___; steps: ___)", or "Add a hook on ___ that runs `___` and blocks if it fails."
- **Sources:** [A1] [O1]

### 12. Tool hygiene: CLI first, few tools, good tool design
`verified: 2026-11-22`
- **What:**
  - Using tools: prefer a CLI (`gh`, or point the agent at `--help`), and use MCP for systems without one. Add tools only when they unlock a real workflow; start with one or two, and turn off unused servers.
  - Building tools: a few consolidated, high-impact tools, namespaced names, meaningful token-efficient responses, actionable errors, and evaluation with agents running realistic tasks.
- **Overkill:** connecting a dozen servers "just in case". Idle tool definitions still cost context.
- **Why it works:** fewer, clearer tools mean less context spent and fewer wrong calls. Lint errors that carry remediation text teach the agent while it works.
- **Redo skeleton:** "For this task use `___` (CLI) and enable only ___. Disable ___."
- **Sources:** [A1] [A5] [A13] [O1] [O5]

### 13. Independent review
`verified: 2026-11-22`
- **What:** a reviewer that never saw the author's reasoning. Options:
  - a fresh subagent or session (`/code-review`)
  - Codex `/review` or automatic PR review
  - Cursor Bugbot
  - agent-to-agent review loops
- **Use when:** before merging anything non-trivial. Make the review check against the spec or acceptance criteria.
- **Overkill:** an evaluator pays off mainly when the task is at the edge of what the model can do. Always say "skip style": a reviewer asked to find problems always finds some, and fixing all of them adds needless abstraction. You still review the code yourself before asking colleagues to.
- **Why it works:** agents grade their own work generously. A separate, skeptical evaluator is far easier to tune.
- **Redo skeleton:** "In a fresh subagent, review the ___ diff against ___ (spec or criteria). Check every requirement is implemented and the edge cases ___ have tests. Report only gaps that affect correctness; skip style."
- **Sources:** [A1] [A7] [O1] [O5] [C1] [P1]

### 14. Long-running agent harnesses
`verified: 2026-11-22`
- **What:** state kept outside the context window, so a long run survives across sessions:
  - a JSON feature list where everything starts as "failing"
  - a progress file
  - an init or smoke-test script
  - one commit per feature
  - every session starts by reading progress and the git log
  - Variants: planner, generator and evaluator agents; ExecPlans; `/goal`; Stop-hook loops with iteration caps.
- **Use when:** multi-hour or unattended work. Before you leave it running, have:
  1. a definition of done
  2. a check the agent runs itself
  3. a limited access scope
  4. a stop condition (max turns or budget)
  5. a known destination for the result and a person who signs off
  - Try it on 3 items before the rest.
- **Overkill:** heavy scaffolding on current models. "Every component in a harness encodes an assumption about what the model can't do." Strip parts as models improve.
- **Why it works:** state outside the context survives compaction and new sessions, and commits make every step reversible.
- **Redo skeleton:** "/goal ___ (measurable). Keep ___/progress.md updated, commit per ___, stop after ___ turns or $___, and report to ___."
- **Sources:** [A1] [A6] [A7] [A12] [O2] [O6] [C1]

### 15. Course correction
`verified: 2026-11-22`
- **What:** watch the first minute and stop drift early.
  - Claude Code: `Esc` stops and keeps the work; `/rewind` restores code and/or conversation (but not files that Bash commands changed).
  - Codex: Enter steers the current turn, Tab queues a message, `/fork` branches.
  - Antigravity: `Esc`, `/rewind`, `/fork`.
  - Cursor: revert, refine the plan, rerun.
  - If you revert the agent's edit yourself, tell it.
- **Use when:** the agent drifts from the plan or repeats a mistake. After two failed corrections, rewind or clear instead.
- **Why it works:** fixing early is cheap, and a long trail of corrections pollutes the context.
- **Redo skeleton:** "`/rewind` to before ___; keep ___ unchanged; this time ___."
- **Sources:** [A1] [O1] [O3] [G1] [C1]

### 16. Safety: contain the agent rather than approving every action
`verified: 2026-11-22`
- **What:** sandbox with both filesystem *and* network isolation, deny rules that hold in every mode, credentials kept out of the agent's reach, and pushes allowed only to PR branches with `main` protected.
- **Use when:** autonomous modes, untrusted repos or content, anything near secrets.
- **Why it works:**
  - People approve almost all permission prompts, so approvals stop being a real check.
  - Auto modes are classifiers, not guarantees, so "never" rules belong in deny rules or hooks.
  - Prompt injection arrives through READMEs, issues and web pages. Avoid the "lethal trifecta" of private data + untrusted content + an exfiltration channel by cutting one leg.
  - Repo-local agent config is untrusted until you accept the folder.
  - Codex: start with tight sandbox and approval settings and loosen them only for trusted repos.
- **Redo skeleton:** "Run this in ___ (sandbox, devcontainer or cloud) with network limited to ___, deny reads of ___, and only allow pushes to a PR branch."
- **Sources:** [A1] [A9] [A10] [A14] [O1] [G1] [P2]

### 17. Measure: evals for prompts, skills and agent workflows
`verified: 2026-11-22`
- **What:**
  - Start with 20–50 tasks taken from real failures, with unambiguous success criteria and reference solutions.
  - Grade outcomes, not the order of tool calls, and read the transcripts.
  - Track pass@k (any success in k tries) versus pass^k (all k succeed).
  - Capability evals graduate into a regression suite. Re-check your setup on every new model.
- **Use when:** changing a prompt, skill, instruction file or harness, or choosing between models or approaches.
- **Overkill:** one-off tasks. For individuals, a 3-item trial and `/usage` are often enough.
- **Why it works:** "it seems better" is noise. Agents are non-deterministic, so judge on several runs and on transcripts.
- **Redo skeleton:** "Run ___ on ___ (N real examples), grade against ___ with this rubric: ___. Report the pass rate and the 3 worst transcripts."
- **Sources:** [A1] [A7] [A8] [O5]

## Retired or demoted (and why)

- **ALL-CAPS "IMPORTANT/ALWAYS/NEVER" in instructions.** Current models over-apply emphasized rules. Use a hook or deny rule, or shorten the file. [A1]
- **"Think hard", "be thorough".** Reasoning effort is a setting now (`/effort` in Claude Code, reasoning effort in Codex, `/boost` in Antigravity). [A1] [O3]
- **"Keep going, don't be lazy."** It causes over-work. Use a goal mode or a Stop hook with a check. [A1] [O2]
- **Treating context size as the main constraint.** Reset for focus and cost instead. [A1]
- **Subagents to "save context" or get a better answer.** Use them for parallel work, noisy output, review and tool restriction. [A1]
- **Prescriptive "how to" rules for frontier models.** Say what something is for, not how to do it. [A11] [C3]
- **Per-action approval prompts as the main safety layer.** Containment comes first. [A1] [A9]
- **Codex custom prompts.** Replaced by skills. [O1]
- **Gemini CLI for consumers.** Replaced by Antigravity CLI (`agy`); extensions became plugins. [G3]
- **Fixing bad output with follow-up prompts.** Revert and re-plan. [C1] [C2]
- **Frozen upfront specs.** Use living plans; spec phases are optional. [C2] [H2]

## Sources

| Key | Source |
|---|---|
| A1 | Claude Code best practices: https://code.claude.com/docs/en/best-practices |
| A2 | CLAUDE.md, AGENTS.md & memory: https://code.claude.com/docs/en/memory |
| A3 | Run agents in parallel: https://code.claude.com/docs/en/agents |
| A4 | Effective context engineering for AI agents (2025-09-29): https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents |
| A5 | Writing effective tools for agents (2025-09-11): https://www.anthropic.com/engineering/writing-tools-for-agents |
| A6 | Effective harnesses for long-running agents (2025-11-26): https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents |
| A7 | Harness design for long-running apps (2026-03-24): https://www.anthropic.com/engineering/harness-design-long-running-apps |
| A8 | Demystifying evals for AI agents (2026-01-09): https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents |
| A9 | How we contain Claude across products (2026-05-25): https://www.anthropic.com/engineering/how-we-contain-claude |
| A10 | How we built Claude Code auto mode (2026-03-25): https://www.anthropic.com/engineering/claude-code-auto-mode |
| A11 | The components of agent memory (2026-11-06): https://www.anthropic.com/engineering/components-of-agent-memory |
| A12 | Building a C compiler with parallel Claudes (2026-02-05): https://www.anthropic.com/engineering/building-c-compiler |
| A13 | Code execution with MCP (2025-11-04): https://www.anthropic.com/engineering/code-execution-with-mcp |
| A14 | Claude Code sandboxing (2025-10-20): https://www.anthropic.com/engineering/claude-code-sandboxing |
| O1 | Codex best practices: https://learn.chatgpt.com/guides/best-practices |
| O2 | Codex long-running work & `/goal`: https://learn.chatgpt.com/docs/long-running-work |
| O3 | Codex prompting: https://learn.chatgpt.com/docs/prompting |
| O4 | AGENTS.md in Codex: https://learn.chatgpt.com/docs/agent-configuration/agents-md |
| O5 | Harness engineering (2026-02-11): https://openai.com/index/harness-engineering/ |
| O6 | ExecPlans / PLANS.md (2025-10-07): https://developers.openai.com/cookbook/articles/codex_exec_plans |
| G1 | Antigravity CLI best practices: https://antigravity.google/docs/cli/best-practices |
| G2 | Antigravity artifact review & subagents: https://antigravity.google/docs/artifact-review, https://antigravity.google/docs/subagents |
| G3 | Gemini CLI → Antigravity CLI (2026-05-19): https://developers.googleblog.com/an-important-update-transitioning-gemini-cli-to-antigravity-cli/ |
| G4 | Plan mode in Gemini CLI (2026-03-11): https://developers.googleblog.com/plan-mode-now-available-in-gemini-cli/ |
| C1 | Cursor: best practices for coding with agents (2026-01-09): https://cursor.com/blog/agent-best-practices |
| C2 | Cursor: dynamic planning agents (2026-01-30): https://cursor.com/blog/dynamic-planning-agents |
| C3 | Cursor: towards self-driving codebases (2026-02-05): https://cursor.com/blog/self-driving-codebases |
| H1 | GitHub Copilot cloud agent best practices: https://docs.github.com/en/copilot/tutorials/cloud-agent/get-the-best-results |
| H2 | GitHub Spec Kit: https://github.com/github/spec-kit |
| P1 | Practitioner — Simon Willison, Agentic Engineering Patterns: https://simonwillison.net/guides/agentic-engineering-patterns/ |
| P2 | Practitioner — Simon Willison, The lethal trifecta (2025-06-16): https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/ |
