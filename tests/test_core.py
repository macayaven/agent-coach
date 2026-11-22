import datetime
import importlib.util
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "bin"))
import coachlib  # noqa: E402

spec = importlib.util.spec_from_file_location("coach_hook", ROOT / "hooks" / "coach_hook.py")
coach_hook = importlib.util.module_from_spec(spec)
spec.loader.exec_module(coach_hook)


class IsolatedState(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.env = {k: os.environ.pop(k, None) for k in ("AGENT_COACH_MODE", "EVAL_AGENT_COACH_MODE")}
        os.environ["AGENT_COACH_STATE"] = self.tmp.name

    def tearDown(self):
        os.environ.pop("AGENT_COACH_STATE", None)
        for k, v in self.env.items():
            if v is not None:
                os.environ[k] = v
        self.tmp.cleanup()


class ModeTests(IsolatedState):
    def test_defaults_to_force(self):
        self.assertEqual(coachlib.get_mode(), "force")

    def test_set_mode_persists_and_on_means_force(self):
        coachlib.set_mode("suggest")
        self.assertEqual(coachlib.get_mode(), "suggest")
        coachlib.set_mode("on")
        self.assertEqual(coachlib.get_mode(), "force")

    def test_env_overrides_saved_mode(self):
        coachlib.set_mode("off")
        os.environ["EVAL_AGENT_COACH_MODE"] = "suggest"
        try:
            self.assertEqual(coachlib.get_mode(), "suggest")
        finally:
            del os.environ["EVAL_AGENT_COACH_MODE"]

    def test_rejects_unknown_mode(self):
        with self.assertRaises(ValueError):
            coachlib.set_mode("loud")

    def test_parse_toggle(self):
        cases = {
            "coach off": "off",
            "  /coach Suggest ": "suggest",
            "/agent-coach:coach force": "force",
            "coach on": "force",
            "coach status": "status",
            "coach off and also fix the bug": None,
            "please coach me": None,
        }
        for prompt, want in cases.items():
            self.assertEqual(coachlib.parse_toggle(prompt), want, prompt)


class RenderTests(unittest.TestCase):
    def test_render_carries_only_the_current_modes_rules(self):
        text = coachlib.render("suggest")
        self.assertIn("suggest mode", text)
        self.assertIn(str(coachlib.SKILL_DIR), text)
        self.assertIn("## suggest", text)
        self.assertIn("## Always", text)
        self.assertNotIn("## force", text)
        self.assertNotIn("description:", text)  # skill frontmatter is stripped

    def test_staleness(self):
        today = datetime.date(2026, 11, 22)
        self.assertFalse(coachlib.is_stale(datetime.date(2026, 11, 1), today))
        self.assertTrue(coachlib.is_stale(datetime.date(2026, 8, 1), today))
        self.assertTrue(coachlib.is_stale(None, today))

    def test_shipped_index_has_a_reviewed_date(self):
        self.assertIsNotNone(coachlib.techniques_reviewed())


class ContextBudgetTests(unittest.TestCase):
    """The coach must stay cheap. Budgets are in estimated tokens (chars / 4)."""

    def size(self, path):
        return coachlib.estimate_tokens(path.read_text(encoding="utf-8"))

    def test_always_on_rules(self):
        self.assertLessEqual(coachlib.estimate_tokens(coachlib.render("force")), 450)
        self.assertLessEqual(coachlib.estimate_tokens(coachlib.render("suggest")), 350)
        self.assertLessEqual(coachlib.estimate_tokens(coachlib.render_off_stub()), 100)

    def test_per_prompt_reminders_are_one_short_line(self):
        for text in coachlib.REMINDERS.values():
            self.assertLessEqual(coachlib.estimate_tokens(text), 25)
            self.assertNotIn("\n", text)

    def test_reference_files(self):
        self.assertLessEqual(self.size(coachlib.INDEX), 1300)
        self.assertLessEqual(self.size(coachlib.RULES), 700)
        for path in coachlib.TECHNIQUES.glob("*.md"):
            self.assertLessEqual(self.size(path), 600, path.name)

    def test_index_and_technique_files_match(self):
        listed = set(re.findall(r"^- `([\w-]+)`", coachlib.INDEX.read_text(encoding="utf-8"), re.MULTILINE))
        files = {p.stem for p in coachlib.TECHNIQUES.glob("*.md")}
        self.assertEqual(listed, files)
        self.assertGreaterEqual(len(files), 10)


class ClaudeHookTests(IsolatedState):
    def test_session_start_injects_rules(self):
        out = coach_hook.handle("claude", "session-start", {"source": "startup"})
        ctx = out["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "SessionStart")
        self.assertIn("force mode", ctx)
        self.assertIn("## force", ctx)

    def test_prompt_gets_mode_reminder(self):
        coachlib.set_mode("suggest")
        out = coach_hook.handle("claude", "prompt", {"prompt": "fix the login bug"})
        self.assertIn("agent-coach: suggest", out["hookSpecificOutput"]["additionalContext"])

    def test_toggle_is_handled_without_the_model(self):
        out = coach_hook.handle("claude", "prompt", {"prompt": "coach off"})
        self.assertEqual(out["decision"], "block")
        self.assertEqual(coachlib.get_mode(), "off")

    def test_off_adds_nothing(self):
        coachlib.set_mode("off")
        self.assertIsNone(coach_hook.handle("claude", "prompt", {"prompt": "fix it"}))
        self.assertIsNone(coach_hook.handle("claude", "session-start", {}))


class OtherToolHookTests(IsolatedState):
    def test_codex_matches_claude_shape(self):
        out = coach_hook.handle("codex", "prompt", {"prompt": "add retries"})
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")

    def test_gemini_uses_before_agent_and_deny(self):
        out = coach_hook.handle("gemini", "prompt", {"prompt": "add retries"})
        self.assertEqual(out["hookSpecificOutput"]["hookEventName"], "BeforeAgent")
        out = coach_hook.handle("gemini", "prompt", {"prompt": "coach suggest"})
        self.assertEqual(out["decision"], "deny")
        self.assertEqual(coachlib.get_mode(), "suggest")

    def test_cursor_session_start_adds_context(self):
        out = coach_hook.handle("cursor", "session-start", {"session_id": "x"})
        self.assertIn("force mode", out["additional_context"])

    def test_cursor_switch_persists_and_reaches_the_model(self):
        out = coach_hook.handle("cursor", "prompt", {"prompt": "coach off"})
        self.assertEqual(out, {"continue": True})
        self.assertEqual(coachlib.get_mode(), "off")


if __name__ == "__main__":
    unittest.main()
