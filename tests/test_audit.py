import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import adapters  # noqa: E402
import audit  # noqa: E402
import coachlib  # noqa: E402

spec = importlib.util.spec_from_file_location("coach_hook", ROOT / "hooks" / "coach_hook.py")
coach_hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coach_hook)

SECRET = "sk-FAKE-do-not-print-0000"


class Fixture(unittest.TestCase):
    """A throwaway home with a repo in it. Nothing outside the temp folder is read."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.home = base / "home"
        self.repo = self.home / "work" / "app"
        (self.repo / ".git").mkdir(parents=True)
        self.state = base / "state"
        self.saved_env = {k: os.environ.pop(k, None) for k in
                          ("AGENT_COACH_MODE", "EVAL_AGENT_COACH_MODE", "AGENT_COACH_AUDIT_HOME",
                           "EVAL_AGENT_COACH_HOME", "AGENT_COACH_AUDIT_REPO", "EVAL_AGENT_COACH_REPO")}
        os.environ["AGENT_COACH_STATE"] = str(self.state)

    def tearDown(self):
        os.environ.pop("AGENT_COACH_STATE", None)
        for k, v in self.saved_env.items():
            if v is not None:
                os.environ[k] = v
        self.tmp.cleanup()

    def write(self, rel, text, base=None):
        path = (base or self.home) / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def run_audit(self):
        return audit.audit(repo=self.repo, home=self.home, overridden=True, managed=None)

    def ids(self, result):
        return [f["id"] for f in result["findings"]]

    def loaded(self, result):
        return [f["path"] for f in result["instruction_files"]]


class InstructionFileTests(Fixture):
    def test_agents_md_loads_only_without_a_claude_md(self):
        self.write(".claude/CLAUDE.md", "user rules\n")
        self.write("AGENTS.md", "shared rules\n")
        self.assertEqual(self.loaded(self.run_audit()), ["~/.claude/CLAUDE.md", "~/AGENTS.md"])
        self.write("CLAUDE.md", "project rules\n", base=self.repo)
        self.assertEqual(self.loaded(self.run_audit()), ["~/.claude/CLAUDE.md", "~/work/app/CLAUDE.md"])

    def test_never_reads_above_a_fixture_home(self):
        self.write("AGENTS.md", "outside the home\n", base=self.home.parent)
        self.assertEqual(self.loaded(self.run_audit()), [])

    def test_home_imports_resolve_against_the_audited_home(self):
        self.write("CLAUDE.md", "@~/shared/rules.md\n", base=self.repo)
        self.write("shared/rules.md", "shared\n")
        self.assertIn("~/shared/rules.md", self.loaded(self.run_audit()))

    def test_paths_to_open_are_absolute(self):
        self.write("CLAUDE.md", "rules\n", base=self.repo)
        self.write(".claude/usage-data/report.html", "<html></html>")
        result = self.run_audit()
        self.assertEqual(result["home"], str(self.home.absolute()))
        self.assertTrue(Path(result["insights"]["file"]).is_file())
        self.assertTrue(all(Path(f["file"]).is_file() for f in result["instruction_files"]))

    def test_imports_are_followed(self):
        self.write("CLAUDE.md", "See @docs/extra.md for more.\nMail me at someone@example.invalid\n", base=self.repo)
        self.write("docs/extra.md", "extra\n", base=self.repo)
        result = self.run_audit()
        self.assertIn("~/work/app/docs/extra.md", self.loaded(result))
        self.assertEqual(len(result["instruction_files"]), 2)

    def test_a1_fires_for_the_same_file_loaded_twice(self):
        canon = self.write("vault/canon.md", "rules\n" * 10)
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "CLAUDE.md").symlink_to(canon)
        (self.home / "AGENTS.md").symlink_to(canon)
        result = self.run_audit()
        a1 = [f for f in result["findings"] if f["id"] == "A1"]
        self.assertEqual(len(a1), 1)
        self.assertIn("~/.claude/CLAUDE.md", a1[0]["evidence"])
        self.assertIn("~/AGENTS.md", a1[0]["evidence"])
        self.assertIn("same file: ~/vault/canon.md", a1[0]["evidence"])

    def test_a1_fires_for_identical_copies_and_not_for_different_files(self):
        self.write(".claude/CLAUDE.md", "same\n")
        self.write("AGENTS.md", "same\n")
        self.assertIn("A1", self.ids(self.run_audit()))
        self.write("AGENTS.md", "different\n")
        self.assertNotIn("A1", self.ids(self.run_audit()))

    def test_a2_long_instructions_threshold(self):
        self.write("CLAUDE.md", "line\n" * 200, base=self.repo)
        self.assertNotIn("A2", self.ids(self.run_audit()))
        self.write("CLAUDE.md", "line\n" * 201, base=self.repo)
        self.assertIn("A2", self.ids(self.run_audit()))

    def test_a3_shouted_rules_with_line_numbers(self):
        self.write("CLAUDE.md", "intro\nALWAYS run the linter.\nAlways is fine in normal case.\n", base=self.repo)
        a3 = [f for f in self.run_audit()["findings"] if f["id"] == "A3"]
        self.assertEqual(a3[0]["evidence"], ["~/work/app/CLAUDE.md:2"])

    def test_a3_ignores_code(self):
        self.write("CLAUDE.md", "Use `NEVER_SET` here.\n```\nIMPORTANT=1\n```\n", base=self.repo)
        self.assertNotIn("A3", self.ids(self.run_audit()))


class RepoTests(Fixture):
    def test_a4_fires_when_tests_exist_and_no_command_is_named(self):
        (self.repo / "tests").mkdir()
        self.write("CLAUDE.md", "Be concise.\n", base=self.repo)
        a4 = [f for f in self.run_audit()["findings"] if f["id"] == "A4"]
        self.assertEqual(len(a4), 1)
        self.assertIn("test setup: tests/", a4[0]["evidence"])

    def test_a4_quiet_when_a_test_command_is_named(self):
        (self.repo / "tests").mkdir()
        self.write("CLAUDE.md", "Run `python3 -m pytest -q` before you finish.\n", base=self.repo)
        self.assertNotIn("A4", self.ids(self.run_audit()))

    def test_repo_root_stays_inside_a_fixture_home(self):
        (self.repo / ".git").rmdir()
        (self.home.parent / ".git").mkdir()
        (self.home.parent / "tests").mkdir()
        result = self.run_audit()
        self.assertEqual(result["repo"], "~/work/app")
        self.assertNotIn("A4", self.ids(result))

    def test_a4_quiet_without_tests(self):
        self.write("CLAUDE.md", "Be concise.\n", base=self.repo)
        self.assertNotIn("A4", self.ids(self.run_audit()))

    def test_package_json_default_test_script_is_not_a_test_setup(self):
        self.write("package.json", json.dumps({"scripts": {"test": 'echo "Error: no test specified" && exit 1'}}), base=self.repo)
        self.assertEqual(audit.test_setup(audit.Reader(self.home), self.repo), [])

    def test_evals_measurement(self):
        m6 = lambda: [m for m in self.run_audit()["measurements"] if m["id"] == "M6"][0]  # noqa: E731
        self.assertFalse(m6()["value"])
        (self.repo / "evals").mkdir()
        self.assertTrue(m6()["value"])

    def test_cloud_folders_are_recognized(self):
        self.assertTrue(audit.in_cloud_folder(Path("/Users/x/Library/Mobile Documents/com~apple~CloudDocs/repo")))
        self.assertTrue(audit.in_cloud_folder(Path("/Users/x/Library/CloudStorage/GoogleDrive-a/repo")))
        self.assertFalse(audit.in_cloud_folder(Path("/Users/x/workspace/repo")))


class PermissionTests(Fixture):
    def settings(self, data, rel=".claude/settings.json", base=None):
        self.write(rel, json.dumps(data), base=base)

    def test_a5_fires_for_bypass_without_containment(self):
        self.settings({"permissions": {"defaultMode": "bypassPermissions", "allow": ["Bash(ls)"]}})
        a5 = [f for f in self.run_audit()["findings"] if f["id"] == "A5"]
        self.assertIn("~/.claude/settings.json: permissions.defaultMode = bypassPermissions", a5[0]["evidence"])

    def test_a5_quiet_with_deny_rules_or_sandbox(self):
        self.settings({"permissions": {"defaultMode": "auto", "deny": ["Read(./.env)"]}})
        self.assertNotIn("A5", self.ids(self.run_audit()))
        self.settings({"permissions": {"defaultMode": "auto"}, "sandbox": {"enabled": True}})
        self.assertNotIn("A5", self.ids(self.run_audit()))

    def test_settings_read_once_when_working_in_home(self):
        self.write(".claude/settings.json", json.dumps({"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "x"}]}]}}))
        result = audit.audit(repo=self.home, home=self.home, overridden=True, managed=None)
        self.assertEqual([m["value"] for m in result["measurements"] if m["id"] == "M4"], [1])

    def test_a5_ignores_modes_claude_code_ignores(self):
        self.settings({"permissions": {"defaultMode": "bypassPermissions"}}, base=self.repo)
        self.settings({"permissions": {"defaultMode": "acceptEdits"}})
        self.assertNotIn("A5", self.ids(self.run_audit()))


class HooksPluginsMcpTests(Fixture):
    def add_plugin(self, key, hooks=None, mcp=None, skills=()):
        folder = self.home / "plugins" / key.split("@")[0]
        self.write(".claude-plugin/plugin.json", json.dumps({"name": key.split("@")[0]}), base=folder)
        if hooks:
            self.write("hooks/hooks.json", json.dumps({"hooks": hooks}), base=folder)
        if mcp:
            self.write(".mcp.json", json.dumps({"mcpServers": mcp}), base=folder)
        for name in skills:
            self.write(f"skills/{name}/SKILL.md", "---\nname: x\n---\n", base=folder)
        return folder

    def hook(self, command):
        return [{"hooks": [{"type": "command", "command": command}]}]

    def test_hooks_by_event_and_source(self):
        folder = self.add_plugin("demo@market", hooks={"UserPromptSubmit": self.hook("run x"), "Stop": self.hook("check")})
        self.write(".claude/plugins/installed_plugins.json",
                   json.dumps({"version": 2, "plugins": {"demo@market": [{"scope": "user", "installPath": str(folder)}]}}))
        self.write(".claude/settings.json", json.dumps({
            "enabledPlugins": {"demo@market": True, "gone@market": True},
            "hooks": {"SessionStart": self.hook("echo hi")},
        }))
        result = self.run_audit()
        m = {x["id"]: x for x in result["measurements"]}
        self.assertEqual(m["M2"]["value"], 2)
        self.assertIn("UserPromptSubmit: plugin demo@market (1)", m["M2"]["detail"])
        self.assertEqual(m["M4"]["value"], 1)
        self.assertTrue(any("gone@market" in u for u in result["unchecked"]))

    def test_synced_plugins_count(self):
        bucket = self.home / ".claude" / "plugins" / "synced" / "bucket-1"
        self.write(".claude-plugin/plugin.json", json.dumps({"name": "stripe"}), base=bucket / "stripe-dir")
        self.write("hooks/hooks.json", json.dumps({"hooks": {"SessionStart": self.hook("x")}}), base=bucket / "stripe-dir")
        self.write(".bucket-marker", "", base=self.home / ".claude" / "plugins" / "synced")
        m2 = [x for x in self.run_audit()["measurements"] if x["id"] == "M2"][0]
        self.assertIn("SessionStart: plugin stripe@synced (1)", m2["detail"])

    def test_mcp_servers_by_scope(self):
        folder = self.add_plugin("demo@market", mcp={"docs": {"type": "http", "url": "https://example.invalid/mcp"}},
                                 skills=("one", "two"))
        self.write(".claude/plugins/installed_plugins.json",
                   json.dumps({"plugins": {"demo@market": [{"installPath": str(folder)}]}}))
        self.write(".claude/settings.json", json.dumps({"enabledPlugins": {"demo@market": True}}))
        self.write(".claude.json", json.dumps({
            "mcpServers": {"memory": {"command": "node", "args": ["bridge.mjs"]}},
            "projects": {str(self.repo.absolute()): {"mcpServers": {"db": {"type": "stdio", "command": "x"}}}},
        }))
        self.write(".mcp.json", json.dumps({"mcpServers": {"shared": {"type": "sse", "url": "https://x.invalid"}}}), base=self.repo)
        m = {x["id"]: x for x in self.run_audit()["measurements"]}
        self.assertEqual(m["M3"]["value"], 2)
        self.assertIn("memory (stdio, user)", m["M3"]["detail"])
        self.assertIn("docs (http, plugin demo@market)", m["M3"]["detail"])
        self.assertIn("db (stdio, local)", m["M3"]["detail"])
        self.assertIn("shared (sse, project .mcp.json, needs approval)", m["M3"]["detail"])
        self.assertIn("plugin demo@market: 2 skills", m["M5"]["detail"])

    def test_config_values_never_reach_the_output(self):
        leak = {"command": f"/bin/{SECRET}", "args": ["--token", SECRET], "env": {"API_KEY": SECRET},
                "headers": {"Authorization": f"Bearer {SECRET}"}, "url": f"https://{SECRET}.ts.net/mcp"}
        self.write(".claude.json", json.dumps({
            "mcpServers": {"memory": leak},
            "projects": {str(self.repo.absolute()): {"mcpServers": {"db": leak}, "history": [SECRET]}},
        }))
        self.write(".claude/settings.json", json.dumps({
            "env": {"TOKEN": SECRET},
            "hooks": {"SessionStart": self.hook(f"curl -H 'x: {SECRET}'")},
            "permissions": {"defaultMode": "bypassPermissions", "allow": [f"Bash(echo {SECRET})"]},
        }))
        self.write(".mcp.json", json.dumps({"mcpServers": {"shared": leak}}), base=self.repo)
        result = self.run_audit()
        audit.save(result)
        self.assertNotIn(SECRET, json.dumps(result))
        self.assertNotIn(SECRET, audit.text_report(result))
        self.assertNotIn(SECRET, Path(result["saved_to"]).read_text())
        self.assertIn("memory (stdio, user)", json.dumps(result))  # it did read the file


class HistoryAndHintTests(Fixture):
    def test_status_against_the_previous_run(self):
        (self.repo / "tests").mkdir()
        self.write("CLAUDE.md", "ALWAYS be nice.\n", base=self.repo)
        first = self.run_audit()
        audit.save(first)
        self.assertEqual({f["status"] for f in first["findings"]}, {"new"})
        self.assertIsNone(first["previous_run"])
        self.write("CLAUDE.md", "Be nice. Test with `make test`.\nNEVER push to main.\n", base=self.repo)
        second = self.run_audit()
        audit.save(second)
        self.assertEqual([f["id"] for f in second["fixed"]], ["A4"])
        self.assertEqual([(f["id"], f["status"]) for f in second["findings"]], [("A3", "open")])
        self.assertEqual(second["previous_run"], first["run"])
        self.assertTrue(Path(second["saved_to"]).is_file())

    def test_memory_hint(self):
        self.assertIsNone(audit.read_memory_hint())
        with open(os.devnull, "w") as quiet:
            stdout, sys.stdout = sys.stdout, quiet
            try:
                audit.memory_command(["hybrid-memory: search core and this repo's project", "--save"])
                hint = audit.read_memory_hint()
                audit.memory_command(["--clear"])
            finally:
                sys.stdout = stdout
        self.assertEqual(hint, {"hint": "hybrid-memory: search core and this repo's project", "save_without_asking": True})
        self.assertIsNone(audit.read_memory_hint())

    def test_insights_report_age(self):
        self.write(".claude/usage-data/report.html", "<html></html>")
        insights = self.run_audit()["insights"]
        self.assertTrue(insights["exists"])
        self.assertTrue(insights["fresh"])

    def test_cli_json_with_an_eval_home(self):
        self.write("CLAUDE.md", "IMPORTANT: be brief.\n", base=self.repo)
        env = dict(os.environ, EVAL_AGENT_COACH_HOME=str(self.home), EVAL_AGENT_COACH_REPO=str(self.repo))
        run = subprocess.run([sys.executable, str(ROOT / "bin" / "coach"), "audit", "--json", "--no-save"],
                             capture_output=True, text=True, env=env)
        self.assertEqual(run.returncode, 0, run.stderr)
        result = json.loads(run.stdout)
        self.assertEqual([f["id"] for f in result["findings"]], ["A3"])
        self.assertNotIn("saved_to", result)
        self.assertFalse((self.state / "audits").exists())

    def test_relative_eval_home_resolves_against_the_checkout(self):
        os.environ["EVAL_AGENT_COACH_HOME"] = "evals/fixtures/audit-home"
        try:
            self.assertEqual(audit.audit_home(), (ROOT / "evals" / "fixtures" / "audit-home", True))
        finally:
            del os.environ["EVAL_AGENT_COACH_HOME"]


class CatalogueTests(unittest.TestCase):
    def test_every_rule_points_at_a_live_technique(self):
        """If a refresh retires a technique, this fails until a person remaps the rule."""
        index = coachlib.INDEX.read_text(encoding="utf-8")
        for rid, (_, techniques) in {**audit.RULES, **audit.MEASUREMENTS}.items():
            for technique in techniques:
                self.assertTrue((coachlib.TECHNIQUES / f"{technique}.md").is_file(), f"{rid}: {technique}")
                self.assertIn(f"`{technique}`", index, f"{rid}: {technique}")

    def test_shouted_rules_are_still_retired(self):
        retired = (coachlib.SKILL_DIR / "references" / "retired.md").read_text(encoding="utf-8")
        self.assertIn("ALL-CAPS", retired)

    def test_long_instructions_threshold_is_still_sourced(self):
        text = (coachlib.TECHNIQUES / "02-instruction-files.md").read_text(encoding="utf-8")
        self.assertIn(f"under {audit.LONG_INSTRUCTIONS_LINES} lines", text)


class SkillAndHookTests(Fixture):
    def test_audit_skill_is_small_and_on_demand(self):
        text = (ROOT / "skills" / "coach-audit" / "SKILL.md").read_text(encoding="utf-8")
        self.assertLessEqual(coachlib.estimate_tokens(text), 700)
        self.assertIn("disable-model-invocation: true", text)
        self.assertTrue(re.search(r"^name: coach-audit$", text, re.MULTILINE))
        self.assertIn("coach-audit", adapters.SKILL_NAMES)

    def test_pack_leaves_the_audit_out(self):
        out = adapters.pack(Path(self.tmp.name) / "skill.zip")
        with zipfile.ZipFile(out) as z:
            self.assertFalse([n for n in z.namelist() if "audit" in n])

    def test_audit_request_matching(self):
        for prompt in ("coach audit", "/coach audit", "/agent-coach:coach audit --repo ~/x", "  Coach Audit  "):
            self.assertTrue(coachlib.is_audit_request(prompt), prompt)
        for prompt in ("please coach audit", "coach auditing", "coach off"):
            self.assertFalse(coachlib.is_audit_request(prompt), prompt)
        self.assertIsNone(coachlib.parse_toggle("coach audit"))

    def test_hook_points_at_the_skill_in_any_mode(self):
        coachlib.set_mode("off")
        out = coach_hook.handle("claude", "prompt", {"prompt": "coach audit"})
        context = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn(str(coachlib.AUDIT_SKILL), context)
        self.assertEqual(coachlib.get_mode(), "off")
        self.assertEqual(coach_hook.handle("cursor", "prompt", {"prompt": "coach audit"}), {"continue": True})

    def test_pointer_is_one_short_line(self):
        pointer = coachlib.audit_pointer()
        self.assertNotIn("\n", pointer)
        self.assertLessEqual(coachlib.estimate_tokens(pointer), 60)


if __name__ == "__main__":
    unittest.main()
