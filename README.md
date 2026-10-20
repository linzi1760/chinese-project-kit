# 中文项目包 · Chinese Project Kit

[![Tests](https://github.com/linzi1760/chinese-project-kit/actions/workflows/tests.yml/badge.svg)](https://github.com/linzi1760/chinese-project-kit/actions/workflows/tests.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)](#快速开始)
[![MIT License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

把代码、文档、研究、学习和日常工作保存成一套容易找到、接着做、核对交付的中文项目包。

本项目提供一个可被助手读取的 [Skill](SKILL.md)，以及可独立运行的 Python 命令行脚本：**十种场景入口、八个统一中文外层目录、一份工作计划和只读检查**。脚本只使用 Python 标准库，不需要安装第三方包。

## 能帮你解决什么

- **启动时少想一遍目录。**给出目标、场景和保存位置，即可建立中文总览、需求说明和计划骨架。
- **继续工作时能找到入口。**原始资料、编辑中的文件、正式成果与验证证据各有位置，工作区保留唯一编辑源。
- **交付时能核对记录。**检查计划依赖、状态和登记文件，发现缺少证据登记、缺失成果或尚未完成的前置工作。

适合独立开发者、个人知识工作者，以及希望把助手产物保存为完整项目的人。混合任务可以共用一个项目包。现有代码仓库、单文件小修改和普通问答沿用原有结构，不自动重组目录。

当前版本是项目组织与记录检查工具。初始化不会生成可运行的应用、完成研究或产出专业文档；这些工作需要随后按任务执行。

## 快速开始

运行要求：Python 3.10+；克隆和更新仓库需要 Git。项目包测试已通过 Windows / Python 3.12 与 Ubuntu / Python 3.10 的 GitHub Actions 验证，macOS 尚未实测。

```sh
git clone https://github.com/linzi1760/chinese-project-kit.git
cd chinese-project-kit
python scripts/project_kit.py --help
```

下面以 PowerShell 创建一个学习项目。请在仓库根目录执行；示例项目保存在仓库旁边，目标目录必须全新或为空。

```powershell
$projectRoot = Join-Path (Split-Path -Parent (Get-Location).Path) "Python学习笔记"
python scripts/project_kit.py init --root "$projectRoot" --scenario learning --goal "用三次练习理解 Python 文件读写" --name "Python学习笔记"
python scripts/project_kit.py check --root "$projectRoot"
```

检查成功返回中文 JSON，退出码为 `0`：

```json
{"ok": true, "messages": ["项目结构检查通过；工作是否完成请另行检查交付记录。"]}
```

此时计划是 `planned`，节点为空。项目结构已建立，学习工作仍待开展。重复初始化或对非空目录执行 `init` 会拒绝操作，避免覆盖已有文件。

## 在助手中一句话调用

将完整仓库放入所用助手支持的个人 Skills 目录后，可以明确给出目标和保存范围：

> 使用 $chinese-project-kit，把我的 Python 文件读写学习任务保存为中文项目包。场景选 learning，目标是用三次练习理解文件读写，保存到【实际绝对路径】，先建立需求与未执行的工作计划。

CLI 可以独立使用。助手模式需要工具支持读取 `SKILL.md`；专业任务还需要该助手具备相应的编码、文档、分析或设计能力。单独提到 Skill 名称不会自动创建项目。

### 可选：Windows 目录联接

对于支持 `~/.agents/skills` 发现目录的工具，可以把完整仓库保存在自己选择的磁盘位置，并在发现目录建立联接。在克隆后的仓库根目录执行：

```powershell
$skillSource = (Get-Location).Path
$skillDiscovery = Join-Path $env:USERPROFILE ".agents\skills"
New-Item -ItemType Directory -Path $skillDiscovery -Force | Out-Null
New-Item -ItemType Junction -Path (Join-Path $skillDiscovery "chinese-project-kit") -Target $skillSource
```

如果同名发现目录已经存在，先核对现有安装；不要用覆盖或删除命令替换它。不同助手的发现目录可能不同，请选择其实际支持的位置。

## 安装与更新

安装就是取得完整仓库，保留 `SKILL.md`、`assets`、`references` 和 `scripts` 的相对位置。无需 `pip install`，也无需专用安装器。

更新时，在工具仓库根目录执行：

```sh
git pull --ff-only
```

如果自己修改过仓库文件，应先保留改动并处理与上游的差异。更新工具不会迁移已有项目包；已有项目的目录或合同差异需单独核对，不会自动搬文件或套用新模板。

## 命令行

下面的 `ABSOLUTE_PROJECT_PATH` 需要替换为项目根目录的实际绝对路径。跨平台使用时，请采用所在系统的绝对路径写法。

```sh
python scripts/project_kit.py init --root "ABSOLUTE_PROJECT_PATH" --scenario code --goal "实现并验证目标功能" --name "我的项目"
python scripts/project_kit.py check --root "ABSOLUTE_PROJECT_PATH"
python scripts/project_kit.py check --root "ABSOLUTE_PROJECT_PATH" --delivery
```

| 命令 | 实际行为 |
| --- | --- |
| `init` | 向全新或空目录写入八目录、场景工作区、项目配置、两份中文说明和空节点计划；`--name` 可省略 |
| `check` | 只读核对布局合同、场景、工作区、必需文件、节点字段、依赖及项目内路径 |
| `check --delivery` | 追加核对总体计划和所有节点为 `done`、验收通过、证据与输出存在，以及至少一个真实交付文件 |

检查或创建失败时返回 `{"ok": false, "messages": [...]}`，退出码为 `1`。已有链接的真实目标不得越出项目根目录，计划内路径也不能使用绝对路径、盘符或 `..` 跳转。

## 统一结构

目录唯一规范是 [assets/项目包规范.json](assets/项目包规范.json)，脚本从该文件读取：

```text
项目名称/
├─ 项目配置.json
├─ 00_项目说明/
│  └─ 项目总览.md
├─ 01_需求与设计/
│  ├─ 需求说明.md
│  └─ 工作计划.json
├─ 02_资料与输入/
├─ 03_工作区/
│  └─ 场景工作子目录/
├─ 04_成果与交付/
├─ 05_验证与验收/
├─ 06_过程记录/
└─ 99_历史归档/
```

| 目录 | 放什么 |
| --- | --- |
| `00_项目说明` | 目标、使用方法和继续工作的入口 |
| `01_需求与设计` | 范围、约束、方案与工作计划 |
| `02_资料与输入` | 原始资料及来源信息 |
| `03_工作区` | 唯一可编辑的源码、草稿、分析文件 |
| `04_成果与交付` | 正式成果、版本交付包或指向工作区的交付索引 |
| `05_验证与验收` | 检查报告与实际验收证据 |
| `06_过程记录` | 关键决定、进度和必要的下一步 |
| `99_历史归档` | 已停用资料与历史交付 |

小项目允许目录为空，不为填满目录增加文档。代码框架内部的 `src`、`tests`、`package.json` 等按技术要求保留；统一的是外层入口。交付清单可以指向工作区中的实际成果，避免建立两份持续编辑的源码。

## 十种场景

| 场景 ID | 场景 | 工作子目录 |
| --- | --- | --- |
| `code` | 代码开发 | `源码` |
| `office` | 办公文档 | `文档草稿` |
| `data` | 数据分析 | `数据处理` |
| `research` | 研究整理 | `研究笔记` |
| `content` | 内容创作 | `内容草稿` |
| `design` | 产品与设计 | `设计工作` |
| `business` | 商业运营 | `运营工作` |
| `learning` | 学习训练 | `学习练习` |
| `planning` | 计划执行 | `执行工作` |
| `daily` | 日常事务 | `事务处理` |

场景入口规定文件组织与交付方向，详细说明见 [场景与交付](references/场景与交付.md)。它们不代表十类专业任务都已完成端到端验证。

## 一个小例子：学习项目怎样走到交付

以上学习项目初始化后，可以把一个实际练习登记到 `01_需求与设计/工作计划.json`。下面是一份仍未执行的计划：

```json
{
  "contract": "chinese-project-kit-workflow-v1",
  "goal": "用三次练习理解 Python 文件读写",
  "scenario": "learning",
  "status": "planned",
  "nodes": [
    {
      "id": "practice_1",
      "title": "完成并检查第一次文件读写练习",
      "depends_on": [],
      "status": "planned",
      "output_files": ["03_工作区/学习练习/练习一.py"],
      "evidence": [],
      "acceptance_status": "pending"
    }
  ]
}
```

接下来真正编写并运行练习，把检查过程和结论写入 `05_验证与验收/练习一检查.md`。实际验收通过后，再将节点的 `evidence` 登记为该相对路径，`acceptance_status` 改为 `passed`，节点状态改为 `done`。前置依赖也必须已经完成。

三次练习应分别登记实际节点。全部完成并验收后，将总体计划状态设为 `done`，在 `项目配置.json` 的 `delivery_files` 中登记需要交付的真实文件，再运行 `check --delivery`。只更新状态或创建一份空证据文件，不能代替学习效果的实际检查。

节点状态支持 `planned`、`doing`、`verifying`、`done`、`blocked`、`cancelled`；验收状态支持 `pending`、`passed`、`failed`。项目布局合同为 `chinese-project-kit-layout-v1`，版本为 `1`。路径均相对项目包根目录。

## 已验证范围

当前 12 项标准库单元测试在本地 Windows 通过，并通过 [Windows / Python 3.12 与 Ubuntu / Python 3.10 的 CI](https://github.com/linzi1760/chinese-project-kit/actions/runs/38251794299)。测试覆盖十种场景初始化及结构检查、中文和空格路径、非空目录与重复初始化保护、只读检查、路径及链接越界、依赖环、伪完成、缺失交付文件和 UTF-8 输出。另完成一个 `learning` 项目包试用。

在仓库根目录复核测试：

```sh
python -m unittest discover -s scripts -p "test_project_kit.py" -v
```

这些证据支持项目包生成和记录检查能力。脚本不判断代码功能、事实正确性、文档排版、设计效果或学习成果；这些需由实际测试、阅读、渲染或相应专业验收确认。macOS 及各专业场景的完整工作链仍待验证。

## Flowkit 状态

目前提供 [Flowkit 映射说明](references/Flowkit映射.md)，**尚未接入 Flowkit**。通用计划与 Flowkit 自有执行合同不同，当前没有可运行的转换适配器或自动同步能力。

目录和工作计划可以作为可视化设计的输入；画出图不等于调度、持久执行或验收流程已经支持。实际接入需另行实现并核验适配器。

## 贡献与许可

欢迎提交可复现的问题、场景规则改进、跨平台验证或检查器修复。问题说明请包含系统、Python 版本、运行命令、预期与实际结果，以及脱敏后的最小样例。代码修改应附对应测试；新增场景也应说明工作目录和真实验收方式。

项目采用 [MIT License](LICENSE)。贡献内容应有可公开分发的权利，请不要提交私人项目、账号信息或真实业务资料。

## 介绍方式参考

本 README 的组织方式参考了两项成熟模板工具的官方材料，中文说明和项目规则按本仓库的实际能力重新编写：

- [Copier 官方 README](https://github.com/copier-org/copier)：借鉴先说明价值和受众、再给最小模板实例的顺序；把工具更新与既有项目更新分开说明。
- [Copier 官方介绍](https://copier.readthedocs.io/en/stable/)：借鉴渐进展示基本概念和更复杂能力的方式，先让读者运行简单命令。
- [Cookiecutter 官方 README](https://github.com/cookiecutter/cookiecutter)：借鉴用具体生成例子展示输入与输出，并为使用者和贡献者分别提供入口。

本项目独立维护，没有使用 Copier 或 Cookiecutter 作为运行依赖，也与它们没有官方合作关系。这里借鉴的是介绍结构，不宣称具备它们的模板渲染、钩子或项目迁移能力。

## AI 多轮项目接续（v0.2 候选功能）

在支持加载 `SKILL.md` 的 AI 助手里，这个工具可作为项目工作的*按需*辅助：用户只说“继续项目”，助手可以判断是否需要读取既有计划，但是否会自动触发取决于助手环境，**当前尚无 ChatGPT 网页版插件自动调用的真实验收**。

新增标准库命令行入口 `scripts/project_kit_agent.py`：

```sh
python scripts/project_kit_agent.py inspect --root "ABSOLUTE_PROJECT_PATH"
python scripts/project_kit_agent.py adopt --root "ABSOLUTE_PROJECT_PATH"
python scripts/project_kit_agent.py status --root "ABSOLUTE_PROJECT_PATH"
# 根据 status 的 revision 新增或更新任务
python scripts/project_kit_agent.py task-add --root "ABSOLUTE_PROJECT_PATH" --expected-revision 0 --id T-01 --title "开展一个具体任务"
```

- 新项目继续使用原 `工作计划.json`，不会复制第二套计划；旧仓库使用仓库**外部**索引，避免搬文件或改代码。
- 写入要求预期修订号，防止多个 AI 或进程用旧计划覆盖较新的任务进度。
- 当前拒绝直接声明 `done`；仅支持推进到 `verifying`，真正完成还需要专业验收与记录。
- 默认项目索引位于当前用户主目录下的 `.chinese-project-kit/projects/`，包含项目绝对路径和任务元信息，仅在明确调用 `adopt` 时创建。

完整规则和限制见 [AI 自动接续与验收](references/自动接续与验收.md)。
