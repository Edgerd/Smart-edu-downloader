"""统一日志模块。

提供线程安全的日志功能，支持控制台、GUI 调试面板以及文件等多种输出目标。
"""
import os
import sys
import threading
from datetime import datetime
from typing import Optional

# 日志级别内部常量（与语言无关，统一使用英文标识）
LOG_LEVEL_DEBUG = 'DEBUG'
LOG_LEVEL_INFO = 'INFO'
LOG_LEVEL_WARNING = 'WARNING'
LOG_LEVEL_ERROR = 'ERROR'

# 兼容旧版设置中可能出现的中文级别值
_LEGACY_LEVEL_MAP = {
    '调试': LOG_LEVEL_DEBUG,
    '信息': LOG_LEVEL_INFO,
    '警告': LOG_LEVEL_WARNING,
    '错误': LOG_LEVEL_ERROR,
}


def _normalize_log_level(level: Optional[str]) -> str:
    """将日志级别统一转换为内部常量值。

    Args:
        level: 原始日志级别值。

    Returns:
        str: 规范化后的日志级别常量。
    """
    if not level:
        return LOG_LEVEL_INFO
    level = level.strip().upper()
    if level in (LOG_LEVEL_DEBUG, LOG_LEVEL_INFO, LOG_LEVEL_WARNING, LOG_LEVEL_ERROR):
        return level
    return _LEGACY_LEVEL_MAP.get(level, LOG_LEVEL_INFO)


class LogHandler:
    """日志处理器基类。"""

    def emit(self, level: str, module: str, message: str) -> None:
        """输出日志。"""
        raise NotImplementedError

class GUIHandler(LogHandler):
    """GUI 日志处理器。"""

    def __init__(self) -> None:
        self._debug_manager = None
        self._lock = threading.RLock()

    def _get_debug_manager(self):
        """延迟获取调试管理器，避免启动时循环依赖。"""
        if self._debug_manager is None:
            with self._lock:
                if self._debug_manager is None:
                    try:
                        from gui.debug_panel import get_debug_manager
                        self._debug_manager = get_debug_manager()
                    except Exception:
                        self._debug_manager = False
        return self._debug_manager if self._debug_manager is not None else None

    def emit(self, level: str, module: str, message: str) -> None:
        """输出日志到 GUI 调试面板。"""
        try:
            dm = self._get_debug_manager()
            if dm:
                dm.log(f'[{module}] {message}', level)
        except Exception:
            pass

class ConsoleHandler(LogHandler):
    """控制台日志处理器。"""

    def emit(self, level: str, module: str, message: str) -> None:
        """输出日志到控制台。"""
        try:
            print(f'[{level}] [{module}] {message}', file=sys.stderr)
        except Exception:
            pass

class Logger:
    """统一日志记录器（单例）。"""
    _instance = None
    _lock = threading.Lock()
    _LEVEL_MAP = {
        LOG_LEVEL_DEBUG: 10,
        LOG_LEVEL_INFO: 20,
        LOG_LEVEL_WARNING: 30,
        LOG_LEVEL_ERROR: 40,
        'DEBUG': 10,
        'INFO': 20,
        'SUCCESS': 20,
        'STEP': 20,
        'WARNING': 30,
        'ERROR': 40,
    }

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._handlers = []
        self._module_name = 'Global'
        self._log_level = LOG_LEVEL_INFO
        self._initialized = True

    def _level_value(self, level: str) -> int:
        """返回日志级别的权重值。"""
        return self._LEVEL_MAP.get(level, 20)

    def _current_level_threshold(self) -> int:
        """获取当前日志级别阈值。"""
        return self._level_value(self._log_level)

    def _should_emit(self, level: str) -> bool:
        """判断指定级别是否满足当前日志过滤条件。"""
        return self._level_value(level) >= self._current_level_threshold()

    def _refresh_log_level(self) -> None:
        """从设置管理器刷新日志级别。"""
        try:
            from core.config.settings_manager import get_setting
            level = get_setting('log_level', LOG_LEVEL_INFO)
            normalized = _normalize_log_level(level)
            if normalized in self._LEVEL_MAP:
                self._log_level = normalized
        except Exception:
            self._log_level = LOG_LEVEL_INFO

    def add_handler(self, handler: LogHandler) -> None:
        """添加日志处理器。"""
        self._handlers.append(handler)

    def set_module_name(self, module_name: str) -> None:
        """设置当前模块名称。"""
        self._module_name = module_name

    def set_log_level(self, level: str) -> None:
        """设置日志级别。"""
        normalized = _normalize_log_level(level)
        if normalized in self._LEVEL_MAP:
            self._log_level = normalized

    def _emit(self, level: str, message: str) -> None:
        """输出日志到所有处理器。"""
        self._refresh_log_level()
        if not self._should_emit(level):
            return
        for handler in self._handlers:
            try:
                handler.emit(level, self._module_name, message)
            except Exception:
                pass

    def debug(self, message: str) -> None:
        """输出 DEBUG 级别日志。"""
        self._emit('DEBUG', message)

    def info(self, message: str) -> None:
        """输出 INFO 级别日志。"""
        self._emit('INFO', message)

    def warning(self, message: str) -> None:
        """输出 WARNING 级别日志。"""
        self._emit('WARNING', message)

    def error(self, message: str) -> None:
        """输出 ERROR 级别日志。"""
        self._emit('ERROR', message)

    def success(self, message: str) -> None:
        """输出 SUCCESS 级别日志。"""
        self._emit('SUCCESS', message)

    def step(self, message: str) -> None:
        """输出 STEP 级别日志。"""
        self._emit('STEP', message)

    def log(self, level: str, message: str) -> None:
        """通用日志输出方法。"""
        self._emit(level, message)

def _get_global_logger() -> Logger:
    """获取全局日志单例。"""
    return Logger()

def get_logger(module_name: Optional[str]=None) -> Logger:
    """获取日志记录器实例。"""
    logger = _get_global_logger()
    if module_name:
        logger.set_module_name(module_name)
    return logger

def setup_gui_logging() -> None:
    """设置 GUI 日志输出。"""
    _get_global_logger().add_handler(GUIHandler())
    setup_file_logging()


def setup_file_logging() -> None:
    """设置文件日志输出。"""
    try:
        from core.infrastructure.log_file_handler import FileLogHandler, clean_old_logs
        deleted_count = clean_old_logs()
        info(f"已清理 {deleted_count} 个过期日志文件")
        _get_global_logger().add_handler(FileLogHandler())
    except Exception as e:
        info(f"文件日志初始化失败，已回退为仅控制台日志: {e}")

def log_crash_safe(crash_log_path: str, summary: str, traceback_text: str) -> None:
    """以原始文件追加模式写入崩溃信息，写入失败时静默处理。"""
    try:
        os.makedirs(os.path.dirname(crash_log_path), exist_ok=True)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(crash_log_path, 'a', encoding='utf-8') as f:
            f.write(f'[{timestamp}] {summary}\n')
            f.write(traceback_text)
            f.write('\n' + '=' * 60 + '\n')
    except Exception:
        pass

def log(level: str, message: str, module: Optional[str]=None) -> None:
    """便捷日志函数。"""
    logger = _get_global_logger()
    if module:
        logger.set_module_name(module)
    logger.log(level, message)

def debug(message: str, module: Optional[str]=None) -> None:
    """便捷 DEBUG 日志。"""
    log('DEBUG', message, module)

def info(message: str, module: Optional[str]=None) -> None:
    """便捷 INFO 日志。"""
    log('INFO', message, module)

def warning(message: str, module: Optional[str]=None) -> None:
    """便捷 WARNING 日志。"""
    log('WARNING', message, module)

def error(message: str, module: Optional[str]=None) -> None:
    """便捷 ERROR 日志。"""
    log('ERROR', message, module)

def success(message: str, module: Optional[str]=None) -> None:
    """便捷 SUCCESS 日志。"""
    log('SUCCESS', message, module)

def step(message: str, module: Optional[str]=None) -> None:
    """便捷 STEP 日志。"""
    log('STEP', message, module)
if __name__ == '__main__':
    get_logger().add_handler(ConsoleHandler())
    info('信息级别日志测试')
    debug('调试级别日志测试')
    error('错误级别日志测试')
