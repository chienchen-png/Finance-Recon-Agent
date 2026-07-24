---
name: 06-VSCode Agent基础工具调用
description: 检查、解释和验证 VS Code Agent 基础工具能力。用户说“检查工具”“工具不可用”“联网”“读写文件”“命令行”“搜索”“委派”“vscode 功能”时使用，确认 .agent.md 的 tools 授权并给出对应工具调用路径。
trigger:
  - "检查工具"
  - "工具不可用"
  - "无法调用工具"
  - "联网"
  - "读写文件"
  - "创建文件"
  - "编辑文件"
  - "命令行"
  - "终端"
  - "搜索"
  - "跟踪"
  - "委派"
  - "子Agent"
  - "VS Code 功能"
autonomous_trigger: true
---

# 06-VSCode Agent基础工具调用

## 触发条件

1. 用户反馈智能体无法调用联网、文件、命令行、读取、VS Code、搜索跟踪或委派工具。
2. 00-环境自检发现 `.github/agents/finance-recon-agent.agent.md` 的 `tools` 授权缺失。
3. 修改 Agent/Skill 设定后，需要验证基础工具配置是否完整。

## 前置条件

- [ ] 能读取 `.github/agents/finance-recon-agent.agent.md`
- [ ] 能使用当前会话已暴露的工具列表判断实际可用工具

> 本 Skill 不依赖 Python 环境，也不要求身份初始化。它只处理 VS Code Agent 自身能力配置。

---

## 步骤 1: 检查 Agent 授权入口

读取 `.github/agents/finance-recon-agent.agent.md` 的 YAML frontmatter，确认存在：

```yaml
tools:
  - read
  - edit
  - search
  - execute
  - web
  - agent
  - todo
  - vscode_askQuestions
  - memory
  - extensions
  - installExtension
  - newWorkspace
  - resolveMemory
  - runCommand
  - toolSearch
  - configurePythonEnvironment
  - getPythonEnvironmentInfo
  - getPythonExecutableCommand
  - installPythonPackage
```

必须理解：

- `tools` 是 VS Code 识别的工具授权字段。
- `python_tools` 只是业务 Python 脚本清单，不会授权 Copilot 工具。
- `copilot_tool_contract` 只是操作手册，不会授权 Copilot 工具。
- 若业务 Skill 位于 `技能核心库/*.md`，需要用 `read_file` 显式读取；它们不是标准 `.github/skills/<name>/SKILL.md` 注册 Skill。

若 `tools` 缺失或不完整，提示用户需要修复；若用户要求修复，使用 `replace_string_in_file` 修改 `.agent.md`。

---

## 步骤 2: 工具能力映射

| 能力 | 授权别名 | 首选工具 | 失败时处理 |
| --- | --- | --- | --- |
| 读取文件 | `read` | `read_file`, `list_dir` | 检查路径是否在工作区内，或改用 `file_search` 定位 |
| 创建文件/目录 | `edit` | `create_file`, `create_directory` | 文件已存在时改用 `replace_string_in_file` |
| 编辑文本文件 | `edit` | `replace_string_in_file` / `multi_replace_string_in_file` | 精确替换文本内容 |
| 搜索文件 | `search` | `file_search` | glob 太宽时缩小到目录 |
| 搜索内容 | `search` | `grep_search` | 优先用正则一次覆盖多个关键词 |
| VS Code 诊断 | `search` | `get_errors` | 修改后用于确认 Problems 是否新增 |
| 符号跟踪 | `search` | `vscode_listCodeUsages` | Python/TS 等语言服务可用时优先于全文搜索 |
| 语义重命名 | `search` | `vscode_renameSymbol` | 无 rename provider 时退回小范围 `replace_string_in_file` |
| 命令行 | `execute` | `run_in_terminal` | 一次性命令用 sync，长期服务用 async |
| 后台终端 | `execute` | `get_terminal_output`, `send_to_terminal`, `kill_terminal` | 只在工具返回后台 ID 或等待输入时调用 |
| Python 环境 | Python 扩展工具 | `configurePythonEnvironment`, `getPythonExecutableCommand`, `installPythonPackage` | 任何 Python 命令前先配置环境 |
| 联网抓取 | `web` | `fetch_webpage` | 指定 URL 时优先抓正文 |
| 子 Agent 委派 | `agent` | `runSubagent` | 多文件只读探索优先委派 `Explore` |
| 任务列表 | `todo` | `manage_todo_list` | 多步骤修复时维护状态 |
| 用户交互 | VS Code 工具 | `vscode_askQuestions` | 需要结构化确认时使用 |
| 扩展管理 | `extensions` / `installExtension` | 搜索/列出/安装 VS Code 扩展 | 扩展不存在时自动安装 |
| 工作区管理 | `newWorkspace` | 创建新工作区 | 用户要求新建项目空间 |
| VS Code 命令 | `runCommand` | 执行 VS Code 内置命令 | 需要调用 VS Code 原生功能 |
| 工具搜索 | `toolSearch` | 搜索可用工具及其参数签名 | 不确定工具名或参数时查询 |
| 记忆解析 | `resolveMemory` | 解析记忆引用获取完整内容 | 需要访问记忆系统深层引用 |

---

## 步骤 3: 最小验证流程

执行工具配置修复后，按以下顺序验证：

1. 用 `read_file` 或 PowerShell 读取 `.agent.md` frontmatter，确认 `tools` 字段完整。
2. 用 `grep_search` 搜索 `apply_patch|mcp_provides_tool`，确认没有把不存在的工具作为可调用工具要求。
3. 用 `file_search` 搜索 `技能核心库/*.md`，确认业务 Skill 文件可被读取。
4. 如需验证命令行能力，用 `run_in_terminal` 执行只读命令，例如列出当前目录。
5. 如需验证联网能力，用 `fetch_webpage` 抓取官方文档或用户指定网页。
6. 如需验证委派能力，用 `runSubagent` 调用 `Explore` 做只读检索。
7. 用 `file_search` 或 `list_dir` 检查 `工具脚本/临时脚本/` 是否存在；若不存在，创建目录并补充 `README.md` 与 `.gitkeep`。

---

## 禁止行为

- 不得把业务脚本名放入 `.agent.md` frontmatter 的 `tools` 字段。
- 不得引用当前工具列表中不存在的工具名。
- 不得声称业务目录下的 `技能核心库/*.md` 会自动注册为 VS Code Skill。
- 不得在没有用户确认的情况下执行破坏性文件操作。
