"""
report_builder.py — 报告构建器
将结构化核对结果转换为 Markdown 格式报告。

被以下 Skill 调用: 02-数据核对与校验, 04-报告生成

核心功能:
  1. 生成季度核对报告（Markdown）— 含身份字段注入
  2. 生成修正方案（JSON → Markdown 摘要）
  3. 整合多季度报告为年度汇总报告

V1.3 注意事项:
  - 正式报告应优先使用 知识库/报告模板库/ 中的模板，本模块为兜底实现
  - 所有报告必须注入执行人/审核人/操作编码（通过 operator_info 参数传入）
  - 模板占位符规范见 04-报告生成 SKILL.md
  - 操作日志函数必须记录执行人/审核人/操作编码（V1.3 强制）
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional


def build_quarterly_check_report(
    match_results: dict,
    quarter: str,
    output_md_path: str,
    operator_info: Optional[dict] = None
) -> str:
    """
    生成季度核对报告（Markdown）。

    Args:
        match_results: matcher.three_level_match() 的返回结果
        quarter: 季度标识 "Q1"/"Q2"/"Q3"/"Q4"
        output_md_path: 输出 Markdown 路径
        operator_info: V1.3 操作员信息 dict，包含 operator_name/reviewer_name/operation_code

    Returns:
        str: 生成的报告内容
    """
    if operator_info is None:
        operator_info = {}

    summary = match_results['summary']
    details = match_results['details']

    date_str = datetime.now().strftime('%Y%m%d')
    operator_name = operator_info.get('operator_name', '')
    reviewer_name = operator_info.get('reviewer_name', '')
    operation_code = operator_info.get('operation_code', '')

    lines = [
        f"# {quarter}核对报告_{date_str}",
        "",
        "## 一、核对基本信息",
        "",
        f"| 项目 | 内容 |",
        f"| --- | --- |",
        f"| 核对日期 | {datetime.now().strftime('%Y-%m-%d')} |",
        f"| 核对期间 | {quarter} |",
        f"| 操作编码 | {operation_code or '—'} |",
        f"| 执行人 | {operator_name or '—'} |",
        f"| 审核人 | {reviewer_name or '—'} |",
        "",
        "## 二、结论",
        f"- 总合同数: **{summary['total']}**",
        f"- 完全匹配: {summary['matched']}",
        f"- A1类(可自动填充): {summary['a1_count']}",
        f"- A2类(可自动修正): {summary['a2_count']}",
        f"- B类(需确认): {summary['b_count']}",
        f"- C类(需人工判断): {summary['c_count']}",
        "",
        "## 三、核对详情",
    ]

    # 按级别分组
    for level, title in [
        ('A1', 'A1类-自动填充（汇总表为空）'),
        ('A2', 'A2类-自动修正（金额不一致）'),
        ('B', 'B类-需确认'),
        ('C', 'C类-无法自动处理'),
        ('OK', '✅ 完全匹配'),
    ]:
        group = [d for d in details if d['level'] == level]
        if not group:
            continue
        # 序号计算
        level_order = {'A1': 1, 'A2': 2, 'B': 3, 'C': 4, 'OK': 5}
        lines.append(f"### 3.{level_order.get(level, 0)} {title}")
        lines.append("| 合同 | 人员 | 客户 | 说明 |")
        lines.append("|------|------|------|------|")
        for item in group:
            src = item['source']
            lines.append(
                f"| {src.get('contract','')} | {src.get('person','')} "
                f"| {src.get('customer','')} | {item['detail']} |"
            )
        lines.append("")

    # 保存
    content = '\n'.join(lines)
    Path(output_md_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_md_path).write_text(content, encoding='utf-8')
    return content


def build_fix_plan(match_results: dict, quarter: str, output_json_path: str) -> dict:
    """
    生成结构化修正方案 JSON（V1.3 含 content_hash 用于幂等性校验）。

    Args:
        match_results: 核对结果
        quarter: 季度
        output_json_path: 输出路径

    Returns:
        dict: 修正方案，包含 content_hash 字段
    """
    import hashlib

    details = match_results['details']
    summary = match_results['summary']

    fixes = []
    for item in details:
        if item['level'] in ('A1', 'A2'):
            fixes.append({
                'type': f"{item['level']}_fill" if item['level'] == 'A1' else f"{item['level']}_correct",
                'level': item['level'],
                'contract': item['source'].get('contract', ''),
                'person': item['source'].get('person', ''),
                'customer': item['source'].get('customer', ''),
                'new_value': item['source'].get('amount', 0),
                'old_value': item.get('target', {}).get('amount', 0),
                'reason': item['detail']
            })

    plan = {
        'period': quarter,
        'generated_at': datetime.now().isoformat(),
        'summary': {
            'total_fixes': summary['a1_count'] + summary['a2_count'],
            'a1_fills': summary['a1_count'],
            'a2_corrections': summary['a2_count']
        },
        'fixes': fixes
    }

    # V1.3: 生成内容哈希用于幂等性校验
    fixes_hash = hashlib.sha256(
        json.dumps(fixes, sort_keys=True, ensure_ascii=False).encode('utf-8')
    ).hexdigest()
    plan['content_hash'] = fixes_hash

    Path(output_json_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    return plan


def build_annual_report(
    quarterly_reports_dir: str,
    output_md_path: str,
    year: str = "2025",
    operator_info: Optional[dict] = None,
    template_path: Optional[str] = None
) -> str:
    """
    整合多季度核对报告为年度汇总报告。

    V1.3: 优先使用 知识库/报告模板库/最终汇总报告_模板.md 模板。
    若提供 template_path 则按模板填充，否则使用内置兜底结构。

    Args:
        quarterly_reports_dir: 季度报告目录（处理后报告/）
        output_md_path: 输出 Markdown 路径
        year: 年度
        operator_info: V1.3 操作员信息 dict
        template_path: 模板 Markdown 文件路径（可选，V1.3 推荐）

    Returns:
        str: 报告内容
    """
    if operator_info is None:
        operator_info = {}
    operator_name = operator_info.get('operator_name', '')
    reviewer_name = operator_info.get('reviewer_name', '')
    operation_code = operator_info.get('operation_code', '')

    # 收集各季度报告
    reports = {}
    report_dir = Path(quarterly_reports_dir)
    for md_file in sorted(report_dir.glob('Q*核对报告_*.md')):
        q = md_file.stem[:2]  # "Q1"
        reports[q] = md_file.read_text(encoding='utf-8')

    # 若提供模板则优先使用模板填充
    if template_path and Path(template_path).exists():
        template = Path(template_path).read_text(encoding='utf-8')
        content = template.replace('{报告编号}', f'FIN-RECON-{year}-{datetime.now().strftime("%Y%m%d")}')
        content = content.replace('{YYYY}', year)
        content = content.replace('{操作编码}', operation_code or '—')
        content = content.replace('{操作人}', operator_name or '—')
        content = content.replace('{执行人}', operator_name or '—')
        content = content.replace('{审核人}', reviewer_name or '—')
        content = content.replace('{YYYY-MM-DD}', datetime.now().strftime('%Y-%m-%d'))
        Path(output_md_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_md_path).write_text(content, encoding='utf-8')
        return content

    # 兜底结构
    lines = [
        f"# 回款提成核对报告_{year}年度",
        "",
        f"> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## 一、基本信息",
        "",
        f"| 项目 | 内容 |",
        f"| --- | --- |",
        f"| 报告日期 | {datetime.now().strftime('%Y-%m-%d')} |",
        f"| 项目周期 | {year}年度 |",
        f"| 操作编码 | {operation_code or '—'} |",
        f"| 执行人 | {operator_name or '—'} |",
        f"| 审核人 | {reviewer_name or '—'} |",
        "",
        "## 二、总体结论",
        f"已完成 {year} 年度 {len(reports)} 个季度的回款提成核对。",
        "",
        "## 三、各季度修正概要",
    ]

    for q in ['Q1', 'Q2', 'Q3', 'Q4']:
        if q in reports:
            lines.append(f"### {q}")
            lines.append("（详见各季度报告）")
        else:
            lines.append(f"### {q}")
            lines.append("（未完成核对）")

    lines.extend([
        "",
        "## 四、待处理问题汇总",
        "（从各季度报告中汇总）",
        "",
        "## 五、人员/客户修正汇总",
        "（从修正日志中汇总）",
        "",
        "## 六、修正统计总览",
        "（从修正日志中汇总）",
    ])

    content = '\n'.join(lines)
    Path(output_md_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_md_path).write_text(content, encoding='utf-8')
    return content


def append_operation_log(log_dir: str, operation_type: str, description: str,
                         result: str = "✅ 成功", changes: str = "",
                         operator_name: str = "", reviewer_name: str = "",
                         operation_code: str = "") -> str:
    """
    追加一条操作日志记录（V1.3 含完整身份字段）。

    Args:
        log_dir: 修改日志目录（如 "项目空间/项目空间1/修改日志"）
        operation_type: 操作类型
        description: 操作描述
        result: 结果
        changes: 变更摘要
        operator_name: V1.3 执行人姓名
        reviewer_name: V1.3 审核人姓名
        operation_code: V1.3 操作编码

    Returns:
        str: 追加的内容
    """
    log_file = Path(log_dir) / "操作日志.md"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    entry = f"""
### [{timestamp}] {operation_type}

| 项目 | 内容 |
|------|------|
| **操作编码** | {operation_code or '—'} |
| **操作类型** | {operation_type} |
| **操作描述** | {description} |
| **执行人** | {operator_name or '—'} |
| **审核人** | {reviewer_name or '—'} |
| **结果** | {result} |
| **变更摘要** | {changes or '—'} |
"""

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(entry)

    return entry.strip()
