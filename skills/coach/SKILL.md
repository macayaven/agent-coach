---
name: coach
description: Switch agent-coach between force, suggest and off, or show its status. Use only when the user asks to change or check the coach mode.
argument-hint: "force | suggest | off | status"
disable-model-invocation: true
---

Arguments: $ARGUMENTS

The agent-coach hook normally handles this command before it reaches you. You're reading this because no hook ran.

- If my message or the Arguments line names `force`, `suggest` or `off`, follow that agent-coach mode for the rest of this session. If a `coach` command is available in the shell, also run `coach <mode>` so the change persists. Confirm in one line.
- Otherwise, tell me the current mode in one line. If the `coach` command is available, run it and report its output.
