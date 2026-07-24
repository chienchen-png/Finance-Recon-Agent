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

### 步骤 0（前置）: 工作副本定位（V2.1 新增——替代路径问答）

> 同一汇总表在项目空间内只有一个工作副本。所有季度修正顺序写入同一文件。

1. 读取 `${project_root}/工作状态.json` → `current_working_copy`
2. **若工作副本存在且文件存在**：直接使用该路径，跳过季度已执行检查
   - 若 `quarters_applied` 包含当前季度 → 警告重复修正，询问是否继续
3. **若工作副本不存在**：自动生成路径
   - 命名规则：`修正后/{原文件名基名}_工作副本.xlsx`
   - 例如：`销售提成汇总表2025.xlsx` → `修正后/销售提成汇总表2025_工作副本.xlsx`
4. **若 `current_working_copy.path` 有值但文件被误删**：从 `snapshot_chain` 最近快照恢复，不重新复制原数据
5. **禁止**手动输入输出路径——工作副本路径由系统自动确定
6. **禁止**使用版本后缀（如 `_v1`、`_v2`、`_最终版`、`_重制版`）

### Procedure
1. 检查身份、Python 环境、`${project_root}/结果输出/核对结果/_工作文件/修正方案/` 下的修正方案 JSON、目标文件和文件锁定状态。
2. 若没有修正方案，先触发 `finance-data-reconciliation`。
3. 确认工作副本路径（见步骤 0）。
4. 做幂等检查，避免同一方案重复执行。
5. 首次修正时创建首版备份；每季度修正前创建带季度标记的快照（`backup_manager.create_quarterly_snapshot`），纳入版本链。
6. 季度分表写入年度汇总表时，必须调用 `工具脚本/reconciliation_engine.py` 的聚合修正能力生成方案，默认 `key_fields=["contract", "person"]`，不得用临时脚本逐行覆盖。
7. 调用 `工具脚本/fix_executor.py` 执行方案，传递 `use_working_copy=True` + `quarter` + `working_state_path`；修正方案必须满足坐标协议。
8. 若执行摘要出现 `skipped_count > 0` 或定位字段不一致：
   a. 从季度快照恢复工作副本（`backup_manager.restore_latest_snapshot`）
   b. 分析 skipped 原因，调整方案
   c. 重新对**同一**工作副本执行修正
   d. **禁止**创建新文件来绕过错误
   e. 若同一方案连续 3 次失败 → 标记为人工介入
9. 修正执行摘要写入 `${project_root}/结果输出/核对结果/_工作文件/执行摘要/`。
10. 修正执行后调用反向校验；有效合同仍有差异时不得进入最终汇总报告。
11. V2.1: `fix_executor.py` 自动更新 `工作状态.json` 中的 `current_working_copy` 字段。
12. 追加操作日志，写入已执行方案。
13. **修正完成后自动触发 `finance-report-generation` 生成处理后报告**。
14. 用 `vscode_askQuestions` 询问下一步：继续下一季度 / 项目空间数据已全部完成 / 暂停。
15. 若用户选择"项目空间数据已全部完成"，自动触发最终汇总报告。
16. 需要完整逐条确认、备份规则、执行 JSON 结构和项目完成确认协议时，加载 [full procedure](./references/full.md)。

## Safety

- 必须用户确认后才能写入处理后数据。
- 不直接覆盖 `${project_root}/数据库/原数据/`。
- AI 不直接打开修正目标 Excel，不读取修正前后完整数据行。
- 机器 JSON 只进入 `_工作文件/` 分类子目录，用户可见报告继续输出到 `处理后报告/`。
