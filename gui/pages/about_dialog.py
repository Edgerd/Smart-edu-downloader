# -*- coding: utf-8 -*-
"""关于对话框"""
from core.i18n import _

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel,
                             QFrame)
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPainterPath

from gui.fonts import title_font, body_font, bold_font
from gui.styles import load_primary_color
from gui.widgets.material_button import MaterialButton

import webbrowser


class AboutDialog(QDialog):
    """关于对话框类"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setFixedSize(500, 450)
        self._accent_color = load_primary_color()
        self._init_ui()
        self._center_on_parent()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)

        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_frame.setStyleSheet("""
            #contentFrame {
                background: white;
                border-radius: 15px;
            }
        """)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)
        content_frame.setLayout(content_layout)

        title = QLabel(_("app.name"))
        title.setFont(title_font())
        title.setStyleSheet(f"color: {self._accent_color};")
        title.setAlignment(Qt.AlignCenter)

        from core.infrastructure.version import VERSION
        version = QLabel(_("dialogs.about.version_template", version=VERSION))
        version.setFont(body_font())
        version.setStyleSheet("color: #666;")
        version.setAlignment(Qt.AlignCenter)

        author_frame = QFrame()
        author_frame.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #F8FAFC, stop:1 #E8F4FC);
            border-radius: 10px;
            padding: 20px;
        """)
        author_layout = QVBoxLayout()
        author_layout.setSpacing(10)
        author_frame.setLayout(author_layout)

        author_title = QLabel(_("dialogs.about.author_info"))
        author_title.setFont(bold_font())
        author_title.setStyleSheet("color: #333;")

        author_name = QLabel(_("dialogs.about.author_name"))
        author_name.setFont(body_font())
        author_name.setStyleSheet("color: #555;")

        bilibili_label = QLabel(_("dialogs.about.bilibili_link"))
        bilibili_label.setFont(body_font())
        bilibili_label.setStyleSheet("color: #555;")

        bilibili_btn = MaterialButton(_("dialogs.about.visit_bilibili"))
        bilibili_btn.setFont(body_font())
        bilibili_btn.setCursor(Qt.PointingHandCursor)
        bilibili_btn.setFixedHeight(35)
        bilibili_btn.clicked.connect(lambda: webbrowser.open("https://space.bilibili.com/3537111380658360"))

        author_layout.addWidget(author_title)
        author_layout.addWidget(author_name)
        author_layout.addWidget(bilibili_label)
        author_layout.addWidget(bilibili_btn)

        desc_label = QLabel(_("dialogs.about.description"))
        desc_label.setFont(body_font())
        desc_label.setStyleSheet("color: #666; line-height: 1.6;")
        desc_label.setWordWrap(True)
        desc_label.setAlignment(Qt.AlignCenter)

        tech_frame = QFrame()
        tech_frame.setStyleSheet("""
            background: #F8FAFC;
            border-radius: 8px;
            padding: 15px;
        """)
        tech_layout = QVBoxLayout()
        tech_layout.setSpacing(8)
        tech_frame.setLayout(tech_layout)

        tech_title = QLabel(_("dialogs.about.tech_features"))
        tech_title.setFont(bold_font())
        tech_title.setStyleSheet("color: #333;")

        tech_features = [
            _("dialogs.about.feature_multi_thread"),
            _("dialogs.about.feature_speed_test"),
            _("dialogs.about.feature_dynamic_resource"),
            _("dialogs.about.feature_auto_save"),
            _("dialogs.about.feature_modern_ui"),
        ]

        for feature in tech_features:
            feat_label = QLabel(feature)
            feat_label.setFont(body_font())
            feat_label.setStyleSheet("color: #555;")
            tech_layout.addWidget(feat_label)

        close_btn = MaterialButton(_("common.close"))
        close_btn.setFont(body_font())
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setFixedHeight(40)
        close_btn.clicked.connect(self.close)

        content_layout.addWidget(title)
        content_layout.addWidget(version)
        content_layout.addWidget(author_frame)
        content_layout.addWidget(desc_label)
        content_layout.addWidget(tech_frame)
        content_layout.addWidget(close_btn, 0, Qt.AlignCenter)

        main_layout.addWidget(content_frame)

    def _center_on_parent(self):
        """在父窗口上居中"""
        if self.parent():
            parent_geo = self.parent().geometry()
            self.move(
                parent_geo.center().x() - self.width() // 2,
                parent_geo.center().y() - self.height() // 2
            )

    def paintEvent(self, event):
        """绘制圆角和阴影"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)

        try:
            shadow_path = QPainterPath()
            shadow_rect = QRectF(self.rect())
            shadow_path.addRoundedRect(shadow_rect, 15, 15)

            for i in range(1, 6):
                painter.setOpacity(0.05 * i)
                painter.fillPath(shadow_path.translated(i, i), painter.background())
        finally:
            if painter.isActive():
                painter.end()
