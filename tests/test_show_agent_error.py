import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / ".github" / "scripts" / "show-agent-error.py"


def run(content=None):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "out.json"
        if content is not None:
            path.write_text(content)
        return subprocess.run([sys.executable, str(SCRIPT), str(path)], capture_output=True, text=True)


class ShowAgentErrorTests(unittest.TestCase):
    def test_rejected_key_in_a_json_array(self):
        out = run(json.dumps([
            {"type": "system", "subtype": "init"},
            {"type": "result", "is_error": True, "api_error_status": 401, "result": "Invalid API key · Fix external API key"},
        ]))
        self.assertEqual(out.returncode, 0)
        self.assertIn("Invalid API key", out.stdout)
        self.assertIn("ANTHROPIC_API_KEY secret", out.stdout)

    def test_denied_keyless_sign_in(self):
        out = run(json.dumps([{"type": "result", "is_error": True, "api_error_status": 401, "result": "Authentication failed"}]))
        self.assertIn("federation rule", out.stdout)

    def test_no_credit_in_json_lines(self):
        lines = [{"type": "system"}, {"type": "result", "is_error": True, "result": "Credit balance is too low"}]
        out = run("\n".join(json.dumps(m) for m in lines))
        self.assertIn("Add credit", out.stdout)

    def test_missing_or_empty_output_still_explains(self):
        self.assertIn("no output file", run(None).stdout)
        self.assertIn("no final result", run("[]").stdout)


if __name__ == "__main__":
    unittest.main()
