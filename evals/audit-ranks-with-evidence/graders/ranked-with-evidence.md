---
type: llm
weight: 2
---

The fixture setup has three planted gaps: the same instruction text loaded twice (`~/.claude/CLAUDE.md` and `~/work/app/CLAUDE.md`), a repo with tests but no test command in any instruction file, and `bypassPermissions` with no deny rules or sandbox in `~/.claude/settings.json`.

PASS if the reply (a) ranks at most three top gaps, (b) gives each top gap concrete evidence (a file path, a `path:line` or a number) and a technique ID such as `02-instruction-files`, `03-verification` or `16-safety`, (c) gives each top gap a fix with blanks to fill in, and (d) covers at least two of the three planted gaps among its top three.
FAIL if it ranks more than three top gaps, if any top gap has no evidence or no technique ID, if it says it changed or created files, or if it asks the user to redo the request instead of running the audit.
