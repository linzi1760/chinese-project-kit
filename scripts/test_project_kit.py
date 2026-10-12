"""通过真实 CLI 验证项目包；所有写入均限定在专用临时目录。"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).with_name("project_kit.py")
SPEC = json.loads((SCRIPT.parent.parent / "assets" / "项目包规范.json").read_text(encoding="utf-8-sig"))


class ProjectKitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="项目包测试 空格 ")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "私人项目 空格"

    def cli(self, *args, ok=True):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)],
                                capture_output=True, encoding="utf-8",
                                env={**os.environ, "PYTHONIOENCODING": "utf-8"})
        self.assertEqual(result.returncode, 0 if ok else 1, result.stdout + result.stderr)
        response = json.loads(result.stdout)
        self.assertEqual(response["ok"], ok)
        self.assertTrue(response["messages"])
        self.assertEqual(result.stderr, "")
        return response

    def init(self, scenario="code", root=None):
        root = root or self.root
        self.cli("init", "--root", root, "--scenario", scenario,
                 "--goal", "在中文目录完成一项可验证工作", "--name", "私人项目")
        return root

    def config(self):
        return json.loads((self.root / "项目配置.json").read_text(encoding="utf-8"))

    def plan(self):
        return json.loads((self.root / "01_需求与设计/工作计划.json").read_text(encoding="utf-8"))

    def write(self, relative, data):
        (self.root / relative).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def nodes(self, *nodes):
        plan = self.plan()
        plan["nodes"] = list(nodes)
        self.write("01_需求与设计/工作计划.json", plan)

    def node(self, node_id="制作", **changes):
        node = dict(id=node_id, title="执行并验收工作", depends_on=[], output_files=[], evidence=[],
                    acceptance_status="pending", status="planned")
        node.update(changes)
        return node

    def snapshot(self, root=None):
        root = root or self.root
        return {str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()}

    def completed_node(self):
        output = "04_成果与交付/成果.txt"
        evidence = "05_验证与验收/检查结果.txt"
        (self.root / output).write_text("可交付成果", encoding="utf-8")
        (self.root / evidence).write_text("人工检查记录", encoding="utf-8")
        node = self.node(status="done", acceptance_status="passed",
                         output_files=[output], evidence=[evidence])
        self.nodes(node)
        return node, output, evidence

    def test_ten_scenarios_with_chinese_spaces(self):
        self.assertEqual(len(SPEC["scenarios"]), 10)
        for scenario, entry in SPEC["scenarios"].items():
            with self.subTest(scenario=scenario):
                root = self.init(scenario, self.base / ("中文项目 空格 " + scenario))
                self.cli("check", "--root", root)
                self.assertTrue((root / "03_工作区" / entry["work_subdir"]).is_dir())
                self.assertEqual({p.name for p in root.iterdir() if p.is_dir()},
                                 {item["path"] for item in SPEC["directories"]})
                plan = json.loads((root / "01_需求与设计/工作计划.json").read_text(encoding="utf-8"))
                self.assertEqual((plan["status"], plan["nodes"]), ("planned", []))

    def test_nonempty_directory_and_repeat_init_preserve_bytes(self):
        self.root.mkdir()
        (self.root / "不要改我.txt").write_bytes(b"sentinel\x00\xff")
        before = self.snapshot()
        self.cli("init", "--root", self.root, "--scenario", "code", "--goal", "目标", ok=False)
        self.assertEqual(self.snapshot(), before)
        empty_root = self.base / "空项目"
        self.init(root=empty_root)
        before = self.snapshot(empty_root)
        self.cli("init", "--root", empty_root, "--scenario", "code", "--goal", "另一个目标", ok=False)
        self.assertEqual(self.snapshot(empty_root), before)

    def test_check_is_read_only_in_success_and_failure(self):
        self.init()
        before = self.snapshot()
        self.cli("check", "--root", self.root)
        self.cli("check", "--root", self.root, "--delivery", ok=False)
        self.assertEqual(self.snapshot(), before)

    def test_path_traversal_and_windows_drive_rejected(self):
        self.init()
        for value in ["../外部.txt", "03_工作区/../../外部.txt", "C:\\外部.txt",
                      "C:外部.txt", "/外部.txt", "\\\\主机\\共享\\文件.txt"]:
            with self.subTest(path=value):
                self.nodes(self.node(output_files=[value]))
                self.cli("check", "--root", self.root, ok=False)
        config = self.config()
        config["delivery_files"] = ["../外部.txt"]
        self.nodes(self.node())
        self.write("项目配置.json", config)
        self.cli("check", "--root", self.root, ok=False)

    def test_dependency_cycle_and_missing_dependency(self):
        self.init()
        self.nodes(self.node("甲", depends_on=["乙"]), self.node("乙", depends_on=["甲"]))
        self.cli("check", "--root", self.root, ok=False)
        self.nodes(self.node(depends_on=["不存在"]))
        self.cli("check", "--root", self.root, ok=False)

    def test_false_done_rejected(self):
        self.init()
        self.nodes(self.node(status="done", acceptance_status="passed"))
        self.cli("check", "--root", self.root, ok=False)
        self.nodes(self.node(status="done", acceptance_status="passed", evidence=["05_验证与验收/不存在.txt"]))
        self.cli("check", "--root", self.root, ok=False)
        node, _, _ = self.completed_node()
        node["acceptance_status"] = "failed"
        self.nodes(node)
        self.cli("check", "--root", self.root, ok=False)

    def test_delivery_missing_files_and_success(self):
        self.init()
        self.cli("check", "--root", self.root, "--delivery", ok=False)
        _, output, _ = self.completed_node()
        self.cli("check", "--root", self.root)
        self.cli("check", "--root", self.root, "--delivery", ok=False)
        config = self.config()
        config["delivery_files"] = ["04_成果与交付/不存在.txt"]
        self.write("项目配置.json", config)
        self.cli("check", "--root", self.root, "--delivery", ok=False)
        config["delivery_files"] = [output]
        self.write("项目配置.json", config)
        self.cli("check", "--root", self.root, "--delivery", ok=False)
        plan = self.plan()
        plan["status"] = "done"
        self.write("01_需求与设计/工作计划.json", plan)
        before = self.snapshot()
        self.cli("check", "--root", self.root, "--delivery")
        self.assertEqual(self.snapshot(), before)
        self.nodes(self.node(status="doing"))
        self.cli("check", "--root", self.root, "--delivery", ok=False)

    def test_node_title_and_unfinished_dependency_rejected(self):
        self.init()
        for title in ["", None, 3]:
            with self.subTest(title=title):
                self.nodes(self.node(title=title))
                self.cli("check", "--root", self.root, ok=False)
        node, _, _ = self.completed_node()
        node["depends_on"] = ["前置"]
        self.nodes(self.node("前置"), node)
        self.cli("check", "--root", self.root, ok=False)

    def test_required_structure_contract_and_scenario(self):
        self.init()
        config = self.config()
        for field, value in [("contract", "错误合同"), ("schema_version", 9),
                             ("scenario", "unknown"), ("work_dir", "03_工作区/错误工作区")]:
            with self.subTest(field=field):
                broken = dict(config)
                broken[field] = value
                self.write("项目配置.json", broken)
                self.cli("check", "--root", self.root, ok=False)
        self.write("项目配置.json", config)
        (self.root / "99_历史归档").rmdir()
        self.cli("check", "--root", self.root, ok=False)

    def test_link_escaping_project_rejected(self):
        self.init()
        outside = self.base / "外部资料"
        outside.mkdir()
        external_file = outside / "证据.txt"
        external_file.write_bytes(b"do not change")
        link = self.root / "03_工作区/外部链接"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError:
            if os.name != "nt":
                self.skipTest("当前环境不能创建目录链接。")
            result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                                    capture_output=True)
            self.assertEqual(result.returncode, 0, "无法创建临时目录联接。")
        self.nodes(self.node(evidence=["03_工作区/外部链接/证据.txt"]))
        self.cli("check", "--root", self.root, ok=False)
        self.assertEqual(external_file.read_bytes(), b"do not change")

    def test_relative_root_and_invalid_arguments_return_json(self):
        self.cli("init", "--root", "相对目录", "--scenario", "code", "--goal", "目标", ok=False)
        self.cli("init", "--root", self.root, "--scenario", "unknown", "--goal", "目标", ok=False)
        self.assertFalse(self.root.exists())
        self.cli("check", ok=False)

    def test_cli_outputs_utf8_with_non_unicode_environment(self):
        result = subprocess.run([sys.executable, str(SCRIPT), "check"],
                                capture_output=True, encoding="utf-8",
                                env={**os.environ, "PYTHONIOENCODING": "ascii"})
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stderr, "")
        response = json.loads(result.stdout)
        self.assertFalse(response["ok"])
        self.assertIn("命令参数", response["messages"][0])


if __name__ == "__main__":
    unittest.main()
