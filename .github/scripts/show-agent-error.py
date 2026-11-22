#!/usr/bin/env python3
"""Print why the Claude step failed, from the output file the action saves.

The action keeps the agent's output out of the log, so a failed refresh would
otherwise say only "is_error: true". Usage: show-agent-error.py <output-file>
"""

import json
import sys
from pathlib import Path

HINTS = [
    ("credit balance", "The API account has no credit. Add credit in the Claude Console under Billing, then rerun."),
    ("invalid api key", "The API rejected the key. Put a valid Claude API key (it starts with sk-ant-api) in the ANTHROPIC_API_KEY secret."),
    ("401", "The API rejected the key. Put a valid Claude API key (it starts with sk-ant-api) in the ANTHROPIC_API_KEY secret."),
    ("403", "The key isn't allowed to do this. Check the key's workspace and its model access."),
    ("429", "A rate limit or the key's spend limit was reached. Raise the limit or rerun later."),
    ("529", "The API was overloaded. Rerun later."),
    ("max turns", "The agent ran out of turns. Raise --max-turns in the workflow."),
]


def load(path):
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(text)
        return data if isinstance(data, list) else [data]
    except ValueError:
        messages = []
        for line in text.splitlines():
            try:
                messages.append(json.loads(line))
            except ValueError:
                pass
        return messages


def main(path):
    try:
        results = [m for m in load(path) if isinstance(m, dict) and m.get("type") == "result"]
    except OSError:
        print("The agent left no output file, so it failed before it started. Check the step's log above.")
        return
    if not results:
        print("The agent's output has no final result, so it stopped early. Check the step's log above.")
        return
    last = results[-1]
    status = last.get("api_error_status")
    reason = str(last.get("result") or last.get("subtype") or "no reason given")[:400]
    print(f"Agent result: {reason}")
    if status:
        print(f"API status: {status}")
    haystack = f"{reason} {status or ''}".lower()
    for needle, hint in HINTS:
        if needle in haystack:
            print(f"Likely fix: {hint}")
            break


if __name__ == "__main__":
    main(sys.argv[1])
