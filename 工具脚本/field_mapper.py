"""
field_mapper.py — 字段映射引擎
处理不同季度/版本的字段名差异，提供一致的字段查找接口。

被以下 Skill 调用: 01-表格扫描与结构化, 02-数据核对与校验

核心功能:
  1. 加载字段映射配置 (知识库/字段映射库/)
  2. 根据季度和上下文自动解析正确的字段位置
  3. 支持字段别名的模糊匹配
"""

import json
from pathlib import Path


def load_field_mapping(knowledge_base_dir: str, quarter: str) -> dict:
    """
    加载指定季度的字段映射配置。

    Args:
        knowledge_base_dir: 知识库根目录的相对路径（如 "知识库"）
        quarter: 季度标识 "Q1"/"Q2"/"Q3"/"Q4"

    Returns:
        dict: 字段映射配置
    """
    config_path = Path(knowledge_base_dir) / "字段映射库" / "季度分表-字段对照.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        full_config = json.load(f)

    if quarter not in full_config:
        raise KeyError(f"未找到 {quarter} 的字段映射配置")

    return full_config[quarter]


def load_summary_field_mapping(knowledge_base_dir: str) -> dict:
    """
    加载汇总表字段说明。

    Args:
        knowledge_base_dir: 知识库根目录的相对路径

    Returns:
        dict: 汇总表字段配置
    """
    config_path = Path(knowledge_base_dir) / "字段映射库" / "汇总表-字段说明.json"
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_field_index(field_config: dict, field_name: str) -> int:
    """
    从字段配置中获取指定字段的列索引。
    支持精确匹配和模糊匹配（字段名包含关系）。

    Args:
        field_config: 字段映射配置
        field_name: 要查找的字段名

    Returns:
        int: 列索引（0-based）
    """
    for key, info in field_config.get('fields', {}).items():
        if info.get('name') == field_name or field_name in info.get('name', ''):
            return info.get('col', -1)
    return -1


def detect_sheet_type(sheet_data: list, header_row: int) -> str:
    """
    自动推断 sheet 类型。

    Args:
        sheet_data: sheet 的数据行列表
        header_row: 表头所在行号

    Returns:
        str: "汇总" | "明细" | "个人明细" | "其他"
    """
    if header_row >= len(sheet_data):
        return "其他"

    header = [str(c).strip() if c else '' for c in sheet_data[header_row]]

    # 关键词检测
    header_str = ' '.join(header)
    if '汇总' in header_str:
        return "汇总"
    if '个人' in header_str or '提成' in header_str:
        return "个人明细"
    if '明细' in header_str:
        return "明细"
    return "其他"


def load_file_specific_mapping(knowledge_base_dir: str, file_name: str) -> dict:
    """
    加载针对特定文件的字段映射配置（如有）。

    优先级: 文件级 > 季度级（全局默认）

    文件级映射配置结构:
      知识库/字段映射库/文件映射/{文件主名}.json
      格式: {"sheets": {"Sheet1": {"fields": {...}}}}

    Args:
        knowledge_base_dir: 知识库根目录
        file_name: 目标文件名（含扩展名）

    Returns:
        dict: 文件级字段映射配置，若不存在返回空字典
    """
    file_stem = Path(file_name).stem
    file_config_path = Path(knowledge_base_dir) / '字段映射库' / '文件映射' / f'{file_stem}.json'
    if file_config_path.exists():
        with open(file_config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def resolve_field_mapping(knowledge_base_dir: str, quarter: str = None,
                          file_name: str = None, sheet_name: str = None) -> dict:
    """
    解析最终生效的字段映射：文件级 > 季度级。

    Args:
        knowledge_base_dir: 知识库根目录
        quarter: 季度标识（Q1-Q4）
        file_name: 文件名
        sheet_name: sheet 名称

    Returns:
        dict: 最终生效的字段映射
    """
    # 先加载季度全局映射
    base_mapping = {}
    if quarter:
        try:
            base_mapping = load_field_mapping(knowledge_base_dir, quarter)
        except (KeyError, FileNotFoundError):
            base_mapping = {}

    # 再加载文件级覆盖
    if file_name:
        file_mapping = load_file_specific_mapping(knowledge_base_dir, file_name)
        if sheet_name and file_mapping:
            sheet_override = file_mapping.get('sheets', {}).get(sheet_name, {})
            # 深度合并：文件级覆盖季度级 fields
            base_mapping = dict(base_mapping)
            base_mapping.update(sheet_override)

    return base_mapping
