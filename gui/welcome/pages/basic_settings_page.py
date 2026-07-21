# -*- coding: utf-8 -*-
"""基本设置页面。

配置默认下载目录与下载前是否询问位置。
"""

import os
import re
from typing import Any, Dict, Optional

from PyQt5.QtCore import Qt, QByteArray
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFileDialog,
    QFrame,
)

from core.i18n import _
from core.config.settings_manager import get_default_download_dir, get_setting
from core.infrastructure.path_resolver import get_project_root
from gui.fonts import body_font, small_font, title_font, subtitle_font
from gui.styles import load_primary_color
from gui.widgets import SwitchWithLabel
from gui.widgets.material_button import MaterialButton
from gui.components.circle_nav_button import CircleNavButton
from gui.welcome.pages.base_page import BaseWelcomePage


class BasicSettingsPage(BaseWelcomePage):
    """基本设置页。

    收集下载目录与 ``ask_download_dir`` 配置。

    属性:
        download_dir: 当前输入框中的下载目录路径。
        ask_download_dir: 是否每次下载前询问位置。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化基本设置页。"""
        super().__init__(parent)
        self._create_content()

    def _create_title(self) -> QLabel:
        """页面标题。"""
        title = QLabel(_("welcome_onboarding.basic_settings.title"))
        title.setFont(title_font())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #212121;")
        return title

    def _create_subtitle(self) -> QLabel:
        """页面副标题。"""
        subtitle = QLabel(_("welcome_onboarding.basic_settings.subtitle"))
        subtitle.setFont(subtitle_font())
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666666;")
        return subtitle

    def _create_content(self) -> None:
        """创建基本设置页内容。"""
        self.title_label.setText(_("welcome_onboarding.basic_settings.title"))
        self.subtitle_label.setText(_("welcome_onboarding.basic_settings.subtitle"))

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 8px;
                border: none;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(20, 20, 20, 20)

        # 文件保存位置行
        dir_row = QHBoxLayout()
        dir_row.setSpacing(12)

        icon_label = QLabel()
        icon_label.setFixedSize(32, 32)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_path = os.path.join(
            get_project_root(), "resources", "images", "welcome", "download.svg"
        )
        if os.path.exists(icon_path):
            icon_label.setPixmap(
                self._load_colored_svg_pixmap(icon_path, self._accent_color, 24)
            )
        self._icon_label = icon_label
        dir_row.addWidget(icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        dir_title = QLabel(_("welcome_onboarding.basic_settings.file_save_location"))
        dir_title.setFont(body_font())
        dir_title.setStyleSheet("color: #212121; font-weight: bold;")
        text_layout.addWidget(dir_title)
        dir_desc = QLabel(_("welcome_onboarding.basic_settings.file_save_location_desc"))
        dir_desc.setFont(small_font())
        dir_desc.setStyleSheet("color: #888888;")
        text_layout.addWidget(dir_desc)
        dir_row.addLayout(text_layout)
        dir_row.addStretch()

        card_layout.addLayout(dir_row)

        # 输入框与浏览按钮
        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self.dir_input = QLineEdit()
        self.dir_input.setFont(body_font())
        self.dir_input.setText(get_default_download_dir())
        self._refresh_input_style()
        input_row.addWidget(self.dir_input, 1)

        self.browse_btn = MaterialButton(_("common.browse"))
        self.browse_btn.setFont(body_font())
        self.browse_btn.setFixedHeight(32)
        self.browse_btn.setAccentColor(self._accent_color)
        self.browse_btn.clicked.connect(self._on_browse)
        input_row.addWidget(self.browse_btn)

        card_layout.addLayout(input_row)

        # 询问下载位置开关（无图标、无描述）
        switch_row = QHBoxLayout()
        switch_row.setSpacing(12)
        switch_title = QLabel(_("welcome_onboarding.basic_settings.ask_before_download"))
        switch_title.setFont(body_font())
        switch_title.setStyleSheet("color: #212121;")
        switch_row.addWidget(switch_title)
        switch_row.addStretch()

        self.ask_switch = SwitchWithLabel("", checked=False)
        self.ask_switch.switch.set_on_color(self._accent_color)
        self.ask_switch.toggled.connect(self._on_ask_switch_changed)
        switch_row.addWidget(self.ask_switch)

        card_layout.addLayout(switch_row)

        self.add_centered_content(card, Qt.AlignCenter)

        # 下一步按钮
        self.next_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_r.svg"),
            button_style=CircleNavButton.STYLE_ACCENT,
            tooltip=_("welcome_onboarding.basic_settings.next_tip"),
            parent=self,
        )
        self.next_btn.setAccentColor(self._accent_color)
        self.set_nav_buttons(self.next_btn)

        # 根据初始状态刷新下载位置可用性
        self._refresh_download_dir_enabled()

    def _refresh_input_style(self) -> None:
        """刷新输入框样式以应用当前主题色。"""
        self.dir_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid #E0E8F0;
                border-radius: 6px;
                padding: 6px 10px;
                background: #F8FAFC;
                outline: none;
            }}
            QLineEdit:focus {{
                border-color: {self._accent_color};
                background: white;
                outline: none;
            }}
            QLineEdit:disabled {{
                background: #F0F0F0;
                color: #999999;
                border-color: #E0E0E0;
            }}
        """)

    def _on_ask_switch_changed(self, checked: bool) -> None:
        """询问开关状态变化时同步禁用/启用下载位置输入。"""
        self._refresh_download_dir_enabled()

    def _refresh_download_dir_enabled(self) -> None:
        """根据询问开关状态刷新下载位置控件的可用性。"""
        enabled = not self.ask_switch.isChecked()
        self.dir_input.setEnabled(enabled)
        self.browse_btn.setEnabled(enabled)

    def _load_colored_svg_pixmap(
        self, svg_path: str, color: str, size: int
    ) -> QPixmap:
        """读取 SVG 并按主题色渲染为指定尺寸的位图。

        Args:
            svg_path: SVG 文件绝对路径。
            color: 目标颜色十六进制字符串。
            size: 输出位图尺寸。

        Returns:
            着色后的 QPixmap。
        """
        try:
            with open(svg_path, "r", encoding="utf-8") as f:
                svg_data = f.read()
            svg_data = re.sub(
                r'(?i)fill="[^"]*"', f'fill="{color}"', svg_data
            )
            renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
            pixmap = QPixmap(size, size)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            try:
                renderer.render(painter)
            finally:
                if painter.isActive():
                    painter.end()
            return pixmap
        except Exception:
            return QPixmap(size, size)

    def set_initial_values(self, settings: Dict[str, Any]) -> None:
        """从已有设置加载默认值。

        Args:
            settings: 当前设置字典。
        """
        if "download_dir" in settings:
            self.dir_input.setText(settings["download_dir"])
        if "ask_download_dir" in settings:
            self.ask_switch.setChecked(bool(settings["ask_download_dir"]))

    def set_accent_color(self, color: str) -> None:
        """更新页面主题色。

        Args:
            color: 新的主题色十六进制字符串。
        """
        super().set_accent_color(color)
        self._refresh_input_style()
        if hasattr(self, "browse_btn") and self.browse_btn:
            self.browse_btn.setAccentColor(color)
        if hasattr(self, "ask_switch") and self.ask_switch:
            self.ask_switch.switch.set_on_color(color)
        if hasattr(self, "next_btn") and self.next_btn:
            self.next_btn.setAccentColor(color)
        if hasattr(self, "_icon_label") and self._icon_label:
            icon_path = os.path.join(
                get_project_root(), "resources", "images", "welcome", "download.svg"
            )
            if os.path.exists(icon_path):
                self._icon_label.setPixmap(
                    self._load_colored_svg_pixmap(icon_path, color, 24)
                )

    def reload_texts(self) -> None:
        """重新加载页面翻译文本。"""
        self.title_label.setText(_("welcome_onboarding.basic_settings.title"))
        self.subtitle_label.setText(_("welcome_onboarding.basic_settings.subtitle"))
        if hasattr(self, "browse_btn") and self.browse_btn:
            self.browse_btn.setText(_("common.browse"))

    def _on_browse(self) -> None:
        """点击浏览按钮选择下载目录。"""
        current = self.dir_input.text() or get_default_download_dir()
        path = QFileDialog.getExistingDirectory(
            self,
            _("settings.common.select_download_dir"),
            current,
        )
        if path:
            self.dir_input.setText(path)

    def get_download_dir(self) -> str:
        """返回当前输入框中的下载目录。"""
        return self.dir_input.text()

    def get_ask_download_dir(self) -> bool:
        """返回是否每次下载前询问位置。"""
        return self.ask_switch.isChecked()
