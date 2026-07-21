# -*- coding: utf-8 -*-
"""崩溃守护进程。

在主程序启动时作为独立子进程运行，监控主进程状态。当主进程异常退出
且产生了新的崩溃日志时，自动启动崩溃提示工具，确保致命性崩溃（包括
C/C++ 段错误）也能被用户感知。
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timedelta


def _process_exists(pid: int) -> bool:
    """检查指定 PID 的进程是否仍然存在。

    Args:
        pid: 进程 ID。

    Returns:
        进程存在返回 True，否则返回 False。
    """
    try:
        import psutil
        return psutil.pid_exists(pid)
    except Exception:
        pass
    # 无 psutil 时使用 os.kill 回退（在部分平台支持 signal 0）
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def _find_latest_crash_log(crash_dir: str, after_time: datetime) -> str:
    """查找指定时间之后生成的最新崩溃日志。

    Args:
        crash_dir: 崩溃日志目录。
        after_time: 时间阈值，只返回在此之后修改的日志。

    Returns:
        最新崩溃日志路径；未找到时返回空字符串。
    """
    latest_path = ''
    latest_mtime = after_time
    if not os.path.isdir(crash_dir):
        return latest_path
    for name in os.listdir(crash_dir):
        if not name.startswith('crash_') or not name.endswith('.log'):
            continue
        path = os.path.join(crash_dir, name)
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(path))
        except Exception:
            continue
        if mtime > latest_mtime:
            latest_path = path
            latest_mtime = mtime
    return latest_path


def _launch_crash_reporter(crash_log: str) -> None:
    """启动崩溃提示工具。

    Args:
        crash_log: 崩溃日志文件路径。
    """
    try:
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        reporter_path = os.path.join(project_root, 'tools', 'crash_reporter.py')
        if not os.path.exists(reporter_path):
            return
        subprocess.Popen(
            [sys.executable, reporter_path, '--crash-log', crash_log],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
    except Exception:
        pass


def _monitor(parent_pid: int, crash_dir: str) -> None:
    """监控主进程，退出后根据崩溃日志启动报告工具。

    Args:
        parent_pid: 主进程 ID。
        crash_dir: 崩溃日志目录。
    """
    # 略微提前记录开始时间，避免边界情况漏掉日志
    start_time = datetime.now() - timedelta(seconds=3)
    while _process_exists(parent_pid):
        time.sleep(1)
    # 主进程已退出，等待 faulthandler 等完成日志写入
    time.sleep(0.5)
    crash_log = _find_latest_crash_log(crash_dir, start_time)
    if crash_log:
        _launch_crash_reporter(crash_log)


def main() -> int:
    """崩溃守护进程入口。"""
    parser = argparse.ArgumentParser(description='崩溃守护进程')
    parser.add_argument('--parent-pid', type=int, required=True, help='主进程 ID')
    parser.add_argument('--crash-dir', required=True, help='崩溃日志目录')
    args = parser.parse_args()
    _monitor(args.parent_pid, args.crash_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
