"""Regression: repeating adopt must not report a corrupt sidecar as reusable."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import project_kit_agent as agent


class ReuseValidationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="项目接续校验 ")
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name).resolve()
        self.root, self.state = base / "source", base / "state"
        self.root.mkdir()
        (self.root / "keep.bin").write_bytes(b"\x00\xffkeep")
        agent.adopt(self.root, str(self.state))
        self.good = json.loads((self.state / "plan.json").read_text(encoding="utf-8"))

    def snapshot(self):
        return {str(p.relative_to(self.root.parent)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in self.root.parent.rglob("*") if p.is_file()}

    def write_plan(self, plan):
        (self.state / "plan.json").write_text(json.dumps(plan), encoding="utf-8")

    def assert_rejected_unchanged(self, plan, error):
        self.write_plan(plan)
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, error):
            agent.adopt(self.root, str(self.state))
        self.assertEqual(self.snapshot(), before)
        self.assertFalse((self.state / ".project-kit.lock").exists())

    def test_repeat_adopt_rejects_invalid_revision(self):
        for revision in (True, -1, "1", None):
            with self.subTest(revision=revision):
                self.assert_rejected_unchanged({**self.good, "revision": revision}, "修订号")

    def test_repeat_adopt_rejects_invalid_nodes(self):
        for nodes, error in (
            (None, "节点列表"), ({}, "节点列表"), ([None], "标识"),
            ([{"id": "T", "status": "not-a-status"}], "状态"),
            ([{"id": "T", "status": None}], "状态"),
            ([{"id": "T", "status": "planned"}] * 2, "重复"),
        ):
            with self.subTest(nodes=nodes):
                self.assert_rejected_unchanged({**self.good, "nodes": nodes}, error)

    def test_repeat_adopt_keeps_legacy_defaults_and_valid_statuses(self):
        plan = {"contract": agent.WORKFLOW,
                "nodes": [{"id": s, "status": s} for s in sorted(agent.STATES)],
                "extension": {"preserve": True}}
        self.write_plan(plan)
        before = self.snapshot()
        self.assertFalse(agent.adopt(self.root, str(self.state))["created"])
        self.assertEqual(agent.status(self.root, str(self.state))["revision"], 0)
        self.assertEqual(self.snapshot(), before)

    def test_repeat_adopt_cli_fails_as_json_without_mutation(self):
        self.write_plan({**self.good, "nodes": [{"id": "T", "status": "unknown"}]})
        before = self.snapshot()
        result = subprocess.run(
            [sys.executable, str(Path(agent.__file__)), "adopt", "--root", str(self.root),
             "--state", str(self.state)], capture_output=True, text=True, encoding="utf-8", timeout=10)
        self.assertEqual(result.returncode, 1, result.stdout)
        self.assertEqual(result.stderr, "")
        output = json.loads(result.stdout)
        self.assertFalse(output["ok"])
        self.assertIn("状态", output["reason"])
        self.assertEqual(self.snapshot(), before)


if __name__ == "__main__":
    unittest.main()
