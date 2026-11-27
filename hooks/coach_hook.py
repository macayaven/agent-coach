#!/usr/bin/env python3
"""agent-coach hook: inject the coaching rules at session start and a mode reminder on
every prompt, handle `coach force|suggest|off|status` without a model call, and point
`coach audit` at the coach-audit skill.

Usage: coach_hook.py <tool> <event>   (reads the hook's JSON input on stdin)
  tool:  claude | codex | gemini | cursor
  event: session-start | prompt
"""

import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import adapters  # noqa: E402
import coachlib  # noqa: E402


def claude_style(prompt_event):
    """Claude Code and Codex share this shape; Gemini CLI differs only in names."""
    block_word = "deny" if prompt_event == "BeforeAgent" else "block"

    def fmt(event, context=None, block_reason=None):
        if block_reason:
            return {"decision": block_word, "reason": block_reason}
        name = {"session-start": "SessionStart", "prompt": prompt_event}[event]
        return {"hookSpecificOutput": {"hookEventName": name, "additionalContext": context}}

    return fmt


def cursor(event, context=None, block_reason=None):
    if event == "session-start":
        return {"additional_context": context} if context else {}
    if block_reason:
        return {"continue": False, "user_message": block_reason}
    return {"continue": True}  # beforeSubmitPrompt can't add context


FORMATTERS = {
    "claude": claude_style("UserPromptSubmit"),
    "codex": claude_style("UserPromptSubmit"),
    "gemini": claude_style("BeforeAgent"),
    "cursor": cursor,
}
# Tools whose hooks can't add context to each prompt: let a mode switch through to
# the model so this session hears about it, instead of blocking it.
PASS_SWITCH_THROUGH = {"cursor"}


def refresh_static_files():
    """Re-render the instruction files other tools read, from the checkout that installed them."""
    repo = Path(adapters.load_installed().get("repo", ""))
    try:
        if repo == coachlib.REPO:
            adapters.refresh()
        elif (repo / "bin" / "coach").exists():
            subprocess.run([sys.executable, str(repo / "bin" / "coach"), "refresh"], timeout=10, capture_output=True)
    except Exception:  # never let bookkeeping break the user's prompt
        pass


def handle(tool, event, payload):
    """Return the JSON to print, or None to add nothing."""
    fmt = FORMATTERS[tool]
    mode = coachlib.get_mode()
    if event == "prompt":
        if coachlib.is_audit_request(payload.get("prompt", "")):
            # In any mode, on this prompt only. Cursor can't add context to a prompt.
            return fmt(event) if tool in PASS_SWITCH_THROUGH else fmt(event, context=coachlib.audit_pointer())
        command = coachlib.parse_toggle(payload.get("prompt", ""))
        if command == "status":
            return fmt(event, block_reason=coachlib.status_line())
        if command:
            coachlib.set_mode(command)
            refresh_static_files()
            if tool in PASS_SWITCH_THROUGH:
                return fmt(event)
            return fmt(event, block_reason=f"agent-coach: mode is now {command} (all tools).")
        if mode == "off":
            return fmt(event) if tool in PASS_SWITCH_THROUGH else None
        return fmt(event, context=coachlib.REMINDERS[mode])
    return fmt(event, context=coachlib.render(mode)) if mode != "off" else None


def main():
    tool, event = sys.argv[1], sys.argv[2]
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        payload = {}
    out = handle(tool, event, payload)
    print(json.dumps(out if out is not None else {}))


if __name__ == "__main__":
    main()
