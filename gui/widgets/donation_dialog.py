# -*- coding: utf-8 -*-
"""赞赏码对话框"""

import os
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QDialog, QFrame, QHBoxLayout, QLabel, QVBoxLayout,
    QWidget, QGraphicsDropShadowEffect
)

from core.i18n import _
from gui.fonts import body_font, small_font, subtitle_font
from gui.widgets.material_button import MaterialButton


class DonationDialog(QDialog):
    """Material Design 风格的赞赏码对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._accent_color = self._load_primary_color()
        self._init_ui()
        self._center_on_screen()

    def _load_primary_color(self) -> str:
        """加载当前主题主色，失败时回退到项目默认值。"""
        try:
            from gui.styles import load_primary_color
            return load_primary_color()
        except Exception:
            return "#1277DD"

    def _init_ui(self):
        """初始化界面：统一浅色背景 + 标题文本 + 带阴影的 QR 卡片 + 关闭按钮。"""
        self.setWindowTitle(_("dialogs.donation.title"))
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        self.setFixedSize(300, 400)
        self.setStyleSheet("background-color: #E8F4FD;")

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        # 标题（统一使用深色文字，避免顶部出现大蓝边）
        title = QLabel(_("dialogs.donation.title"))
        title.setFont(subtitle_font())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333333;")
        layout.addWidget(title)

        # 提示文字
        message = QLabel(_("dialogs.donation.message"))
        message.setFont(body_font())
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)
        message.setStyleSheet("color: #333333;")
        layout.addWidget(message)

        # QR 卡片
        qr_card = QFrame()
        qr_card.setFixedSize(180, 180)
        qr_card.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border-radius: 10px; border: 1px solid #E0E0E0; }"
        )
        qr_layout = QVBoxLayout(qr_card)
        qr_layout.setContentsMargins(8, 8, 8, 8)
        qr_layout.setSpacing(0)
        qr_layout.setAlignment(Qt.AlignCenter)

        qr_path = self._qr_image_path()
        if os.path.exists(qr_path):
            qr_label = QLabel()
            pixmap = QPixmap(qr_path)
            qr_label.setPixmap(
                pixmap.scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
            qr_label.setAlignment(Qt.AlignCenter)
            qr_layout.addWidget(qr_label)
        else:
            missing_label = QLabel(_("dialogs.donation.qr_missing"))
            missing_label.setFont(body_font())
            missing_label.setAlignment(Qt.AlignCenter)
            missing_label.setWordWrap(True)
            missing_label.setStyleSheet("color: #999999;")
            qr_layout.addWidget(missing_label)

        # 卡片阴影
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(12)
        shadow.setColor(QColor(0, 0, 0, 35))
        shadow.setOffset(0, 3)
        qr_card.setGraphicsEffect(shadow)

        layout.addWidget(qr_card, alignment=Qt.AlignCenter)

        # 卡片下方说明
        caption = QLabel(_("dialogs.donation.scan_tip"))
        caption.setFont(small_font())
        caption.setAlignment(Qt.AlignCenter)
        caption.setStyleSheet("color: #666666;")
        layout.addWidget(caption)

        layout.addStretch()

        # 关闭按钮
        self.close_btn = MaterialButton(_("common.close"))
        self.close_btn.setFont(body_font())
        self.close_btn.setFixedHeight(32)
        self.close_btn.setMinimumWidth(100)
        self.close_btn.setAccentColor(self._accent_color)
        self.close_btn.clicked.connect(self.accept)
        layout.addWidget(self.close_btn, alignment=Qt.AlignCenter)

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新关闭按钮颜色。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        self._accent_color = primary
        if hasattr(self, "close_btn") and self.close_btn is not None:
            self.close_btn.setAccentColor(primary)

    def _qr_image_path(self) -> str:
        """返回赞赏码图片路径。"""
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        return os.path.join(project_root, "resources", "images", "donation_qr.png")

    def _center_on_screen(self):
        """将对话框居中显示到主屏幕。"""
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)


def show_donation_dialog(parent=None):
    """显示赞赏码对话框。"""
    try:
        if QApplication.instance() is None:
            QApplication(sys.argv)
        dialog = DonationDialog(parent)
        dialog.exec()
    except Exception as e:
        from core.infrastructure.logger import log
        log("WARNING", f"显示赞赏码失败: {e}")
