# -*- coding: utf-8 -*-
"""Fluent Design 风格进度条组件"""
from core.i18n import _

from PyQt5.QtWidgets import QWidget, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import (
    QPainter, QColor, QLinearGradient, QPainterPath, 
    QCursor, QPen, QRadialGradient
)

from gui.fonts import body_font
from gui.styles import load_primary_color


class FluentProgressBar(QWidget):
    """Fluent Design 风格进度条组件"""
    
    # 信号
    clicked = pyqtSignal()
    valueChanged = pyqtSignal(int)
    
    # 状态常量
    STATE_WAITING = "waiting"
    STATE_DOWNLOADING = "downloading"
    STATE_PAUSED = "paused"
    STATE_COMPLETED = "completed"
    STATE_FAILED = "failed"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._value = 0
        self._maximum = 100
        self._state = self.STATE_WAITING
        
        self._animated_value = 0.0
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._animate_progress)
        self._animation_speed = 0.18
        
        self._cornerRadius = 4
        self._track_color = QColor("#F3F3F3")
        self._track_border_color = QColor("#E1E1E1")
        self._text_color = QColor("#333333")
        self._overlay_text_color = QColor("#FFFFFF")

        accent_color = load_primary_color()
        self._accent_color = QColor(accent_color)
        self._glow_color = QColor(accent_color)

        self._colors = {
            self.STATE_WAITING: QColor("#8A8A8A"),
            self.STATE_DOWNLOADING: self._accent_color,
            self.STATE_PAUSED: QColor("#F7B500"),
            self.STATE_COMPLETED: QColor("#107C10"),
            self.STATE_FAILED: QColor("#D13438"),
        }

        self._gradient_colors = {
            self.STATE_DOWNLOADING: (self._accent_color, self._accent_color.lighter(115)),
            self.STATE_PAUSED: (QColor("#F7B500"), QColor("#FFD335")),
            self.STATE_COMPLETED: (QColor("#107C10"), QColor("#2EAD2E")),
            self.STATE_FAILED: (QColor("#D13438"), QColor("#E8555A")),
        }
        
        self._hovered = False
        self._pulse_offset = 0.0
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._animate_pulse)
        
        self.setFixedHeight(28)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setAttribute(Qt.WA_Hover, True)
        self.setMouseTracking(True)
        self.destroyed.connect(self._stop_timers)

    def _stop_timers(self):
        """停止所有动画定时器。"""
        if self._animation_timer and self._animation_timer.isActive():
            self._animation_timer.stop()
        if self._pulse_timer and self._pulse_timer.isActive():
            self._pulse_timer.stop()

    def paintEvent(self, event):
        """绘制进度条"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        try:
            width = self.width()
            height = self.height()

            # 绘制轨道背景
            from PyQt5.QtCore import QRectF
            track_rect = QRectF(0.5, 0.5, width - 1, height - 1)
            track_path = QPainterPath()
            track_path.addRoundedRect(track_rect, self._cornerRadius, self._cornerRadius)
            painter.fillPath(track_path, self._track_color)

            # 绘制轨道边框
            if self._hovered:
                painter.setPen(QPen(self._track_border_color, 1))
            else:
                painter.setPen(QPen(QColor(0, 0, 0, 0), 0))
            painter.setBrush(Qt.NoBrush)
            painter.drawRoundedRect(track_rect, self._cornerRadius, self._cornerRadius)

            # 计算进度宽度
            if self._maximum > 0:
                fill_width = max(0, int((self._animated_value / self._maximum) * (width - 1)))
            else:
                fill_width = 0

            # 绘制进度填充
            if fill_width > 0:
                fill_path = QPainterPath()
                fill_path.addRoundedRect(0.5, 0.5, fill_width, height - 1,
                                         self._cornerRadius, self._cornerRadius)

                # 获取状态对应的渐变色
                if self._state in self._gradient_colors:
                    start_color, end_color = self._gradient_colors[self._state]
                else:
                    color = self._colors.get(self._state, self._colors[self.STATE_DOWNLOADING])
                    start_color = color
                    end_color = color.lighter(115)

                # 绘制渐变填充
                gradient = QLinearGradient(0, 0, 0, height)
                gradient.setColorAt(0, start_color.lighter(105))
                gradient.setColorAt(0.5, start_color)
                gradient.setColorAt(1, end_color)
                painter.fillPath(fill_path, gradient)

                # 绘制顶部高光效果
                if fill_width > 4:
                    highlight_path = QPainterPath()
                    highlight_path.addRoundedRect(1.5, 1.5, fill_width - 2, height // 2 - 2,
                                                 self._cornerRadius - 1, self._cornerRadius - 1)
                    highlight_gradient = QLinearGradient(0, 0, 0, height // 2)
                    highlight_gradient.setColorAt(0, QColor(255, 255, 255, 60))
                    highlight_gradient.setColorAt(1, QColor(255, 255, 255, 10))
                    painter.fillPath(highlight_path, highlight_gradient)

                # 下载状态时添加脉动光效
                if self._state == self.STATE_DOWNLOADING and fill_width > 10:
                    pulse_width = 40
                    pulse_x = int(self._pulse_offset * fill_width) - pulse_width

                    if 0 <= pulse_x < fill_width:
                        pulse_gradient = QLinearGradient(pulse_x, 0, pulse_x + pulse_width, 0)
                        pulse_gradient.setColorAt(0, QColor(255, 255, 255, 0))
                        pulse_gradient.setColorAt(0.5, QColor(255, 255, 255, 45))
                        pulse_gradient.setColorAt(1, QColor(255, 255, 255, 0))

                        pulse_path = QPainterPath()
                        pulse_path.addRect(0.5, 0.5, fill_width, height - 1)
                        painter.save()
                        painter.setClipPath(pulse_path)
                        painter.fillRect(pulse_x, 0, pulse_width, height, pulse_gradient)
                        painter.restore()

            # 绘制百分比文字
            if self._maximum > 0:
                progress_text = f"{int(self._animated_value / self._maximum * 100)}%"
            else:
                progress_text = "0%"

            font = body_font()
            font.setPixelSize(11)
            font.setWeight(500)
            painter.setFont(font)

            # 绘制轨道区域的文字
            painter.setPen(self._text_color)
            text_rect = self.rect().adjusted(0, 0, 0, 0)
            painter.drawText(text_rect, Qt.AlignCenter, progress_text)

            # 在进度填充区域上绘制白色文字（裁剪）
            if fill_width > 0:
                painter.save()
                clip_path = QPainterPath()
                clip_path.addRect(0, 0, fill_width, height)
                painter.setClipPath(clip_path)
                painter.setPen(self._overlay_text_color)
                painter.drawText(text_rect, Qt.AlignCenter, progress_text)
                painter.restore()

            # 悬停时绘制外发光边框
            if self._hovered:
                glow_pen = QPen(self._glow_color, 1.5)
                glow_pen.setCosmetic(True)
                painter.setPen(glow_pen)
                painter.setBrush(Qt.NoBrush)
                painter.drawRoundedRect(1, 1, width - 2, height - 2,
                                       self._cornerRadius, self._cornerRadius)
        finally:
            if painter.isActive():
                painter.end()

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        """鼠标进入"""
        self._hovered = True
        self.update()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """鼠标离开"""
        self._hovered = False
        self.update()
        super().leaveEvent(event)
    
    def setValue(self, value):
        """设置进度值"""
        if value != self._value:
            self._value = min(max(0, value), self._maximum)
            self.valueChanged.emit(self._value)
            self._startAnimation()
            
            # 下载状态时启动脉动动画
            if self._state == self.STATE_DOWNLOADING:
                self._startPulse()
            else:
                self._stopPulse()
    
    def value(self):
        """获取当前进度值"""
        return self._value
    
    def setMaximum(self, maximum):
        """设置最大值"""
        self._maximum = max(1, maximum)
        if self._value > maximum:
            self._value = maximum
        
    def maximum(self):
        """获取最大值"""
        return self._maximum
    
    def setState(self, state):
        """设置状态"""
        if state != self._state:
            self._state = state
            self.update()
            
            # 下载状态时启动脉动动画
            if state == self.STATE_DOWNLOADING and self._value > 0:
                self._startPulse()
            else:
                self._stopPulse()
    
    def state(self):
        """获取当前状态"""
        return self._state
    
    def setBarHeight(self, height):
        """设置进度条高度"""
        self.setFixedHeight(height)
        self.update()
    
    def setCornerRadius(self, radius):
        """设置圆角半径"""
        self._cornerRadius = radius
        self.update()
    
    def setTrackColor(self, color):
        """设置轨道颜色"""
        if isinstance(color, str):
            self._track_color = QColor(color)
        else:
            self._track_color = color
        self.update()
    
    def setTextColor(self, color):
        """设置文字颜色（轨道区域）"""
        if isinstance(color, str):
            self._text_color = QColor(color)
        else:
            self._text_color = color
        self.update()
    
    def setOverlayTextColor(self, color):
        """设置填充区域上的文字颜色"""
        if isinstance(color, str):
            self._overlay_text_color = QColor(color)
        else:
            self._overlay_text_color = color
        self.update()
    
    def setColors(self, state, color):
        """设置特定状态的颜色"""
        if isinstance(color, str):
            self._colors[state] = QColor(color)
        else:
            self._colors[state] = color
        self.update()
    
    def setGradientColors(self, start_color, end_color):
        """设置渐变颜色"""
        if isinstance(start_color, str):
            start_color = QColor(start_color)
        if isinstance(end_color, str):
            end_color = QColor(end_color)
        self._gradient_colors[self._state] = (start_color, end_color)
        self.update()
    
    def setAnimationSpeed(self, speed):
        """设置动画速度 (0.01-1.0)"""
        self._animation_speed = max(0.01, min(1.0, speed))
    
    def reset(self):
        """重置进度条（仅归零进度值，保留当前状态）"""
        self._animation_timer.stop()
        self._pulse_timer.stop()
        self._value = 0
        self._animated_value = 0.0
        self._pulse_offset = 0.0
        self.update()
    
    def _startAnimation(self):
        """启动动画"""
        if not self._animation_timer.isActive():
            self._animation_timer.start(16)
    
    def _animate_progress(self):
        """动画步进"""
        diff = self._value - self._animated_value
        
        if abs(diff) < 0.3:
            self._animated_value = float(self._value)
            self._animation_timer.stop()
        else:
            self._animated_value += diff * self._animation_speed
            if diff > 0:
                self._animated_value = min(self._animated_value, float(self._value))
            else:
                self._animated_value = max(self._animated_value, float(self._value))
        
        self.update()
    
    def _startPulse(self):
        """启动脉动动画"""
        if not self._pulse_timer.isActive():
            self._pulse_offset = 0.0
            self._pulse_timer.start(20)
    
    def _stopPulse(self):
        """停止脉动动画"""
        self._pulse_timer.stop()
        self._pulse_offset = 0.0
        self.update()
    
    def _animate_pulse(self):
        """脉动动画步进"""
        self._pulse_offset += 0.02
        if self._pulse_offset > 1.2:
            self._pulse_offset = -0.2
        self.update()


# 保持向后兼容
iOSProgressBar = FluentProgressBar


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel
    from gui.widgets.material_button import MaterialButton

    app = QApplication(sys.argv)
    accent_color = load_primary_color()

    window = QWidget()
    window.setWindowTitle(_("widgets.progress_bar.demo_title"))
    window.setMinimumWidth(400)

    layout = QVBoxLayout(window)
    layout.setSpacing(20)
    layout.setContentsMargins(30, 30, 30, 30)

    # 标题
    title = QLabel(_("widgets.progress_bar.title"))
    title.setStyleSheet("font-size: 18px; font-weight: bold; color: #333;")
    layout.addWidget(title)
    
    # 创建多个进度条演示不同状态
    states = [
        (_("widgets.status_indicator.waiting"), FluentProgressBar.STATE_WAITING, 0),
        (_("widgets.status_indicator.downloading"), FluentProgressBar.STATE_DOWNLOADING, 65),
        (_("widgets.status_indicator.paused"), FluentProgressBar.STATE_PAUSED, 45),
        (_("common.status_done"), FluentProgressBar.STATE_COMPLETED, 100),
        (_("common.status_failed"), FluentProgressBar.STATE_FAILED, 30),
    ]
    
    progress_bars = []
    for label_text, state, value in states:
        # 标签
        label = QLabel(label_text)
        label.setStyleSheet("font-size: 12px; color: #666;")
        layout.addWidget(label)
        
        # 进度条
        bar = FluentProgressBar()
        bar.setState(state)
        bar.setValue(value)
        layout.addWidget(bar)
        progress_bars.append(bar)
    
    # 控制按钮
    btn_layout = QVBoxLayout()
    
    btn_add = MaterialButton(_("widgets.progress_bar.increase_progress"))
    btn_add.setAccentColor(accent_color)
    btn_add.setFixedHeight(36)
    btn_add.clicked.connect(lambda: [b.setValue(min(b.value() + 10, 100)) for b in progress_bars])
    btn_layout.addWidget(btn_add)
    
    btn_reset = MaterialButton(_("widgets.progress_bar.reset"), variant=MaterialButton.VARIANT_OUTLINED)
    btn_reset.setAccentColor("#666666")
    btn_reset.setFixedHeight(36)
    btn_reset.clicked.connect(lambda: [b.reset() for b in progress_bars])
    btn_layout.addWidget(btn_reset)
    
    layout.addLayout(btn_layout)
    layout.addStretch()
    
    window.setStyleSheet("QWidget { background-color: #FAFAFA; }")
    window.show()
    
    sys.exit(app.exec())
