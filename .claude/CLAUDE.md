> Governed by ~/.claude/CLAUDE.md (canon)

# agent-coach

Commands:
- All unit tests: `python3 -m unittest discover -s tests`
- One test: `python3 -m unittest tests.test_audit.RepoTests.test_a4_quiet_without_tests`
- Refresh scripts: `bash tests/test_accept_refresh.sh` and `bash tests/test_run_refresh_agent.sh`
- Plugin manifests: `claude plugin validate .`
- Behavioral evals make real model calls, so ask first: `claude plugin eval . --runs 3 --ablation none` (add `--case 'audit-*' --allow-tools Bash` for the audit cases)

Gotchas:
- An install runs from its checkout, so edits here reach every installed tool at once. Work in a worktree or branch, and try installer changes with `HOME=$(mktemp -d)`.
- Standard library only, Python 3.8 syntax. The hook runs on every prompt, so keep its imports light.
- Tests enforce token budgets for the rules, reminders, index, technique files and skills. Shorten the text rather than raise a budget.
- `skills/agent-coach/references/` is rewritten by the monthly refresh; follow `REFRESH.md` there.
- Where things live and how to check a change: `CONTRIBUTING.md`.
