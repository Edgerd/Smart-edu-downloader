# -*- coding: utf-8 -*-
"""教程展示页面。

用于新手引导中的两页教程，分别展示主页和资源库的使用说明。
"""

import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QSizePolicy,
)

from core.i18n import _
from core.infrastructure.path_resolver import get_project_root
from gui.fonts import body_font
from gui.components.circle_nav_button import CircleNavButton
from gui.welcome.pages.base_page import BaseWelcomePage


class TutorialPage(BaseWelcomePage):
    """教程页。

    根据教程索引加载对应的截图与说明文字。

    属性:
        tutorial_index: 当前教程页序号（从 1 开始）。
    """

    # 内容区最大可用宽高，用于限制截图缩放尺寸
    MAX_IMAGE_WIDTH = 760
    MAX_IMAGE_HEIGHT = 360

    def __init__(self, tutorial_index: int, parent: Optional[QWidget] = None):
        """初始化教程页。

        Args:
            tutorial_index: 教程页序号，取值为 1 或 2。
            parent: 父组件。
        """
        super().__init__(parent)
        self.tutorial_index = tutorial_index
        self._raw_pixmap: Optional[QPixmap] = None
        self._create_content()

    def _create_title(self) -> QLabel:
        """教程页不使用标题。"""
        title = QLabel("")
        title.hide()
        return title

    def _create_subtitle(self) -> QLabel:
        """教程页不使用副标题。"""
        subtitle = QLabel("")
        subtitle.hide()
        return subtitle

    def _create_content(self) -> None:
        """创建截图与说明文字区域。"""
        self.title_label.hide()
        self.subtitle_label.hide()

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setAlignment(Qt.AlignCenter)

        image_path = os.path.join(
            get_project_root(),
            "resources",
            "images",
            "welcome",
            "Teach",
            f"{self.tutorial_index}.png",
        )

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        self.image_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.image_label.setMinimumSize(200, 120)
        if os.path.exists(image_path):
            self._raw_pixmap = QPixmap(image_path)
            self._scale_image()
        content_layout.addWidget(self.image_label, 1, Qt.AlignCenter)

        description_key = f"welcome_onboarding.tutorial_{self.tutorial_index}.description"
        self.desc_label = QLabel(_(description_key))
        self.desc_label.setFont(body_font())
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #333333;")
        content_layout.addWidget(self.desc_label, 0, Qt.AlignCenter)

        self.add_centered_content(content_widget)

        prev_tip = _(f"welcome_onboarding.tutorial_{self.tutorial_index}.previous_tip")
        next_tip = _(f"welcome_onboarding.tutorial_{self.tutorial_index}.next_tip")
        self.prev_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_l.svg"),
            button_style=CircleNavButton.STYLE_LIGHT,
            tooltip=prev_tip,
            parent=self,
        )
        self.next_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_r.svg"),
            button_style=CircleNavButton.STYLE_ACCENT,
            tooltip=next_tip,
            parent=self,
        )
        self.next_btn.setAccentColor(self._accent_color)
        self.set_nav_buttons(self.prev_btn, self.next_btn)

    def set_accent_color(self, color: str) -> None:
        """更新教程页主题色。

        Args:
            color: 新的主题色十六进制字符串。
        """
        super().set_accent_color(color)
        if hasattr(self, "next_btn") and self.next_btn:
            self.next_btn.setAccentColor(color)
        if hasattr(self, "prev_btn") and self.prev_btn:
            self.prev_btn.setAccentColor(color)

    def reload_texts(self) -> None:
        """重新加载页面翻译文本与提示。"""
        description_key = f"welcome_onboarding.tutorial_{self.tutorial_index}.description"
        if hasattr(self, "desc_label") and self.desc_label:
            self.desc_label.setText(_(description_key))
        if hasattr(self, "prev_btn") and self.prev_btn:
            self.prev_btn.setTooltip(_(f"welcome_onboarding.tutorial_{self.tutorial_index}.previous_tip"))
        if hasattr(self, "next_btn") and self.next_btn:
            self.next_btn.setTooltip(_(f"welcome_onboarding.tutorial_{self.tutorial_index}.next_tip"))

    def _scale_image(self) -> None:
        """根据内容区实际可用宽度和高度等比例缩放截图。"""
        if not self._raw_pixmap or self._raw_pixmap.isNull():
            return
        available_width = max(200, self.width() - 80)
        available_height = max(160, self.height() - 220)
        scaled = self._raw_pixmap.scaled(
            min(self.MAX_IMAGE_WIDTH, available_width),
            min(self.MAX_IMAGE_HEIGHT, available_height),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation,
        )
        self.image_label.setPixmap(scaled)

    def resizeEvent(self, event) -> None:
        """窗口尺寸变化时重新缩放截图。"""
        self._scale_image()
        super().resizeEvent(event)
