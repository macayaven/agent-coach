import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git(cwd, *args):
    cmd = ["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid", "-C", str(cwd), *args]
    subprocess.run(cmd, check=True, capture_output=True)


@unittest.skipUnless(shutil.which("git"), "needs git")
class UpdateHandoffTests(unittest.TestCase):
    def test_update_finishes_with_the_code_it_just_pulled(self):
        """An update can replace the updater's own files, so the steps after the
        pull must run the new code, not the old code already in memory."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            upstream = tmp / "upstream"
            ignore = shutil.ignore_patterns(".git", "dist", "__pycache__", "results")
            shutil.copytree(ROOT, upstream, ignore=ignore)
            git(upstream, "init", "-q", "-b", "main")
            git(upstream, "add", "-A")
            git(upstream, "commit", "-q", "-m", "v1")
            git(tmp, "clone", "-q", str(upstream), "installed")

            # v2 changes what the post-pull step prints.
            cli = upstream / "bin" / "coach"
            text = cli.read_text()
            marker = '        adapters.update()\n        print(coachlib.status_line())\n'
            self.assertIn(marker, text)
            cli.write_text(text.replace(marker, marker + '        print("ran-new-code")\n'))
            git(upstream, "commit", "-q", "-am", "v2")

            env = dict(os.environ, HOME=str(tmp / "home"), AGENT_COACH_STATE=str(tmp / "state"))
            run = subprocess.run(
                [sys.executable, str(tmp / "installed" / "bin" / "coach"), "update"],
                capture_output=True, text=True, env=env,
            )
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("ran-new-code", run.stdout)


if __name__ == "__main__":
    unittest.main()
