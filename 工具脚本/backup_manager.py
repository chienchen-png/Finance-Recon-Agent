"""
backup_manager.py — 备份管理器
首版快照 + 备份恢复。

被以下 Skill 调用: 03-修正执行与填充

核心功能:
  1. create_single_snapshot() — V1.3 首版快照策略（唯一使用方式）
  2. restore_backup() — 从备份恢复
  3. list_backups() — 列出所有备份（兼容新旧命名）
"""

import os
import shutil
from datetime import datetime
from pathlib import Path


def restore_backup(backup_path: str, target_path: str) -> str:
    """
    从备份恢复文件。

    Args:
        backup_path: 备份文件路径
        target_path: 恢复到目标路径

    Returns:
        str: 目标文件路径
    """
    shutil.copy2(backup_path, target_path)
    return target_path


def list_backups(backup_dir: str) -> list:
    """
    列出所有备份文件（兼容 V1.3 *_原始* 命名和旧版 *_backup_* 命名）。

    Args:
        backup_dir: 备份目录路径

    Returns:
        list: 备份文件路径列表，按时间倒序
    """
    backup_dir = Path(backup_dir)
    if not backup_dir.exists():
        return []
    backups = sorted(
        list(backup_dir.glob('*_原始*')) + list(backup_dir.glob('*_backup_*')),
        key=os.path.getmtime,
        reverse=True
    )
    return [str(b) for b in backups]


def create_single_snapshot(file_path: str, backup_dir: str) -> str:
    """
    V1.3 首版快照策略 — 仅创建一份原始快照（三重备份机制第3层）。

    若该文件的快照已存在则跳过，不会创建多份。

    Args:
        file_path: 要备份的文件路径
        backup_dir: 备份目录路径（如 "项目空间/项目空间1/修改日志/备份"）

    Returns:
        str: 备份文件路径（已存在时返回已有路径，未创建时返回新路径）
    """
    src = Path(file_path)
    if not src.exists():
        raise FileNotFoundError(f"源文件不存在: {file_path}")

    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    # V1.3 固定命名，不含时间戳
    backup_name = f"{src.stem}_原始{src.suffix}"
    backup_path = backup_dir / backup_name

    if backup_path.exists():
        return str(backup_path)

    shutil.copy2(src, backup_path)
    return str(backup_path)
