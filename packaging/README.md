# 中文项目包 · Skills 插件候选

版本：0.2.0-alpha.2。包含项目目录工具、安全进度接续工具及使用指令。
没有远程 MCP、网络请求、生命周期钩子、登录流程或后台服务。

## 安装边界

此 ZIP 使用官方 portable Agent Plugins 格式：根目录 `plugin.json`，
工作流位于 `skills/chinese-project-kit/`。它不是公开插件目录中的已发布产品。
本地 Codex 支持通过 marketplace 安装；可用配套的本地市场包进行测试。
安装到 ChatGPT 网页版不自动获得本地工作区访问能力，也不提供跨设备同步。

实际操作需要 Python 3.10+ 和助手对目标工作区的访问授权。先在隔离测试目录使用，
不要直接在已有用户项目上试验。安装本包不授予删除、迁移、发布、合并或部署权限。

## 状态安全

- 复用已有计划；对旧仓库的索引位于源码仓库外。
- 每次写入要求 expected-revision，冲突时重新读取；不清除占用锁。
- 已有人工 `done` 保留，CLI 不接受直接把任务改为 `done`。
- 包含 2026-10-27 的 read_state 校验修复；不把损坏计划假报为成功接入。

## 真实验收尚未完成

安装检查、脚本测试不等于模型自动触发。只有在真实 Codex 中，分别给出三轮
不点名插件的自然语言开发请求，并保存加载技能、读写进度、产物和测试证据，
才能确认该环境的自动接续。没有这些证据时不得宣称全部验收或可上线。

源码：https://github.com/linzi1760/chinese-project-kit
打包格式：https://developers.openai.com/plugins/build/plugins
