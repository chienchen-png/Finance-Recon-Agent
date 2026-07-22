---
name: finance-report-generation
description: 'Use when: 用户说报告、汇总、整合、年度报告、核对报告、出报告。按模板生成校验核对报告、处理后报告和最终汇总报告。'
argument-hint: '报告 / 出报告 / 年度报告'
---

# Finance Report Generation

## When To Use

- 02 核对完成后生成校验核对报告。
- 03 修正完成后生成处理后报告。
- 用户要求出报告、年度汇总或整合全部季度结果。

## Procedure

1. 检查身份、Python 环境、报告模板和对应源数据。
2. 根据触发来源选择校验核对报告、处理后报告或最终汇总报告。
3. 注入执行人、审核人和操作编码。
4. 读取核对结果、修正日志、季度报告和汇总数据。
5. 按模板输出 Markdown 到项目空间结果目录。
6. 需要完整模板字段、三类报告章节和输出规范时，加载 [full procedure](./references/full.md)。

## Safety

- 报告生成不修改原始 Excel。
- 身份信息缺失时暂停生成财务责任报告。
