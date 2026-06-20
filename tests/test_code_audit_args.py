#!/usr/bin/env python3
"""Regression tests for code_audit argument-kind handling."""
import sys
import unittest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import code_audit  # noqa: E402


def _kinds(code):
    return {r.kind for r in code_audit.audit_source(code)}


class TestRecursionArgKinds(unittest.TestCase):
    def test_keyword_only_depth_is_recognized(self):
        # depth passed as a keyword-only arg must NOT trip the recursion check.
        code = (
            "def agent(prompt, *, depth):\n"
            "    if depth <= 0:\n"
            "        return\n"
            "    r = client.messages.create(max_tokens=10, messages=prompt)\n"
            "    return agent(r, depth=depth - 1)\n"
        )
        self.assertNotIn("unbounded_recursion_api", _kinds(code))

    def test_positional_only_depth_is_recognized(self):
        code = (
            "def agent(prompt, depth, /):\n"
            "    if depth <= 0:\n"
            "        return\n"
            "    r = client.messages.create(max_tokens=10, messages=prompt)\n"
            "    return agent(r, depth - 1)\n"
        )
        self.assertNotIn("unbounded_recursion_api", _kinds(code))

    def test_unbounded_recursion_still_flagged(self):
        code = (
            "def agent(prompt):\n"
            "    r = client.messages.create(max_tokens=10, messages=prompt)\n"
            "    return agent(r)\n"
        )
        self.assertIn("unbounded_recursion_api", _kinds(code))


if __name__ == "__main__":
    unittest.main()
