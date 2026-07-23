# -*- coding: utf-8 -*-
"""设置收集模块"""

from typing import Any, Dict


class SettingsCollector:
    """设置收集器——从标签页控件读取值并收集到 settings 字典

    注意：重构后 SettingPage._collect_settings() 直接遍历标签页
    并调用 ``tab.collect_settings(settings)``。此类保留主要供
    外部直接传入 page 对象使用，内部适配新结构。
    """

    def __init__(self, settings: Dict[str, Any]):
        """初始化设置收集器"""
        self._settings = settings

    @staticmethod
    def _normalize_domain(domain: str) -> str:
        """规范化域名"""
        if not domain:
            return ""
        d = domain.strip().lower()
        for prefix in ("http://", "https://"):
            if d.startswith(prefix):
                d = d[len(prefix):]
                break
        for sep in ("/", "?", "#"):
            if sep in d:
                d = d.split(sep, 1)[0]
                break
        return d.strip()

    def collect_from(self, page) -> None:
        """从 SettingPage 实例收集所有设置（适配新标签页结构）"""
        tabs = getattr(page, "_tabs", {})
        for key, tab in tabs.items():
            if hasattr(tab, "collect_settings"):
                tab.collect_settings(self._settings)

        # 补充主题配置（由 SettingPage 管理）
        theme_config = getattr(page, "_theme_config", None)
        if theme_config:
            self._settings["theme_color"] = theme_config