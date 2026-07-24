---
name: finance-data-reconciliation
description: 'Use when: 用户说核对、我要核对、核对数据、校验、比对、检查差异、核对Q1、核对Q2、核对Q3、核对Q4。按合同编号、销售人员、客户编码和金额执行三层匹配核对。'
argument-hint: '核对 / 核对Q1 / 检查差异'
---

# Finance Data Reconciliation

## When To Use

- 用户要求对季度分表和汇总表进行核对。
- 扫描结构化完成后，用户确认进入核对。
- 修正前发现尚未生成核对报告或修正方案。

## Procedure

1. 检查身份、Python 环境、依据文件、目标文件和结构元数据 JSON。
2. 若结构元数据 JSON 缺失，先触发 `finance-table-structuring`。
3. **V2.1: 检查工作状态** — 读取 `${project_root}/工作状态.json` → `current_working_copy`，若 `quarters_applied` 已含目标季度则警告重复核对。
4. 用结构化问卷确认依据文件、目标文件、匹配字段、金额字段和字段映射。
4. 调用 `工具脚本/reconciliation_engine.py`，仅传文件路径、sheet 名和字段列索引，由本地 Python 读取 Excel 并执行三层匹配。
5. 若核对目标是季度分表写入年度汇总表，修正方案必须使用聚合模式生成；默认 `aggregation_mode="contract_person"`，即按合同编号+销售人员聚合源金额。
6. 输出 AI 可读取的安全核对摘要和修正方案 JSON；核对摘要写入 `${project_root}/结果输出/核对结果/_工作文件/核对摘要/`，修正方案写入 `${project_root}/结果输出/核对结果/_工作文件/修正方案/`，不得写入 `核对结果/` 根层。
7. 修正方案中的 `target_row` 必须是 Excel 1-based 行号，`target_col` 必须是 0-based 列索引；用户报告展示 Excel 列字母和字段名，不只展示程序列索引。
8. **核对完成后自动触发 `finance-report-generation` 生成校验核对报告**（无需用户额外触发）。
9. 校验核对报告生成后，用 `vscode_askQuestions` 询问用户修正策略，路由至 `finance-fix-fill`。
10. 若校验核对报告生成失败，不得直接进入修正；必须用 `vscode_askQuestions` 提供"重试生成报告 / 暂停 / 查看错误摘要"选项。
11. 需要完整 6 问协议、差异分级或报告字段时，加载 [full procedure](./references/full.md)。

## Safety

- 本 Skill 只核对和生成报告/方案，不直接修改 Excel。
- 身份未初始化时拒绝执行。
- AI 不得读取 Excel 原数据、含明细行的 JSON，或将原始单元格值写入终端命令。
- 同一合同+销售人员存在多行源数据时，必须聚合求和后生成修正方案，不得生成逐行覆盖方案。
- 面向用户的 `核对结果/` 根层只保留报告目录和 `_工作文件/`，所有机器 JSON 必须进入 `_工作文件/` 分类子目录。
