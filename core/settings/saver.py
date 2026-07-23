# -*- coding: utf-8 -*-
"""
设置保存模块
负责将收集的设置保存到存储，并应用相关配置到运行中的组件
"""

import traceback
from typing import Any, Dict, Optional

from core.infrastructure.logger import log


class SettingsSaver:
    """设置保存器 - 负责持久化设置并应用到运行时组件

    职责：
    - 保存设置到 SettingsManager
    - 应用代理配置到下载器
    - 应用剪贴板监控设置
    """

    @staticmethod
    def save_settings(settings: Dict[str, Any]) -> None:
        """保存设置到统一设置管理器

        Args:
            settings: 完整的设置字典
        """
        from core.config.settings_manager import get_settings_manager
        get_settings_manager().update(settings)
        log("SUCCESS", "设置已保存")

    @staticmethod
    def apply_proxy_to_downloader(settings: Dict[str, Any], downloader) -> None:
        """实时应用代理设置到下载器

        Args:
            settings: 设置字典
            downloader: Downloader 实例
        """
        if not downloader:
            return

        try:
            if settings.get("proxy_enabled", False):
                proxy_config = {
                    "type": settings.get("proxy_type", "http"),
                    "host": settings.get("proxy_host", ""),
                    "port": settings.get("proxy_port", ""),
                    "username": settings.get("proxy_username", ""),
                    "password": settings.get("proxy_password", "")
                }
                downloader.set_proxy(proxy_config)
            else:
                downloader.set_proxy(None)
        except Exception as e:
            log("ERROR", f"应用代理设置失败: {e}\n{traceback.format_exc()}")

    @staticmethod
    def apply_clipboard_monitor_settings(settings: Dict[str, Any]) -> None:
        """实时应用剪贴板监控设置

        Args:
            settings: 设置字典
        """
        try:
            from gui.main_window import get_main_window
            main_window = get_main_window()
            if not main_window or not hasattr(main_window, 'clipboard_monitor') or main_window.clipboard_monitor is None:
                return

            enabled = settings.get("clipboard_monitor_enabled", True)
            interval = settings.get("clipboard_check_interval", 1000)

            if enabled and not main_window.clipboard_monitor.is_enabled():
                main_window.clipboard_monitor.set_check_interval(interval)
                main_window.clipboard_monitor.start()
                log("INFO", "剪贴板监控已启用")
            elif not enabled and main_window.clipboard_monitor.is_enabled():
                main_window.clipboard_monitor.stop()
                log("INFO", "剪贴板监控已禁用")
            elif enabled:
                main_window.clipboard_monitor.set_check_interval(interval)
        except Exception as e:
            log("ERROR", f"应用剪贴板监控设置失败: {e}\n{traceback.format_exc()}")

    @staticmethod
    def update_download_dir(settings: Dict[str, Any], downloader) -> None:
        """更新下载器的下载目录

        Args:
            settings: 设置字典
            downloader: Downloader 实例
        """
        if downloader:
            downloader.set_download_dir(settings.get("download_dir", ""))