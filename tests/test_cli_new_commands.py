#!/usr/bin/env python3
"""Smoke tests for the newly-wired unified CLI subcommands."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CLI = REPO / "scripts" / "cost_watchdog.py"


def _run(args, home):
    env = dict(os.environ)
    env["HOME"] = home
    env["CW_LOG_DIR"] = str(Path(home) / ".cost-watchdog")
    env["CW_STATIC_ONLY"] = "1"
    env["CW_OFFLINE"] = "1"
    return subprocess.run([sys.executable, str(CLI), *args],
                          capture_output=True, text=True, env=env, cwd=str(REPO))


class TestNewCommands(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()

    def test_set_budget_priority_adjusts(self):
        r = _run(["set-budget", "5", "--priority=high"], self._tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("7.50", r.stdout)  # 5 * 1.5

    def test_learn_then_smart_estimate(self):
        r1 = _run(["learn", "summ", "0.85", "120000", "15"], self._tmp)
        self.assertEqual(r1.returncode, 0, r1.stderr)
        r2 = _run(["smart-estimate", "summ", "150000"], self._tmp)
        self.assertEqual(r2.returncode, 0, r2.stderr)
        self.assertIn("Estimate for summ", r2.stdout)

    def test_visualize_empty_and_with_data(self):
        # empty log
        r = _run(["visualize", "daily"], self._tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("Cost Report", r.stdout)
        # seed a usage row, then it should appear
        seed = (
            "import sys; sys.path.insert(0, 'scripts'); import usage_log; "
            "usage_log.append_usage({'model':'gpt-4o','provider':'openai',"
            "'input_tokens':1000,'output_tokens':200,'cost_total':0.012})"
        )
        env = dict(os.environ)
        env["CW_LOG_DIR"] = str(Path(self._tmp) / ".cost-watchdog")
        subprocess.run([sys.executable, "-c", seed], env=env, cwd=str(REPO), check=True)
        r2 = _run(["visualize", "providers"], self._tmp)
        self.assertIn("openai", r2.stdout)

    def test_visualize_rejects_bad_kind(self):
        r = _run(["visualize", "nope"], self._tmp)
        self.assertNotEqual(r.returncode, 0)  # argparse choices rejects it


if __name__ == "__main__":
    unittest.main()
