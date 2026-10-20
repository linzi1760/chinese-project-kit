"""CLI integration tests: native and existing repos, multi-session state, and safety."""
import hashlib
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

BASE = Path(__file__).resolve().parent
AGENT = BASE / "project_kit_agent.py"
CORE = BASE / "project_kit.py"
import project_kit as core_module
import project_kit_agent as agent_module


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="中文项目包多轮 空格 ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.legacy = self.base / "现有产品仓库"
        self.legacy.mkdir()
        (self.legacy / "src").mkdir()
        (self.legacy / "src" / "main.py").write_text("print('hello')\n", encoding="utf-8")
        (self.legacy / "README.md").write_text("# real legacy project\n", encoding="utf-8")
        (self.legacy / "binary.dat").write_bytes(b"\x00\xfe\xff\x01")
        self.state = self.base / "仓库外进度索引"

    def call(self, cmd, *params, ok=True, script=AGENT):
        buffer = io.StringIO()
        module = core_module if script == CORE else agent_module
        with contextlib.redirect_stdout(buffer):
            returncode = module.main([cmd, *map(str, params)]) if script == CORE else module.run([cmd, *map(str, params)])
        self.assertEqual(returncode, 0 if ok else 1, buffer.getvalue())
        data = json.loads(buffer.getvalue())
        self.assertEqual(data["ok"], ok, data)
        return data

    def snapshot(self, root):
        return {str(f.relative_to(root)): hashlib.sha256(f.read_bytes()).hexdigest()
                for f in root.rglob("*") if f.is_file()}

    def setup_native(self):
        root = self.base / "新项目"
        self.call("init", "--root", root, "--scenario", "code", "--goal", "连续完成三轮开发", script=CORE)
        return root

    def adopt(self):
        return self.call("adopt", "--root", self.legacy, "--state", self.state)

    def status(self, root=None, state=None):
        root = root or self.legacy
        params = ["--root", root]
        if state is not None or root == self.legacy:
            params.extend(["--state", state or self.state])
        return self.call("status", *params)

    def add(self, root, revision, task, title, state=None, ok=True):
        params = ["--root", root, "--expected-revision", revision, "--id", task, "--title", title]
        if state is not None or root == self.legacy:
            params.extend(["--state", state or self.state])
        return self.call("task-add", *params, ok=ok)

    def set_state(self, root, revision, task, next_state, state=None, ok=True):
        params = ["--root", root, "--expected-revision", revision, "--id", task, "--status", next_state]
        if state is not None or root == self.legacy:
            params.extend(["--state", state or self.state])
        return self.call("task-set", *params, ok=ok)

    def test_existing_inspection_changes_nothing(self):
        before = self.snapshot(self.legacy)
        r = self.call("inspect", "--root", self.legacy)
        self.assertEqual(r["kind"], "existing")
        self.assertEqual(self.snapshot(self.legacy), before)
        self.assertFalse(self.state.exists())

    def test_existing_adopt_outside_source(self):
        before = self.snapshot(self.legacy)
        r = self.adopt()
        self.assertTrue(r["created"])
        self.assertTrue((self.state / "manifest.json").is_file())
        self.assertEqual(self.snapshot(self.legacy), before)
        self.assertEqual(self.status()["revision"], 0)

    def test_adopt_repeat_reuses_same_state(self):
        self.adopt()
        self.add(self.legacy, 0, "T1", "已经登记的任务")
        before = self.snapshot(self.state)
        out = self.adopt()
        self.assertFalse(out["created"])
        self.assertEqual(self.snapshot(self.state), before)

    def test_inside_source_refused(self):
        inside = self.legacy / ".project-kit"
        result = self.call("adopt", "--root", self.legacy, "--state", inside, ok=False)
        self.assertIn("仓库外", result["reason"])
        self.assertFalse(inside.exists())

    def test_unadopted_status_does_not_write(self):
        r = self.call("status", "--root", self.legacy, "--state", self.state, ok=False)
        self.assertFalse(r["ok"])
        self.assertFalse(self.state.exists())

    def test_wrong_source_reuse_prevented(self):
        self.adopt()
        other = self.base / "另一个仓库"
        other.mkdir()
        r = self.call("status", "--root", other, "--state", self.state, ok=False)
        self.assertIn("不匹配", r["reason"])

    def test_three_rounds_resume_without_recreating(self):
        self.adopt()
        r1 = self.add(self.legacy, 0, "T-01", "第一轮：修复已知问题")
        self.assertEqual(r1["revision"], 1)
        r2 = self.set_state(self.legacy, 1, "T-01", "doing")
        self.assertEqual(r2["revision"], 2)
        # Fresh invocation simulates a separate AI conversation reading prior work.
        r3 = self.status()
        self.assertEqual(r3["nodes"][0]["status"], "doing")
        self.add(self.legacy, 2, "T-02", "第二轮：补充测试")
        self.set_state(self.legacy, 3, "T-02", "doing")
        r4 = self.status()
        self.assertEqual(len(r4["nodes"]), 2)
        self.add(self.legacy, 4, "T-03", "第三轮：交付检查")
        final = self.status()
        self.assertEqual(final["revision"], 5)
        self.assertEqual(len(final["nodes"]), 3)
        self.assertEqual(final["unfinished"], ["T-01", "T-02", "T-03"])

    def test_stale_revision_preserves_newer_progress(self):
        self.adopt()
        self.add(self.legacy, 0, "A", "开始")
        self.add(self.legacy, 1, "B", "接着做")
        self.set_state(self.legacy, 2, "A", "doing")
        fail = self.set_state(self.legacy, 2, "B", "doing", ok=False)
        self.assertIn("修订号冲突", fail["reason"])
        self.set_state(self.legacy, 3, "B", "doing")
        self.assertEqual([n["status"] for n in self.status()["nodes"]], ["doing", "doing"])

    def test_parallel_writes_only_one_success(self):
        self.adopt()
        self.add(self.legacy, 0, "A", "A")
        self.add(self.legacy, 1, "B", "B")
        common = [sys.executable, str(AGENT), "task-set", "--root", str(self.legacy),
                  "--state", str(self.state), "--expected-revision", "2"]
        procs = [subprocess.Popen(common + ["--id", task, "--status", "doing"],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                  text=True, encoding="utf-8") for task in ("A", "B")]
        seen = []
        for proc in procs:
            stdout, stderr = proc.communicate(timeout=20)
            self.assertEqual(stderr, "")
            seen.append((proc.returncode, json.loads(stdout)))
        self.assertEqual(sorted(code for code, _ in seen), [0, 1])
        self.assertEqual(self.status()["revision"], 3)
        waiting = next(n["id"] for n in self.status()["nodes"] if n["status"] == "planned")
        self.set_state(self.legacy, 3, waiting, "doing")
        self.assertEqual(self.status()["revision"], 4)
        self.assertTrue(all(n["status"] == "doing" for n in self.status()["nodes"]))

    def test_unverified_done_rejected(self):
        self.adopt()
        self.add(self.legacy, 0, "T", "待验收功能")
        self.set_state(self.legacy, 1, "T", "doing")
        self.set_state(self.legacy, 2, "T", "verifying")
        fail = self.set_state(self.legacy, 3, "T", "done", ok=False)
        self.assertIn("真实验收", fail["reason"])
        self.assertEqual(self.status()["revision"], 3)
        self.assertEqual(self.status()["nodes"][0]["status"], "verifying")

    def test_invalid_transition_rejected(self):
        self.adopt()
        self.add(self.legacy, 0, "T", "任务")
        self.set_state(self.legacy, 1, "T", "verifying", ok=False)
        self.assertEqual(self.status()["revision"], 1)

    def test_duplicate_task_refused(self):
        self.adopt()
        self.add(self.legacy, 0, "T", "任务")
        self.add(self.legacy, 1, "T", "重复任务", ok=False)
        self.assertEqual(len(self.status()["nodes"]), 1)

    def test_native_new_project_uses_original_workflow(self):
        root = self.setup_native()
        before = self.snapshot(root)
        self.assertEqual(self.call("inspect", "--root", root)["kind"], "native")
        out = self.call("adopt", "--root", root)
        self.assertFalse(out["created"])
        self.assertEqual(before, self.snapshot(root))
        self.add(root, 0, "T-01", "落实需求")
        self.set_state(root, 1, "T-01", "doing")
        self.call("check", "--root", root, script=CORE)
        self.assertEqual(self.status(root)["revision"], 2)
        self.assertEqual(len(self.status(root)["nodes"]), 1)
        self.assertFalse((root / "manifest.json").exists())
        self.assertFalse((root / "plan.json").exists())

    def test_native_stale_revision_refused(self):
        root = self.setup_native()
        self.add(root, 0, "T-01", "任务 1")
        self.add(root, 0, "T-02", "任务 2", ok=False)
        self.assertEqual(self.status(root)["revision"], 1)

    def test_native_false_done_rejected(self):
        root = self.setup_native()
        self.add(root, 0, "T-01", "执行任务")
        self.set_state(root, 1, "T-01", "done", ok=False)
        self.call("check", "--root", root, script=CORE)

    def test_native_partial_config_refused(self):
        root = self.base / "损坏的旧项目"
        root.mkdir()
        (root / "项目配置.json").write_text("{}", encoding="utf-8")
        self.call("inspect", "--root", root, ok=False)
        self.assertEqual(len(list(root.iterdir())), 1)

    def test_legacy_never_changes_original_source(self):
        before = self.snapshot(self.legacy)
        self.adopt()
        self.add(self.legacy, 0, "T", "编写功能")
        self.set_state(self.legacy, 1, "T", "doing")
        self.set_state(self.legacy, 2, "T", "verifying")
        self.assertEqual(self.snapshot(self.legacy), before)

    def test_invalid_manifest_rejected(self):
        self.adopt()
        manifest = self.state / "manifest.json"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        data["source_root"] = "/a/stranger"
        manifest.write_text(json.dumps(data), encoding="utf-8")
        self.call("adopt", "--root", self.legacy, "--state", self.state, ok=False)
        self.call("task-add", "--root", self.legacy, "--state", self.state,
                  "--expected-revision", "0", "--id", "T", "--title", "不允许", ok=False)

    def test_existing_write_lock_refuses_to_overwrite(self):
        self.adopt()
        (self.state / ".project-kit.lock").write_text("stale", encoding="ascii")
        self.call("task-add", "--root", self.legacy, "--state", self.state,
                  "--expected-revision", "0", "--id", "A", "--title", "任务", ok=False)
        self.assertEqual(self.status()["revision"], 0)


if __name__ == "__main__":
    unittest.main()
