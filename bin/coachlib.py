"""Shared logic for the agent-coach CLI and hooks. Standard library only."""

import datetime
import os
import re
from pathlib import Path

MODES = ("force", "suggest", "off")
DEFAULT_MODE = "force"
STALE_AFTER_DAYS = 60

REPO = Path(__file__).resolve().parent.parent
RULES = REPO / "skills" / "agent-coach" / "SKILL.md"
PLAYBOOK = REPO / "skills" / "agent-coach" / "references" / "playbook.md"

# "coach off", "/coach suggest", "/agent-coach:coach force", "coach status"
TOGGLE_RE = re.compile(
    r"^\s*/?(?:agent-coach:)?coach\s+(force|suggest|off|on|status)\s*$", re.IGNORECASE
)

REMINDERS = {
    "force": (
        "[agent-coach · force] Before acting on this request, apply the force loop: "
        "diagnose it against the playbook, name 1-3 techniques, and ask me to redo it "
        "using a skeleton. Don't execute yet. Exempt: pure questions, tiny edits, "
        "`coach skip`, `urgent`. If this message is my redo of an earlier request, "
        "grade it briefly, then execute it."
    ),
    "suggest": (
        "[agent-coach · suggest] Do the request as asked, then add a Coach note of at "
        "most 5 lines: 1-2 techniques and a reusable rewrite of my request. Skip the "
        "note if nothing meaningful applies."
    ),
}


def state_dir() -> Path:
    return Path(os.environ.get("AGENT_COACH_STATE") or Path.home() / ".agent-coach" / "state")


def get_mode() -> str:
    # EVAL_ prefix: the only variables `claude plugin eval` passes to a run.
    env = os.environ.get("AGENT_COACH_MODE") or os.environ.get("EVAL_AGENT_COACH_MODE")
    if env in MODES:
        return env
    try:
        saved = (state_dir() / "mode").read_text().strip()
    except OSError:
        return DEFAULT_MODE
    return saved if saved in MODES else DEFAULT_MODE


def set_mode(mode: str) -> str:
    mode = "force" if mode == "on" else mode
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}; expected one of {', '.join(MODES)}")
    state_dir().mkdir(parents=True, exist_ok=True)
    (state_dir() / "mode").write_text(mode + "\n")
    return mode


def parse_toggle(prompt: str):
    """Return 'force' | 'suggest' | 'off' | 'status' if the prompt is a coach command."""
    m = TOGGLE_RE.match(prompt or "")
    if not m:
        return None
    word = m.group(1).lower()
    return "force" if word == "on" else word


def playbook_reviewed(playbook: Path = PLAYBOOK):
    try:
        head = playbook.read_text(encoding="utf-8")[:500]
    except OSError:
        return None
    m = re.search(r"^reviewed:\s*(\d{4}-\d{2}-\d{2})", head, re.MULTILINE)
    return datetime.date.fromisoformat(m.group(1)) if m else None


def is_stale(reviewed, today=None) -> bool:
    if reviewed is None:
        return True
    today = today or datetime.date.today()
    return (today - reviewed).days > STALE_AFTER_DAYS


def rules_body() -> str:
    """The coaching rules: the agent-coach skill without its frontmatter."""
    text = RULES.read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    return text.strip()


def render(mode: str, playbook_path: Path = PLAYBOOK) -> str:
    """The always-on instructions: a header with the mode and playbook path, then the rules."""
    reviewed = playbook_reviewed(playbook_path)
    header = (
        f"Agent Coach is active. Current mode: {mode}. "
        f"Playbook: `{playbook_path}` (reviewed {reviewed.isoformat() if reviewed else 'unknown'})."
    )
    if is_stale(reviewed):
        header += (
            f" The playbook is more than {STALE_AFTER_DAYS} days old: tell me once this session "
            "to run `coach update`, and take extra care to flag practices that may have changed."
        )
    return header + "\n\n" + rules_body() + "\n"


def render_off_stub() -> str:
    """What static instruction files carry while the coach is off: just enough to turn it back on."""
    return (
        "Agent Coach is installed but off: no coaching. If I say `coach force` or "
        f"`coach suggest`, read `{RULES}` and follow it in that mode for the rest of this "
        "session. If you can run shell commands, also run `coach <mode>` to persist it.\n"
    )


def status_line() -> str:
    reviewed = playbook_reviewed()
    age = "unknown"
    if reviewed:
        age = f"{reviewed.isoformat()} ({(datetime.date.today() - reviewed).days} days ago)"
    note = " — stale, run `coach update`" if is_stale(reviewed) else ""
    return f"agent-coach mode: {get_mode()} · playbook reviewed {age}{note}"
