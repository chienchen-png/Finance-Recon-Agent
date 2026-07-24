---
name: finance-table-structuring
description: 'Use when: 用户说导入数据、整理文件、上传数据、帮我导入、扫描、扫描表格、分析结构、结构化、生成JSON。先让用户选择导入方式：扫描用户上传数据库，或指定系统路径扫描并确认导入清单；随后分类导入项目空间并生成结构化 JSON。'
argument-hint: '导入数据 / 扫描表格 / 结构化'
---

# Finance Table Structuring

## When To Use

- 用户将 Excel 放入 `用户上传数据库/` 后要求导入。
- 用户要求扫描已有依据文件或待处理数据。
- 核对前发现结构化 JSON 缺失。

## Procedure

1. 检查身份初始化、Python 环境、Office Viewer 和当前项目空间。
2. 用户说“导入数据”时，必须先用 `vscode_askQuestions` 询问导入方式：复制到 `用户上传数据库/` 后导入，或指定系统路径文件夹自动扫描。
3. 若用户选择指定系统路径，必须继续用 `vscode_askQuestions` 收集文件夹路径；扫描后展示候选 Excel 清单，并再次用 `vscode_askQuestions` 让用户确认导入清单，防止缺失或过多导入。
4. 外部路径只作为待导入来源；用户确认后，先把选中文件复制到 `用户上传数据库/`，再进入统一导入流程。
5. 通过结构化问卷确认文件分类。
6. 复制 Excel 到项目空间原数据目录，保留上传原件。
7. 调用 `工具脚本/excel_reader.py` 的 `read_schema_only()` 生成仅含 sheet、行列数和字段名的结构 JSON。
8. 需要完整导入问答、结构字段规范和输出路径时，加载 [full procedure](./references/full.md)。

## Safety

- 不修改 `${project_root}/数据库/原数据/` 中既有原始文件内容。
- 不在身份未初始化时导入财务数据。
- 指定系统路径扫描时，不得在用户确认导入清单前复制任何文件。
- 外部路径文件不得直接进入项目空间，必须先复制到 `用户上传数据库/` 形成统一入口记录。
- 不生成含原始单元格值、明细行或金额明细的 JSON；AI 只允许读取结构元数据。
