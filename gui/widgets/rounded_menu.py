# -*- coding: utf-8 -*-
"""圆角阴影菜单控件。

用于解决 QMenu 在部分平台上启用圆角后，圆角区域出现黑/灰色直角底色，以及阴影呈直角的问题。
"""

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QPainter, QPaintEvent
from PyQt5.QtWidgets import QMenu


class RoundedMenu(QMenu):
    """带圆角与圆角阴影的 QMenu。"""

    def __init__(self, parent=None, radius: int = 8, shadow_size: int = 6):
        super().__init__(parent)
        self._radius = max(0, int(radius))
        self._shadow_size = max(0, int(shadow_size))
        self.setWindowFlag(Qt.FramelessWindowHint, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAutoFillBackground(False)

    def paintEvent(self, event: QPaintEvent):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        try:
            rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
            shadow = self._shadow_size
            radius = float(self._radius)

            if shadow > 0:
                for i in range(shadow, 0, -1):
                    t = i / shadow
                    alpha = int(40 * (t ** 2))
                    color = QColor(0, 0, 0, alpha)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(color)
                    shadow_rect = rect.adjusted(shadow - i, shadow - i, -(shadow - i), -(shadow - i))
                    painter.drawRoundedRect(shadow_rect, radius, radius)

            background_rect = rect.adjusted(shadow, shadow, -shadow, -shadow)
            painter.setPen(QColor("#E0E0E0"))
            painter.setBrush(QColor("#FFFFFF"))
            painter.drawRoundedRect(background_rect, radius, radius)
        finally:
            if painter.isActive():
                painter.end()

        super().paintEvent(event)
