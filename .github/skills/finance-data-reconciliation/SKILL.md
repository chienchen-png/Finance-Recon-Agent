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
3. 用结构化问卷确认依据文件、目标文件、匹配字段、金额字段和字段映射。
4. 调用 `工具脚本/reconciliation_engine.py`，仅传文件路径、sheet 名和字段列索引，由本地 Python 读取 Excel 并执行三层匹配。
5. 输出 AI 可读取的安全核对摘要和修正方案 JSON。
6. **核对完成后自动触发 `finance-report-generation` 生成校验核对报告**（无需用户额外触发）。
7. 校验核对报告生成后，用 `vscode_askQuestions` 询问用户修正策略，路由至 `finance-fix-fill`。
8. 若校验核对报告生成失败，不得直接进入修正；必须用 `vscode_askQuestions` 提供"重试生成报告 / 暂停 / 查看错误摘要"选项。
9. 需要完整 6 问协议、差异分级或报告字段时，加载 [full procedure](./references/full.md)。

## Safety

- 本 Skill 只核对和生成报告/方案，不直接修改 Excel。
- 身份未初始化时拒绝执行。
- AI 不得读取 Excel 原数据、含明细行的 JSON，或将原始单元格值写入终端命令。
