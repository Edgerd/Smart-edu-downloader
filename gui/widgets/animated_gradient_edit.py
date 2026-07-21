# -*- coding: utf-8 -*-
"""
Animated Gradient Border Edit Widget
带流光渐变色动画边框的文本编辑器

实现类似 Apple Intelligent Siri 激活时的彩色渐变边框效果，
输入框获得焦点时边框呈现平滑流动的多色渐变动画。

采用 QFrame + QTextEdit 组合模式，渐变边框绘制在外层 QFrame 上，
避免 QTextEdit 内部 QPainter 冲突导致的 "Painter not active" 错误。
"""

from PyQt5.QtWidgets import QFrame, QVBoxLayout, QTextEdit
from PyQt5.QtCore import Qt, QTimer, QRectF, QEvent, pyqtSignal
from PyQt5.QtGui import (
    QPainter, QPen, QConicalGradient, QColor, QPainterPath
)

from gui.fonts import body_font
from gui.widgets import CustomContextMenu


class AnimatedGradientBorderEdit(QFrame):
    """
    带流光渐变色动画边框的文本编辑器

    继承自 QFrame，内部嵌入 QTextEdit。渐变边框在 QFrame 的 paintEvent 中绘制，
    避免直接覆写 QTextEdit.paintEvent 导致的 QPainter 冲突。
    """

    # 回车键按下信号
    returnPressed = pyqtSignal()

    # 流光渐变色系（鲜艳的彩虹色，模拟 Siri 效果）
    GRADIENT_COLORS = [
        (0.0, QColor(0, 122, 255)),       # 蓝
        (0.15, QColor(100, 60, 255)),      # 紫蓝
        (0.30, QColor(175, 82, 222)),      # 紫
        (0.45, QColor(255, 45, 85)),       # 红粉
        (0.55, QColor(255, 149, 0)),       # 橙
        (0.65, QColor(255, 204, 0)),       # 金
        (0.80, QColor(52, 199, 89)),       # 绿
        (0.90, QColor(0, 199, 190)),       # 青
        (1.0, QColor(0, 122, 255)),        # 蓝（闭合）
    ]

    def __init__(self, parent=None):
        """初始化控件"""
        super().__init__(parent)
        self._animation_timer = None
        self._gradient_angle = 0.0
        self._is_focused = False
        self._base_opacity = 0.0
        self._target_opacity = 0.0
        self._border_width = 3

        self._setup_ui()
        self._setup_animation()
        self.destroyed.connect(self._stop_animation)

    def _setup_ui(self):
        """设置 UI 布局"""
        self.setFrameShape(QFrame.NoFrame)
        self.setContentsMargins(0, 0, 0, 0)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(self._border_width, self._border_width,
                                  self._border_width, self._border_width)
        layout.setSpacing(0)

        self._text_edit = QTextEdit(self)
        self._text_edit.setStyleSheet("""
            QTextEdit {
                border: none;
                border-radius: 6px;
                background: white;
                padding: 6px;
                color: #333;
                selection-background-color: #D6EAF8;
                font-size: 10pt;
            }
            QTextEdit:hover {
                background: white;
            }
        """)
        layout.addWidget(self._text_edit)

        # 自定义右键菜单
        CustomContextMenu.setup_for_text_edit(self._text_edit, body_font())

        # 将 QTextEdit 的焦点事件转发到本控件
        self._text_edit.installEventFilter(self)

    def _setup_animation(self):
        """设置渐变色动画定时器（约60FPS）"""
        self._animation_timer = QTimer(self)
        self._animation_timer.timeout.connect(self._update_gradient_animation)
        self._animation_timer.setInterval(16)  # 约60FPS

    def _stop_animation(self):
        """停止动画定时器。"""
        if self._animation_timer and self._animation_timer.isActive():
            self._animation_timer.stop()

    def _update_gradient_animation(self):
        """
        更新渐变色动画角度

        平滑旋转渐变角度，同时处理淡入/淡出过渡。
        """
        # 平滑过渡透明度
        if abs(self._base_opacity - self._target_opacity) > 0.01:
            self._base_opacity += (self._target_opacity - self._base_opacity) * 0.3
        else:
            self._base_opacity = self._target_opacity

        # 如果已完全透明且未聚焦，停止定时器
        if self._base_opacity < 0.01 and not self._is_focused:
            self._animation_timer.stop()
            self.update()
            return

        # 旋转渐变角度（每次旋转2度，约120度/秒）
        self._gradient_angle = (self._gradient_angle + 2.0) % 360.0
        self.update()

    def _create_gradient(self, rect, rotation_offset=0):
        """
        创建锥形渐变色

        Args:
            rect: 渐变区域
            rotation_offset: 旋转角度偏移

        Returns:
            QConicalGradient 对象
        """
        center = rect.center()
        gradient = QConicalGradient(center, self._gradient_angle + rotation_offset)

        for position, color in self.GRADIENT_COLORS:
            alpha = int(color.alpha() * self._base_opacity)
            adjusted_color = QColor(color.red(), color.green(), color.blue(), alpha)
            gradient.setColorAt(position, adjusted_color)

        return gradient

    def _draw_gradient_border(self, painter, rect, border_width=3):
        """
        绘制流光渐变边框

        Args:
            painter: QPainter 对象
            rect: 绘制区域
            border_width: 边框宽度
        """
        if self._base_opacity < 0.02:
            return

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        # 绘制外发光效果（多层半透明边框模拟发光）
        glow_alpha = int(self._base_opacity * 80)
        if glow_alpha > 0:
            for glow_offset in range(1, 4):
                glow_rect = QRectF(rect).adjusted(
                    -glow_offset, -glow_offset, glow_offset, glow_offset
                )
                glow_gradient = self._create_gradient(
                    glow_rect, rotation_offset=glow_offset * 30
                )
                glow_pen = QPen()
                glow_pen.setWidth(1)
                glow_pen.setStyle(Qt.SolidLine)
                glow_pen.setBrush(glow_gradient)

                # 降低发光层的透明度
                glow_color = glow_pen.color()
                glow_color.setAlpha(glow_alpha // (glow_offset + 1))
                glow_pen.setColor(glow_color)

                painter.setPen(glow_pen)
                painter.setBrush(Qt.NoBrush)
                glow_path = QPainterPath()
                glow_path.addRoundedRect(glow_rect, 8 + glow_offset, 8 + glow_offset)
                painter.drawPath(glow_path)

        # 绘制主渐变边框
        main_gradient = self._create_gradient(rect)
        pen = QPen()
        pen.setWidth(border_width)
        pen.setStyle(Qt.SolidLine)
        pen.setBrush(main_gradient)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        border_path = QPainterPath()
        border_path.addRoundedRect(QRectF(rect), 8, 8)
        painter.drawPath(border_path)

        painter.restore()

    def paintEvent(self, event):
        """
        重绘事件 - 在 QFrame 上绘制边框

        未聚焦时显示淡灰色边框，聚焦时显示流光渐变动画边框。

        Args:
            event: 绘制事件
        """
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        try:
            # 边框区域：控件整体区域，缩进1px避免被裁剪
            border_rect = QRectF(self.rect()).adjusted(1, 1, -1, -1)

            if self._base_opacity >= 0.02:
                # 聚焦状态：绘制流光渐变边框
                self._draw_gradient_border(painter, border_rect, border_width=self._border_width)
            else:
                # 未聚焦状态：绘制淡灰色边框
                pen = QPen(QColor(224, 232, 240), self._border_width)
                pen.setStyle(Qt.SolidLine)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)
                border_path = QPainterPath()
                border_path.addRoundedRect(border_rect, 8, 8)
                painter.drawPath(border_path)
        finally:
            if painter.isActive():
                painter.end()

    def eventFilter(self, obj, event):
        """
        事件过滤器 - 将 QTextEdit 的焦点事件转发到本控件，拦截回车键

        Args:
            obj: 事件源对象
            event: 事件

        Returns:
            是否拦截事件
        """
        if obj is self._text_edit:
            if event.type() == QEvent.FocusIn:
                self._on_focus_in()
            elif event.type() == QEvent.FocusOut:
                self._on_focus_out()
            elif event.type() == QEvent.KeyPress:
                key_event = event
                if key_event.key() in (Qt.Key_Return, Qt.Key_Enter):
                    if key_event.modifiers() & Qt.ShiftModifier:
                        # Shift+回车：正常换行
                        return False
                    else:
                        # 回车：发射信号，不插入换行
                        self.returnPressed.emit()
                        return True
        return super().eventFilter(obj, event)

    def _on_focus_in(self):
        """获得焦点时启动渐变动画"""
        self._is_focused = True
        self._target_opacity = 1.0
        if self._animation_timer and not self._animation_timer.isActive():
            self._animation_timer.start()
        self.update()

    def _on_focus_out(self):
        """失去焦点时停止渐变动画"""
        self._is_focused = False
        self._target_opacity = 0.0
        # 不立即停止定时器，让淡出动画先播放

    def focusInEvent(self, event):
        """
        获得焦点事件

        Args:
            event: 焦点事件
        """
        super().focusInEvent(event)
        self._text_edit.setFocus()

    def focusOutEvent(self, event):
        """
        失去焦点事件

        Args:
            event: 焦点事件
        """
        super().focusOutEvent(event)

    # ========== QTextEdit 代理方法 ==========

    @property
    def text_edit(self):
        """获取内部 QTextEdit 控件"""
        return self._text_edit

    @property
    def textChanged(self):
        """返回文本变化信号（属性形式，兼容 .connect 调用）"""
        return self._text_edit.textChanged

    def toPlainText(self):
        """获取纯文本"""
        return self._text_edit.toPlainText()

    def setPlainText(self, text):
        """设置纯文本"""
        self._text_edit.setPlainText(text)

    def setPlaceholderText(self, text):
        """
        设置占位符文本

        Args:
            text: 占位符文本
        """
        try:
            self._text_edit.setPlaceholderText(text)
        except AttributeError:
            pass

    def clear(self):
        """清空文本"""
        self._text_edit.clear()

    def setReadOnly(self, read_only):
        """设置只读状态"""
        self._text_edit.setReadOnly(read_only)

    def setFont(self, font):
        """设置字体"""
        self._text_edit.setFont(font)

    def setMaximumHeight(self, max_height):
        """设置最大高度"""
        self._text_edit.setMaximumHeight(max_height)

    def setText(self, text):
        """设置文本（别名，兼容 QTextEdit.setText）"""
        self._text_edit.setPlainText(text)
