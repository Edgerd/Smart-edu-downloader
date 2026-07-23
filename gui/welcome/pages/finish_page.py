# -*- coding: utf-8 -*-
"""引导完成页面。

展示庆祝插图、完成标题与说明文字，并提供进入主界面的对号按钮。
"""

import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

from core.i18n import _
from core.infrastructure.path_resolver import get_project_root
from gui.fonts import title_font, body_font, get_harmonyos_family
from gui.components.circle_nav_button import CircleNavButton
from gui.welcome.pages.base_page import BaseWelcomePage


class FinishPage(BaseWelcomePage):
    """完成页。

    作为新手引导的最后一屏，汇总提示用户基础设置已完成。
    """

    # 庆祝图片的目标显示尺寸
    IMAGE_SIZE = 180

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化完成页。"""
        super().__init__(parent)
        self._create_content()

    def _create_title(self) -> QLabel:
        """页面标题。"""
        title = QLabel(_("welcome_onboarding.completion.title"))
        title.setFont(title_font())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #212121;")
        return title

    def _create_subtitle(self) -> QLabel:
        """完成页不使用副标题。"""
        subtitle = QLabel("")
        subtitle.hide()
        return subtitle

    def _create_content(self) -> None:
        """创建庆祝图片、说明文字与导航按钮。"""
        self.title_label.setText(_("welcome_onboarding.completion.title"))
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
            "help",
            "celebration.png",
        )

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path).scaled(
                self.IMAGE_SIZE,
                self.IMAGE_SIZE,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            self.image_label.setPixmap(pixmap)
        content_layout.addWidget(self.image_label, 0, Qt.AlignCenter)

        self.desc_label = QLabel(self._build_description_text())
        self.desc_label.setFont(body_font())
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setWordWrap(True)
        self.desc_label.setTextFormat(Qt.RichText)
        self.desc_label.setMaximumWidth(720)
        self.desc_label.setMinimumHeight(40)
        self.desc_label.setStyleSheet("color: #555555;")
        content_layout.addWidget(self.desc_label, 0, Qt.AlignCenter)

        self.add_centered_content(content_widget)

        self.prev_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_l.svg"),
            button_style=CircleNavButton.STYLE_LIGHT,
            tooltip=_("welcome_onboarding.completion.previous_tip"),
            parent=self,
        )
        self.next_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_r.svg"),
            button_style=CircleNavButton.STYLE_ACCENT,
            tooltip=_("welcome_onboarding.completion.next_tip"),
            parent=self,
        )
        self.next_btn.setAccentColor(self._accent_color)
        self.set_nav_buttons(self.prev_btn, self.next_btn)

    def _build_description_text(self) -> str:
        """组装包含删除线样式的完成说明文本。"""
        strikethrough = _("welcome_onboarding.completion.strikethrough_text")
        description = _("welcome_onboarding.completion.description")
        font = body_font()
        family = font.family() or get_harmonyos_family()
        size = font.pointSize()
        return (
            f'<span style="font-family: {family}; font-size: {size}pt; '
            f'text-decoration: line-through;">{strikethrough}</span> '
            f'<span style="font-family: {family}; font-size: {size}pt;">{description}</span>'
        )

    def set_accent_color(self, color: str) -> None:
        """更新完成页主题色。

        Args:
            color: 新的主题色十六进制字符串。
        """
        super().set_accent_color(color)
        if hasattr(self, "next_btn") and self.next_btn:
            self.next_btn.setAccentColor(color)
        if hasattr(self, "prev_btn") and self.prev_btn:
            self.prev_btn.setAccentColor(color)

    def reload_texts(self) -> None:
        """重新加载页面翻译文本。"""
        self.title_label.setText(_("welcome_onboarding.completion.title"))
        if hasattr(self, "desc_label") and self.desc_label:
            self.desc_label.setText(self._build_description_text())
        if hasattr(self, "next_btn") and self.next_btn:
            self.next_btn.setToolTip(_("welcome_onboarding.completion.next_tip"))
