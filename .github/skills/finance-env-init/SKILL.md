---
name: finance-env-init
description: 'Use when: 用户说你好、hi、开始、启动、初始化、配置环境、检查环境、归零、重置、恢复出厂。自动完成财务 Agent 环境自检、Python 依赖、VS Code 工具授权检查、身份初始化、项目状态引导和系统归零。'
argument-hint: '你好 / 初始化 / 配置环境 / 检查环境 / 归零'
---

# Finance Environment Init

## When To Use

- 用户首次打开 Finance Recon Agent 或说“你好”“开始”“初始化”。
- 用户要求配置环境、检查环境、修复工具授权。
- 用户要求归零、重置、恢复出厂或清空运行数据。
- 任何财务业务 Skill 的前置检查失败，需要回到环境自检。

## Procedure

1. 优先检查 `.github/agents/finance-recon-agent.agent.md` frontmatter 的 `tools` 是否显式包含通用别名以及 VS Code 内置能力，例如 `read/edit/search/execute/web/agent/todo`，以及 `vscode_askQuestions/install_extension/memory/resolve_memory_file_uri/create_new_workspace/run_vscode_command/get_vscode_api/vscode_searchExtensions_internal` 与 Python 环境工具。
2. 检查 Python、`.venv`、`openpyxl`、`xlrd`、Office Viewer、报告模板、项目空间和身份初始化状态。
3. 若用户请求归零，执行双重确认后再清理运行数据。
4. 若需要完整步骤、输出模板或归零清单，加载 [full procedure](./references/full.md)。

## Tool Notes

- Python 相关操作前先使用 Python 环境工具配置解释器。
- 一次性命令使用终端 sync 模式。
- 需要用户身份、归零确认、扩展安装、下一步选择时必须使用结构化问卷 `vscode_askQuestions`。
- 扩展安装前优先使用 `vscode_searchExtensions_internal` 查找扩展，再调用 `install_extension`。
