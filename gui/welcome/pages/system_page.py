# -*- coding: utf-8 -*-
"""系统快捷方式设置页面。

允许用户选择是否在桌面和开始菜单创建快捷方式。
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
    QFrame,
)

from core.i18n import _
from core.infrastructure.path_resolver import get_project_root
from core.config.theme_config import ICON_BASE_COLORS
from gui.fonts import title_font, subtitle_font, body_font, small_font
from gui.components.material_checkbox import MaterialCheckBox
from gui.components.circle_nav_button import CircleNavButton
from gui.welcome.pages.base_page import BaseWelcomePage


# 在图标基准色基础上增加常用暗色占位
_ICON_FILL_COLORS = ICON_BASE_COLORS | {"#000000", "#000", "#212121"}
_FILL_REGEX = re.compile(
    rf'fill="({"|".join(re.escape(c) for c in _ICON_FILL_COLORS)})"',
    re.IGNORECASE,
)


class _OptionRow(QWidget):
    """单个可点击的快捷方式选项行。

    点击行内任意位置（图标、标题、描述）都会切换右侧复选框状态，
    整个行作为可点击区域，提升交互易用性。

    属性:
        checkbox: 右侧的 MaterialCheckBox 实例。
    """

    def __init__(
        self,
        title_text: str,
        desc_text: str,
        icon_pixmap: Optional[QPixmap],
        accent_color: str,
        parent: Optional[QWidget] = None,
    ):
        """初始化选项行。

        Args:
            title_text: 选项主标题。
            desc_text: 选项描述文本。
            icon_pixmap: 已着色的图标 QPixmap，可为 None。
            accent_color: 当前主题色。
            parent: 父组件。
        """
        super().__init__(parent)
        self._accent_color = accent_color
        self._init_ui(title_text, desc_text, icon_pixmap)
        self.setCursor(Qt.PointingHandCursor)

    def _init_ui(
        self,
        title_text: str,
        desc_text: str,
        icon_pixmap: Optional[QPixmap],
    ) -> None:
        """构建行内布局。"""
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignVCenter)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(40, 40)
        self.icon_label.setAlignment(Qt.AlignCenter)
        if icon_pixmap is not None:
            self.icon_label.setPixmap(
                icon_pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        layout.addWidget(self.icon_label)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        self.title_label = QLabel(title_text)
        self.title_label.setFont(body_font())
        self.title_label.setStyleSheet("color: #212121; font-weight: bold;")
        text_layout.addWidget(self.title_label)

        self.desc_label = QLabel(desc_text)
        self.desc_label.setFont(small_font())
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #888888;")
        text_layout.addWidget(self.desc_label)
        layout.addLayout(text_layout)

        layout.addStretch()

        self.checkbox = MaterialCheckBox()
        self.checkbox.setFixedSize(24, 24)
        self.checkbox.setAccentColor(self._accent_color)
        layout.addWidget(self.checkbox)

    def mousePressEvent(self, event) -> None:
        """点击行时切换复选框状态。

        若点击位置落在右侧复选框本身，则不重复切换，
        避免与 ``MaterialCheckBox`` 自身的事件处理冲突。
        """
        if (
            event.button() == Qt.LeftButton
            and self.isEnabled()
            and not self.checkbox.geometry().contains(event.pos())
        ):
            self.checkbox.setChecked(not self.checkbox.isChecked())
        super().mousePressEvent(event)

    def enterEvent(self, event) -> None:
        """鼠标进入时高亮标题。"""
        self.title_label.setStyleSheet(f"color: {self._accent_color}; font-weight: bold;")
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """鼠标离开时恢复标题颜色。"""
        self.title_label.setStyleSheet("color: #212121; font-weight: bold;")
        super().leaveEvent(event)


class SystemPage(BaseWelcomePage):
    """系统集成功能设置页。

    通过可点击选项行收集桌面和开始菜单快捷方式的创建选项。

    属性:
        shortcuts: 包含两个布尔选项的字典。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化系统设置页。"""
        super().__init__(parent)
        self._create_content()

    def _create_title(self) -> QLabel:
        """页面标题。"""
        title = QLabel(_("welcome_onboarding.system.title"))
        title.setFont(title_font())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #212121;")
        return title

    def _create_subtitle(self) -> QLabel:
        """页面副标题。"""
        subtitle = QLabel(_("welcome_onboarding.system.subtitle"))
        subtitle.setFont(subtitle_font())
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #666666;")
        return subtitle

    def _create_content(self) -> None:
        """创建快捷方式选项卡片与导航按钮。"""
        self.title_label.setText(_("welcome_onboarding.system.title"))
        self.subtitle_label.setText(_("welcome_onboarding.system.subtitle"))

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

        self.desktop_row = self._create_option_row(
            card_layout,
            _("welcome_onboarding.system.create_desktop_shortcut"),
            _("welcome_onboarding.system.create_desktop_shortcut_desc"),
            "desktop",
        )
        self.start_menu_row = self._create_option_row(
            card_layout,
            _("welcome_onboarding.system.create_start_menu_shortcut"),
            _("welcome_onboarding.system.create_start_menu_shortcut_desc"),
            "start_menu",
        )

        self.add_content(card, Qt.AlignCenter)

        self.prev_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_l.svg"),
            button_style=CircleNavButton.STYLE_LIGHT,
            tooltip=_("welcome_onboarding.system.previous_tip"),
            parent=self,
        )
        self.next_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_r.svg"),
            button_style=CircleNavButton.STYLE_ACCENT,
            tooltip=_("welcome_onboarding.system.next_tip"),
            parent=self,
        )
        self.next_btn.setAccentColor(self._accent_color)
        self.set_nav_buttons(self.prev_btn, self.next_btn)

    def _create_option_row(
        self,
        parent_layout: QVBoxLayout,
        title_text: str,
        desc_text: str,
        icon_kind: str,
    ) -> _OptionRow:
        """创建单个快捷方式选项行。

        Args:
            parent_layout: 用于添加选项行的父布局。
            title_text: 选项主标题。
            desc_text: 选项描述文本。
            icon_kind: 图标类型，``desktop`` 或 ``start_menu``。

        Returns:
            该选项对应的 _OptionRow 实例。
        """
        icon_path = os.path.join(
            get_project_root(), "resources", "images", "welcome", f"{icon_kind}.svg"
        )
        pixmap = self._load_colored_svg_pixmap(icon_path, self._accent_color, (24, 24))

        row = _OptionRow(title_text, desc_text, pixmap, self._accent_color, parent=self)
        parent_layout.addWidget(row)
        return row

    @staticmethod
    def _load_colored_svg_pixmap(
        icon_path: str,
        color: str,
        size: tuple,
    ) -> Optional[QPixmap]:
        """读取 SVG 文件并按主题色渲染为 QPixmap。

        Args:
            icon_path: SVG 文件路径。
            color: 目标颜色。
            size: 输出尺寸。

        Returns:
            着色后的 QPixmap，文件不存在或渲染失败返回 None。
        """
        if not os.path.exists(icon_path):
            return None
        try:
            with open(icon_path, "r", encoding="utf-8") as f:
                svg_content = f.read()
            svg_content = _FILL_REGEX.sub(f'fill="{color}"', svg_content)
            renderer = QSvgRenderer(QByteArray(svg_content.encode("utf-8")))
            if not renderer.isValid():
                return None
            pixmap = QPixmap(size[0], size[1])
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
            return None

    def get_shortcuts(self) -> Dict[str, bool]:
        """返回快捷方式设置字典。"""
        return {
            "create_desktop_shortcut": self.desktop_row.checkbox.isChecked(),
            "create_start_menu_shortcut": self.start_menu_row.checkbox.isChecked(),
        }

    def set_initial_values(self, settings: Dict[str, Any]) -> None:
        """从已有设置加载快捷方式选项默认值。

        Args:
            settings: 当前设置字典。
        """
        if "create_desktop_shortcut" in settings:
            self.desktop_row.checkbox.setChecked(
                bool(settings["create_desktop_shortcut"])
            )
        if "create_start_menu_shortcut" in settings:
            self.start_menu_row.checkbox.setChecked(
                bool(settings["create_start_menu_shortcut"])
            )

    def set_accent_color(self, color: str) -> None:
        """更新页面主题色。

        Args:
            color: 新的主题色十六进制字符串。
        """
        super().set_accent_color(color)
        if hasattr(self, "next_btn") and self.next_btn:
            self.next_btn.setAccentColor(color)
        if hasattr(self, "prev_btn") and self.prev_btn:
            self.prev_btn.setAccentColor(color)
        if hasattr(self, "desktop_row") and self.desktop_row:
            self.desktop_row.checkbox.setAccentColor(color)
            self.desktop_row._accent_color = color
            # 更新图标颜色
            icon_path = os.path.join(
                get_project_root(), "resources", "images", "welcome", "desktop.svg"
            )
            pixmap = self._load_colored_svg_pixmap(icon_path, color, (24, 24))
            if pixmap:
                self.desktop_row.icon_label.setPixmap(
                    pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
        if hasattr(self, "start_menu_row") and self.start_menu_row:
            self.start_menu_row.checkbox.setAccentColor(color)
            self.start_menu_row._accent_color = color
            # 更新图标颜色
            icon_path = os.path.join(
                get_project_root(), "resources", "images", "welcome", "start_menu.svg"
            )
            pixmap = self._load_colored_svg_pixmap(icon_path, color, (24, 24))
            if pixmap:
                self.start_menu_row.icon_label.setPixmap(
                    pixmap.scaled(24, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )

    def reload_texts(self) -> None:
        """重新加载页面翻译文本。"""
        self.title_label.setText(_("welcome_onboarding.system.title"))
        self.subtitle_label.setText(_("welcome_onboarding.system.subtitle"))
