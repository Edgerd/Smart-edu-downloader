# -*- coding: utf-8 -*-
"""启动初始化器。

将程序启动阶段的耗时 IO 操作（如下载器/资源库初始化、缓存清理、
封面缓存过期清理等）放到后台线程执行，避免阻塞 GUI 主线程，
从而解决窗口显示后短暂未响应的问题。
"""

from PyQt5.QtCore import QObject, pyqtSignal, QThread

from core.infrastructure.logger import log


class StartupInitializer(QObject):
    """启动初始化器 - 在后台线程完成耗时初始化并通过信号通知主线程。

    Signals:
        core_modules_ready: 核心模块（Downloader、ResourceLibrary）初始化完成，
            参数为 (downloader, resource_lib)。
        cleanup_finished: 缓存与封面清理完成。
        error_occurred: 初始化过程中发生错误，参数为错误信息字符串。
    """

    core_modules_ready = pyqtSignal(object, object)
    cleanup_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        """初始化启动初始化器。

        Args:
            parent: 父 QObject 对象。
        """
        super().__init__(parent)
        self._worker_thread = None
        self._worker = None

    def start(self):
        """启动后台初始化流程。

        在工作线程中完成 Downloader、ResourceLibrary 的创建以及缓存清理，
        完成后通过信号回到调用者所在线程（通常为 GUI 主线程）。
        """
        self._worker_thread = QThread()
        self._worker = _StartupWorker()
        self._worker.moveToThread(self._worker_thread)

        self._worker_thread.started.connect(self._worker.initialize)
        self._worker.core_modules_ready.connect(self._on_core_modules_ready)
        self._worker.cleanup_finished.connect(self.cleanup_finished)
        self._worker.error_occurred.connect(self.error_occurred)
        self._worker.finished.connect(self._worker_thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker_thread.finished.connect(self._worker_thread.deleteLater)

        self._worker_thread.start()

    def _on_core_modules_ready(self, downloader, resource_lib):
        """核心模块初始化完成的中间处理。

        Downloader 和 ResourceLibrary 在工作线程中创建，保持在该线程中。
        后续所有信号与槽的连接都会自动处理线程归属，无需手动移动对象。

        Args:
            downloader: Downloader 实例，可能为 None。
            resource_lib: ResourceLibrary 实例，可能为 None。
        """
        if downloader is not None:
            log("DEBUG", f"Downloader 保持在 {_StartupWorker.__name__} 线程中")
        if resource_lib is not None:
            log("DEBUG", f"ResourceLibrary 保持在 {_StartupWorker.__name__} 线程中")
        self.core_modules_ready.emit(downloader, resource_lib)


class _StartupWorker(QObject):
    """后台工作对象 - 在独立线程中执行耗时初始化。"""

    core_modules_ready = pyqtSignal(object, object)
    cleanup_finished = pyqtSignal()
    error_occurred = pyqtSignal(str)
    finished = pyqtSignal()

    def initialize(self):
        """执行初始化流程。

        依次完成核心模块创建和缓存清理，任何步骤出错都会记录日志并发射错误信号，
        避免单个失败影响后续流程。
        """
        try:
            downloader, resource_lib = self._init_core_modules()
            self.core_modules_ready.emit(downloader, resource_lib)
        except Exception as e:
            log("ERROR", f"后台初始化核心模块失败: {e}")
            self.error_occurred.emit(f"核心模块初始化失败: {e}")
            self.core_modules_ready.emit(None, None)

        try:
            self._do_cleanup()
            self.cleanup_finished.emit()
        except Exception as e:
            log("WARNING", f"后台清理失败: {e}")
            self.error_occurred.emit(f"启动清理失败: {e}")

        self.finished.emit()

    def _init_core_modules(self):
        """初始化下载器和资源库。

        Returns:
            tuple: (Downloader 实例, ResourceLibrary 实例)。
        """
        from core import Downloader, ResourceLibrary

        log("STEP", "后台初始化下载器与资源库...")
        downloader = Downloader()
        resource_lib = ResourceLibrary()
        log("SUCCESS", "后台初始化下载器与资源库完成")
        return downloader, resource_lib

    def _do_cleanup(self):
        """执行缓存与封面清理。

        读取设置中的缓存策略，在后台完成临时文件、过期缓存和过期封面的清理，
        避免主线程因扫描大目录而卡顿。
        """
        from core.cache.cache_manager import get_cache_manager
        from core import get_cover_cache
        from core.config.settings_manager import get_settings_manager

        log("STEP", "后台执行启动清理...")

        cache_manager = get_cache_manager()
        settings = get_settings_manager().get_all()

        if settings.get("auto_clean_temp", False):
            cache_manager.cleanup_temp_files()

        if settings.get("cache_enabled", True):
            max_size = settings.get("cache_size_limit", 500)
            cleanup_period = settings.get("cache_cleanup_period", "每周")
            _period_to_days = {"每天": 1, "每周": 7, "每月": 30}
            if cleanup_period not in ("never", "从不"):
                cleanup_days = _period_to_days.get(cleanup_period, 7)
                cache_manager.cleanup_cache(max_size, cleanup_days)

        get_cover_cache().clear_expired_covers()
        log("SUCCESS", "后台启动清理完成")
