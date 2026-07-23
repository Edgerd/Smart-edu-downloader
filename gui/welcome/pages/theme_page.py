# -*- coding: utf-8 -*-
"""主题设置页面。

复用 :class:`gui.components.theme_selector.ThemeSelector`，允许用户在首次启动时
选择主题预设或自定义主题颜色。
"""

import os
from typing import Any, Dict, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QScrollArea,
    QFrame,
)

from core.config.theme_config import config_from_preset_key, get_theme_config
from core.i18n import _
from gui.fonts import title_font, subtitle_font
from gui.components.theme_selector import ThemeSelector
from gui.components.circle_nav_button import CircleNavButton
from gui.welcome.pages.base_page import BaseWelcomePage


class ThemePage(BaseWelcomePage):
    """主题设置页。

    通过复用设置页中的主题选择器收集用户的主题偏好。

    属性:
        theme_config: 当前选中的主题配置字典。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化主题设置页。"""
        super().__init__(parent)
        self._create_content()

    def _create_title(self) -> QLabel:
        """页面标题，左对齐显示。"""
        title = QLabel(_("welcome_onboarding.theme.title"))
        title.setFont(title_font())
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title.setStyleSheet("color: #212121;")
        return title

    def _create_subtitle(self) -> QLabel:
        """页面副标题，左对齐显示。"""
        subtitle = QLabel(_("welcome_onboarding.theme.subtitle"))
        subtitle.setFont(subtitle_font())
        subtitle.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        subtitle.setStyleSheet("color: #666666;")
        return subtitle

    def _create_content(self) -> None:
        """创建主题选择区域与导航按钮。"""
        self.title_label.setText(_("welcome_onboarding.theme.title"))
        self.subtitle_label.setText(_("welcome_onboarding.theme.subtitle"))

        self.theme_selector = ThemeSelector(self, config_from_preset_key("jingdianlan"), show_title=False)
        self.theme_selector.set_accent_color(self._accent_color)

        # 将主题选择器放入滚动区，避免窗口高度不足时内容被截断
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollArea > QWidget > QWidget { background: transparent; }
        """)
        scroll.setWidget(self.theme_selector)

        self.add_centered_content(scroll, Qt.AlignCenter)

        self.prev_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_l.svg"),
            button_style=CircleNavButton.STYLE_LIGHT,
            tooltip=_("welcome_onboarding.theme.previous_tip"),
            parent=self,
        )
        self.next_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_r.svg"),
            button_style=CircleNavButton.STYLE_ACCENT,
            tooltip=_("welcome_onboarding.theme.next_tip"),
            parent=self,
        )
        self.next_btn.setAccentColor(self._accent_color)
        self.set_nav_buttons(self.prev_btn, self.next_btn)

    def get_theme_config(self) -> Dict[str, Any]:
        """返回当前选中的主题配置字典副本。"""
        return self.theme_selector.get_theme_config()

    def set_initial_values(self, settings: Dict[str, Any]) -> None:
        """从已有设置加载当前主题配置。

        Args:
            settings: 当前设置字典。
        """
        theme_config = get_theme_config(settings)
        if theme_config:
            self.theme_selector.set_theme_config(theme_config)

    def set_accent_color(self, color: str) -> None:
        """更新页面主题色并同步刷新主题选择器。

        Args:
            color: 新的主题色十六进制字符串。
        """
        super().set_accent_color(color)
        if self.theme_selector:
            self.theme_selector.set_accent_color(color)
        if hasattr(self, "next_btn") and self.next_btn:
            self.next_btn.setAccentColor(color)
        if hasattr(self, "prev_btn") and self.prev_btn:
            self.prev_btn.setAccentColor(color)

    def reload_texts(self) -> None:
        """重新加载页面翻译文本。"""
        self.title_label.setText(_("welcome_onboarding.theme.title"))
        self.subtitle_label.setText(_("welcome_onboarding.theme.subtitle"))
