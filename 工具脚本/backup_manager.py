"""
backup_manager.py — 备份管理器
首版快照 + 季度快照 + 备份恢复（V2.1 版本链模型）。

被以下 Skill 调用: 03-修正执行与填充

核心功能:
  1. create_single_snapshot() — V1.3 首版快照策略（唯一使用方式，幂等）
  2. create_quarterly_snapshot() — V2.1 每季度修正前创建带季度标记的快照
  3. restore_backup() — 从备份恢复
  4. list_backups() — 列出所有备份（兼容新旧命名）
  5. restore_latest_snapshot() — V2.1 恢复最近一次季度快照
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


def create_quarterly_snapshot(working_copy_path: str, backup_dir: str, quarter: str) -> str:
    """
    V2.1 每季度修正前创建带季度标记的快照，纳入版本链。

    Args:
        working_copy_path: 工作副本路径
        backup_dir: 备份目录
        quarter: 季度标识（Q1/Q2/Q3/Q4）

    Returns:
        str: 快照文件路径
    """
    src = Path(working_copy_path)
    if not src.exists():
        raise FileNotFoundError(f"工作副本不存在: {working_copy_path}")

    backup_dir = Path(backup_dir)
    backup_dir.mkdir(parents=True, exist_ok=True)

    snap_name = f"snap_{quarter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    snap_path = backup_dir / snap_name
    shutil.copy2(src, snap_path)
    return str(snap_path)


def restore_latest_snapshot(backup_dir: str, quarter: str = None) -> str:
    """
    V2.1 恢复最近一次快照。若指定 quarter，则恢复该季度的最新快照。

    Args:
        backup_dir: 备份目录
        quarter: 可选，指定季度

    Returns:
        str: 恢复的快照路径（最新）
    """
    backup_dir = Path(backup_dir)
    if not backup_dir.exists():
        raise FileNotFoundError(f"备份目录不存在: {backup_dir}")

    pattern = f"snap_{quarter}_*" if quarter else "snap_*"
    snaps = sorted(backup_dir.glob(pattern), key=os.path.getmtime, reverse=True)
    if not snaps:
        raise FileNotFoundError(
            f"未找到{'「'+quarter+'」' if quarter else ''}快照文件"
        )
    return str(snaps[0])


def get_snapshot_chain(backup_dir: str) -> list:
    """
    V2.1 获取完整快照链，按时间排序。

    Args:
        backup_dir: 备份目录

    Returns:
        list: [{'quarter': 'Q1', 'path': '...', 'time': '...'}, ...]
    """
    backup_dir = Path(backup_dir)
    if not backup_dir.exists():
        return []
    snaps = sorted(backup_dir.glob("snap_Q*"), key=os.path.getmtime)
    return [
        {
            'quarter': s.stem.split('_')[1] if '_' in s.stem else '?',
            'path': str(s),
            'mtime': datetime.fromtimestamp(os.path.getmtime(s)).isoformat(),
        }
        for s in snaps
    ]
