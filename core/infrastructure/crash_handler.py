"""全局崩溃捕获与记录模块。

注册 ``sys.excepthook``、``threading.excepthook`` 以及 ``faulthandler``，
在主线程、子线程发生未处理 Python 异常或 C/C++ 层段错误时，
将异常摘要与完整堆栈写入 ``Smart-edu-downloader/logs/crashes/`` 下，
并尝试启动崩溃提示工具。
"""
import faulthandler
from core.i18n import _
import os
import shutil
import subprocess
import sys
import threading
import traceback
from datetime import datetime
from types import TracebackType
from typing import Optional, Tuple, Type

# 保持 faulthandler 文件句柄，避免被垃圾回收
_FAULT_HANDLER_FILE = None

def _get_deepest_frame(tb: Optional[TracebackType]) -> Optional[TracebackType]:
    """遍历 traceback 链，返回最深层帧。"""
    if tb is None:
        return None
    while tb.tb_next is not None:
        tb = tb.tb_next
    return tb

def _extract_last_error_location(tb: Optional[TracebackType]) -> Tuple[str, int]:
    """提取最后出错的文件路径与行号。"""
    deepest = _get_deepest_frame(tb)
    if deepest is None:
        return ('<unknown>', 0)
    frame = deepest.tb_frame
    return (frame.f_code.co_filename, deepest.tb_lineno)

def _generate_crash_log_path() -> str:
    """生成崩溃日志文件路径。"""
    from core.infrastructure.path_resolver import get_crash_logs_dir
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'crash_{timestamp}.log'
    return os.path.join(get_crash_logs_dir(), filename)


def _copy_crash_log_to_root(crash_log_path: str) -> Optional[str]:
    """将崩溃日志复制到项目根目录，便于用户直接查看与反馈。

    Args:
        crash_log_path: 原始崩溃日志文件路径。

    Returns:
        项目根目录下的崩溃日志路径；复制失败时返回 None。
    """
    try:
        from core.infrastructure.path_resolver import get_project_root
        project_root = get_project_root()
        filename = os.path.basename(crash_log_path)
        root_path = os.path.join(project_root, filename)
        shutil.copy2(crash_log_path, root_path)
        return root_path
    except Exception:
        return None

def _build_summary(exc_type: Type[BaseException], exc_value: BaseException, filepath: str, lineno: int) -> str:
    """构建崩溃摘要文本。"""
    return f'{exc_type.__name__}: {exc_value} at {filepath}:{lineno}'

def _reported_marker_path(crash_log_path: str) -> str:
    """返回崩溃日志对应的已报告标记文件路径。"""
    return crash_log_path + '.reported'


def _mark_crash_reported(crash_log_path: str) -> None:
    """标记崩溃日志已启动过提示工具，避免重复弹窗。"""
    try:
        with open(_reported_marker_path(crash_log_path), 'w', encoding='utf-8') as f:
            f.write('1')
    except Exception:
        pass


def _is_crash_reported(crash_log_path: str) -> bool:
    """检查崩溃日志是否已启动过提示工具。"""
    return os.path.exists(_reported_marker_path(crash_log_path))


def _launch_crash_reporter(crash_log_path: str) -> None:
    """以独立进程启动崩溃提示工具。"""
    if _is_crash_reported(crash_log_path):
        return
    try:
        from core.infrastructure.path_resolver import get_project_root
        reporter_path = os.path.join(get_project_root(), 'tools', 'crash_reporter.py')
        if not os.path.exists(reporter_path):
            return
        subprocess.Popen(
            [sys.executable, reporter_path, '--crash-log', crash_log_path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        _mark_crash_reported(crash_log_path)
    except Exception:
        pass

def _write_crash_log(crash_log_path: str, exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: Optional[TracebackType]) -> None:
    """将崩溃信息写入日志文件。"""
    traceback_text = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    filepath, lineno = _extract_last_error_location(exc_traceback)
    summary = _build_summary(exc_type, exc_value, filepath, lineno)
    from core.infrastructure.logger import log_crash_safe
    log_crash_safe(crash_log_path, summary, traceback_text)

def _handle_exception(exc_type: Type[BaseException], exc_value: BaseException, exc_traceback: Optional[TracebackType]) -> None:
    """``sys.excepthook`` 回调函数。"""
    try:
        crash_log_path = _generate_crash_log_path()
        _write_crash_log(crash_log_path, exc_type, exc_value, exc_traceback)
        root_crash_log_path = _copy_crash_log_to_root(crash_log_path)
        _launch_crash_reporter(root_crash_log_path or crash_log_path)
    except Exception:
        pass
    sys.__excepthook__(exc_type, exc_value, exc_traceback)

def _handle_thread_exception(args: threading.ExceptHookArgs) -> None:
    """``threading.excepthook`` 回调函数（Python 3.8+）。"""
    _handle_exception(args.exc_type, args.exc_value, args.exc_traceback)

def install_crash_handler() -> None:
    """安装全局崩溃捕获处理器。"""
    global _FAULT_HANDLER_FILE
    sys.excepthook = _handle_exception
    if hasattr(threading, 'excepthook'):
        threading.excepthook = _handle_thread_exception

    # 启用 faulthandler 捕获 C/C++ 段错误、SIGABRT 等致命信号
    try:
        crash_log_path = _generate_crash_log_path()
        _FAULT_HANDLER_FILE = open(crash_log_path, 'a', encoding='utf-8')
        faulthandler.enable(file=_FAULT_HANDLER_FILE, all_threads=True)
    except Exception:
        pass
if __name__ == '__main__':
    install_crash_handler()
    raise RuntimeError(_('core.infrastructure.crash_handler.auto_001'))