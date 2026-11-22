"""Shared logic for the agent-coach CLI and hooks. Standard library only."""

import datetime
import os
import re
from pathlib import Path

MODES = ("force", "suggest", "off")
DEFAULT_MODE = "force"
STALE_AFTER_DAYS = 60

REPO = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO / "skills" / "agent-coach"
RULES = SKILL_DIR / "SKILL.md"
INDEX = SKILL_DIR / "references" / "index.md"
TECHNIQUES = SKILL_DIR / "references" / "techniques"

# "coach off", "/coach suggest", "/agent-coach:coach force", "coach status"
TOGGLE_RE = re.compile(
    r"^\s*/?(?:agent-coach:)?coach\s+(force|suggest|off|on|status)\s*$", re.IGNORECASE
)

# Added to every prompt by hooks, so keep these to one short line: the rules
# themselves are already in context from session start.
REMINDERS = {
    "force": "[agent-coach: force] Coach before acting, unless this is exempt or my redo.",
    "suggest": "[agent-coach: suggest] Do it, then end with the Coach note.",
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


def techniques_reviewed(index: Path = INDEX):
    try:
        head = index.read_text(encoding="utf-8")[:500]
    except OSError:
        return None
    m = re.search(r"^reviewed:\s*(\d{4}-\d{2}-\d{2})", head, re.MULTILINE)
    return datetime.date.fromisoformat(m.group(1)) if m else None


def is_stale(reviewed, today=None) -> bool:
    if reviewed is None:
        return True
    today = today or datetime.date.today()
    return (today - reviewed).days > STALE_AFTER_DAYS


def rules_sections() -> dict:
    """The agent-coach skill's `## ` sections, keyed by heading."""
    text = RULES.read_text(encoding="utf-8")
    if text.startswith("---"):
        text = text.split("---", 2)[2]
    parts = re.split(r"^## (.+)$", text, flags=re.MULTILINE)
    return {parts[i].strip(): parts[i + 1].strip() for i in range(1, len(parts), 2)}


def render(mode: str) -> str:
    """The always-on instructions: only the current mode's rules, to keep context small."""
    sections = rules_sections()
    reviewed = techniques_reviewed()
    header = f"Agent Coach is active in {mode} mode. Its skill folder is `{SKILL_DIR}`."
    if is_stale(reviewed):
        header += (
            f" Its techniques were last reviewed over {STALE_AFTER_DAYS} days ago: tell me once "
            "this session to run `coach update`, and flag practices that may have changed."
        )
    return f"{header}\n\n## {mode}\n\n{sections[mode]}\n\n## Always\n\n{sections['Always']}\n"


def render_off_stub() -> str:
    """What static instruction files carry while the coach is off: just enough to turn it back on."""
    return (
        "Agent Coach is installed but off: no coaching. If I say `coach force` or "
        f"`coach suggest`, read `{RULES}` and follow it in that mode for the rest of this "
        "session. If you can run shell commands, also run `coach <mode>` to persist it.\n"
    )


def estimate_tokens(text: str) -> int:
    """Rough token count (about 4 characters per token). Good enough for budgets."""
    return round(len(text) / 4)


def context_cost() -> dict:
    """Estimated tokens the coach adds to context, by when they are spent."""
    technique_sizes = [estimate_tokens(p.read_text(encoding="utf-8")) for p in TECHNIQUES.glob("*.md")]
    return {
        "every session, force": estimate_tokens(render("force")),
        "every session, suggest": estimate_tokens(render("suggest")),
        "every session, off (instruction-file tools)": estimate_tokens(render_off_stub()),
        "every prompt, force (hook tools)": estimate_tokens(REMINDERS["force"]),
        "every prompt, suggest (hook tools)": estimate_tokens(REMINDERS["suggest"]),
        "once per coached session (technique index)": estimate_tokens(INDEX.read_text(encoding="utf-8")),
        "each `why` (largest technique file)": max(technique_sizes),
    }


def status_line() -> str:
    reviewed = techniques_reviewed()
    age = "unknown"
    if reviewed:
        age = f"{reviewed.isoformat()} ({(datetime.date.today() - reviewed).days} days ago)"
    note = " — stale, run `coach update`" if is_stale(reviewed) else ""
    return f"agent-coach mode: {get_mode()} · techniques reviewed {age}{note}"
