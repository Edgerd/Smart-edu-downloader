# -*- coding: utf-8 -*-
"""崩溃提示工具独立子进程入口。

接收命令行参数 ``--crash-log <path>``，启动 Qt 对话框展示崩溃信息。
保持轻量，不在顶层导入业务模块或 ``main.py``。
"""

import argparse
import os
import sys


def _calculate_project_root() -> str:
    """基于当前文件位置推导项目根目录。"""
    current_file = os.path.realpath(__file__)
    return os.path.dirname(os.path.dirname(current_file))


_PROJECT_ROOT = _calculate_project_root()
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from PyQt5.QtWidgets import QApplication

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
    crash_log_path = args.crash_log

    app = QApplication(sys.argv)
    dialog = CrashReporterDialog(crash_log_path, project_root=_PROJECT_ROOT)
    dialog.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
