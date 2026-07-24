"""
verification_engine.py - 本地反向校验引擎

读取源季度文件和最终修正版汇总表，在本地按复合键聚合比对，
只输出安全摘要、差异统计和待人工复核清单。
"""

import json
from datetime import datetime
from pathlib import Path

from excel_reader import read_excel
from matcher import load_aliases, normalize_contract


def _safe_text(value):
    if value is None:
        return ''
    return str(value).strip()


def _safe_number(value):
    if value is None or value == '':
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _get_cell(row, col_index):
    if col_index is None or col_index < 0 or col_index >= len(row):
        return None
    return row[col_index]


def _build_key(record, key_fields, aliases):
    values = []
    for field in key_fields:
        value = record.get(field, '')
        if field == 'contract':
            value = normalize_contract(value, aliases)
        values.append(_safe_text(value))
    return tuple(values)


def _group_sheet_rows(rows, field_mapping, key_fields, aliases, data_start_row=1, exclude_contracts=None):
    exclude_contracts = set(exclude_contracts or [])
    grouped = {}
    ignored = []
    for row_number, row in enumerate(rows[data_start_row:], start=data_start_row + 1):
        contract = _safe_text(_get_cell(row, field_mapping['contract']))
        person = _safe_text(_get_cell(row, field_mapping['person']))
        customer = _safe_text(_get_cell(row, field_mapping.get('customer', -1)))
        amount = _safe_number(_get_cell(row, field_mapping['amount']))
        normalized_contract = normalize_contract(contract, aliases)
        if not contract or normalized_contract in exclude_contracts:
            ignored.append({'contract': contract, 'person': person, 'row_number': row_number, 'reason': '空合同或排除合同'})
            continue
        record = {
            'contract': contract,
            'person': person,
            'customer': customer,
            'amount': amount,
            'row_number': row_number,
        }
        key = _build_key(record, key_fields, aliases)
        grouped.setdefault(key, {
            'contract': contract,
            'person': person,
            'customer': customer,
            'amount': 0.0,
            'rows': [],
        })
        grouped[key]['amount'] += amount
        grouped[key]['rows'].append(row_number)
    return grouped, ignored


def run_reverse_verification(
    quarters,
    target_file,
    target_sheet,
    target_field_mapping,
    knowledge_base_dir='知识库',
    key_fields=None,
    amount_tolerance=0.01,
    exclude_contracts=None,
    output_json_path=None,
):
    """执行源数据到目标汇总表的反向交叉校验。"""
    key_fields = key_fields or ['contract', 'person']
    aliases = load_aliases(knowledge_base_dir)
    target_rows = read_excel(target_file, target_sheet).get(target_sheet, [])

    quarter_results = []
    all_failed = []
    all_manual = []
    source_group_total = 0
    matched_total = 0

    for quarter_config in quarters:
        quarter = quarter_config['quarter']
        source_rows = read_excel(quarter_config['source_file'], quarter_config['source_sheet']).get(
            quarter_config['source_sheet'], []
        )
        source_groups, ignored = _group_sheet_rows(
            source_rows,
            quarter_config['source_field_mapping'],
            key_fields,
            aliases,
            quarter_config.get('source_data_start_row', 1),
            exclude_contracts,
        )
        target_amount_mapping = dict(target_field_mapping)
        target_amount_mapping['amount'] = quarter_config['target_amount_col']
        target_groups, _ = _group_sheet_rows(
            target_rows,
            target_amount_mapping,
            key_fields,
            aliases,
            quarter_config.get('target_data_start_row', 2),
            exclude_contracts,
        )

        matched = 0
        failed = []
        manual = []
        for key, source in source_groups.items():
            target = target_groups.get(key)
            source_amount = round(source['amount'], 2)
            if not target:
                manual.append({
                    'quarter': quarter,
                    'contract': source.get('contract', ''),
                    'person': source.get('person', ''),
                    'reason': '目标汇总表中无匹配记录',
                })
                continue
            target_amount = round(target['amount'], 2)
            if abs(source_amount - target_amount) <= amount_tolerance:
                matched += 1
                continue
            failed.append({
                'quarter': quarter,
                'contract': source.get('contract', ''),
                'person': source.get('person', ''),
                'source_amount': source_amount,
                'target_amount': target_amount,
                'diff_amount': round(source_amount - target_amount, 2),
            })

        source_group_total += len(source_groups)
        matched_total += matched
        all_failed.extend(failed)
        all_manual.extend(manual)
        quarter_results.append({
            'quarter': quarter,
            'source_groups': len(source_groups),
            'matched_groups': matched,
            'manual_review_count': len(manual),
            'failed_count': len(failed),
            'ignored_count': len(ignored),
        })

    result = {
        'generated_at': datetime.now().isoformat(),
        'target_file': target_file,
        'target_sheet': target_sheet,
        'key_fields': key_fields,
        'exclude_contracts': exclude_contracts or [],
        'summary': {
            'source_groups': source_group_total,
            'matched_groups': matched_total,
            'manual_review_count': len(all_manual),
            'failed_count': len(all_failed),
        },
        'quarters': quarter_results,
        'manual_review_items': all_manual,
        'failed_items': all_failed,
    }

    if output_json_path:
        output_path = Path(output_json_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    return result


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='执行本地安全反向校验')
    parser.add_argument('--config', required=True, help='反向校验配置 JSON 路径')
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding='utf-8-sig'))
    print(json.dumps(run_reverse_verification(**config), ensure_ascii=False, indent=2))
