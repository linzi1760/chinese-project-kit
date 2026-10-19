# 用一个小任务试试中文项目包

[English](try-it.en.md) · [完整说明](../README.md)

用 AI 做过几个小项目后，资料、草稿和最终文件容易散在不同位置。中文项目包给中文独立开发者和个人知识工作者一个固定入口：先建立项目目录与计划骨架，再核对文件、依赖和交付记录。

它是 MIT 开源的 Python 命令行工具，也提供助手可读取的 Skill。只用 Python 标准库，无需安装第三方包。欢迎先用一个不含私人资料的小任务试试，再反馈哪里不顺手。

## 三步试用：整理一次 Python 学习练习

准备 Python 3.10+ 和 Git。以下命令在 **Windows PowerShell** 中运行；如果工具仓库已存在，直接进入它，不要重复克隆。目标项目目录必须全新或为空。

### 1. 取得工具

```powershell
git clone https://github.com/linzi1760/chinese-project-kit.git
cd chinese-project-kit
python scripts/project_kit.py --help
```

### 2. 建立项目骨架

在工具仓库根目录运行：

```powershell
$projectRoot = Join-Path (Split-Path -Parent (Get-Location).Path) "项目包首次试用"
python scripts/project_kit.py init --root "$projectRoot" --scenario learning --goal "完成一次 Python 文件读写练习并记录检查结果" --name "项目包首次试用"
```

打开生成项目里的 `00_项目说明/项目总览.md` 和 `01_需求与设计/工作计划.json`。应该看到八个中文外层目录、中文说明和未执行的空节点计划。此时练习还没有完成，也没有自动生成练习代码。

### 3. 检查结构，记录一次真实体验

```powershell
python scripts/project_kit.py check --root "$projectRoot"
```

成功时返回中文 JSON，包含 `"ok": true`，退出码为 `0`。这说明结构检查通过，**不代表学习任务或交付完成**。重复初始化应被拒绝；请不要为重试而删除已有工作。

接下来可以按 [README 的交付例子](../README.md#一个小例子学习项目怎样走到交付)登记一个练习节点，实际写代码、运行并记录检查证据，最后再登记成果。仅在工作确实完成、验收记录和交付文件都已登记后运行 `check --delivery`。不要为了让检查变绿而把未完成工作标为完成。

Ubuntu 用户可参考 [完整命令行说明](../README.md#命令行)，用系统实际的绝对路径替换示例路径；上面的 PowerShell 变量写法不能直接粘贴到 Bash。

## 它检查什么，哪些仍需要你判断

- 能做：生成目录和计划骨架；只读检查布局、依赖、状态、已登记证据与成果文件。
- 不做：替你写完项目、判断代码功能与事实是否正确、验证文档排版或学习效果。
- 不自动重组旧仓库，不迁移已有项目，也尚未接入 Flowkit。
- [既有 CI 记录](https://github.com/linzi1760/chinese-project-kit/actions/runs/38251794299)覆盖 Windows / Python 3.12 与 Ubuntu / Python 3.10 的 12 项测试。它们验证项目包生成与记录检查；macOS 和十类专业任务的完整工作链仍待验证。

## 把反馈留在项目 Issue

先搜索 [已有 Issues](https://github.com/linzi1760/chinese-project-kit/issues)，同一个问题补充复现信息即可。没有对应问题时，可以 [新建 Issue](https://github.com/linzi1760/chinese-project-kit/issues/new)，复制下面的模板：

```text
试用场景与目标：
系统 / Python 版本：
仓库版本（git rev-parse HEAD）：
运行命令（删去私人路径和信息）：
预期结果：
实际结果 / 错误信息：
最小复现步骤：
目录是否让你更容易继续工作？具体哪一步：
愿不愿意在下一个类似任务继续用？原因：
```

只提供可公开分享的脱敏最小样例。不要上传客户材料、个人项目原件、简历、账号凭据或含私人信息的完整日志。成功、失败以及“这套目录不适合我的任务”的反馈都值得记录；无需先提交完整项目。
