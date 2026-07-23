# -*- coding: utf-8 -*-
"""赞助页面。

作为新手引导向导的最后一屏，展示赞赏码并引导用户进入主界面。
"""

import os
import webbrowser
from typing import Optional

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QFrame,
    QGraphicsDropShadowEffect,
)

from core.i18n import _
from core.infrastructure.path_resolver import get_project_root
from gui.fonts import title_font, body_font, small_font, subtitle_font
from gui.utils.svg_icon_loader import load_svg_library_icon
from gui.components.circle_nav_button import CircleNavButton
from gui.widgets.material_button import MaterialButton
from gui.welcome.pages.base_page import BaseWelcomePage


AFDIAN_URL = "https://ifdian.net/a/edgerd"


class DonationPage(BaseWelcomePage):
    """赞赏码展示页。

    位于新手引导向导末尾，与独立赞助弹窗内容一致，但整体遵循向导的
    居中布局规范。
    """

    # 赞赏码卡片尺寸
    QR_CARD_SIZE = 180
    QR_IMAGE_SIZE = 160

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化赞助页面。"""
        super().__init__(parent)
        self._create_content()

    def _create_title(self) -> QLabel:
        """页面标题。"""
        title = QLabel(_("dialogs.donation.title"))
        title.setFont(title_font())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #212121;")
        return title

    def _create_subtitle(self) -> QLabel:
        """页面副标题。"""
        subtitle = QLabel(_("dialogs.donation.message"))
        subtitle.setFont(subtitle_font())
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #666666;")
        return subtitle

    def _create_content(self) -> None:
        """创建赞赏码卡片与进入主界面按钮。"""
        self.title_label.setText(_("dialogs.donation.title"))
        self.subtitle_label.setText(_("dialogs.donation.message"))

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(16)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setAlignment(Qt.AlignCenter)

        qr_card = self._create_qr_card()
        content_layout.addWidget(qr_card, 0, Qt.AlignCenter)

        caption = QLabel(_("dialogs.donation.scan_tip"))
        caption.setFont(small_font())
        caption.setAlignment(Qt.AlignCenter)
        caption.setStyleSheet("color: #666666;")
        content_layout.addWidget(caption, 0, Qt.AlignCenter)

        afdian_desc = QLabel(_("dialogs.donation.afdian_desc"))
        afdian_desc.setFont(small_font())
        afdian_desc.setAlignment(Qt.AlignCenter)
        afdian_desc.setStyleSheet("color: #666666;")
        content_layout.addWidget(afdian_desc, 0, Qt.AlignCenter)

        self.afdian_btn = MaterialButton(_("dialogs.donation.afdian_button"))
        self.afdian_btn.setFont(body_font())
        self.afdian_btn.setFixedHeight(40)
        self.afdian_btn.setMinimumWidth(160)
        self.afdian_btn.setAccentColor("#FF7A45")
        self.afdian_btn.setIconSize(QSize(20, 20))
        afdian_icon = load_svg_library_icon(
            "07_nature_food/爱发电_svg.svg",
            size=(20, 20),
            color_map={"#FF7A45": "#FFFFFF", "#FF955C": "#FFFFFF", "#FFFFFF": "#FF7A45"},
        )
        if afdian_icon:
            self.afdian_btn.setIcon(afdian_icon)
        self.afdian_btn.clicked.connect(lambda: webbrowser.open(AFDIAN_URL))
        content_layout.addWidget(self.afdian_btn, 0, Qt.AlignCenter)

        self.add_content(content_widget, Qt.AlignCenter)

        self.prev_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_l.svg"),
            button_style=CircleNavButton.STYLE_LIGHT,
            tooltip=_("welcome_onboarding.completion.previous_tip"),
            parent=self,
        )
        self.finish_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "true.svg"),
            button_style=CircleNavButton.STYLE_ACCENT,
            tooltip=_("welcome_onboarding.completion.finish_tip"),
            parent=self,
        )
        self.finish_btn.setAccentColor(self._accent_color)
        self.set_nav_buttons(self.prev_btn, self.finish_btn)

    def _create_qr_card(self) -> QFrame:
        """创建带阴影的赞赏码卡片。"""
        qr_card = QFrame()
        qr_card.setFixedSize(self.QR_CARD_SIZE, self.QR_CARD_SIZE)
        qr_card.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border-radius: 10px; "
            "border: none; }"
        )
        qr_layout = QVBoxLayout(qr_card)
        qr_layout.setContentsMargins(8, 8, 8, 8)
        qr_layout.setSpacing(0)
        qr_layout.setAlignment(Qt.AlignCenter)

        qr_path = os.path.join(
            get_project_root(), "resources", "images", "donation_qr.png"
        )
        if os.path.exists(qr_path):
            qr_label = QLabel()
            pixmap = QPixmap(qr_path).scaled(
                self.QR_IMAGE_SIZE,
                self.QR_IMAGE_SIZE,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
            qr_label.setPixmap(pixmap)
            qr_label.setAlignment(Qt.AlignCenter)
            qr_layout.addWidget(qr_label)
        else:
            missing_label = QLabel(_("dialogs.donation.qr_missing"))
            missing_label.setFont(body_font())
            missing_label.setAlignment(Qt.AlignCenter)
            missing_label.setWordWrap(True)
            missing_label.setStyleSheet("color: #999999;")
            qr_layout.addWidget(missing_label)

        shadow = QGraphicsDropShadowEffect(qr_card)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 35))
        shadow.setOffset(0, 3)
        qr_card.setGraphicsEffect(shadow)

        return qr_card

    def set_accent_color(self, color: str) -> None:
        """更新赞助页主题色。

        Args:
            color: 新的主题色十六进制字符串。
        """
        super().set_accent_color(color)
        if hasattr(self, "finish_btn") and self.finish_btn:
            self.finish_btn.setAccentColor(color)
        if hasattr(self, "prev_btn") and self.prev_btn:
            self.prev_btn.setAccentColor(color)

    def reload_texts(self) -> None:
        """重新加载页面翻译文本。"""
        self.title_label.setText(_("dialogs.donation.title"))
        self.subtitle_label.setText(_("dialogs.donation.message"))
