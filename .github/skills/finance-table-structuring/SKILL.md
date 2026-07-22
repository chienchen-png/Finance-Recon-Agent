---
name: finance-table-structuring
description: 'Use when: 用户说导入数据、整理文件、上传数据、帮我导入、扫描、扫描表格、分析结构、结构化、生成JSON。将用户上传数据库中的 Excel 分类导入项目空间，并扫描为结构化 JSON。'
argument-hint: '导入数据 / 扫描表格 / 结构化'
---

# Finance Table Structuring

## When To Use

- 用户将 Excel 放入 `用户上传数据库/` 后要求导入。
- 用户要求扫描已有依据文件或待处理数据。
- 核对前发现结构化 JSON 缺失。

## Procedure

1. 检查身份初始化、Python 环境、Office Viewer 和当前项目空间。
2. 扫描 `用户上传数据库/` 或 `${project_root}/数据库/原数据/`。
3. 通过结构化问卷确认文件分类。
4. 复制 Excel 到项目空间原数据目录，保留上传原件。
5. 调用 `工具脚本/excel_reader.py` 和 `field_mapper.py` 生成 JSON。
6. 需要完整导入问答、结构字段规范和输出路径时，加载 [full procedure](./references/full.md)。

## Safety

- 不修改 `${project_root}/数据库/原数据/` 中既有原始文件内容。
- 不在身份未初始化时导入财务数据。
