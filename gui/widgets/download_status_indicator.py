# -*- coding: utf-8 -*-
"""iOS风格下载状态指示器"""

from PyQt5.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QPainterPath

from gui.fonts import small_font
from gui.styles import load_primary_color
from core.i18n import _


class DownloadStatusIndicator(QWidget):
    """iOS风格下载状态指示器"""
    
    STATE_WAITING = "waiting"
    STATE_DOWNLOADING = "downloading"
    STATE_PAUSED = "paused"
    STATE_COMPLETED = "completed"
    STATE_FAILED = "failed"
    
    def __init__(self, parent=None, state=STATE_WAITING, text=""):
        super().__init__(parent)
        
        self._state = state
        self._text = text
        
        self._colors = {
            self.STATE_WAITING: QColor("#8E8E93"),
            self.STATE_DOWNLOADING: QColor(load_primary_color()),
            self.STATE_PAUSED: QColor("#FF9500"),
            self.STATE_COMPLETED: QColor("#34C759"),
            self.STATE_FAILED: QColor("#FF3B30"),
        }
        
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._animate)
        self._pulse_radius = 0
        self._pulse_alpha = 0
        self._rotation_angle = 0
        self._dot_positions = 0
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        
        self.icon_label = QLabel()
        self.icon_label.setFixedSize(16, 16)
        self.text_label = QLabel(text)
        self.text_label.setFont(small_font())
        self.text_label.setStyleSheet("color: #333333;")
        
        layout.addWidget(self.icon_label)
        layout.addWidget(self.text_label)
        layout.addStretch()
        
        self.setFixedHeight(20)
        self.updateDisplay()
        self._startAnimation()
    
    def setState(self, state):
        """设置状态"""
        if state != self._state:
            self._state = state
            self.updateDisplay()
            self._startAnimation()
    
    def state(self):
        """获取当前状态"""
        return self._state
    
    def setText(self, text):
        """设置文本"""
        self._text = text
        self.text_label.setText(text)
    
    def updateDisplay(self):
        """更新显示"""
        color = self._colors.get(self._state, self._colors[self.STATE_WAITING])
        
        if self._state == self.STATE_WAITING:
            self._drawWaitingIcon(color)
            self.text_label.setText(self._text or _("widgets.status_indicator.waiting"))
        elif self._state == self.STATE_DOWNLOADING:
            self._drawDownloadingIcon(color)
            self.text_label.setText(self._text or _("widgets.status_indicator.downloading"))
        elif self._state == self.STATE_PAUSED:
            self._drawPausedIcon(color)
            self.text_label.setText(self._text or _("widgets.status_indicator.paused"))
        elif self._state == self.STATE_COMPLETED:
            self._drawCompletedIcon(color)
            self.text_label.setText(self._text or _("widgets.status_indicator.completed"))
        elif self._state == self.STATE_FAILED:
            self._drawFailedIcon(color)
            self.text_label.setText(self._text or _("widgets.status_indicator.failed"))
    
    def _drawWaitingIcon(self, color):
        """绘制等待图标"""
        from PyQt5.QtGui import QPixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            center_x, center_y = 8, 8
            radius = 4

            painter.setPen(QPen(color, 1))
            painter.setBrush(QColor(color.red(), color.green(), color.blue(), 50))
            painter.drawEllipse(center_x - radius - 2, center_y - radius - 2,
                              (radius + 2) * 2, (radius + 2) * 2)

            painter.setPen(Qt.NoPen)
            painter.setBrush(color)
            painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        finally:
            if painter.isActive():
                painter.end()
        self.icon_label.setPixmap(pixmap)

    def _drawDownloadingIcon(self, color):
        """绘制下载中图标"""
        from PyQt5.QtGui import QPixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            positions = [3, 8, 13]
            for i, x in enumerate(positions):
                offset = (self._dot_positions + i * 2) % 6
                size = 2 + abs(offset - 3) * 0.5
                alpha = 100 + abs(offset - 3) * 30

                painter.setPen(Qt.NoPen)
                painter.setBrush(QColor(color.red(), color.green(), color.blue(), alpha))
                painter.drawEllipse(int(x - size/2), 8 - int(size/2), int(size), int(size))
        finally:
            if painter.isActive():
                painter.end()
        self.icon_label.setPixmap(pixmap)

    def _drawPausedIcon(self, color):
        """绘制暂停图标"""
        from PyQt5.QtGui import QPixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            painter.setPen(Qt.NoPen)
            painter.setBrush(color)

            painter.drawRect(5, 4, 2, 8)
            painter.drawRect(9, 4, 2, 8)
        finally:
            if painter.isActive():
                painter.end()
        self.icon_label.setPixmap(pixmap)

    def _drawCompletedIcon(self, color):
        """绘制完成图标"""
        from PyQt5.QtGui import QPixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            pen = QPen(color, 2)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)

            path = QPainterPath()
            path.moveTo(4, 8)
            path.lineTo(7, 11)
            path.lineTo(12, 5)
            painter.drawPath(path)
        finally:
            if painter.isActive():
                painter.end()
        self.icon_label.setPixmap(pixmap)

    def _drawFailedIcon(self, color):
        """绘制失败图标"""
        from PyQt5.QtGui import QPixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            pen = QPen(color, 2)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)

            painter.drawLine(4, 4, 12, 12)
            painter.drawLine(12, 4, 4, 12)
        finally:
            if painter.isActive():
                painter.end()
        self.icon_label.setPixmap(pixmap)
    
    def _startAnimation(self):
        """启动动画"""
        if self._state in [self.STATE_WAITING, self.STATE_DOWNLOADING]:
            if not self._animation_timer.isActive():
                self._animation_timer.start(100)
        else:
            self._animation_timer.stop()
    
    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新下载中状态指示器颜色。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        self._colors[self.STATE_DOWNLOADING] = QColor(primary)
        self.updateDisplay()

    def _animate(self):
        """动画步进"""
        if self._state == self.STATE_WAITING:
            self._pulse_radius = (self._pulse_radius + 1) % 20
            self._pulse_alpha = max(0, 100 - self._pulse_radius * 5)
            self._drawWaitingIcon(self._colors[self.STATE_WAITING])
        elif self._state == self.STATE_DOWNLOADING:
            self._dot_positions = (self._dot_positions + 1) % 6
            self._drawDownloadingIcon(self._colors[self.STATE_DOWNLOADING])
