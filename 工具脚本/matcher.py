"""
matcher.py — 三层匹配引擎
按 合同编号 → 销售人员 → 客户编码 三级渐进式匹配。

被以下 Skill 调用: 02-数据核对与校验

核心功能:
  1. 加载别名库并规范化合同编号
  2. 执行三层匹配逻辑
  3. 按 A/B/C 三级对差异分级
  4. 输出结构化的核对结果
"""

import json
from pathlib import Path
from typing import Optional


def load_aliases(knowledge_base_dir: str) -> dict:
    """
    加载合同编号别名库。

    Args:
        knowledge_base_dir: 知识库根目录的相对路径

    Returns:
        dict: {规范名称: [别名列表], ...}
    """
    alias_path = Path(knowledge_base_dir) / "别名库" / "合同别名.json"
    with open(alias_path, 'r', encoding='utf-8') as f:
        return json.load(f).get('aliases', {})


def normalize_contract(contract: str, aliases: dict) -> str:
    """
    将合同编号规范化为标准名称。

    Args:
        contract: 原始合同编号
        aliases: 别名映射表

    Returns:
        str: 规范化后的合同编号
    """
    # 先查是否本身就是规范名
    if contract in aliases:
        return contract
    # 再查是否在某个规范名的别名列表中
    for canonical, alias_list in aliases.items():
        if contract in alias_list:
            return canonical
    return contract


def three_level_match(
    source_records: list,
    target_records: list,
    aliases: dict,
    amount_tolerance: float = 0.01,
    auto_fix_threshold: float = 1.0,
    allow_fallback: bool = True  # V2.0: 合同未匹配时是否降级到 (人员+客户)
) -> dict:
    """
    执行三层匹配。

    Args:
        source_records: 季度分表明细数据 [{"contract":"", "person":"", "customer":"", "amount":0}, ...]
        target_records: 汇总表数据 [{"contract":"", "person":"", "customer":"", "amount":0}, ...]
        aliases: 合同别名映射
        amount_tolerance: 金额比较容差
        auto_fix_threshold: 自动修正阈值（≤此值的差异自动修正）
        allow_fallback: V2.0 — 合同未匹配时是否尝试 (人员+客户) 降级匹配

    Returns:
        dict: {
            "summary": {"total", "matched", "a1_count", "a2_count", "b_count", "c_count"},
            "details": [...]
        }
    """
    # 建立汇总表索引: {contract: record}
    target_index = {}
    for rec in target_records:
        c = normalize_contract(rec.get('contract', ''), aliases)
        target_index[c] = rec

    # V2.0: 降级匹配索引（人员+客户 → 目标行）
    fallback_index = {}
    if allow_fallback:
        for rec in target_records:
            key = (rec.get('person', ''), rec.get('customer', ''))
            existing = fallback_index.get(key)
            if existing:
                existing['duplicate'] = True
            else:
                fallback_index[key] = rec

    results = []
    summary = {
        'total': len(source_records),
        'matched': 0, 'a1_count': 0, 'a2_count': 0,
        'b_count': 0, 'c_count': 0
    }

    for src in source_records:
        contract = normalize_contract(src.get('contract', ''), aliases)
        result = {'source': src, 'level': '', 'detail': ''}

        # ① 合同编号匹配
        target = target_index.get(contract)
        if not target and allow_fallback:
            fb_key = (src.get('person', ''), src.get('customer', ''))
            fb = fallback_index.get(fb_key)
            if fb and not fb.get('duplicate'):
                target = fb
                result['detail'] = '[FALLBACK] 降级匹配（合同未匹配，人员+客户命中）'
        if not target:
            result['level'] = 'C'
            result['detail'] = result.get('detail', '') or 'C类-季度独有（汇总表无此合同）'
            if not result['detail'].startswith('[FALLBACK]'):
                result['detail'] = 'C类-季度独有（汇总表无此合同）'
            summary['c_count'] += 1
            results.append(result)
            continue

        # 如果已经通过 fallback 找到 target，需要更新 detail
        if result.get('detail', '').startswith('[FALLBACK]'):
            # 降级匹配成功，继续走正常比对流程
            pass

        target = target_index.get(contract, target)

        # ② 销售人员校验
        src_person = src.get('person', '')
        tgt_person = target.get('person', '')
        person_match = (src_person == tgt_person)

        # ③ 客户编码校验
        src_customer = src.get('customer', '')
        tgt_customer = target.get('customer', '')
        customer_match = (src_customer == tgt_customer)

        # ④ 金额比对
        src_amount = src.get('amount', 0) or 0
        tgt_amount = target.get('amount', 0) or 0
        diff = abs(src_amount - tgt_amount)

        if person_match and customer_match and diff <= amount_tolerance:
            result['level'] = 'OK'
            result['detail'] = '✅ 完全匹配'
            summary['matched'] += 1
        elif tgt_amount == 0 and src_amount > 0:
            result['level'] = 'A1'
            result['detail'] = f'A1类-汇总表为空，应填充 {src_amount}'
            summary['a1_count'] += 1
        elif not person_match or not customer_match:
            # V1.3 修复: 人员/客户校验必须在金额判断之前，防止将身份不匹配误判为 A2 自动修正
            result['level'] = 'B'
            reasons = []
            if not person_match:
                reasons.append(f'人员差异:{src_person}≠{tgt_person}')
            if not customer_match:
                reasons.append(f'客户差异:{src_customer}≠{tgt_customer}')
            result['detail'] = f'B类-{"；".join(reasons)}'
            summary['b_count'] += 1
        elif diff > amount_tolerance and diff <= auto_fix_threshold:
            result['level'] = 'A2'
            result['detail'] = f'A2类-金额差异{diff:.2f}元，以分表为准自动修正'
            summary['a2_count'] += 1
        elif diff > auto_fix_threshold:
            result['level'] = 'B'
            result['detail'] = f'B类-金额差异{diff:.2f}元(>{auto_fix_threshold}元)，待确认'
            summary['b_count'] += 1
        else:
            result['level'] = 'C'
            result['detail'] = 'C类-无法自动判断'
            summary['c_count'] += 1

        result['target'] = target
        result['diff'] = diff
        results.append(result)

    return {'summary': summary, 'details': results}
