# -*- coding: utf-8 -*-
"""崩溃提示工具独立子进程入口。

接收命令行参数 ``--crash-log <path>``，启动 Qt 对话框展示崩溃信息。
保持轻量，不在顶层导入业务模块或 ``main.py``。
"""

import argparse
import os
import shutil
import sys


def _calculate_project_root() -> str:
    """基于当前文件位置推导项目根目录。"""
    current_file = os.path.realpath(__file__)
    return os.path.dirname(os.path.dirname(current_file))


_PROJECT_ROOT = _calculate_project_root()
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)


def _copy_crash_log_to_root(crash_log_path: str, project_root: str) -> str:
    """若崩溃日志不在项目根目录，则将其复制到根目录。

    Args:
        crash_log_path: 崩溃日志文件路径。
        project_root: 项目根目录路径。

    Returns:
        项目根目录下的崩溃日志路径；复制失败时返回原始路径。
    """
    if os.path.dirname(os.path.abspath(crash_log_path)) == os.path.abspath(project_root):
        return crash_log_path
    try:
        root_path = os.path.join(project_root, os.path.basename(crash_log_path))
        shutil.copy2(crash_log_path, root_path)
        return root_path
    except Exception:
        return crash_log_path

from PyQt5.QtWidgets import QApplication

from gui.styles import apply_global_message_box_style
from gui.widgets.crash_reporter_dialog import CrashReporterDialog


def _parse_args() -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(description="崩溃提示工具")
    parser.add_argument(
        "--crash-log",
        required=True,
        help="崩溃日志文件路径",
    )
    return parser.parse_args()


def main() -> int:
    """崩溃提示工具主入口。"""
    args = _parse_args()
    crash_log_path = _copy_crash_log_to_root(args.crash_log, _PROJECT_ROOT)

    app = QApplication(sys.argv)
    apply_global_message_box_style(app)
    dialog = CrashReporterDialog(crash_log_path, project_root=_PROJECT_ROOT)
    return dialog.exec()


if __name__ == "__main__":
    sys.exit(main())
