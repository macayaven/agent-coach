import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import adapters  # noqa: E402
import coachlib  # noqa: E402


class FakeHome(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.home = Path(self.tmp.name)
        env = {"AGENT_COACH_STATE": str(self.home / ".agent-coach" / "state"), "CODEX_HOME": str(self.home / ".codex")}
        for patcher in (mock.patch.object(adapters, "HOME", self.home), mock.patch.dict(os.environ, env)):
            patcher.start()
            self.addCleanup(patcher.stop)
        for key in ("AGENT_COACH_MODE", "EVAL_AGENT_COACH_MODE"):
            os.environ.pop(key, None)
        self.addCleanup(self.tmp.cleanup)

    def read(self, rel):
        return (self.home / rel).read_text()


class BlockTests(FakeHome):
    def test_block_keeps_existing_content_and_is_idempotent(self):
        path = self.home / "AGENTS.md"
        path.write_text("# My rules\n\nUse tabs.\n")
        adapters.write_block(path, "v1")
        adapters.write_block(path, "v2")
        text = path.read_text()
        self.assertTrue(text.startswith("# My rules\n\nUse tabs.\n"))
        self.assertEqual(text.count(adapters.BEGIN), 1)
        self.assertIn("v2", text)
        self.assertNotIn("v1", text)
        adapters.remove_block(path)
        self.assertEqual(path.read_text(), "# My rules\n\nUse tabs.\n")

    def test_first_change_leaves_a_backup(self):
        path = self.home / "AGENTS.md"
        path.write_text("original\n")
        adapters.write_block(path, "v1")
        self.assertEqual((self.home / "AGENTS.md.agent-coach.bak").read_text(), "original\n")

    def test_refuses_to_rewrite_json_it_cannot_parse(self):
        path = self.home / "settings.json"
        path.write_text('{ // comment\n "a": 1 }')
        with self.assertRaises(RuntimeError):
            adapters.edit_json(path, lambda d: d.update(b=2))
        self.assertIn("// comment", path.read_text())


class BlockRemovalTests(FakeHome):
    def test_removal_restores_the_original_bytes_and_drops_the_backup(self):
        path = self.home / "AGENTS.md"
        original = "# Mine\n\nNo trailing newline, two blank lines above the end\n\n\n"
        path.write_text(original)
        adapters.write_block(path, "rules")
        adapters.remove_block(path)
        self.assertEqual(path.read_text(), original)
        self.assertFalse((self.home / "AGENTS.md.agent-coach.bak").exists())

    def test_removal_keeps_edits_made_after_the_block_was_added(self):
        path = self.home / "AGENTS.md"
        path.write_text("old line\n")
        adapters.write_block(path, "rules")
        path.write_text("new line\n\n" + path.read_text().split("old line\n", 1)[1].lstrip())
        adapters.remove_block(path)
        self.assertEqual(path.read_text(), "new line\n")
        self.assertTrue((self.home / "AGENTS.md.agent-coach.bak").exists())  # differs, so it's kept


class InstallTests(FakeHome):
    def hooks(self, rel):
        return json.loads(self.read(rel))["hooks"]

    def test_codex_uses_hooks_and_leaves_agents_md_alone(self):
        (self.home / ".codex").mkdir()
        (self.home / ".codex" / "AGENTS.md").write_text("# Mine\n")
        (self.home / ".codex" / "hooks.json").write_text(json.dumps(
            {"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "mine.sh"}]}]}}))
        adapters.install(["codex"])
        adapters.install(["codex"])  # twice: must not duplicate
        self.assertEqual(self.read(".codex/AGENTS.md"), "# Mine\n")
        hooks = self.hooks(".codex/hooks.json")
        self.assertEqual(len(hooks["SessionStart"]), 1)
        self.assertIn("codex session-start", hooks["SessionStart"][0]["hooks"][0]["command"])
        self.assertEqual(len(hooks["UserPromptSubmit"]), 2)
        self.assertEqual(hooks["UserPromptSubmit"][0]["hooks"][0]["command"], "mine.sh")
        self.assertTrue((self.home / ".agents/skills/agent-coach/SKILL.md").exists())

        adapters.uninstall(["codex"])
        hooks = self.hooks(".codex/hooks.json")
        self.assertNotIn("SessionStart", hooks)
        self.assertEqual([g["hooks"][0]["command"] for g in hooks["UserPromptSubmit"]], ["mine.sh"])
        self.assertFalse((self.home / ".agents/skills/agent-coach").exists())

    def test_install_cleans_up_a_block_an_earlier_version_wrote_through_a_link(self):
        # A setup like a shared "canon" file that several tools' instruction files link to.
        canon = self.home / "vault" / "canon.md"
        canon.parent.mkdir()
        original = "# Canon\n\nShared rules.\n"
        canon.write_text(original)
        for rel in (".codex/AGENTS.md", ".gemini/GEMINI.md"):
            link = self.home / rel
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(canon)
        adapters.write_block(self.home / ".codex" / "AGENTS.md", "old rules")  # what earlier versions did
        self.assertIn("old rules", canon.read_text())

        adapters.install(["codex", "gemini", "antigravity"])
        self.assertEqual(canon.read_text(), original)
        self.assertTrue((self.home / ".codex" / "AGENTS.md").is_symlink())
        coachlib.set_mode("suggest")
        adapters.refresh()
        self.assertEqual(canon.read_text(), original)  # mode changes never touch it either

    def test_gemini_uses_hooks_and_antigravity_its_own_rules_file(self):
        (self.home / ".gemini").mkdir()
        (self.home / ".gemini" / "GEMINI.md").write_text("# Mine\n")
        adapters.install(["gemini", "antigravity"])
        self.assertEqual(self.read(".gemini/GEMINI.md"), "# Mine\n")
        hooks = self.hooks(".gemini/settings.json")
        self.assertIn("gemini session-start", hooks["SessionStart"][0]["hooks"][0]["command"])
        self.assertIn("gemini prompt", hooks["BeforeAgent"][0]["hooks"][0]["command"])
        rule = self.read(".gemini/config/rules/agent-coach.md")
        self.assertTrue(rule.startswith("---\ntrigger: always_on\n---\n"))
        self.assertIn("active in force mode", rule)

        adapters.uninstall(["gemini", "antigravity"])
        self.assertEqual(self.hooks(".gemini/settings.json"), {})
        self.assertFalse((self.home / ".gemini/config/rules/agent-coach.md").exists())
        self.assertEqual(self.read(".gemini/GEMINI.md"), "# Mine\n")

    def test_mode_change_rewrites_only_the_coachs_own_files(self):
        adapters.install(["antigravity", "vscode"])
        coachlib.set_mode("suggest")
        adapters.refresh()
        self.assertIn("active in suggest mode", self.read(".gemini/config/rules/agent-coach.md"))
        self.assertIn("active in suggest mode", self.read(".copilot/copilot-instructions.md"))
        coachlib.set_mode("off")
        adapters.refresh()
        self.assertIn("installed but off", self.read(".gemini/config/rules/agent-coach.md"))
        self.assertNotIn("## force", self.read(".gemini/config/rules/agent-coach.md"))
        self.assertFalse((self.home / ".gemini/config/rules/agent-coach.md.agent-coach.bak").exists())

    def test_vscode_uses_its_own_file_when_the_general_one_is_a_link(self):
        shared = self.home / "vault" / "copilot.md"
        shared.parent.mkdir()
        shared.write_text("# Shared\n")
        (self.home / ".copilot").mkdir()
        (self.home / ".copilot" / "copilot-instructions.md").symlink_to(shared)
        adapters.install(["vscode"])
        self.assertEqual(shared.read_text(), "# Shared\n")
        own = self.read(".copilot/instructions/agent-coach.instructions.md")
        self.assertTrue(own.startswith('---\napplyTo: "**"\n---\n'))
        self.assertIn("active in force mode", own)

    def test_cursor_hooks(self):
        adapters.install(["cursor"])
        adapters.install(["cursor"])
        data = json.loads(self.read(".cursor/hooks.json"))
        self.assertEqual(data["version"], 1)
        self.assertEqual(len(data["hooks"]["sessionStart"]), 1)
        self.assertEqual(len(data["hooks"]["beforeSubmitPrompt"]), 1)
        adapters.uninstall(["cursor"])
        self.assertEqual(json.loads(self.read(".cursor/hooks.json"))["hooks"], {})

    def test_reinstall_replaces_hooks_from_earlier_versions(self):
        (self.home / ".cursor").mkdir()
        (self.home / ".cursor" / "hooks.json").write_text(json.dumps({"version": 1, "hooks": {
            "sessionStart": [{"command": '"/old/python3.15" "/x/hooks/coach_hook.py" cursor session-start'}]}}))
        adapters.install(["cursor"])
        commands = [h["command"] for h in json.loads(self.read(".cursor/hooks.json"))["hooks"]["sessionStart"]]
        self.assertEqual(len(commands), 1)
        self.assertIn("coach-hook", commands[0])

    def test_will_not_overwrite_someone_elses_skill(self):
        other = self.home / ".copilot" / "skills" / "coach"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("not ours")
        lines = adapters.install(["vscode"])
        self.assertTrue(any(line.startswith("✗ vscode") for line in lines))
        self.assertEqual((other / "SKILL.md").read_text(), "not ours")


@unittest.skipIf(os.name == "nt", "the launcher is a shell script")
class LauncherTests(FakeHome):
    def run_launcher(self, *args):
        import subprocess
        return subprocess.run([str(adapters.launcher_path()), *args], input='{"prompt": "coach status"}',
                              capture_output=True, text=True)

    def test_hooks_run_through_the_launcher(self):
        adapters.install(["cursor"])
        self.assertTrue(os.access(adapters.launcher_path(), os.X_OK))
        out = self.run_launcher("claude", "prompt")
        self.assertEqual(out.returncode, 0, out.stderr)
        self.assertIn("agent-coach mode:", json.loads(out.stdout)["reason"])

    def test_launcher_survives_the_install_time_python_disappearing(self):
        with mock.patch.object(sys, "executable", "/gone/python3.99"):
            adapters.write_launcher()
        self.assertIn("/gone/python3.99", adapters.launcher_path().read_text())
        out = self.run_launcher("claude", "prompt")
        self.assertIn("agent-coach mode:", json.loads(out.stdout)["reason"])


class PackTests(FakeHome):
    def test_skill_zip_has_one_top_level_folder_and_portable_frontmatter(self):
        import zipfile
        out = adapters.pack(self.home / "skill.zip")
        with zipfile.ZipFile(out) as z:
            names = z.namelist()
            self.assertTrue(all(n.startswith("agent-coach/") for n in names))
            self.assertIn("agent-coach/references/index.md", names)
            self.assertIn("agent-coach/references/techniques/03-verification.md", names)
            self.assertFalse(any("REFRESH" in n or "sources" in n for n in names))
            front = z.read("agent-coach/SKILL.md").decode().split("---")[1]
        keys = {line.split(":")[0] for line in front.strip().splitlines()}
        self.assertLessEqual(keys, {"name", "description", "license", "compatibility", "metadata", "allowed-tools"})


if __name__ == "__main__":
    unittest.main()
