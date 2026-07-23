# -*- coding: utf-8 -*-
"""反诈通知弹窗。

以右下角固定位置的非模态横幅形式展示反诈提醒，不阻塞用户操作，
提供关闭按钮与 Bilibili 官方链接。
"""

import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
)

from core.i18n import _
from core.infrastructure.path_resolver import get_project_root
from core.infrastructure.logger import log
from gui.fonts import body_font, small_font


class AntiFraudDialog(QDialog):
    """反诈通知横幅。

    固定在父窗口右下角显示，黄色背景卡片，包含警示图标、正文与关闭按钮。

    属性:
        accent_color: 当前主题色，用于超链接。
    """

    # 卡片尺寸
    CARD_WIDTH = 380
    CARD_HEIGHT = 92
    # 距离父窗口右下角的边距
    MARGIN = 20

    def __init__(self, accent_color: str, parent: Optional[QDialog] = None):
        """初始化反诈通知横幅。

        Args:
            accent_color: 主题色十六进制字符串，用于超链接颜色。
            parent: 父窗口。
        """
        super().__init__(parent)
        self._accent_color = accent_color
        self._init_ui()
        self._position_at_bottom_right()

    def _init_ui(self) -> None:
        """创建无边框反诈通知横幅界面。"""
        self.setWindowFlags(
            Qt.Dialog | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setModal(False)
        self.setFixedSize(self.CARD_WIDTH, self.CARD_HEIGHT)
        self.setStyleSheet("QDialog { background: transparent; }")

        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #FFF4CE;
                border-radius: 8px;
                border: none;
            }
        """)
        card_layout = QHBoxLayout(card)
        card_layout.setSpacing(10)
        card_layout.setContentsMargins(12, 10, 10, 10)
        layout.addWidget(card)

        # 左侧警示图标
        icon_label = QLabel()
        icon_label.setFixedSize(24, 24)
        icon_label.setStyleSheet("background: #9D5D00; border-radius: 12px;")
        icon_label.setAlignment(Qt.AlignCenter)
        bang_path = os.path.join(
            get_project_root(), "resources", "images", "welcome", "bang.svg"
        )
        if os.path.exists(bang_path):
            pixmap = QPixmap(bang_path)
            icon_label.setPixmap(
                pixmap.scaled(14, 14, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        card_layout.addWidget(icon_label, alignment=Qt.AlignTop)

        # 文本内容
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)

        title_label = QLabel(_("welcome_onboarding.license.anti_fraud_title"))
        title_label.setFont(body_font())
        title_label.setStyleSheet("color: #6B4A00; font-weight: bold;")
        text_layout.addWidget(title_label)

        content_label = QLabel(self._build_content_text())
        content_label.setFont(small_font())
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.RichText)
        content_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        content_label.setOpenExternalLinks(True)
        content_label.setStyleSheet("color: #6B4A00;")
        text_layout.addWidget(content_label)

        card_layout.addLayout(text_layout, 1)

        # 关闭按钮
        close_btn = QPushButton("×")
        close_btn.setFixedSize(22, 22)
        close_btn.setFont(body_font())
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #9D5D00;
                border: none;
                font-weight: bold;
                outline: none;
            }
            QPushButton:hover {
                background: #F9D99A;
                border-radius: 11px;
            }
            QPushButton:focus {
                outline: none;
            }
        """)
        close_btn.clicked.connect(self.accept)
        card_layout.addWidget(close_btn, alignment=Qt.AlignTop)

    def _build_content_text(self) -> str:
        """组装反诈通知富文本内容。

        Returns:
            包含 Bilibili 超链接的富文本字符串。
        """
        link_text = _("welcome_onboarding.license.bilibili_link")
        link_html = (
            f'<a href="https://space.bilibili.com/3537111380658360" '
            f'style="color: {self._accent_color}; text-decoration: none;">'
            f"{link_text}</a>"
        )
        content = _("welcome_onboarding.license.anti_fraud_content")
        if "{link}" in content:
            return content.replace("{link}", link_html)
        return f"{content}{link_html}。"

    def _position_at_bottom_right(self) -> None:
        """将横幅定位到父窗口右下角，无父窗口时居中显示。"""
        parent = self.parent()
        if parent is None:
            from PyQt5.QtWidgets import QApplication
            screen = QApplication.primaryScreen().geometry()
            x = (screen.width() - self.CARD_WIDTH) // 2
            y = (screen.height() - self.CARD_HEIGHT) // 2
            self.move(x, y)
            return

        try:
            geo = parent.geometry()
            x = geo.x() + geo.width() - self.CARD_WIDTH - self.MARGIN
            y = geo.y() + geo.height() - self.CARD_HEIGHT - self.MARGIN
            self.move(max(geo.x(), x), max(geo.y(), y))
        except Exception as e:
            log("WARNING", f"反诈通知定位失败: {e}")
            self.move(0, 0)
