# Contributing

Changes reach `main` through pull requests; direct pushes are blocked. Merge only when CI is green.

## Where things live

| To change | Edit |
|---|---|
| How the coach behaves in each mode | `skills/agent-coach/SKILL.md` |
| When a technique applies, or its redo skeleton | `skills/agent-coach/references/index.md` |
| A technique's rationale and sources | `skills/agent-coach/references/techniques/<NN>-<name>.md` |
| What a tool's installer does | `bin/adapters.py` |
| What the hooks send | `hooks/coach_hook.py` and `bin/coachlib.py` |
| What `coach audit` reads and the rules it checks | `bin/audit.py` (rules need a sourced threshold; see `docs/specs/coach-audit.md`) |
| How the audit report is ranked and written | `skills/coach-audit/SKILL.md` |

`SKILL.md` is the single source of the rules. The always-on text each tool receives is built from it, so don't copy rules anywhere else.

## Rules for techniques

- Every technique needs at least one official source from an AI lab or tool maker. Practitioner posts can support a technique but not justify one alone.
- A technique has an index line and a file with the same `<NN>-<name>`. The tests check that they match.
- When a practice stops being recommended, move it to `references/retired.md` with the reason and a link.
- The monthly refresh follows [`REFRESH.md`](skills/agent-coach/references/REFRESH.md). Follow it for manual updates too.

## Keep it cheap

The coach is loaded into every session, so size matters. The tests enforce a budget for the always-on rules, the per-prompt reminder, the index and each technique file. If a test fails on size, shorten the text; raise a budget only with a reason in the pull request.

## Check your change

```bash
python3 -m unittest discover -s tests     # logic, installers, budgets
bash tests/test_accept_refresh.sh         # the refresh acceptance script
bash tests/test_run_refresh_agent.sh      # the refresh agent's sign-in handling
claude plugin validate .                  # plugin manifests
claude plugin eval . --runs 3 --ablation none   # behavior; makes real model calls
claude plugin eval . --runs 3 --ablation none --case 'audit-*' --allow-tools Bash   # audit behavior
```

Run the evals when you change `SKILL.md`, the reminders in `bin/coachlib.py`, or `index.md`. A wording change that looks harmless can stop the coach from coaching. Run the `audit-*` cases when you change `skills/coach-audit/SKILL.md` or the audit's JSON. They replay `tests/fixtures/audit-replay.json`; after changing the collector or its fixture, rebuild it with `python3 tests/fixtures/make_replay.py` (a unit test fails until you do).

If a refresh retires or renames a technique that an audit rule points to, `tests/test_audit.py` fails. Remap or retire the rule in `bin/audit.py`; the refresh agent can't edit code, so this keeps a person in the loop.

To try an installer change without touching your real setup, point `HOME` at an empty folder:

```bash
HOME=$(mktemp -d) bin/coach install codex cursor
```
