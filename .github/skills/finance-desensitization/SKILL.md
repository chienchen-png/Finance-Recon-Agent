---
name: finance-desensitization
description: 'Use when: 用户说脱密、去敏感、脱敏、替换客户名、客户名转编码。将 Excel 中客户名称替换为客户编码，并删除回款型号、料号等敏感列。'
argument-hint: '脱密 / 脱敏 / 客户名转编码'
---

# Finance Desensitization

## When To Use

- 用户要求客户名称脱密或客户名转编码。
- 用户需要输出不含敏感客户名称和敏感列的 Excel。
- 首次导入后用户希望先脱敏再共享结果。

## Procedure

1. 检查 Python 环境和 `知识库/客户编码/Customer.xlsx`。
2. 扫描当前项目空间原数据目录中的 Excel。
3. 构建客户名称、简称到编码的映射。
4. 替换客户名称并删除敏感列。
5. 输出到 `${project_root}/结果输出/处理后数据/脱密后/`。
6. 需要完整匹配优先级、输入输出规范和禁止行为时，加载 [full procedure](./references/full.md)。

## Safety

- 不要求身份初始化，但仍不得覆盖原始文件。
- 不得写回 `${project_root}/数据库/原数据/`。
