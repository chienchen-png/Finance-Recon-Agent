---
name: finance-fix-fill
description: 'Use when: 用户说填充、我要填充、修正、修正数据、执行方案、修改、更新汇总表。根据已确认的修正方案，创建工作副本并执行 A 类自动修正、B 类逐条确认、C 类人工复核。'
argument-hint: '填充 / 修正数据 / 执行方案'
---

# Finance Fix And Fill

## When To Use

- 用户明确要求修正、填充或执行方案。
- 核对完成后用户确认修正策略。
- 已存在修正方案 JSON，需要生成处理后数据。

## Procedure

1. 检查身份、Python 环境、修正方案 JSON、目标文件和文件锁定状态。
2. 若没有修正方案，先触发 `finance-data-reconciliation`。
3. 做幂等检查，避免同一方案重复执行。
4. 创建首版备份和处理后数据工作副本。
5. 调用 `工具脚本/fix_executor.py`，仅传修正方案路径、目标文件路径和输出路径，由本地 Python 执行 A/B 类修正，C 类只进入人工清单。
6. 追加操作日志，写入已执行方案。
7. **修正完成后自动触发 `finance-report-generation` 生成处理后报告**（无需用户额外触发）。
8. 处理后报告生成后，用 `vscode_askQuestions` 询问下一步：继续下一季度 / 项目空间数据已全部完成 / 暂停。
9. 若用户选择"项目空间数据已全部完成"，自动触发 `finance-report-generation` 生成最终汇总报告。
10. 若处理后报告生成失败，用 `vscode_askQuestions` 提供"重试生成报告 / 暂停 / 查看错误摘要"选项。
11. 需要完整逐条确认、备份规则、执行 JSON 结构和项目完成确认协议时，加载 [full procedure](./references/full.md)。

## Safety

- 必须用户确认后才能写入处理后数据。
- 不直接覆盖 `${project_root}/数据库/原数据/`。
- AI 不直接打开修正目标 Excel，不读取修正前后完整数据行。
