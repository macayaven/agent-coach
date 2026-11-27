"""coach audit: read the setup a coding agent works in and report the gaps the
technique catalogue names. Standard library only, no network, and it edits nothing
outside its own state folder.

v0 covers Claude Code. A rule (A1-A5) fires only where a catalogue source states the
threshold; every other number is a measurement (M1-M6) for the coach-audit skill to
weigh. It never outputs config values: MCP servers by name and transport only, hooks
by event and source only, settings by key name.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import sys
from pathlib import Path

import coachlib

AUDIT_VERSION = 1
LONG_INSTRUCTIONS_LINES = 200  # "Claude recommends under 200 lines", cited in 02-instruction-files
MAX_IMPORT_HOPS = 4            # Claude Code expands @imports this deep
MAX_FILE_BYTES = 1_000_000
INSIGHTS_MAX_AGE_DAYS = 30
CONTEXT_EVENTS = ("SessionStart", "UserPromptSubmit")
CHECK_EVENTS = ("Stop", "SubagentStop")
UNATTENDED_MODES = ("auto", "bypassPermissions")  # honored only in user or managed settings
CLOUD_MARKERS = ("/Library/Mobile Documents", "/Library/CloudStorage", "/Dropbox", "/OneDrive", "/Google Drive")
TRANSPORTS = ("stdio", "http", "sse", "ws")

# Rule and measurement IDs, their names, and the catalogue techniques they come from.
# tests/test_audit.py checks every technique still exists, so a refresh that retires
# one fails CI until a person remaps the rule.
RULES = {
    "A1": ("duplicate-instructions", ["02-instruction-files"]),
    "A2": ("long-instructions", ["02-instruction-files"]),
    "A3": ("shouted-rules", ["11-skills-hooks"]),  # and retired.md: ALL-CAPS rules
    "A4": ("no-test-command", ["02-instruction-files", "03-verification"]),
    "A5": ("auto-without-containment", ["16-safety"]),
}
MEASUREMENTS = {
    "M1": ("instruction-tokens", ["02-instruction-files"]),
    "M2": ("context-hooks", ["11-skills-hooks", "12-tool-hygiene"]),
    "M3": ("mcp-servers", ["12-tool-hygiene"]),
    "M4": ("stop-hooks", ["03-verification"]),
    "M5": ("plugins-and-skills", ["11-skills-hooks"]),
    "M6": ("evals", ["17-evals"]),
}

SHOUT_RE = re.compile(r"\b(IMPORTANT|ALWAYS|NEVER)\b")
IMPORT_RE = re.compile(r"(?:^|\s)@((?:~|\.{1,2})?/?[\w.~/-]*[\w/-])")
TEST_CMD_RE = re.compile(
    r"\b(?:pytest|unittest|tox|nox|(?:npm|pnpm|yarn|bun)\s+(?:run\s+)?test|make\s+test|cargo\s+test"
    r"|go\s+test|jest|vitest|mvn\s+test|gradlew?\s+test|rspec|phpunit|dotnet\s+test|swift\s+test"
    r"|ctest|mix\s+test)\b"
    r"|`[^`\n]*(?:\btest\.sh\b|\brun[-_]tests?\b|\bbin/test\b)[^`\n]*`"
)
UNCHECKED_ALWAYS = [
    "MCP servers and connectors added through claude.ai or the desktop app (not in local files)",
    "command-line flags and shell aliases (for example --dangerously-skip-permissions, --mcp-config)",
    "CLAUDE.md files in subdirectories, which load only when the agent reads files there",
    "what hook commands do: the audit records each hook's event and source, not its command",
]


# ---------- paths ----------

def audit_home():
    """The home folder to audit, and whether it was overridden (tests and evals)."""
    raw = os.environ.get("AGENT_COACH_AUDIT_HOME") or os.environ.get("EVAL_AGENT_COACH_HOME")
    if not raw:
        return Path.home(), False
    path = Path(raw).expanduser()
    return (path if path.is_absolute() else coachlib.REPO / path), True


def default_repo():
    raw = os.environ.get("AGENT_COACH_AUDIT_REPO") or os.environ.get("EVAL_AGENT_COACH_REPO")
    if not raw:
        return Path.cwd()
    path = Path(raw).expanduser()
    return path if path.is_absolute() else coachlib.REPO / path


def managed_root():
    if sys.platform == "darwin":
        return Path("/Library/Application Support/ClaudeCode")
    if sys.platform.startswith("linux"):
        return Path("/etc/claude-code")
    return None


def in_cloud_folder(path):
    text = str(path.resolve())
    return any(marker in text for marker in CLOUD_MARKERS)


class Reader:
    """Reads files for one audit and remembers what it couldn't read."""

    def __init__(self, home):
        self.home = home
        self.problems = []

    def show(self, path):
        """A path as the report shows it, with ~ for the audited home."""
        text = str(path)
        for home in (str(self.home), str(self.home.resolve())):
            if text == home or text.startswith(home + os.sep):
                return "~" + text[len(home):]
        return text

    def text(self, path):
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                self.problems.append(f"{self.show(path)}: over 1 MB, not read")
                return None
            return path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return None

    def json(self, path):
        text = self.text(path)
        if text is None:
            return None
        try:
            return json.loads(text)
        except ValueError:
            self.problems.append(f"{self.show(path)}: not valid JSON, skipped")
            return None


def as_dict(value):
    return value if isinstance(value, dict) else {}


# ---------- collect: instruction files ----------

def strip_code(text):
    """Lines with fenced blocks blanked and inline code removed, numbering kept."""
    out, fenced = [], False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            out.append("")
            continue
        out.append("" if fenced else re.sub(r"`[^`\n]*`", "", line))
    return out


def instruction_candidates(home, overridden, cwd, managed):
    """(scope, path) for each instruction file Claude Code loads at launch, in load order."""
    found = []
    if managed and (managed / "CLAUDE.md").is_file():
        found.append(("managed", managed / "CLAUDE.md"))
    if (home / ".claude" / "CLAUDE.md").is_file():
        found.append(("user", home / ".claude" / "CLAUDE.md"))
    dirs = [cwd] + list(cwd.parents)
    if overridden:  # a fixture home: never read the real folders above it
        dirs = [d for d in dirs if d == home or home in d.parents]
    claude, agents = [], []
    for d in reversed(dirs):
        scope = "project" if d == cwd else "parent"
        for name in ("CLAUDE.md", ".claude/CLAUDE.md", "CLAUDE.local.md"):
            if name == ".claude/CLAUDE.md" and d == home:
                continue  # that's the user file, already listed
            if (d / name).is_file():
                claude.append((scope, d / name))
        if (d / "AGENTS.md").is_file():
            agents.append((scope, d / "AGENTS.md"))
    # AGENTS.md loads only when no CLAUDE.md, .claude/CLAUDE.md or CLAUDE.local.md
    # exists in the working folder or above it (~/.claude/CLAUDE.md doesn't count).
    return found + (claude or agents)


def imports_of(path, text, home):
    targets = []
    for line in strip_code(text):
        for ref in IMPORT_RE.findall(line):
            target = home / ref[2:] if ref.startswith("~/") else (path.parent / ref)
            if target.is_file():
                targets.append(target)
    return targets


def collect_instructions(reader, candidates, home):
    files, seen = [], set()
    queue = [(scope, path, 0) for scope, path in candidates]
    while queue:
        scope, path, hops = queue.pop(0)
        key = str(path.absolute())
        if key in seen:
            continue
        seen.add(key)
        text = reader.text(path)
        if text is None:
            continue
        files.append({
            "scope": scope,
            "path": reader.show(path),
            "file": str(path.absolute()),
            "resolved": reader.show(path.resolve()),
            "lines": len(text.splitlines()),
            "tokens": coachlib.estimate_tokens(text),
            "_text": text,
            "_hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        })
        if hops < MAX_IMPORT_HOPS:
            queue.extend(("import", target, hops + 1) for target in imports_of(path, text, home))
    return files


# ---------- collect: settings, plugins, hooks, MCP ----------

def settings_files(reader, home, cwd, managed):
    paths = [
        ("user", home / ".claude" / "settings.json"),
        ("project", cwd / ".claude" / "settings.json"),
        ("local", cwd / ".claude" / "settings.local.json"),
    ]
    if managed:
        paths.append(("managed", managed / "managed-settings.json"))
    out, seen = [], set()
    for scope, path in paths:
        if str(path.resolve()) in seen:
            continue  # the working folder is the home: its settings are the user's
        seen.add(str(path.resolve()))
        data = reader.json(path) if path.is_file() else None
        if isinstance(data, dict):
            out.append((scope, reader.show(path), data))
    return out


def plugin_dirs(reader, home, settings):
    """(name, folder) for each plugin Claude Code loads: enabled installs, then synced ones."""
    enabled = {}
    for _, _, data in settings:
        for key, on in as_dict(data.get("enabledPlugins")).items():
            enabled[key] = bool(on)
    installed = as_dict(as_dict(reader.json(home / ".claude" / "plugins" / "installed_plugins.json")).get("plugins"))
    out = []
    for key, on in sorted(enabled.items()):
        if not on or key.endswith("@synced"):
            continue
        records = installed.get(key)
        folder = None
        for record in records if isinstance(records, list) else []:
            path = Path(str(as_dict(record).get("installPath", "")))
            if str(path) and path.is_dir():
                folder = path
                break
        out.append((key, folder))
    synced = home / ".claude" / "plugins" / "synced"
    for bucket in sorted(p for p in synced.glob("*") if p.is_dir()) if synced.is_dir() else []:
        for folder in sorted(p for p in bucket.iterdir() if p.is_dir()):
            manifest = as_dict(reader.json(folder / ".claude-plugin" / "plugin.json") or reader.json(folder / "plugin.json"))
            name = str(manifest.get("name") or folder.name)
            if enabled.get(f"{name}@synced", True):
                out.append((f"{name}@synced", folder))
    return out


def plugin_manifest(reader, folder):
    return as_dict(reader.json(folder / ".claude-plugin" / "plugin.json") or reader.json(folder / "plugin.json"))


def hook_counts(hooks):
    """{event: number of hook commands} from a settings-style hooks object."""
    counts = {}
    for event, groups in as_dict(hooks).items():
        n = 0
        for group in groups if isinstance(groups, list) else []:
            inner = as_dict(group).get("hooks")
            n += len(inner) if isinstance(inner, list) else 1
        if n:
            counts[event] = n
    return counts


def plugin_hooks(reader, folder):
    counts = {}
    sources = [reader.json(folder / "hooks" / "hooks.json")]
    declared = plugin_manifest(reader, folder).get("hooks")
    for item in declared if isinstance(declared, list) else [declared]:
        if isinstance(item, dict):
            sources.append(item)
        elif isinstance(item, str):
            sources.append(reader.json(folder / item))
    for data in sources:
        data = as_dict(data)
        for event, n in hook_counts(data.get("hooks", data)).items():
            counts[event] = counts.get(event, 0) + n
    return counts


def transport(server):
    kind = server.get("type")
    if kind in TRANSPORTS:
        return kind
    if "command" in server:
        return "stdio"
    if "url" in server:
        return "http"
    return "unknown"


def servers_in(data):
    """{name: transport} from an mcpServers object, reading only names and transport."""
    data = as_dict(data)
    block = data.get("mcpServers", data)
    return {str(name): transport(as_dict(s)) for name, s in as_dict(block).items() if isinstance(s, dict)}


def plugin_servers(reader, folder):
    servers = servers_in(reader.json(folder / ".mcp.json"))
    declared = plugin_manifest(reader, folder).get("mcpServers")
    if isinstance(declared, dict):
        servers.update(servers_in({"mcpServers": declared}))
    elif isinstance(declared, str):
        servers.update(servers_in(reader.json(folder / declared)))
    return servers


def skill_names(folder):
    if not folder or not folder.is_dir():
        return []
    return sorted(p.parent.name for p in folder.glob("*/SKILL.md"))


# ---------- collect: repository ----------

def project_root(cwd, home, overridden):
    for d in [cwd] + list(cwd.parents):
        if overridden and d != home and home not in d.parents:
            break  # a fixture home: never treat the real folders above it as the repo
        if (d / ".git").exists():
            return d
    return cwd


def test_setup(reader, root):
    hits = [f"{d}/" for d in ("tests", "test", "spec", "__tests__") if (root / d).is_dir()]
    hits += [f for f in ("pytest.ini", "tox.ini", "noxfile.py", "Cargo.toml", "go.mod") if (root / f).is_file()]
    hits += [p.name for p in sorted(root.glob("jest.config.*")) + sorted(root.glob("vitest.config.*"))]
    pyproject = reader.text(root / "pyproject.toml") if (root / "pyproject.toml").is_file() else None
    if pyproject and "[tool.pytest" in pyproject:
        hits.append("pyproject.toml [tool.pytest]")
    package = as_dict(reader.json(root / "package.json")) if (root / "package.json").is_file() else {}
    script = str(as_dict(package.get("scripts")).get("test", ""))
    if script and "no test specified" not in script:
        hits.append("package.json scripts.test")
    makefile = reader.text(root / "Makefile") if (root / "Makefile").is_file() else None
    if makefile and re.search(r"^test\s*:", makefile, re.MULTILINE):
        hits.append("Makefile test target")
    return hits


def ci_config(root):
    hits = [f".github/workflows/{p.name}" for p in sorted((root / ".github" / "workflows").glob("*.y*ml"))]
    hits += [f for f in (".gitlab-ci.yml", ".circleci/config.yml", "azure-pipelines.yml") if (root / f).is_file()]
    return hits


def evals_present(root):
    hits = [f"{d}/" for d in ("evals", "eval") if (root / d).is_dir()]
    hits += [p.name for p in sorted(root.glob("promptfooconfig.*"))]
    return hits


# ---------- check ----------

def finding(rule, subject, summary, evidence):
    name, techniques = RULES[rule]
    return {"id": rule, "name": name, "techniques": techniques, "subject": subject,
            "summary": summary, "evidence": evidence}


def check_instructions(files):
    out = []
    groups = {}
    for f in files:
        groups.setdefault(f["_hash"], []).append(f)
    for group in groups.values():
        if len(group) < 2:
            continue
        paths = [f["path"] for f in group]
        same_file = len({f["resolved"] for f in group}) == 1
        target = group[0]["resolved"] if same_file else "identical content"
        wasted = group[0]["tokens"] * (len(group) - 1)
        out.append(finding(
            "A1", " + ".join(paths),
            f"{len(group)} instruction files load the same text: about {wasted} tokens loaded twice every session",
            paths + [f"same file: {target}" if same_file else "different files, identical content"],
        ))
    unique = list({f["_hash"]: f for f in files}.values())
    for f in unique:
        if f["lines"] > LONG_INSTRUCTIONS_LINES:
            out.append(finding(
                "A2", f["path"],
                f"{f['path']} is {f['lines']} lines; Claude recommends under {LONG_INSTRUCTIONS_LINES}",
                [f"{f['path']}: {f['lines']} lines, about {f['tokens']} tokens"],
            ))
    for f in unique:
        lines = [i for i, line in enumerate(strip_code(f["_text"]), 1) if SHOUT_RE.search(line)]
        if lines:
            shown = [f"{f['path']}:{i}" for i in lines[:5]]
            more = [f"and {len(lines) - 5} more lines"] if len(lines) > 5 else []
            out.append(finding(
                "A3", f["path"],
                f"{len(lines)} line(s) in {f['path']} use all-caps IMPORTANT/ALWAYS/NEVER",
                shown + more,
            ))
    return out


def check_tests(files, tests, root_shown):
    if not tests:
        return []
    named = [f["path"] for f in files if any(TEST_CMD_RE.search(line) for line in f["_text"].splitlines())]
    if named:
        return []
    checked = sorted({f["path"] for f in files}) or ["no instruction files are loaded"]
    return [finding(
        "A4", root_shown,
        "the repo has tests, but no instruction file the agent loads says how to run them",
        [f"test setup: {', '.join(tests)}", f"files checked: {', '.join(checked)}"],
    )]


def check_permissions(settings):
    modes = [(shown, mode) for scope, shown, data in settings
             if scope in ("user", "managed")
             for mode in [as_dict(data.get("permissions")).get("defaultMode")]
             if mode in UNATTENDED_MODES]
    if not modes:
        return []
    deny = any(as_dict(data.get("permissions")).get("deny") for _, _, data in settings)
    sandbox = any(as_dict(data.get("sandbox")).get("enabled") is True for _, _, data in settings)
    if deny or sandbox:
        return []
    return [finding(
        "A5", modes[0][0],
        f"permissions.defaultMode is {modes[0][1]}, with no deny rules and no sandbox",
        [f"{shown}: permissions.defaultMode = {mode}" for shown, mode in modes]
        + ["permissions.deny: none in any settings file", "sandbox.enabled: not true in any settings file"],
    )]


def measurement(mid, value, summary, detail):
    name, techniques = MEASUREMENTS[mid]
    return {"id": mid, "name": name, "techniques": techniques, "value": value,
            "summary": summary, "detail": detail}


# ---------- run ----------

def audit(repo=None, home=None, overridden=None, managed="default"):
    if home is None:
        home, overridden = audit_home()
    cwd = Path(repo or default_repo()).expanduser().absolute()
    if managed == "default":
        managed = None if overridden else managed_root()
    reader = Reader(home)
    unchecked = list(UNCHECKED_ALWAYS)
    if managed is None:
        unchecked.append("managed (organization) settings and instructions")

    files = collect_instructions(reader, instruction_candidates(home, overridden, cwd, managed), home)
    settings = settings_files(reader, home, cwd, managed)
    plugins = plugin_dirs(reader, home, settings)

    root = project_root(cwd, home, overridden)
    cloud = in_cloud_folder(root)
    if cloud:
        unchecked.append("the repository's tests, CI and evals: it's in a cloud-synced folder, which the audit doesn't scan")
    tests = [] if cloud else test_setup(reader, root)
    ci = [] if cloud else ci_config(root)
    evals = [] if cloud else evals_present(root)

    findings = check_instructions(files) + check_tests(files, tests, reader.show(root)) + check_permissions(settings)

    # Hooks by event and source.
    hook_rows = []
    for scope, shown, data in settings:
        for event, n in hook_counts(data.get("hooks")).items():
            hook_rows.append({"event": event, "source": shown, "count": n})
    for name, folder in plugins:
        if folder is None:
            unchecked.append(f"plugin {name}: enabled but not installed here")
            continue
        for event, n in plugin_hooks(reader, folder).items():
            hook_rows.append({"event": event, "source": f"plugin {name}", "count": n})
    context_hooks = [r for r in hook_rows if r["event"] in CONTEXT_EVENTS]
    check_hooks = [r for r in hook_rows if r["event"] in CHECK_EVENTS]

    # MCP servers by scope.
    claude_json = as_dict(reader.json(home / ".claude.json"))
    every_project, this_project = [], []
    for name, kind in sorted(servers_in({"mcpServers": claude_json.get("mcpServers")}).items()):
        every_project.append(f"{name} ({kind}, user)")
    if managed:
        for name, kind in sorted(servers_in(reader.json(managed / "managed-mcp.json")).items()):
            every_project.append(f"{name} ({kind}, managed)")
    for pname, folder in plugins:
        for name, kind in sorted(plugin_servers(reader, folder).items()) if folder else []:
            every_project.append(f"{name} ({kind}, plugin {pname})")
    local = as_dict(as_dict(claude_json.get("projects")).get(str(cwd)))
    for name, kind in sorted(servers_in({"mcpServers": local.get("mcpServers")}).items()):
        this_project.append(f"{name} ({kind}, local)")
    for name, kind in sorted(servers_in(reader.json(cwd / ".mcp.json")).items()):
        this_project.append(f"{name} ({kind}, project .mcp.json, needs approval)")

    # Plugins and skills: names for your own skills, counts for plugins'.
    skill_rows, skill_total = [], 0
    synced_skills = home / ".claude" / "skills" / "synced"
    own = [("user", skill_names(home / ".claude" / "skills")), ("project", skill_names(cwd / ".claude" / "skills"))]
    for bucket in sorted(p for p in synced_skills.glob("*") if p.is_dir()) if synced_skills.is_dir() else []:
        own.append(("synced", skill_names(bucket)))
    for label, names in own:
        names = [n for n in names if n != "synced"]
        if names:
            skill_rows.append(f"{label} skills: {', '.join(names)}")
            skill_total += len(names)
    for pname, folder in plugins:
        n = len(skill_names(folder / "skills" if folder else None))
        skill_rows.append(f"plugin {pname}: {n} skills")
        skill_total += n

    total_tokens = sum(f["tokens"] for f in files)
    measurements = [
        measurement("M1", total_tokens, f"about {total_tokens} tokens of instruction files load every session",
                    [f"{f['path']} ({f['scope']}): {f['lines']} lines, about {f['tokens']} tokens" for f in files]),
        measurement("M2", sum(r["count"] for r in context_hooks),
                    f"{sum(r['count'] for r in context_hooks)} hooks can add context at session start or on every prompt",
                    [f"{r['event']}: {r['source']} ({r['count']})" for r in context_hooks]),
        measurement("M3", len(every_project), f"{len(every_project)} MCP servers are on in every project, {len(this_project)} more in this one",
                    every_project + this_project),
        measurement("M4", sum(r["count"] for r in check_hooks),
                    f"{sum(r['count'] for r in check_hooks)} Stop hooks; whether any runs a check is for you to judge",
                    [f"{r['event']}: {r['source']} ({r['count']})" for r in check_hooks]),
        measurement("M5", {"plugins": len(plugins), "skills": skill_total},
                    f"{len(plugins)} plugins and {skill_total} skills are enabled",
                    skill_rows),
        measurement("M6", bool(evals), "the repo has evals" if evals else "no evals found in the repo",
                    evals),
    ]

    insights = home / ".claude" / "usage-data" / "report.html"
    insights_info = {"path": reader.show(insights), "file": str(insights.absolute()), "exists": insights.is_file(),
                     "age_days": None, "fresh": False}
    if insights.is_file():
        age = (datetime.datetime.now() - datetime.datetime.fromtimestamp(insights.stat().st_mtime)).days
        insights_info.update(age_days=age, fresh=age <= INSIGHTS_MAX_AGE_DAYS)

    return {
        "audit_version": AUDIT_VERSION,
        "tool": "claude-code",
        "date": datetime.date.today().isoformat(),
        "home": str(home.absolute()),  # what ~ means in the paths below
        "repo": reader.show(root),
        "cwd": reader.show(cwd),
        "findings": findings,
        "measurements": measurements,
        "instruction_files": [{k: v for k, v in f.items() if not k.startswith("_")} for f in files],
        "hooks": hook_rows,
        "repo_facts": {"tests": tests, "ci": ci, "evals": evals},
        "insights": insights_info,
        "memory_hint": read_memory_hint(),
        "unchecked": unchecked + reader.problems,
    }


# ---------- history ----------

def finding_key(f):
    return f"{f['id']}:{f['subject']}"


def audits_dir(result):
    slug = re.sub(r"[^\w.-]+", "-", Path(result["repo"]).name) or "repo"
    digest = hashlib.sha1(result["repo"].encode("utf-8")).hexdigest()[:8]
    return coachlib.state_dir() / "audits" / f"{slug}-{digest}"


def previous_audit(folder):
    runs = sorted(folder.glob("*.json")) if folder.is_dir() else []
    for path in reversed(runs):
        try:
            return path, json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
    return None, None


def mark_status(result, previous):
    before = {finding_key(f) for f in (previous or {}).get("findings", [])}
    now = {finding_key(f) for f in result["findings"]}
    for f in result["findings"]:
        f["status"] = "open" if finding_key(f) in before else "new"
    result["previous_run"] = (previous or {}).get("run")
    result["fixed"] = [
        {"id": f["id"], "name": f.get("name"), "subject": f["subject"]}
        for f in (previous or {}).get("findings", []) if finding_key(f) not in now
    ]


def save(result):
    folder = audits_dir(result)
    _, previous = previous_audit(folder)
    run = datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")
    result["run"] = run
    mark_status(result, previous)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{run}.json"
    result["saved_to"] = str(path)
    path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return path


# ---------- memory hint ----------

def hint_path():
    return coachlib.state_dir() / "memory-hint"


def read_memory_hint():
    try:
        lines = hint_path().read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    if not lines:
        return None
    return {"hint": lines[0], "save_without_asking": "save-without-asking: yes" in lines[1:]}


def memory_command(args):
    parser = argparse.ArgumentParser(prog="coach memory", description="Tell coach audit which memory tool and projects to use.")
    parser.add_argument("hint", nargs="?", help='one line, e.g. "hybrid-memory: search core and this repo\'s project"')
    parser.add_argument("--save", action="store_true", help="let the audit save its summary to memory without asking")
    parser.add_argument("--clear", action="store_true", help="remove the hint")
    opts = parser.parse_args(args)
    if opts.clear:
        if hint_path().exists():
            hint_path().unlink()
        print("memory hint cleared")
        return 0
    if not opts.hint:
        current = read_memory_hint()
        if current:
            print(f"memory hint: {current['hint']}")
            print(f"save summaries without asking: {'yes' if current['save_without_asking'] else 'no'}")
        else:
            print("no memory hint set (coach audit searches whatever memory tool the agent has)")
        return 0
    hint = " ".join(opts.hint.split())
    hint_path().parent.mkdir(parents=True, exist_ok=True)
    hint_path().write_text(hint + "\n" + ("save-without-asking: yes\n" if opts.save else ""), encoding="utf-8")
    print(f"memory hint saved{' (summaries save without asking)' if opts.save else ''}")
    return 0


# ---------- output ----------

def text_report(result):
    out = [f"coach audit · Claude Code · {result['repo']} · {result['date']}"]
    if result.get("previous_run"):
        out.append(f"compared with the run of {result['previous_run']}")
    out.append("")
    out.append("Findings" if result["findings"] else "Findings: none")
    for f in result["findings"]:
        status = f" ({f['status']})" if f.get("status") else ""
        out.append(f"  {f['id']} {f['name']} [{', '.join(f['techniques'])}]{status}")
        out.append(f"     {f['summary']}")
        out += [f"     - {e}" for e in f["evidence"]]
    for f in result.get("fixed", []):
        out.append(f"  fixed since last run: {f['id']} {f.get('name') or ''} ({f['subject']})")
    out += ["", "Measurements"]
    for m in result["measurements"]:
        out.append(f"  {m['id']} {m['name']} [{', '.join(m['techniques'])}]: {m['summary']}")
        out += [f"     - {d}" for d in m["detail"][:12]]
        if len(m["detail"]) > 12:
            out.append(f"     - and {len(m['detail']) - 12} more")
    insights = result["insights"]
    out += ["", "Session history: " + (
        f"/insights report from {insights['age_days']} days ago" if insights["exists"] else "no /insights report")]
    out += ["", "Not checked"] + [f"  - {u}" for u in result["unchecked"]]
    if result.get("saved_to"):
        out += ["", f"Saved to {result['saved_to']}"]
    out += ["", "For a ranked report with fixes, ask your agent for the coach-audit skill (in Claude Code: /agent-coach:coach-audit)."]
    return "\n".join(out)


def main(args):
    parser = argparse.ArgumentParser(prog="coach audit", description="Audit the setup your coding agent works in.")
    parser.add_argument("--json", action="store_true", help="print JSON for the coach-audit skill")
    parser.add_argument("--repo", help="the folder you start the agent in (default: the current folder)")
    parser.add_argument("--no-save", action="store_true", help="don't keep this run in ~/.agent-coach/state/audits")
    opts = parser.parse_args(args)
    result = audit(repo=opts.repo)
    if not opts.no_save:
        save(result)
    print(json.dumps(result, separators=(",", ":")) if opts.json else text_report(result))
    return 0
