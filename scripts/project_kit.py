#!/usr/bin/env python3
"""创建中文项目包并只读检查结构、工作记录和交付文件。仅使用标准库。"""
import argparse
import json
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath

SPEC_FILE = Path(__file__).resolve().parent.parent / "assets" / "项目包规范.json"
LAYOUT_CONTRACT = "chinese-project-kit-layout-v1"
WORKFLOW_CONTRACT = "chinese-project-kit-workflow-v1"
STATES = {"planned", "doing", "verifying", "done", "blocked", "cancelled"}


def read_json(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"无法读取有效的 JSON 文件：{path.name}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"JSON 文件的顶层必须为对象：{path.name}")
    return data


def relative_path(root, value):
    """拒绝盘符、绝对路径和父级跳转，并核对现有链接的真实目标。"""
    if not isinstance(value, str) or not value.strip():
        raise ValueError("项目内路径必须为非空字符串。")
    normalized = value.replace("\\", "/")
    parts = normalized.split("/")
    if (PurePosixPath(normalized).is_absolute() or PureWindowsPath(value).drive
            or any(part in {"", ".", ".."} for part in parts)
            or any(":" in part or "\x00" in part for part in parts)):
        raise ValueError(f"项目内路径无效或越界：{value}")
    candidate = root.joinpath(*parts)
    try:
        candidate.resolve().relative_to(root.resolve())
    except (ValueError, OSError, RuntimeError) as exc:
        raise ValueError(f"项目内路径或链接目标越界：{value}") from exc
    return candidate


def project_root(value):
    root = Path(value)
    if not root.is_absolute():
        raise ValueError("--root 必须是项目目录的绝对路径。")
    if root.exists() and not root.is_dir():
        raise ValueError("项目根路径必须是目录。")
    return root


def load_spec(root):
    spec = read_json(SPEC_FILE)
    if spec.get("contract") != LAYOUT_CONTRACT or spec.get("schema_version") != 1:
        raise ValueError("项目包规范合同或版本不匹配。")
    entries = spec.get("directories")
    if not isinstance(entries, list) or len(entries) != 8:
        raise ValueError("项目包规范必须定义八个目录。")
    directories = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("key"), str):
            raise ValueError("项目包目录规范无效。")
        key, path = entry["key"], entry.get("path")
        relative_path(root, path)
        if not key or key in directories or path in directories.values():
            raise ValueError("项目包目录键或路径重复。")
        directories[key] = path
    if not {"00_项目说明", "01_需求与设计", "03_工作区"}.issubset(directories.values()):
        raise ValueError("项目包规范缺少项目说明、需求设计或工作区目录。")
    scenarios = spec.get("scenarios")
    if not isinstance(scenarios, dict) or not scenarios:
        raise ValueError("项目包场景规范无效。")
    return directories, scenarios


def work_path(root, directories, scenarios, scenario):
    if scenario not in scenarios:
        raise ValueError(f"未知项目场景：{scenario}")
    entry = scenarios[scenario]
    if not isinstance(entry, dict) or not isinstance(entry.get("label"), str):
        raise ValueError("项目场景规范无效。")
    subdir = entry.get("work_subdir")
    relative_path(root, subdir)
    value = directories["workspace"] + "/" + subdir.replace("\\", "/")
    relative_path(root, value)
    return value


def write_json(path, data):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def init_project(root, scenario, goal, name=None):
    directories, scenarios = load_spec(root)
    work_dir = work_path(root, directories, scenarios, scenario)
    name = name or root.name
    if not isinstance(goal, str) or not goal.strip() or not name.strip():
        raise ValueError("项目名称和目标不能为空。")
    if root.exists() and any(root.iterdir()):
        raise ValueError("目标目录非空，拒绝创建；请提供全新或空目录。")
    root.mkdir(parents=True, exist_ok=True)
    for path in directories.values():
        relative_path(root, path).mkdir(parents=True, exist_ok=True)
    relative_path(root, work_dir).mkdir(parents=True, exist_ok=True)
    config = dict(contract=LAYOUT_CONTRACT, schema_version=1, name=name,
                  scenario=scenario, goal=goal, directories=directories,
                  work_dir=work_dir, delivery_files=[])
    write_json(root / "项目配置.json", config)
    write_json(root / "01_需求与设计" / "工作计划.json",
               dict(contract=WORKFLOW_CONTRACT, goal=goal, scenario=scenario,
                    status="planned", nodes=[]))
    overview = (f"# {name}\n\n场景：{scenarios[scenario]['label']}\n\n"
                f"目标：{goal}\n\n工作区：{work_dir}\n\n"
                "项目刚完成初始化。请补充需求、工作计划与验收标准后执行。\n\n"
                "结构检查通过仅说明目录与记录符合规范，不代表工作已完成。\n")
    requirements = (f"# 需求说明\n\n## 目标\n\n{goal}\n\n## 范围\n\n待补充。\n\n"
                    "## 输入材料\n\n待补充。\n\n## 验收标准\n\n待补充。\n")
    for path, content in [("00_项目说明/项目总览.md", overview),
                          ("01_需求与设计/需求说明.md", requirements)]:
        with relative_path(root, path).open("x", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    return ["项目包已创建；工作计划尚未执行。"]


def path_list(root, values, field):
    if not isinstance(values, list):
        raise ValueError(f"{field} 必须为项目相对文件路径数组。")
    return [relative_path(root, item) for item in values]


def check_workflow(root, config, delivery):
    plan = read_json(relative_path(root, "01_需求与设计/工作计划.json"))
    if plan.get("contract") != WORKFLOW_CONTRACT:
        raise ValueError("工作计划合同不匹配。")
    if plan.get("goal") != config["goal"] or plan.get("scenario") != config["scenario"]:
        raise ValueError("工作计划目标或场景与项目配置不一致。")
    if plan.get("status") not in STATES or not isinstance(plan.get("nodes"), list):
        raise ValueError("工作计划状态或节点数组无效。")
    nodes = plan["nodes"]
    ids, dependencies = set(), {}
    for node in nodes:
        if not isinstance(node, dict):
            raise ValueError("工作计划节点必须为对象。")
        node_id = node.get("id")
        if not isinstance(node_id, str) or not node_id.strip() or node_id in ids:
            raise ValueError("节点标识为空或重复。")
        if not isinstance(node.get("title"), str) or not node["title"].strip():
            raise ValueError(f"节点 {node_id} 标题必须为非空字符串。")
        ids.add(node_id)
        deps = node.get("depends_on")
        if not isinstance(deps, list) or any(not isinstance(dep, str) for dep in deps):
            raise ValueError(f"节点 {node_id} 的依赖必须为标识数组。")
        if len(set(deps)) != len(deps):
            raise ValueError(f"节点 {node_id} 存在重复依赖。")
        dependencies[node_id] = deps
        outputs = path_list(root, node.get("output_files"), f"节点 {node_id} 输出")
        evidence = path_list(root, node.get("evidence"), f"节点 {node_id} 证据")
        if node.get("status") not in STATES:
            raise ValueError(f"节点 {node_id} 状态无效。")
        if node.get("acceptance_status") not in {"pending", "passed", "failed"}:
            raise ValueError(f"节点 {node_id} 验收状态无效。")
        if node["status"] == "done":
            if node["acceptance_status"] != "passed" or not evidence:
                raise ValueError(f"节点 {node_id} 标为完成，但缺少验收通过记录或证据。")
            if any(not path.is_file() for path in outputs + evidence):
                raise ValueError(f"节点 {node_id} 标为完成，但输出或证据文件不存在。")
    if any(dep not in ids for deps in dependencies.values() for dep in deps):
        raise ValueError("工作计划存在指向未知节点的依赖。")
    states = {node["id"]: node["status"] for node in nodes}
    for node in nodes:
        if node["status"] == "done" and any(states[dep] != "done" for dep in dependencies[node["id"]]):
            raise ValueError(f"节点 {node['id']} 标为完成，但仍有未完成的前置依赖。")
    visited, active = set(), set()

    def visit(node_id):
        if node_id in active:
            raise ValueError("工作计划存在循环依赖。")
        if node_id in visited:
            return
        active.add(node_id)
        for dep in dependencies[node_id]:
            visit(dep)
        active.remove(node_id)
        visited.add(node_id)

    for node_id in ids:
        visit(node_id)
    if delivery and (not nodes or any(node["status"] != "done" for node in nodes)):
        raise ValueError("交付检查要求有非空工作节点，且所有节点均已完成。")
    if delivery and plan["status"] != "done":
        raise ValueError("交付检查要求总体工作计划状态为完成。")
    if plan["status"] == "done" and (not nodes or any(node["status"] != "done" for node in nodes)):
        raise ValueError("工作计划标为完成，但节点为空或仍有未完成节点。")


def check_project(root, delivery=False):
    directories, scenarios = load_spec(root)
    config = read_json(relative_path(root, "项目配置.json"))
    if config.get("contract") != LAYOUT_CONTRACT or config.get("schema_version") != 1:
        raise ValueError("项目配置合同或版本不匹配。")
    for field, label in [("name", "名称"), ("goal", "目标"), ("scenario", "场景")]:
        if not isinstance(config.get(field), str) or not config[field].strip():
            raise ValueError(f"项目{label}必须为非空字符串。")
    if config.get("directories") != directories:
        raise ValueError("项目目录配置与八目录规范不一致。")
    for path in directories.values():
        if not relative_path(root, path).is_dir():
            raise ValueError(f"缺少项目目录：{path}")
    expected = work_path(root, directories, scenarios, config["scenario"])
    relative_path(root, config.get("work_dir"))
    if config["work_dir"] != expected or not relative_path(root, expected).is_dir():
        raise ValueError("项目工作区与场景规范不一致或目录不存在。")
    for required in ["00_项目说明/项目总览.md", "01_需求与设计/需求说明.md"]:
        if not relative_path(root, required).is_file():
            raise ValueError(f"缺少项目说明文件：{required}")
    deliverables = path_list(root, config.get("delivery_files"), "交付文件")
    check_workflow(root, config, delivery)
    if delivery and (not deliverables or any(not path.is_file() for path in deliverables)):
        raise ValueError("交付检查要求至少一个交付文件，且所有登记文件均真实存在。")
    message = "交付记录与文件检查通过；此结果不评价内容质量。" if delivery else "项目结构检查通过；工作是否完成请另行检查交付记录。"
    return [message]


class ChineseParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError("命令参数不完整或不正确，请使用 --help 查看用法。")


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = ChineseParser(description="创建和检查中文项目包（检查操作只读）。")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=ChineseParser)
    create = commands.add_parser("init", help="向全新或空目录创建项目包")
    create.add_argument("--root", required=True, help="项目目录绝对路径")
    create.add_argument("--scenario", required=True, help="规范中的场景标识")
    create.add_argument("--goal", required=True, help="本次项目目标")
    create.add_argument("--name", help="项目名称；默认使用根目录名称")
    check = commands.add_parser("check", help="只读检查项目结构或交付记录")
    check.add_argument("--root", required=True, help="项目目录绝对路径")
    check.add_argument("--delivery", action="store_true", help="追加工作节点和交付文件检查")
    try:
        args = parser.parse_args(argv)
        root = project_root(args.root)
        messages = (init_project(root, args.scenario, args.goal, args.name)
                    if args.command == "init" else check_project(root, args.delivery))
        result, exit_code = {"ok": True, "messages": messages}, 0
    except (ValueError, OSError, RuntimeError, RecursionError) as exc:
        message = str(exc) if isinstance(exc, ValueError) else "文件系统操作失败，请检查路径、链接与读写权限。"
        result, exit_code = {"ok": False, "messages": [message]}, 1
    print(json.dumps(result, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
