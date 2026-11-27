---
name: coach
description: Switch agent-coach between force, suggest and off, or show its status. Use only when the user asks to change or check the coach mode.
argument-hint: "force | suggest | off | status | audit | reminder on|off"
disable-model-invocation: true
---

Arguments: $ARGUMENTS

The agent-coach hook normally handles mode commands before they reach you, so you're reading this because no hook ran, or for an audit.

- If my message or the Arguments line names `force`, `suggest` or `off`, follow that agent-coach mode for the rest of this session. If a `coach` command is available in the shell, also run `coach <mode>` so the change persists. Confirm in one line.
- If it names `reminder on` or `reminder off`, run `coach reminder <on|off>` if a `coach` command is available in the shell, and report its output. Otherwise tell me to run it in a terminal.
- If it names `audit`, follow the `coach-audit` skill (`../coach-audit/SKILL.md` from this skill's folder), passing on any other arguments.
- Otherwise, tell me the current mode in one line. If the `coach` command is available, run it and report its output.
