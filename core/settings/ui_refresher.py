# -*- coding: utf-8 -*-
"""UI 刷新模块。

从 settings 字典刷新设置页面的所有 GUI 控件，将刷新逻辑从 SettingPage
中独立出来，便于维护与单元测试。

注意：重构后 SettingPage._refresh_all_tabs() 直接遍历标签页
并调用 ``tab.refresh_from(settings)``。此类保留主要供
外部直接传入 page 对象使用，内部适配新结构。
"""

from core.config.theme_config import get_theme_config, primary_color


class SettingsRefresher:
    """设置页面 UI 刷新器

    通过 :meth:`refresh_from` 将 ``settings`` 字典中的配置项
    同步到 ``SettingPage`` 实例的各标签页控件上。
    """

    @staticmethod
    def refresh_from(page) -> None:
        """从 settings 字典刷新所有 GUI 控件

        Args:
            page: ``SettingPage`` 实例，需提供 ``settings`` 属性及 ``_tabs`` 字典
        """
        settings = page.settings
        tabs = getattr(page, "_tabs", {})
        for key, tab in tabs.items():
            if hasattr(tab, "refresh_from"):
                tab.refresh_from(settings)

        # 更新主题色相关 UI
        theme_config = getattr(page, "_theme_config", None)
        if theme_config is None:
            theme_config = get_theme_config(page.settings)
        accent = primary_color(theme_config)
        try:
            if hasattr(page, "header_title"):
                page.header_title.setStyleSheet(f"color: {accent};")
        except AttributeError:
            pass
        for tab in tabs.values():
            if hasattr(tab, "set_accent_color"):
                tab.set_accent_color(accent)