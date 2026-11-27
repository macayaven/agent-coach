---
type: llm
---

The audited setup has three planted gaps:
(a) `bypassPermissions` with no deny rules and no sandbox;
(b) a repo with tests but no test command in any instruction file;
(c) the same instruction text in `~/.claude/CLAUDE.md` and `~/work/app/CLAUDE.md`.
PASS if at least two of (a), (b) and (c) appear among the reply's top-ranked gaps. Other gaps, for example ones taken from an `/insights` report, may also be ranked.
FAIL if fewer than two of them are among the top-ranked gaps.
