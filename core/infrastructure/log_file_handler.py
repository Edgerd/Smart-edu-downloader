# -*- coding: utf-8 -*-
"""文件日志处理器。

支持按日期命名主日志文件、按大小轮转备份、自动清理过期日志以及
崩溃日志目录的过期文件清理。
"""

import os
import time
import threading
import logging
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Optional

from core.infrastructure.logger import LogHandler
from core.infrastructure.path_resolver import get_logs_dir


class FileLogHandler(LogHandler):
    """文件日志处理器（支持轮转和自动管理）。"""

    MAX_BYTES = 5 * 1024 * 1024  # 5MB
    BACKUP_COUNT = 10
    LOG_FILE_PREFIX = "app"
    LOG_FILE_SUFFIX = ".log"

    def __init__(self, logs_dir: Optional[str] = None):
        """初始化文件日志处理器。"""
        if logs_dir is None:
            logs_dir = get_logs_dir()

        self.logs_dir = logs_dir
        self.log_file = os.path.join(
            logs_dir,
            f"{self.LOG_FILE_PREFIX}_{datetime.now().strftime('%Y%m%d')}{self.LOG_FILE_SUFFIX}",
        )
        self.max_bytes = self.MAX_BYTES
        self.backup_count = self.BACKUP_COUNT
        self._lock = threading.Lock()

        self._ensure_log_dir()

        self._handler = RotatingFileHandler(
            filename=self.log_file,
            maxBytes=self.max_bytes,
            backupCount=self.backup_count,
            encoding="utf-8",
        )

        self._formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(module)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self._handler.setFormatter(self._formatter)

    def _ensure_log_dir(self) -> None:
        """确保日志目录存在。"""
        try:
            os.makedirs(self.logs_dir, exist_ok=True)
        except OSError:
            pass

    def emit(self, level: str, module: str, message: str) -> None:
        """输出日志到文件。"""
        try:
            with self._lock:
                level_map = {
                    "DEBUG": logging.DEBUG,
                    "INFO": logging.INFO,
                    "SUCCESS": logging.INFO,
                    "STEP": logging.INFO,
                    "WARNING": logging.WARNING,
                    "ERROR": logging.ERROR,
                }
                log_level = level_map.get(level.upper(), logging.INFO)

                record = logging.LogRecord(
                    name=module,
                    level=log_level,
                    pathname="",
                    lineno=0,
                    msg=message,
                    args=(),
                    exc_info=None,
                )
                record.created = time.time()
                record.asctime = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(record.created)
                )
                record.levelname = level.upper()
                record.module = module

                self._handler.emit(record)
        except Exception:
            pass

    def cleanup(self) -> None:
        """关闭日志文件句柄。"""
        try:
            with self._lock:
                self._handler.close()
        except Exception:
            pass


def _get_retention_days(days: Optional[int]) -> int:
    """获取日志保留天数，None 时从设置读取，失败返回 7。"""
    if days is not None:
        return days
    try:
        # 局部导入避免循环依赖
        from core.config.settings_manager import get_setting
        configured = get_setting("log_retention_days", 7)
        return int(configured) if configured is not None else 7
    except Exception:
        return 7


def _clean_directory(directory: str, cutoff_time: float) -> int:
    """清理目录中修改时间早于阈值的文件。"""
    deleted_count = 0
    if not os.path.exists(directory):
        return deleted_count

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isdir(filepath):
            continue

        try:
            file_mtime = os.path.getmtime(filepath)
            if file_mtime < cutoff_time:
                os.remove(filepath)
                deleted_count += 1
        except OSError:
            continue

    return deleted_count


def clean_old_logs(logs_dir: Optional[str] = None, days: Optional[int] = None) -> int:
    """清理指定天数之前的旧日志文件。"""
    deleted_count = 0

    try:
        if logs_dir is None:
            from core.infrastructure.path_resolver import get_logs_dir
            logs_dir = get_logs_dir()

        retention_days = _get_retention_days(days)
        cutoff_time = time.time() - (retention_days * 24 * 60 * 60)

        deleted_count += _clean_directory(logs_dir, cutoff_time)

        try:
            from core.infrastructure.path_resolver import get_crash_logs_dir
            crash_logs_dir = get_crash_logs_dir()
            deleted_count += _clean_directory(crash_logs_dir, cutoff_time)
        except Exception:
            pass

    except Exception:
        pass

    return deleted_count
