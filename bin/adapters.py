"""Install agent-coach into each coding agent's user-level configuration.

Each tool gets the strongest mechanism it supports, and the coach keeps to files
of its own: it adds hooks, or a rules file that belongs to it, and never writes
its rules into an instruction file you share with other things.
  - Hooks at session start and on every prompt: Claude Code, Codex, Gemini CLI.
  - Hooks at session start: Cursor.
  - A rules file of its own: Antigravity, VS Code Copilot.
Plus the portable Agent Skills (`agent-coach`, `coach`) wherever skills are read.
"""

import json
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

import coachlib

HOME = Path.home()
REPO = coachlib.REPO
SKILL_NAMES = ("agent-coach", "coach")
COPY_MARKER = ".installed-by-agent-coach"
BEGIN = "<!-- agent-coach:begin (managed by `coach`; edits inside this block are overwritten) -->"
END = "<!-- agent-coach:end -->"


def codex_home() -> Path:
    return Path(os.environ.get("CODEX_HOME") or HOME / ".codex")


def launcher_path() -> Path:
    return coachlib.state_dir().parent / "bin" / "coach-hook"


def hook_command(tool: str, event: str) -> str:
    """The command a tool runs for a hook. It goes through a launcher, so the command
    stays the same when Python or the checkout moves."""
    if os.name == "nt":
        return f'"{sys.executable}" "{REPO / "hooks" / "coach_hook.py"}" {tool} {event}'
    return f'"{launcher_path()}" {tool} {event}'


def write_launcher():
    """A small shell script that runs the hook with whichever Python 3 is available."""
    if os.name == "nt":
        return
    hook = REPO / "hooks" / "coach_hook.py"
    script = (
        "#!/bin/sh\n"
        "# Written by `coach install`. Runs the agent-coach hook with whichever Python 3\n"
        "# is available, so the hooks keep working after a Python upgrade.\n"
        f'for py in "{sys.executable}" python3 /opt/homebrew/bin/python3 /usr/local/bin/python3 /usr/bin/python3; do\n'
        '  if command -v "$py" > /dev/null 2>&1; then\n'
        f'    exec "$py" "{hook}" "$@"\n'
        "  fi\n"
        "done\n"
        "# No Python: add nothing, and never hold up the prompt.\n"
        'if [ "$1" = cursor ] && [ "$2" = prompt ]; then echo \'{"continue": true}\'; else echo \'{}\'; fi\n'
    )
    path = launcher_path()
    write_text(path, script, keep_backup=False)
    path.chmod(0o755)


def is_ours(handler) -> bool:
    text = json.dumps(handler)
    return "coach_hook.py" in text or "coach-hook" in text


# --- file helpers -----------------------------------------------------------


def backup_path(path: Path) -> Path:
    return path.with_name(path.name + ".agent-coach.bak")


def write_text(path: Path, new: str, keep_backup: bool = True):
    """Write a file if its content changed. The first change to a file that isn't
    ours keeps a copy of the original beside it."""
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if new == old:
        return
    if keep_backup and path.exists() and not backup_path(path).exists():
        shutil.copy2(path, backup_path(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(new, encoding="utf-8")


def write_block(path: Path, body: str):
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    block = f"{BEGIN}\n{body.rstrip()}\n{END}"
    if BEGIN in text and END in text:
        new = text[: text.index(BEGIN)] + block + text[text.index(END) + len(END) :]
    else:
        new = (text.rstrip() + "\n\n" if text.strip() else "") + block + "\n"
    write_text(path, new)


def remove_block(path: Path):
    """Take our managed block out of a file, putting the file back exactly as it
    was before the coach touched it when the saved original still matches."""
    bak = backup_path(path)
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if BEGIN in text and END in text:
            new = (text[: text.index(BEGIN)].rstrip() + "\n" + text[text.index(END) + len(END) :].lstrip()).strip()
            new = new + "\n" if new else ""
            if bak.exists():
                original = bak.read_text(encoding="utf-8")
                if original.strip() == new.strip():
                    new = original
            write_text(path, new, keep_backup=False)
    if bak.exists() and path.exists():
        saved, current = bak.read_text(encoding="utf-8"), path.read_text(encoding="utf-8")
        if saved == current or BEGIN in saved:  # nothing left worth keeping
            bak.unlink()


def write_own_file(path: Path, content: str):
    """Write a file that belongs to the coach (no backup: there is no original)."""
    write_text(path, content, keep_backup=False)


def edit_json(path: Path, change):
    """Apply change(data) to a JSON file, refusing to touch files we can't parse."""
    raw = path.read_text(encoding="utf-8") if path.exists() else ""
    try:
        data = json.loads(raw) if raw.strip() else {}
    except ValueError as e:
        raise RuntimeError(f"{path} isn't plain JSON ({e}); add the hook by hand (see README)")
    change(data)
    write_text(path, json.dumps(data, indent=2) + "\n")


def set_hook(hooks: dict, event: str, group):
    """Replace our handler for `event` in Claude-style {event: [group, ...]} hooks."""
    groups = [g for g in hooks.get(event, []) if not is_ours(g)]
    if group is not None:
        groups.append(group)
    if groups:
        hooks[event] = groups
    else:
        hooks.pop(event, None)


def install_skills(dest: Path):
    """Symlink the skills so `coach update` reaches every tool; copy where symlinks fail."""
    dest.mkdir(parents=True, exist_ok=True)
    for name in SKILL_NAMES:
        src, dst = REPO / "skills" / name, dest / name
        if dst.is_symlink():
            dst.unlink()
        elif dst.exists():
            if not (dst / COPY_MARKER).exists():
                raise RuntimeError(f"{dst} already exists and isn't ours; remove or rename it first")
            shutil.rmtree(dst)
        try:
            dst.symlink_to(src, target_is_directory=True)
        except OSError:
            shutil.copytree(src, dst)
            (dst / COPY_MARKER).write_text("")


def remove_skills(dest: Path):
    for name in SKILL_NAMES:
        dst = dest / name
        if dst.is_symlink():
            dst.unlink()
        elif (dst / COPY_MARKER).exists():
            shutil.rmtree(dst)


def instructions() -> str:
    mode = coachlib.get_mode()
    return coachlib.render(mode) if mode != "off" else coachlib.render_off_stub()


def run(cmd):
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"`{' '.join(cmd)}` failed: {(result.stderr or result.stdout).strip()}")


# --- adapters ---------------------------------------------------------------
#
# Each adapter: detect() -> bool, install() -> [notes], uninstall(), render() to
# rewrite its own rules file after a mode change, update() after `git pull`.


class Claude:
    """Claude Code CLI, desktop app and IDE extensions: installed as a plugin from this checkout."""

    name = "claude"

    def detect(self):
        return shutil.which("claude") is not None or (HOME / ".claude").exists()

    def install(self):
        if not shutil.which("claude"):
            return [f"In Claude Code, run: /plugin marketplace add {REPO}  then  /plugin install agent-coach@agent-coach"]
        run(["claude", "plugin", "marketplace", "add", str(REPO)])
        run(["claude", "plugin", "install", "agent-coach@agent-coach"])
        return ["Restart Claude Code to load the plugin."]

    def uninstall(self):
        if shutil.which("claude"):
            run(["claude", "plugin", "uninstall", "agent-coach@agent-coach"])
            run(["claude", "plugin", "marketplace", "remove", "agent-coach"])

    def render(self):
        pass  # the plugin's hooks read the mode on every prompt

    def update(self):
        if shutil.which("claude"):
            run(["claude", "plugin", "marketplace", "update", "agent-coach"])
            run(["claude", "plugin", "update", "agent-coach@agent-coach"])


class Codex:
    """Codex CLI, IDE extension and desktop app (they share $CODEX_HOME). Hooks only."""

    name = "codex"
    EVENTS = (("SessionStart", "session-start"), ("UserPromptSubmit", "prompt"))

    def detect(self):
        return shutil.which("codex") is not None or codex_home().exists()

    def remove_old_block(self):
        # Earlier versions wrote the rules into AGENTS.md.
        for name in ("AGENTS.md", "AGENTS.override.md"):
            remove_block(codex_home() / name)

    def set_hooks(self, on: bool):
        def change(d):
            for event, arg in self.EVENTS:
                group = {"hooks": [{"type": "command", "command": hook_command("codex", arg),
                                    "statusMessage": "agent-coach"}]}
                set_hook(d.setdefault("hooks", {}), event, group if on else None)

        path = codex_home() / "hooks.json"
        if on or path.exists():
            edit_json(path, change)

    def install(self):
        self.remove_old_block()
        self.set_hooks(True)
        install_skills(HOME / ".agents" / "skills")
        return ["In Codex, run /hooks and trust the two agent-coach hooks (Codex asks again whenever they change)."]

    def uninstall(self):
        self.remove_old_block()
        self.set_hooks(False)

    def render(self):
        pass  # the hooks read the mode

    def update(self):
        self.install()


class Gemini:
    """Gemini CLI (API-key and Enterprise users; consumers moved to Antigravity CLI). Hooks only."""

    name = "gemini"
    EVENTS = (("SessionStart", "session-start"), ("BeforeAgent", "prompt"))

    def detect(self):
        return shutil.which("gemini") is not None or (HOME / ".gemini" / "settings.json").exists()

    def set_hooks(self, on: bool):
        def change(d):
            for event, arg in self.EVENTS:
                group = {"hooks": [{"type": "command", "name": "agent-coach",
                                    "command": hook_command("gemini", arg), "timeout": 10000}]}
                set_hook(d.setdefault("hooks", {}), event, group if on else None)

        path = HOME / ".gemini" / "settings.json"
        if on or path.exists():
            edit_json(path, change)

    def install(self):
        remove_block(HOME / ".gemini" / "GEMINI.md")  # earlier versions wrote the rules here
        self.set_hooks(True)
        install_skills(HOME / ".agents" / "skills")
        write_own_file(HOME / ".gemini" / "commands" / "coach.toml",
                       (REPO / "adapters" / "gemini" / "coach.toml").read_text())
        return []

    def uninstall(self):
        remove_block(HOME / ".gemini" / "GEMINI.md")
        self.set_hooks(False)
        (HOME / ".gemini" / "commands" / "coach.toml").unlink(missing_ok=True)

    def render(self):
        pass  # the hooks read the mode

    def update(self):
        self.install()


class Antigravity:
    """Antigravity App, IDE and CLI (`agy`). A global rules file of the coach's own."""

    name = "antigravity"

    def detect(self):
        return shutil.which("agy") is not None or (HOME / ".gemini" / "config").exists()

    def rule_file(self) -> Path:
        return HOME / ".gemini" / "config" / "rules" / "agent-coach.md"

    def install(self):
        remove_block(HOME / ".gemini" / "GEMINI.md")  # earlier versions wrote the rules here
        self.render()
        install_skills(HOME / ".gemini" / "config" / "skills")
        return ["Antigravity reads the mode when a session starts. To switch mid-session, say `coach <mode>` in chat."]

    def uninstall(self):
        remove_block(HOME / ".gemini" / "GEMINI.md")
        self.rule_file().unlink(missing_ok=True)
        remove_skills(HOME / ".gemini" / "config" / "skills")

    def render(self):
        # Antigravity drops a rules file that has no valid trigger.
        write_own_file(self.rule_file(), "---\ntrigger: always_on\n---\n\n" + instructions())

    def update(self):
        self.install()


class Cursor:
    """Cursor IDE and `agent` CLI. User Rules aren't files, so a sessionStart hook injects the rules."""

    name = "cursor"

    def detect(self):
        return (HOME / ".cursor").exists() or shutil.which("cursor") is not None

    def install(self):
        def change(d):
            d.setdefault("version", 1)
            hooks = d.setdefault("hooks", {})
            for event, arg in (("sessionStart", "session-start"), ("beforeSubmitPrompt", "prompt")):
                hooks[event] = [h for h in hooks.get(event, []) if not is_ours(h)]
                hooks[event].append({"command": hook_command("cursor", arg)})

        edit_json(HOME / ".cursor" / "hooks.json", change)
        install_skills(HOME / ".agents" / "skills")
        return ["If coaching doesn't show up in Cursor, paste `coach render` into Customize > Rules > User Rules."]

    def uninstall(self):
        path = HOME / ".cursor" / "hooks.json"
        if not path.exists():
            return

        def change(d):
            hooks = d.get("hooks", {})
            for event in ("sessionStart", "beforeSubmitPrompt"):
                kept = [h for h in hooks.get(event, []) if not is_ours(h)]
                if kept:
                    hooks[event] = kept
                else:
                    hooks.pop(event, None)

        edit_json(path, change)

    def render(self):
        pass  # sessionStart reads the mode for each new chat

    def update(self):
        self.install()


class VSCode:
    """VS Code with GitHub Copilot (Copilot harness; the Claude and Codex harnesses use those adapters)."""

    name = "vscode"

    def detect(self):
        return (HOME / ".copilot").exists() or shutil.which("code") is not None

    def general_file(self) -> Path:
        return HOME / ".copilot" / "copilot-instructions.md"

    def own_file(self) -> Path:
        return HOME / ".copilot" / "instructions" / "agent-coach.instructions.md"

    def install(self):
        self.render()
        install_skills(HOME / ".copilot" / "skills")
        return []

    def uninstall(self):
        remove_block(self.general_file())
        self.own_file().unlink(missing_ok=True)
        remove_skills(HOME / ".copilot" / "skills")

    def render(self):
        # Copilot's general file is the surest always-on place. If it is a link to a
        # file you keep elsewhere, leave that file alone and use one of our own.
        if self.general_file().is_symlink():
            remove_block(self.general_file())
            write_own_file(self.own_file(), '---\napplyTo: "**"\n---\n\n' + instructions())
        else:
            self.own_file().unlink(missing_ok=True)
            write_block(self.general_file(), instructions())

    def update(self):
        self.install()


ADAPTERS = {a.name: a for a in (Claude(), Codex(), Gemini(), Antigravity(), Cursor(), VSCode())}
SHARED_SKILL_USERS = {"codex", "gemini", "cursor"}  # all read ~/.agents/skills


# --- install state ----------------------------------------------------------


def installed_path() -> Path:
    return coachlib.state_dir() / "installed.json"


def load_installed() -> dict:
    try:
        return json.loads(installed_path().read_text())
    except (OSError, ValueError):
        return {"repo": str(REPO), "tools": []}


def save_installed(tools):
    installed_path().parent.mkdir(parents=True, exist_ok=True)
    installed_path().write_text(json.dumps({"repo": str(REPO), "tools": sorted(tools)}, indent=2) + "\n")


def pick(names, default):
    if not names or names == ["all"]:
        return default
    unknown = [n for n in names if n not in ADAPTERS]
    if unknown:
        raise SystemExit(f"unknown tool(s): {', '.join(unknown)}. Choose from: {', '.join(ADAPTERS)}")
    return names


def install(names=None):
    names = pick(names, [n for n, a in ADAPTERS.items() if a.detect()])
    if not coachlib.state_dir().joinpath("mode").exists():
        coachlib.set_mode(coachlib.DEFAULT_MODE)
    write_launcher()
    done = set(load_installed()["tools"])
    lines = []
    for name in names:
        try:
            notes = ADAPTERS[name].install()
            done.add(name)
            lines.append(f"✓ {name}")
            lines += [f"    {n}" for n in notes]
        except (RuntimeError, OSError) as e:
            lines.append(f"✗ {name}: {e}")
    save_installed(done)
    lines.append(link_cli())
    lines.append(coachlib.status_line())
    return lines


def uninstall(names=None):
    done = set(load_installed()["tools"])
    names = pick(names, sorted(done))
    lines = []
    for name in names:
        try:
            ADAPTERS[name].uninstall()
            done.discard(name)
            lines.append(f"✓ removed {name}")
        except (RuntimeError, OSError) as e:
            lines.append(f"✗ {name}: {e}")
    if not done & SHARED_SKILL_USERS:
        remove_skills(HOME / ".agents" / "skills")
    if not done and os.name != "nt":
        launcher_path().unlink(missing_ok=True)
    save_installed(done)
    return lines


def refresh():
    """Rewrite the coach's own rules files after a mode change."""
    for name in load_installed()["tools"]:
        ADAPTERS[name].render()


def update():
    write_launcher()
    for name in load_installed()["tools"]:
        ADAPTERS[name].update()


def doctor():
    done = set(load_installed()["tools"])
    for name, adapter in ADAPTERS.items():
        state = "installed" if name in done else ("detected" if adapter.detect() else "not found")
        yield f"  {name:<12} {state:<10} {adapter.__doc__.strip()}"
    yield "Estimated context cost (tokens):"
    for label, tokens in coachlib.context_cost().items():
        yield f"  {tokens:>5}  {label}"


def pack(out: Path = None) -> Path:
    """Zip the agent-coach skill for upload to claude.ai, the Gemini app or ChatGPT."""
    out = out or REPO / "dist" / "agent-coach-skill.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    skill = coachlib.SKILL_DIR
    files = [skill / "SKILL.md", skill / "references" / "index.md", skill / "references" / "retired.md"]
    files += sorted(coachlib.TECHNIQUES.glob("*.md"))
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in files:
            z.write(path, f"agent-coach/{path.relative_to(skill).as_posix()}")
    return out


def link_cli():
    """Put `coach` on PATH via ~/.local/bin (POSIX). On Windows, print how to run it."""
    if os.name == "nt":
        return f'Run the CLI as: "{sys.executable}" "{REPO / "bin" / "coach"}"'
    target = HOME / ".local" / "bin" / "coach"
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.is_symlink() or not target.exists():
        if target.is_symlink():
            target.unlink()
        target.symlink_to(REPO / "bin" / "coach")
    on_path = str(target.parent) in os.environ.get("PATH", "").split(os.pathsep)
    return f"`coach` linked at {target}" + ("" if on_path else " (add ~/.local/bin to your PATH)")
