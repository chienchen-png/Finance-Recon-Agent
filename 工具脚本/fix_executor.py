"""
fix_executor.py - 本地修正执行器

接收修正方案 JSON 路径，在本地完成 Excel 修正、备份和验证。
AI 只读取执行摘要，不读取原始单元格值。
"""

import json
import shutil
from datetime import datetime
from pathlib import Path

from openpyxl import load_workbook

from backup_manager import create_single_snapshot


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


def execute_fix_plan(plan_json_path, target_file, output_file, backup_dir, operator_info=None):
    """执行本地修正，只返回安全摘要。"""
    operator_info = operator_info or {}
    plan = json.loads(Path(plan_json_path).read_text(encoding='utf-8'))
    fixes = plan.get('fixes', [])

    backup_path = create_single_snapshot(target_file, backup_dir)
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(target_file, output_file)

    wb = load_workbook(output_file)
    ws = wb.active

    executed = []
    skipped = []

    for item in fixes:
        target_row = item.get('target_row')
        target_col = item.get('target_col')
        new_value = item.get('new_value')
        if not target_row or not target_col:
            skipped.append({'contract': item.get('contract', ''), 'reason': '缺少定位信息'})
            continue
        ws.cell(row=target_row, column=target_col + 1, value=new_value)
        executed.append({
            'contract': item.get('contract', ''),
            'level': item.get('level', ''),
            'target_row': target_row,
            'target_col': target_col,
            'new_value': new_value,
        })

    wb.save(output_file)
    wb.close()

    verify_wb = load_workbook(output_file, data_only=True)
    verify_ws = verify_wb.active
    verified = []
    for item in executed:
        cell_value = verify_ws.cell(row=item['target_row'], column=item['target_col'] + 1).value
        verified.append({
            'contract': item['contract'],
            'level': item['level'],
            'target_row': item['target_row'],
            'target_col': item['target_col'],
            'verified_value': _safe_number(cell_value),
        })
    verify_wb.close()

    summary = {
        'executed_count': len(executed),
        'skipped_count': len(skipped),
        'backup_file': backup_path,
        'output_file': output_file,
        'generated_at': datetime.now().isoformat(),
        'operator_name': operator_info.get('operator_name', ''),
        'reviewer_name': operator_info.get('reviewer_name', ''),
        'operation_code': operator_info.get('operation_code', ''),
    }

    result = {
        'summary': summary,
        'executed': executed,
        'skipped': skipped,
        'verified': verified,
    }

    result_path = Path(output_file).with_suffix('.执行摘要.json')
    result_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='执行本地安全修正')
    parser.add_argument('--config', required=True, help='修正配置 JSON 路径')
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding='utf-8'))
    print(json.dumps(execute_fix_plan(**config), ensure_ascii=False, indent=2))
