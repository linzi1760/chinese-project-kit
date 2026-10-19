# Try Chinese Project Kit on one small task

[中文](try-it.zh-CN.md) · [Full README, in Chinese](../README.md)

AI-assisted work can leave source material, drafts, and final files in different places. Chinese Project Kit gives Chinese-speaking independent developers and individual knowledge workers a consistent place to resume: a project structure and plan skeleton, plus checks for files, dependencies, and delivery records.

It is an MIT-licensed standalone Python CLI, with an optional assistant-readable Skill. It uses only the Python standard library. The generated folders, documents, and CLI messages are in Chinese. Try it with a small task that contains no private material, and tell us where the structure gets in your way.

## Three steps: organize one Python learning exercise

You need Python 3.10+ and Git. These commands use **Windows PowerShell**. If you already have the tool repository, enter it rather than cloning it again. The new project directory must not exist or must be empty.

### 1. Get the tool

```powershell
git clone https://github.com/linzi1760/chinese-project-kit.git
cd chinese-project-kit
python scripts/project_kit.py --help
```

### 2. Create a project skeleton

Run from the tool repository root:

```powershell
$projectRoot = Join-Path (Split-Path -Parent (Get-Location).Path) "项目包首次试用"
python scripts/project_kit.py init --root "$projectRoot" --scenario learning --goal "完成一次 Python 文件读写练习并记录检查结果" --name "项目包首次试用"
```

The goal means “complete one Python file-reading/writing exercise and record the checks.” Open `00_项目说明/项目总览.md` and `01_需求与设计/工作计划.json` inside the generated project. Expect eight Chinese top-level directories, introductory documents, and a planned workflow with no task nodes yet. The exercise has not been completed, and no exercise code has been generated.

### 3. Check the structure and record your experience

```powershell
python scripts/project_kit.py check --root "$projectRoot"
```

A successful check returns Chinese JSON containing `"ok": true` and exit code `0`. This confirms a structure check, **not completion of the learning task or its deliverables**. Repeated initialization should be refused; do not delete existing work just to retry.

Next, follow the [README delivery example](../README.md#一个小例子学习项目怎样走到交付): register an exercise node, actually write and run the exercise, record its verification evidence, and register the output. Run `check --delivery` only after the work and its records are complete. Do not mark unfinished work as done just to pass a check.

Ubuntu users can follow the [CLI reference](../README.md#命令行) with an actual absolute path for their system. The PowerShell variable syntax above cannot be pasted directly into Bash.

## Scope and evidence

- Creates folders and a plan skeleton; performs read-only checks of layout, dependencies, statuses, and registered evidence/output files.
- Does not complete the project or judge code behavior, factual accuracy, document layout, or learning outcomes.
- Does not reorganize existing repositories or migrate old projects. Flowkit integration is not implemented.
- The [existing CI record](https://github.com/linzi1760/chinese-project-kit/actions/runs/38251794299) covers 12 tests on Windows / Python 3.12 and Ubuntu / Python 3.10. This supports package generation and record checking. macOS and complete professional workflows across all ten scenarios remain unverified.

## Share a small, reproducible report

Search [existing Issues](https://github.com/linzi1760/chinese-project-kit/issues) first. Add useful reproduction details to a matching issue; otherwise [open an issue](https://github.com/linzi1760/chinese-project-kit/issues/new) using this template:

```text
Scenario and goal:
Operating system / Python version:
Repository revision (git rev-parse HEAD):
Command (remove private paths and information):
Expected result:
Actual result / error:
Minimal reproduction steps:
Did the structure make it easier to resume? Which step helped or got in the way?
Would you use it for another similar task? Why?
```

Share only a sanitized minimal example that you have the right to publish. Do not upload customer materials, private project originals, résumés, account credentials, or full logs containing personal information. Successful attempts, failures, and cases where the structure does not fit are all useful; a complete project upload is unnecessary.
