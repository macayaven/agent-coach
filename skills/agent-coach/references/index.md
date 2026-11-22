---
reviewed: 2026-11-22
---

# Technique index

Match my request to the entries whose "When" fits, pick the one to three with the most leverage, and hand me their "Redo" skeleton, adapted to the request. For the rationale and sources of an entry, read `techniques/<name>.md` (only when I ask `why` or `explain`).

- `01-context-hygiene` — When: third correction in a row, or one session mixing unrelated tasks. Redo: `/clear` → "Fix ___ in ___ without changing ___. The last attempt did ___; don't. Done = ___."
- `02-instruction-files` — When: the agent repeats a mistake across sessions, or the repo has no (or a bloated) instruction file. Redo: "Commands: test `___`, one test `___`, typecheck `___`. Gotchas: ___ (looks like ___, but actually ___)."
- `03-verification` — When: no way to tell when the work is done or correct. Redo: "___. Done when `___` passes, ___ is clean, and you've shown me ___ (command and output, or a screenshot)."
- `04-plan-first` — When: multi-file change, unfamiliar code, or several valid approaches. Redo: "Explore how ___ works (read only). Write a plan to ___, covering files touched, risks and how we'll verify. Don't edit until I approve."
- `05-spec-driven` — When: big feature, work spanning sessions, or a handoff. Redo: "Interview me until you could write SPEC.md (goal, users, requirements, non-goals, acceptance tests), then stop." Then, in a fresh session: "Implement SPEC.md; every requirement gets a test."
- `06-test-first` — When: a bug fix or behavior with clear inputs and outputs. Redo: "Users report ___ when ___. Look at ___. Write a failing test that reproduces it, run it to show it fails, then fix it. Don't modify the test."
- `07-scoping` — When: no pointers to files, patterns, constraints or a finish line. Redo: "Goal: ___. Follow the pattern in ___. Constraints: ___ (no new libraries? don't touch ___?). Done when: ___."
- `08-interview` — When: vague goal, or I haven't decided the scope. Redo: "I haven't decided ___. Interview me (multiple choice where possible) until you can write a goal with measurable success criteria. No code yet."
- `09-subagents` — When: noisy output (full test runs, wide searches) that would flood the main thread. Redo: "In a subagent, ___ and return only ___ (e.g., failing test names and the first error line of each)."
- `10-parallel-agents` — When: several independent tasks bundled into one request. Redo: "Split into independent tasks: (1) ___ (2) ___ (3) ___. Run each in its own worktree or cloud task; each one opens a PR with its own verification."
- `11-skills-hooks` — When: the same prompt typed again, or an ALWAYS/NEVER rule. Redo: "Turn ___ into a skill named ___ (when to use it: ___; steps: ___)", or "Add a hook on ___ that runs `___` and blocks if it fails."
- `12-tool-hygiene` — When: connecting many tools "just in case". Redo: "For this task use `___` (CLI) and enable only ___. Disable ___."
- `13-independent-review` — When: about to merge something non-trivial. Redo: "In a fresh subagent, review the ___ diff against ___ (spec or criteria). Check every requirement is implemented and the edge cases ___ have tests. Report only gaps that affect correctness; skip style."
- `14-long-running` — When: multi-hour or unattended run. Redo: "/goal ___ (measurable). Keep ___/progress.md updated, commit per ___, stop after ___ turns or $___, and report to ___."
- `15-course-correction` — When: the agent is drifting from the plan mid-task. Redo: "`/rewind` to before ___; keep ___ unchanged; this time ___."
- `16-safety` — When: autonomous mode, untrusted content, or secrets nearby. Redo: "Run this in ___ (sandbox, devcontainer or cloud) with network limited to ___, deny reads of ___, and only allow pushes to a PR branch."
- `17-evals` — When: "it seems better" with no measurement. Redo: "Run ___ on ___ (N real examples), grade against ___ with this rubric: ___. Report the pass rate and the 3 worst transcripts."

## Outdated: don't recommend

Reasons and sources are in `retired.md`.

- ALL-CAPS "IMPORTANT/ALWAYS/NEVER" in instructions → a hook, a deny rule or a shorter file
- "think hard", "be thorough" → the tool's reasoning-effort setting
- "keep going, don't be lazy" → a goal mode or a Stop hook with a check
- Subagents to save context or get a better answer → use them for parallel work, noisy output and review
- Step-by-step "how to" rules for frontier models → say what it's for
- Per-action approval prompts as the main safety layer → sandbox and deny rules
- Patching bad output with follow-up prompts → revert and re-plan
- Frozen upfront specs → living plans
