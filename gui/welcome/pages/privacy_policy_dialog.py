# -*- coding: utf-8 -*-
"""隐私政策对话框。

以模态窗口形式展示 ``resources/docs/privacy_policy.md`` 内容，并提供生效日期与关闭按钮。
"""

import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTextBrowser,
    QPushButton,
    QFrame,
)

from core.i18n import _
from core.infrastructure.path_resolver import get_project_root
from gui.fonts import title_font, body_font, small_font
from gui.styles import load_primary_color
from gui.utils.color_utils import darken


class PrivacyPolicyDialog(QDialog):
    """隐私政策模态对话框。

    自动从 ``resources/docs/privacy_policy.md`` 读取内容并渲染展示。

    属性:
        effective_date: 隐私政策生效日期字符串。
    """

    def __init__(self, accent_color: str = "", parent: Optional[QDialog] = None):
        """初始化隐私政策对话框。

        Args:
            accent_color: 主题色十六进制字符串，为空时自动读取当前主题色。
            parent: 父窗口。
        """
        super().__init__(parent)
        self._accent_color = accent_color or load_primary_color()
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(660, 520)
        self.setModal(True)
        self.effective_date = "2026-07-11"
        self._drag_pos = None
        self._init_ui()

    def _init_ui(self) -> None:
        """创建无边框卡片式对话框界面。"""
        self.setStyleSheet("QDialog { background: #FFFFFF; }")
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 8px;
                border: none;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(card)

        title = QLabel(_("welcome_onboarding.privacy_policy.title"))
        title.setFont(title_font())
        title.setStyleSheet("color: #212121;")
        card_layout.addWidget(title)

        date_label = QLabel(
            f"{_('welcome_onboarding.privacy_policy.effective_date')}：{self.effective_date}"
        )
        date_label.setFont(small_font())
        date_label.setStyleSheet("color: #888888;")
        card_layout.addWidget(date_label)

        self.text_browser = QTextBrowser()
        self.text_browser.setFont(body_font())
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background: #F8F9FA;
                border: none;
                border-radius: 6px;
                padding: 10px;
                color: #333333;
                outline: none;
            }
            QTextBrowser:focus {
                outline: none;
            }
        """)
        self._load_content()
        card_layout.addWidget(self.text_browser, 1)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton(_("welcome_onboarding.privacy_policy.close"))
        close_btn.setFont(body_font())
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {self._accent_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                outline: none;
            }}
            QPushButton:hover {{
                background: {darken(self._accent_color, 15)};
            }}
            QPushButton:focus {{
                outline: none;
            }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        card_layout.addLayout(btn_layout)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """记录拖拽起始位置。"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """拖拽移动无边框弹窗。"""
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """释放拖拽。"""
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _load_content(self) -> None:
        """加载并显示隐私政策 Markdown 内容。"""
        file_path = os.path.join(get_project_root(), "resources", "docs", "privacy_policy.md")
        content = ""
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                content = ""
        if not content:
            content = _("welcome_onboarding.privacy_policy.title")

        if hasattr(self.text_browser, "setMarkdown"):
            self.text_browser.setMarkdown(content)
        else:
            self.text_browser.setPlainText(content)
