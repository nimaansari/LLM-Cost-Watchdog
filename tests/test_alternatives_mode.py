#!/usr/bin/env python3
"""
Regression test: cheaper-alternative suggestions must match the source model's
BILLING UNIT *and* MODE. Embeddings are priced per token (same unit as chat),
so a unit-only filter wrongly offered them as cheaper chat alternatives.
"""
import os
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
os.environ["CW_STATIC_ONLY"] = "1"

import _pricing  # noqa: E402
import optimized_calculator as oc  # noqa: E402
import smart_budget  # noqa: E402


class TestAlternativesMode(unittest.TestCase):
    def _assert_all_chat(self, slugs):
        for s in slugs:
            p = _pricing.get_price(s)
            self.assertIsNotNone(p, f"no price for suggested {s!r}")
            self.assertEqual(
                p.mode, "chat",
                f"{s!r} (mode={p.mode}) should not be offered as a chat alternative",
            )

    def test_optimized_calculator_only_same_mode(self):
        alts = oc.find_cheaper_alternatives("claude-sonnet-4-6", 100000, 20000, 0.5)
        self.assertTrue(alts, "expected at least one cheaper chat alternative")
        self._assert_all_chat(a["model"] for a in alts)

    def test_smart_budget_only_same_mode(self):
        mgr = smart_budget.SmartBudgetManager()
        alts = mgr.suggest_cheaper_alternatives("claude-sonnet-4-6", "general", 50)
        self._assert_all_chat(a["model"] for a in alts)


if __name__ == "__main__":
    unittest.main()
