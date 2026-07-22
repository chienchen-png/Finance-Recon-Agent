---
name: vscode-agent-tools
description: 'Use when: 用户说检查工具、工具不可用、无法调用工具、联网、读写文件、创建文件、编辑文件、命令行、终端、搜索、跟踪、委派、子Agent、VS Code 功能。检查 VS Code Agent 工具授权与调用路径。'
argument-hint: '检查工具 / 工具不可用 / 联网 / 命令行 / 委派'
---

# VS Code Agent Tools

## When To Use

- 用户反馈 Finance Recon Agent 无法调用基础工具。
- 需要确认 `.agent.md` 是否授权 `read/edit/search/execute/web/agent/todo`。
- 需要解释或验证联网、文件、终端、VS Code 功能、搜索跟踪或子 Agent 委派。

## Procedure

1. 检查 `.github/agents/finance-recon-agent.agent.md` frontmatter 的 `tools` 字段。
2. 确认 `python_tools` 没有占用 VS Code 的工具授权字段。
3. 按能力域选择当前会话实际可用工具。
4. 搜索并修正旧工具名，例如 `replace_string_in_file`、`multi_replace_string_in_file`、`mcp_provides_tool_pylanceRunCodeSnippet`。
5. 需要完整工具映射、验证流程和禁止行为时，加载 [full procedure](./references/full.md)。

## Safety

- 只检查和修复 Agent/Skill 配置，不处理财务数据。
- 不引用当前工具列表中不存在的工具。
