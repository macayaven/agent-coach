"""Record what `coach audit` finds in audit-home/, for the behavioral evals to replay.

The eval sandbox can't read the plugin's evals/ folder or any .claude/ folder, so a live
collector can't see a planted user settings.json or /insights report. Run this after changing the collector or the fixture:

    python3 tests/fixtures/make_replay.py

tests/test_audit.py fails if the recording no longer matches the collector.
"""

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO / "bin"))
import audit  # noqa: E402

HOME = HERE / "audit-home"
OUT = HERE / "audit-replay.json"
VOLATILE = ("date",)  # differs per run; fixed in the recording


def relative(path):
    return str(Path(path).relative_to(REPO))


def build():
    result = audit.audit(repo=HOME / "work" / "app", home=HOME, overridden=True, managed=None)
    result["date"] = "2026-11-27"
    result["home"] = relative(HOME)
    for f in result["instruction_files"]:
        f["file"] = relative(f["file"])
    # The planted /insights report lives outside .claude/ so the agent's Read tool can open it.
    result["insights"] = {"path": "~/.claude/usage-data/report.html", "file": relative(HERE / "insights-report.html"),
                          "exists": True, "age_days": 2, "fresh": True}
    result["memory_hint"] = None
    return result


if __name__ == "__main__":
    OUT.write_text(json.dumps(build(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")
