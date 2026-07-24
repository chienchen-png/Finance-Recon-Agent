"""
reconciliation_engine.py - 本地核对引擎

AI 只传入文件路径、sheet 名和字段列索引；本脚本在本地读取 Excel、执行核对，
只输出 AI 可读取的安全摘要、差异索引和修正方案。
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path

from excel_reader import read_excel, read_schema_only
from matcher import load_aliases, normalize_contract


def _safe_number(value):
    if value is None or value == '':
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _safe_text(value):
    if value is None:
        return ''
    return str(value).strip()


def _get_cell(row, col_index):
    if col_index is None or col_index < 0 or col_index >= len(row):
        return None
    return row[col_index]


def _extract_records(file_path, sheet_name, field_mapping, data_start_row):
    sheet_data = read_excel(file_path, sheet_name).get(sheet_name, [])
    records = []
    for row_number, row in enumerate(sheet_data[data_start_row:], start=data_start_row + 1):
        contract = _safe_text(_get_cell(row, field_mapping['contract']))
        if not contract:
            continue
        records.append({
            'row_number': row_number,
            'contract': contract,
            'person': _safe_text(_get_cell(row, field_mapping['person'])),
            'customer': _safe_text(_get_cell(row, field_mapping['customer'])),
            'amount': _safe_number(_get_cell(row, field_mapping['amount'])),
        })
    return records


def _build_target_index(records, aliases):
    index = {}
    for record in records:
        contract = normalize_contract(record['contract'], aliases)
        index[contract] = record
    return index


def _difference_item(level, detail, source, target=None, diff=None, target_amount_col=None, include_identity=False):
    item = {
        'level': level,
        'contract': source['contract'],
        'source_row': source['row_number'],
        'target_row': target['row_number'] if target else None,
        'target_col': target_amount_col,
        'detail': detail,
    }
    if diff is not None:
        item['diff_amount'] = round(float(diff), 2)
    if include_identity:
        item['person'] = source.get('person', '')
        item['customer'] = source.get('customer', '')
    return item


def run_full_reconciliation(
    source_file,
    target_file,
    source_sheet,
    target_sheet,
    source_field_mapping,
    target_field_mapping,
    target_amount_col,
    knowledge_base_dir='知识库',
    amount_tolerance=0.01,
    auto_fix_threshold=1.0,
    source_header_row=0,
    target_header_row=1,
    source_data_start_row=None,
    target_data_start_row=None,
    quarter='Q1',
    output_dir=None,
):
    """执行本地核对并写出 AI 可安全读取的摘要和修正方案。"""
    source_data_start_row = source_header_row + 1 if source_data_start_row is None else source_data_start_row
    target_data_start_row = target_header_row + 1 if target_data_start_row is None else target_data_start_row

    aliases = load_aliases(knowledge_base_dir)
    source_records = _extract_records(source_file, source_sheet, source_field_mapping, source_data_start_row)
    target_amount_mapping = dict(target_field_mapping)
    target_amount_mapping['amount'] = target_amount_col
    target_records = _extract_records(target_file, target_sheet, target_amount_mapping, target_data_start_row)
    target_index = _build_target_index(target_records, aliases)

    summary = {
        'total': len(source_records),
        'matched': 0,
        'a1_count': 0,
        'a2_count': 0,
        'b_count': 0,
        'c_count': 0,
    }
    differences = []
    fixes = []

    for source in source_records:
        contract = normalize_contract(source['contract'], aliases)
        target = target_index.get(contract)
        if not target:
            summary['c_count'] += 1
            differences.append(_difference_item(
                'C', 'C类-依据独有（目标缺失）', source, target_amount_col=target_amount_col
            ))
            continue

        person_match = source['person'] == target['person']
        customer_match = source['customer'] == target['customer']
        diff = abs(source['amount'] - target['amount'])

        if person_match and customer_match and diff <= amount_tolerance:
            summary['matched'] += 1
            continue
        if target['amount'] == 0 and source['amount'] > 0:
            summary['a1_count'] += 1
            detail = 'A1类-目标为空，可按依据文件填充'
            differences.append(_difference_item(
                'A1', detail, source, target, diff=source['amount'], target_amount_col=target_amount_col
            ))
            fixes.append({
                'type': 'A1_fill',
                'level': 'A1',
                'contract': source['contract'],
                'source_row': source['row_number'],
                'target_row': target['row_number'],
                'target_col': target_amount_col,
                'new_value': source['amount'],
                'reason': detail,
            })
            continue
        if not person_match or not customer_match:
            summary['b_count'] += 1
            reasons = []
            if not person_match:
                reasons.append('人员差异')
            if not customer_match:
                reasons.append('客户差异')
            differences.append(_difference_item(
                'B', f"B类-{'；'.join(reasons)}", source, target,
                diff=diff, target_amount_col=target_amount_col, include_identity=True
            ))
            continue
        if diff <= auto_fix_threshold:
            summary['a2_count'] += 1
            detail = 'A2类-金额小额差异，可按依据文件修正'
            differences.append(_difference_item(
                'A2', detail, source, target, diff=diff, target_amount_col=target_amount_col
            ))
            fixes.append({
                'type': 'A2_correct',
                'level': 'A2',
                'contract': source['contract'],
                'source_row': source['row_number'],
                'target_row': target['row_number'],
                'target_col': target_amount_col,
                'new_value': source['amount'],
                'reason': detail,
            })
            continue

        summary['b_count'] += 1
        differences.append(_difference_item(
            'B', 'B类-金额差异超过自动修正阈值', source, target,
            diff=diff, target_amount_col=target_amount_col, include_identity=True
        ))

    generated_at = datetime.now().isoformat()
    source_schema = read_schema_only(source_file, source_header_row, source_sheet)
    target_schema = read_schema_only(target_file, target_header_row, target_sheet)
    meta = {
        'generated_at': generated_at,
        'period': quarter,
        'source_file': Path(source_file).name,
        'target_file': Path(target_file).name,
        'source_sheet': source_sheet,
        'target_sheet': target_sheet,
        'source_rows': source_schema['sheets'][source_sheet]['row_count'],
        'source_cols': source_schema['sheets'][source_sheet]['col_count'],
        'target_rows': target_schema['sheets'][target_sheet]['row_count'],
        'target_cols': target_schema['sheets'][target_sheet]['col_count'],
    }

    plan = {
        'period': quarter,
        'generated_at': generated_at,
        'target_file': target_file,
        'target_sheet': target_sheet,
        'summary': {
            'total_fixes': summary['a1_count'] + summary['a2_count'],
            'a1_fills': summary['a1_count'],
            'a2_corrections': summary['a2_count'],
        },
        'fixes': fixes,
    }
    plan['content_hash'] = hashlib.sha256(
        json.dumps(fixes, sort_keys=True, ensure_ascii=False).encode('utf-8')
    ).hexdigest()

    result = {
        'meta': meta,
        'summary': summary,
        'differences': differences,
        'fix_plan': plan,
    }

    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime('%Y%m%d')
        result_path = output_path / f'{quarter}核对结果摘要_{date_str}.json'
        plan_path = output_path / f'{quarter}修正方案_{date_str}.json'
        result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding='utf-8')
        result['output_files'] = {
            'summary': str(result_path),
            'fix_plan': str(plan_path),
        }

    return result


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='执行本地安全核对')
    parser.add_argument('--config', required=True, help='核对配置 JSON 路径')
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    print(json.dumps(run_full_reconciliation(**config), ensure_ascii=False, indent=2))
