# -*- coding: utf-8 -*-
"""标题栏控制按钮组件。

提供透明背景、圆形、带 Material Design 水波纹动效的控制按钮，
用于标题栏右上角的最小化、最大化、关闭等操作。
"""

from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt, QTimer, QPointF, QSize
from PyQt5.QtGui import QPainter, QColor, QIcon, QMouseEvent, QPaintEvent, QEnterEvent

from gui.widgets.ripple_effect import RippleEffect


class TitleBarButton(QPushButton):
    """标题栏圆形控制按钮。

    特性:
    - 36x36 圆形透明背景
    - 白色图标居中显示
    - 基于 RippleEffect 的点击水波纹动效
    - 支持自定义悬浮/按下背景色
    """

    def __init__(self, parent=None, icon_size: int = 20):
        """初始化标题栏按钮。

        Args:
            parent: 父组件
            icon_size: 图标尺寸，默认 20
        """
        super().__init__(parent)
        self.setFixedSize(36, 36)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self.setStyleSheet("QPushButton { background: transparent; border: none; outline: none; }")

        self._hovered = False
        self._pressed = False
        self._icon = QIcon()
        self._icon_size = QSize(icon_size, icon_size)
        self._hover_bg = QColor(255, 255, 255, 40)
        self._pressed_bg = QColor(255, 255, 255, 60)
        self._ripple_color = QColor(255, 255, 255, 80)
        self._ripples = []
        self._ripple_timer = QTimer(self)
        self._ripple_timer.timeout.connect(self._update_ripples)

    def setHoverBackground(self, color: str):
        """设置悬浮背景色。

        Args:
            color: 十六进制颜色字符串或 rgba 字符串
        """
        self._hover_bg = QColor(color)
        self.update()

    def setPressedBackground(self, color: str):
        """设置按下背景色。

        Args:
            color: 十六进制颜色字符串或 rgba 字符串
        """
        self._pressed_bg = QColor(color)
        self.update()

    def setRippleColor(self, color: str):
        """设置水波纹颜色。

        Args:
            color: 十六进制颜色字符串或 rgba 字符串
        """
        self._ripple_color = QColor(color)
        self.update()

    def setIcon(self, icon: QIcon):
        """设置按钮图标。

        Args:
            icon: QIcon 图标对象
        """
        self._icon = icon
        self.update()

    def setIconSize(self, size: QSize):
        """设置图标大小。

        Args:
            size: 图标 QSize
        """
        self._icon_size = size
        self.update()

    def enterEvent(self, event: QEnterEvent):
        """鼠标进入"""
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下"""
        if event.button() == Qt.LeftButton and self.isEnabled():
            self._pressed = True
            self._start_ripple(event.pos())
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放"""
        if event.button() == Qt.LeftButton:
            self._pressed = False
            self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event: QPaintEvent):
        """自定义绘制"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        try:
            rect = self.rect()

            # 绘制背景
            if self._pressed:
                painter.setBrush(self._pressed_bg)
            elif self._hovered:
                painter.setBrush(self._hover_bg)
            else:
                painter.setBrush(Qt.NoBrush)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect)

            # 绘制水波纹
            painter.setClipRect(rect)
            for ripple in self._ripples:
                ripple.draw(painter)
            painter.setClipping(False)

            # 绘制图标
            if not self._icon.isNull():
                pixmap = self._icon.pixmap(self._icon_size)
                if not pixmap.isNull():
                    pixmap_rect = pixmap.rect()
                    pixmap_rect.moveCenter(rect.center())
                    painter.drawPixmap(pixmap_rect, pixmap)
        finally:
            if painter.isActive():
                painter.end()

    def _start_ripple(self, pos):
        """启动水波纹"""
        max_radius = max(self.width(), self.height()) * 1.5
        ripple = RippleEffect(QPointF(pos), 0, self._ripple_color, max_radius)
        self._ripples.append(ripple)
        if not self._ripple_timer.isActive():
            self._ripple_timer.start(16)

    def _update_ripples(self):
        """更新水波纹动画"""
        for ripple in self._ripples[:]:
            ripple.update()
            if ripple.finished:
                self._ripples.remove(ripple)
        try:
            self.update()
        except RuntimeError:
            # 控件可能已被销毁，停止定时器避免继续触发
            self._ripple_timer.stop()
        if not self._ripples:
            self._ripple_timer.stop()
