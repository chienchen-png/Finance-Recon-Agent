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
5. 按用户确认策略执行 A/B 类修正，C 类只进入人工清单。
6. 追加操作日志，写入已执行方案，并触发报告生成。
7. 需要完整逐条确认、备份规则和执行 JSON 结构时，加载 [full procedure](./references/full.md)。

## Safety

- 必须用户确认后才能写入处理后数据。
- 不直接覆盖 `${project_root}/数据库/原数据/`。
