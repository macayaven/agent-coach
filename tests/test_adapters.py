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


class InstallTests(FakeHome):
    def test_codex(self):
        (self.home / ".codex").mkdir()
        (self.home / ".codex" / "hooks.json").write_text(json.dumps(
            {"hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": "mine.sh"}]}]}}))
        adapters.install(["codex"])
        adapters.install(["codex"])  # twice: must not duplicate
        self.assertIn("Current mode: force", self.read(".codex/AGENTS.md"))
        groups = json.loads(self.read(".codex/hooks.json"))["hooks"]["UserPromptSubmit"]
        self.assertEqual(len(groups), 2)
        self.assertEqual(groups[0]["hooks"][0]["command"], "mine.sh")
        self.assertTrue((self.home / ".agents/skills/agent-coach/SKILL.md").exists())

        adapters.uninstall(["codex"])
        self.assertNotIn("Agent Coach", self.read(".codex/AGENTS.md"))
        groups = json.loads(self.read(".codex/hooks.json"))["hooks"]["UserPromptSubmit"]
        self.assertEqual([g["hooks"][0]["command"] for g in groups], ["mine.sh"])
        self.assertFalse((self.home / ".agents/skills/agent-coach").exists())

    def test_codex_respects_an_existing_override_file(self):
        (self.home / ".codex").mkdir()
        (self.home / ".codex" / "AGENTS.override.md").write_text("override rules\n")
        adapters.install(["codex"])
        self.assertIn("Agent Coach", self.read(".codex/AGENTS.override.md"))
        self.assertFalse((self.home / ".codex" / "AGENTS.md").exists())

    def test_mode_change_rewrites_static_files(self):
        adapters.install(["antigravity", "vscode"])
        coachlib.set_mode("suggest")
        adapters.refresh()
        self.assertIn("Current mode: suggest", self.read(".gemini/GEMINI.md"))
        self.assertIn("Current mode: suggest", self.read(".copilot/copilot-instructions.md"))
        coachlib.set_mode("off")
        adapters.refresh()
        self.assertIn("installed but off", self.read(".gemini/GEMINI.md"))
        self.assertNotIn("## force", self.read(".gemini/GEMINI.md"))

    def test_gemini_and_antigravity_share_one_block(self):
        adapters.install(["gemini", "antigravity"])
        self.assertEqual(self.read(".gemini/GEMINI.md").count(adapters.BEGIN), 1)
        hooks = json.loads(self.read(".gemini/settings.json"))["hooks"]
        self.assertIn("gemini prompt", hooks["BeforeAgent"][0]["hooks"][0]["command"])
        adapters.uninstall(["gemini"])
        self.assertIn("Agent Coach", self.read(".gemini/GEMINI.md"))  # antigravity still needs it
        adapters.uninstall(["antigravity"])
        self.assertNotIn("Agent Coach", self.read(".gemini/GEMINI.md"))

    def test_cursor_hooks(self):
        adapters.install(["cursor"])
        adapters.install(["cursor"])
        data = json.loads(self.read(".cursor/hooks.json"))
        self.assertEqual(data["version"], 1)
        self.assertEqual(len(data["hooks"]["sessionStart"]), 1)
        self.assertEqual(len(data["hooks"]["beforeSubmitPrompt"]), 1)
        adapters.uninstall(["cursor"])
        self.assertEqual(json.loads(self.read(".cursor/hooks.json"))["hooks"], {})

    def test_will_not_overwrite_someone_elses_skill(self):
        other = self.home / ".copilot" / "skills" / "coach"
        other.mkdir(parents=True)
        (other / "SKILL.md").write_text("not ours")
        lines = adapters.install(["vscode"])
        self.assertTrue(any(line.startswith("✗ vscode") for line in lines))
        self.assertEqual((other / "SKILL.md").read_text(), "not ours")


class PackTests(FakeHome):
    def test_skill_zip_has_one_top_level_folder_and_portable_frontmatter(self):
        import zipfile
        out = adapters.pack(self.home / "skill.zip")
        with zipfile.ZipFile(out) as z:
            self.assertEqual(sorted(z.namelist()), ["agent-coach/SKILL.md", "agent-coach/references/playbook.md"])
            front = z.read("agent-coach/SKILL.md").decode().split("---")[1]
        keys = {line.split(":")[0] for line in front.strip().splitlines()}
        self.assertLessEqual(keys, {"name", "description", "license", "compatibility", "metadata", "allowed-tools"})


if __name__ == "__main__":
    unittest.main()
