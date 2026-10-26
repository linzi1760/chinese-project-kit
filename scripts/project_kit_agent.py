#!/usr/bin/env python3
"""中文项目包：已有项目只读识别、外部索引以及多轮 AI 安全任务更新。

只依赖标准库；不移动或重命名用户源码。调用者仍须决定何时使用本工具。
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from pathlib import Path

from project_kit import check_project, read_json

CONTRACT = "chinese-project-kit-agent-v1"
WORKFLOW = "chinese-project-kit-workflow-v1"
STATES = {"planned", "doing", "verifying", "blocked", "done", "cancelled"}
TRANSITIONS = {
    "planned": {"doing", "blocked", "cancelled"},
    "doing": {"verifying", "blocked", "cancelled"},
    "blocked": {"doing", "cancelled"},
    "verifying": {"doing", "blocked"},
    "done": set(),
    "cancelled": set(),
}


def root_path(value):
    path = Path(value).expanduser()
    if not path.exists() or not path.is_dir():
        raise ValueError("原项目目录不存在或不是目录。")
    return path.resolve(strict=True)


def state_path(root, override=None):
    if override:
        raw = Path(override).expanduser()
        if not raw.is_absolute():
            raise ValueError("--state 必须为绝对路径。")
    else:
        digest = hashlib.sha256(os.fsencode(str(root))).hexdigest()[:24]
        raw = Path.home() / ".chinese-project-kit" / "projects" / digest
    path = raw.resolve()
    if path == root or root in path.parents:
        raise ValueError("项目索引必须在源码仓库外，拒绝改写原项目。")
    return path


def identify(root):
    cfg = root / "项目配置.json"
    plan = root / "01_需求与设计" / "工作计划.json"
    if cfg.exists() or plan.exists():
        if not (cfg.is_file() and plan.is_file()):
            raise ValueError("检测到不完整的旧项目配置，拒绝自动接管。")
        check_project(root)
        return "native"
    return "existing"


def inspect(root):
    kind = identify(root)
    names = sorted(p.name for p in root.iterdir())
    return {"root": str(root), "kind": kind,
            "items": len(names), "entries": names[:30],
            "truncated": len(names) > 30, "source_modified": False}


def save_atomic(path, data):
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent),
                                         prefix=".pk-", suffix=".tmp", delete=False,
                                         newline="\n") as f:
            temp_path = Path(f.name)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path is not None:
            temp_path.unlink(missing_ok=True)


class WriteLock:
    """跨进程短时独占锁。异常退出遗留锁不会被静默抢占。"""
    def __init__(self, folder):
        self.path = folder / ".project-kit.lock"
        self.owned = False

    def __enter__(self):
        for _ in range(40):
            try:
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                with os.fdopen(fd, "w", encoding="ascii") as handle:
                    handle.write(str(os.getpid()))
                self.owned = True
                return self
            except FileExistsError:
                time.sleep(.05)
        raise ValueError(f"项目计划正被其他进程写入或存在遗留锁：{self.path.name}；未覆盖任何数据。")

    def __exit__(self, *_):
        if self.owned:
            self.path.unlink(missing_ok=True)


def adopt(root, custom_state):
    kind = identify(root)
    if kind == "native":
        return {"kind": kind, "created": False, "message": "标准项目包已具备计划文件，不额外创建第二套任务台账。"}
    state = state_path(root, custom_state)
    if state.exists():
        manifest, _ = read_state(root, state)
        return {"kind": kind, "created": False, "state": str(state),
                "root": manifest["source_root"], "message": "已接入；复用原索引。"}
    state.parent.mkdir(parents=True, exist_ok=True)
    # Do not follow a preexisting symbolic link or overwrite an occupied location.
    state.mkdir(exist_ok=False)
    try:
        save_atomic(state / "manifest.json", {"contract": CONTRACT, "source_root": str(root),
                                               "mode": "external-sidecar", "schema_version": 1})
        save_atomic(state / "plan.json", {"contract": WORKFLOW, "revision": 0,
                                          "status": "planned", "nodes": []})
    except BaseException:
        for item in state.iterdir():
            if item.is_file():
                item.unlink()
        state.rmdir()
        raise
    return {"kind": kind, "created": True, "state": str(state),
            "source_modified": False, "message": "已建立仓库外索引；原项目文件未修改。"}


def read_state(root, state):
    manifest = read_json(state / "manifest.json")
    plan = read_json(state / "plan.json")
    if (manifest.get("contract") != CONTRACT or manifest.get("source_root") != str(root)
            or manifest.get("mode") != "external-sidecar"
            or plan.get("contract") != WORKFLOW):
        raise ValueError("索引格式或项目路径不匹配；拒绝读取/覆盖。")
    return manifest, plan


def locate(root, custom_state):
    kind = identify(root)
    if kind == "native":
        path = root / "01_需求与设计" / "工作计划.json"
        if root not in path.resolve().parents:
            raise ValueError("项目计划链接指向仓库之外；拒绝操作。")
        plan = read_json(path)
        if plan.get("contract") != WORKFLOW:
            raise ValueError("项目计划合同不匹配。")
        return kind, path
    state = state_path(root, custom_state)
    read_state(root, state)
    return kind, state / "plan.json"


def read_plan(root, custom_state):
    kind, path = locate(root, custom_state)
    plan = read_json(path)
    validate_plan(plan)
    return kind, path, plan


def validate_plan(plan):
    revision = plan.get("revision", 0)
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 0:
        raise ValueError("任务修订号非法。")
    nodes = plan.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError("任务节点列表非法。")
    ids = []
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str) or not node["id"].strip():
            raise ValueError("任务标识非法。")
        if not isinstance(node.get("status"), str) or node["status"] not in STATES:
            raise ValueError("任务状态非法。")
        ids.append(node["id"])
    if len(ids) != len(set(ids)):
        raise ValueError("任务标识重复。")
    return revision


def status(root, custom_state):
    kind, _, plan = read_plan(root, custom_state)
    nodes = plan["nodes"]
    return {"kind": kind, "root": str(root), "revision": plan.get("revision", 0),
            "nodes": nodes, "unfinished": [n["id"] for n in nodes if n.get("status") not in {"done", "cancelled"}],
            "message": "状态仅来自持久记录；不等于 AI 已完成专业验收。"}


def change_task(root, custom_state, revision, action, task_id, title=None, new_status=None):
    if not isinstance(revision, int) or revision < 0:
        raise ValueError("更新必须指定非负 expected-revision。")
    if not task_id.strip() or len(task_id) > 80:
        raise ValueError("任务 ID 必须为 1–80 字符。")
    kind, plan_path = locate(root, custom_state)
    with WriteLock(plan_path.parent):
        if kind == "existing":
            # Check that a different project did not replace the index while waiting for lock.
            read_state(root, plan_path.parent)
        plan = read_json(plan_path)
        current = validate_plan(plan)
        if current != revision:
            raise ValueError(f"修订号冲突：预期 {revision}，实际 {current}；请重新读取状态后重试。")
        node = next((n for n in plan["nodes"] if n["id"] == task_id), None)
        if action == "add":
            if node is not None or not title or not title.strip():
                raise ValueError("任务重复或任务标题为空。")
            node = {"id": task_id, "title": title.strip(), "depends_on": [],
                    "status": "planned", "output_files": [], "evidence": [],
                    "acceptance_status": "pending"}
            plan["nodes"].append(node)
        elif action == "set":
            if node is None or new_status not in STATES:
                raise ValueError("任务不存在或状态值不合法。")
            previous = node.get("status")
            if new_status == "done":
                raise ValueError("不能仅凭 AI 的文字声明把任务设为 done；需要另行执行真实验收。")
            if new_status not in TRANSITIONS.get(previous, set()):
                raise ValueError(f"不允许从 {previous} 跳转为 {new_status}。")
            node["status"] = new_status
        else:
            raise ValueError("未知任务操作。")
        plan["revision"] = current + 1
        save_atomic(plan_path, plan)
        return {"kind": kind, "revision": plan["revision"], "task": task_id,
                "status": node["status"], "source_modified": kind == "native"}


def run(argv=None):
    parser = argparse.ArgumentParser(description="中文项目包 AI 接续层（只读识别 / 无损接入 / 乐观锁任务管理）")
    sub = parser.add_subparsers(dest="command", required=True)
    for cmd in ("inspect", "adopt", "status", "task-add", "task-set"):
        p = sub.add_parser(cmd)
        p.add_argument("--root", default=".", help="项目根目录，默认当前工作目录")
        if cmd != "inspect":
            p.add_argument("--state", help="已有项目的外部索引目录；默认为用户主目录下的固定路径")
        if cmd in ("task-add", "task-set"):
            p.add_argument("--expected-revision", type=int, required=True)
            p.add_argument("--id", required=True)
        if cmd == "task-add":
            p.add_argument("--title", required=True)
        if cmd == "task-set":
            p.add_argument("--status", required=True)
    args = parser.parse_args(argv)
    try:
        root = root_path(args.root)
        custom_state = getattr(args, "state", None)
        if args.command == "inspect":
            data = inspect(root)
        elif args.command == "adopt":
            data = adopt(root, custom_state)
        elif args.command == "status":
            data = status(root, custom_state)
        else:
            data = change_task(root, custom_state, args.expected_revision,
                               "add" if args.command == "task-add" else "set",
                               args.id, getattr(args, "title", None), getattr(args, "status", None))
        print(json.dumps({"ok": True, **data}, ensure_ascii=False))
        return 0
    except (ValueError, OSError, UnicodeError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "reason": str(exc)}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    sys.exit(run())
