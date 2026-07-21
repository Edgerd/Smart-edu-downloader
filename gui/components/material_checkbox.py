# -*- coding: utf-8 -*-
"""Material Design 3 自定义复选框组件。

本模块提供不依赖原生 ``QCheckBox`` 的自定义复选框，支持：

- 24 dp 圆角方形勾选框；
- 未选中时的浅灰色细边框；
- 选中时主题色从中心向外扩散填充；
- 白色对勾以路径描边动画逐笔出现；
- 点击位置触发的水波纹涟漪动效；
- FastOutSlowIn 缓动曲线与柔和 1 dp 投影。

桌面端按 1 dp = 1 px 处理。
"""

from typing import Optional

from PyQt5.QtCore import (
    Qt,
    QPointF,
    QRectF,
    QSize,
    QTimer,
    QEasingCurve,
    QPropertyAnimation,
    pyqtProperty,
    pyqtSignal,
)
from PyQt5.QtGui import (
    QPainter,
    QColor,
    QPainterPath,
    QPen,
    QFontMetrics,
    QMouseEvent,
    QPaintEvent,
    QKeyEvent,
)
from PyQt5.QtWidgets import QWidget

from gui.fonts import body_font
from gui.styles import load_primary_color


class _Ripple:
    """单个水波纹状态。

    属性:
        center: 涟漪中心点（组件局部坐标）。
        radius: 当前半径。
        max_radius: 最大半径。
        color: 涟漪基础颜色（含 RGB，alpha 动态计算）。
        alpha: 当前不透明度。
        speed: 每帧半径增量。
        finished: 涟漪是否已结束。
    """

    def __init__(self, center: QPointF, max_radius: float, color: QColor):
        """初始化水波纹。

        Args:
            center: 涟漪中心点。
            max_radius: 涟漪扩散的最大半径。
            color: 涟漪颜色（alpha 通道会被覆盖）。
        """
        self.center = center
        self.radius = 0.0
        self.max_radius = max_radius
        self.color = color
        self.alpha = 255
        self.speed = max(2.0, max_radius / 24.0)
        self.finished = False

    def update(self) -> None:
        """更新涟漪状态。"""
        self.radius += self.speed
        progress = min(1.0, self.radius / self.max_radius)
        # 使用平方衰减，使涟漪消失更柔和
        self.alpha = int(255 * (1.0 - progress * progress))
        if self.radius >= self.max_radius or self.alpha <= 0:
            self.finished = True

    def draw(self, painter: QPainter) -> None:
        """绘制涟漪。

        Args:
            painter: 已激活的 QPainter。
        """
        if self.finished or self.radius <= 0:
            return
        color = QColor(self.color)
        color.setAlpha(max(0, self.alpha))
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.center, self.radius, self.radius)


class MaterialCheckBox(QWidget):
    """Material Design 3 风格复选框。

    不使用 Qt 原生 ``QCheckBox``，完全自绘勾选框、文本、水波纹与勾选动画。

    信号:
        toggled(bool): 选中状态发生改变时发射，参数为新的选中状态。
        clicked(): 用户完成一次点击操作时发射。

    属性:
        checked: 当前是否选中。
        text: 复选框右侧显示的文本。
        accent_color: 勾选填充与焦点环的主题色。
    """

    toggled = pyqtSignal(bool)
    clicked = pyqtSignal()

    # 尺寸常量（桌面端 1 dp = 1 px）
    BOX_SIZE = 24
    BOX_RADIUS = 6
    BOX_TEXT_SPACING = 10
    SHADOW_OFFSET = 1
    BORDER_WIDTH = 1.5
    CHECK_STROKE_WIDTH = 2.5

    def __init__(self, text: str = '', parent: Optional[QWidget] = None):
        """初始化复选框。

        Args:
            text: 复选框右侧显示的标签文本，默认为空。
            parent: 父组件。
        """
        super().__init__(parent)
        self._text = text
        self._checked = False
        self._pressed = False
        self._hovered = False
        self._accent_color = load_primary_color()
        self._border_color = '#BDBDBD'
        self._unchecked_bg = '#FFFFFF'
        self._disabled_color = '#9E9E9E'

        self._fill_progress = 0.0
        self._check_progress = 0.0
        self._ripples = []

        self._ripple_timer = QTimer(self)
        self._ripple_timer.timeout.connect(self._update_ripples)
        self._ripple_timer.setInterval(16)

        self._fill_animation = QPropertyAnimation(self, b'fill_progress', self)
        self._fill_animation.setDuration(200)
        self._fill_animation.setEasingCurve(self._fast_out_slow_in_easing())

        self._check_animation = QPropertyAnimation(self, b'check_progress', self)
        self._check_animation.setDuration(250)
        self._check_animation.setEasingCurve(self._fast_out_slow_in_easing())

        self.setFont(body_font())
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setMinimumHeight(self.BOX_SIZE)
        self._update_size()

    # ----- 公共 API -----

    def isChecked(self) -> bool:
        """返回当前选中状态。

        Returns:
            True 表示已选中，False 表示未选中。
        """
        return self._checked

    def setChecked(self, checked: bool, animated: bool = True) -> None:
        """设置选中状态。

        Args:
            checked: 目标选中状态。
            animated: 是否播放状态过渡动画；False 则立即切换。
        """
        if self._checked == checked:
            return
        self._checked = checked
        if animated and self.isVisible():
            self._start_state_animation()
        else:
            self._fill_progress = 1.0 if checked else 0.0
            self._check_progress = 1.0 if checked else 0.0
            self.update()
        self.toggled.emit(self._checked)

    def text(self) -> str:
        """返回复选框文本。"""
        return self._text

    def setText(self, text: str) -> None:
        """设置复选框文本。

        Args:
            text: 要显示的标签文本。
        """
        self._text = text
        self._update_size()
        self.update()

    def setAccentColor(self, color: str) -> None:
        """设置勾选时的主题色。

        Args:
            color: 十六进制颜色字符串，例如 ``'#2078DA'``。
        """
        self._accent_color = color
        self.update()

    def sizeHint(self) -> QSize:
        """返回建议大小。"""
        return self.minimumSizeHint()

    def setEnabled(self, enabled: bool) -> None:
        """设置启用状态。

        禁用时会停止所有动画并清空水波纹。

        Args:
            enabled: 是否启用。
        """
        super().setEnabled(enabled)
        if not enabled:
            self._fill_animation.stop()
            self._check_animation.stop()
            self._ripple_timer.stop()
            self._ripples.clear()
        self.update()

    # ----- 动画属性 -----

    @pyqtProperty(float)
    def fill_progress(self) -> float:
        """填充扩散进度（0.0 ~ 1.0）。"""
        return self._fill_progress

    @fill_progress.setter
    def fill_progress(self, value: float) -> None:
        self._fill_progress = max(0.0, min(1.0, value))
        self.update()

    @pyqtProperty(float)
    def check_progress(self) -> float:
        """对勾描边进度（0.0 ~ 1.0）。"""
        return self._check_progress

    @check_progress.setter
    def check_progress(self, value: float) -> None:
        self._check_progress = max(0.0, min(1.0, value))
        self.update()

    # ----- 事件处理 -----

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件：记录按下状态并启动水波纹。"""
        if event.button() == Qt.LeftButton and self.isEnabled():
            self._pressed = True
            self._start_ripple(event.pos())
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """鼠标释放事件：在组件范围内释放时切换选中状态。"""
        if event.button() == Qt.LeftButton and self._pressed:
            self._pressed = False
            if self.rect().contains(event.pos()):
                self.setChecked(not self._checked)
                self.clicked.emit()
            self.update()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event) -> None:
        """鼠标进入：更新悬浮状态。"""
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """鼠标离开：取消悬浮与按下状态。"""
        self._hovered = False
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """键盘事件：空格或回车切换选中状态。"""
        if event.key() in (Qt.Key_Space, Qt.Key_Return, Qt.Key_Enter) and self.isEnabled():
            self.setChecked(not self._checked)
            self.clicked.emit()
            event.accept()
            return
        super().keyPressEvent(event)

    # ----- 绘制 -----

    def paintEvent(self, event: QPaintEvent) -> None:
        """自定义绘制复选框。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        try:
            box_rect = self._box_rect()
            self._draw_shadow(painter, box_rect)
            self._draw_box(painter, box_rect)
            if self._check_progress > 0 or self._checked:
                self._draw_checkmark(painter, box_rect)
            self._draw_ripples(painter)

            if self._text:
                self._draw_text(painter, box_rect)
        finally:
            if painter.isActive():
                painter.end()

    def _box_rect(self) -> QRectF:
        """返回勾选框的绘制矩形（垂直居中）。"""
        return QRectF(
            0.0,
            (self.height() - self.BOX_SIZE) / 2.0,
            self.BOX_SIZE,
            self.BOX_SIZE,
        )

    def _draw_shadow(self, painter: QPainter, box_rect: QRectF) -> None:
        """绘制勾选框下方的柔和 1 dp 投影。"""
        if not self.isEnabled():
            return
        shadow_rect = box_rect.translated(0, self.SHADOW_OFFSET)
        shadow_color = QColor(0, 0, 0, 30)
        painter.setPen(Qt.NoPen)
        painter.setBrush(shadow_color)
        painter.drawRoundedRect(
            shadow_rect, self.BOX_RADIUS, self.BOX_RADIUS
        )

    def _draw_box(self, painter: QPainter, box_rect: QRectF) -> None:
        """绘制圆角方形勾选框背景、边框与选中填充。"""
        path = QPainterPath()
        path.addRoundedRect(box_rect, self.BOX_RADIUS, self.BOX_RADIUS)

        # 背景
        if self.isEnabled():
            bg_color = QColor(self._unchecked_bg)
        else:
            bg_color = QColor('#F5F5F5')
        painter.fillPath(path, bg_color)

        # 选中填充：以中心圆逐渐扩大的裁剪区域揭示主题色
        if self._fill_progress > 0:
            fill_color = QColor(self._accent_color)
            clip_path = QPainterPath()
            center = box_rect.center()
            half_diagonal = (self.BOX_SIZE / 2.0) * 1.4142
            radius = half_diagonal * self._fill_progress
            clip_path.addEllipse(center, radius, radius)
            painter.save()
            painter.setClipPath(clip_path)
            painter.fillPath(path, fill_color)
            painter.restore()

        # 边框
        if self.isEnabled():
            if self._checked or self._fill_progress > 0.5:
                border_color = QColor(self._accent_color)
            else:
                border_color = QColor(self._border_color)
                if self._hovered:
                    border_color = QColor('#9E9E9E')
        else:
            border_color = QColor(self._disabled_color)

        pen = QPen(border_color, self.BORDER_WIDTH)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        border_rect = box_rect.adjusted(
            self.BORDER_WIDTH / 2.0,
            self.BORDER_WIDTH / 2.0,
            -self.BORDER_WIDTH / 2.0,
            -self.BORDER_WIDTH / 2.0,
        )
        painter.drawRoundedRect(
            border_rect, self.BOX_RADIUS, self.BOX_RADIUS
        )

    def _draw_checkmark(self, painter: QPainter, box_rect: QRectF) -> None:
        """绘制以路径描边动画逐笔出现的白色对勾。"""
        check_path = QPainterPath()
        # 在 24x24 的局部坐标中定义对勾路径
        check_path.moveTo(6, 13)
        check_path.lineTo(10, 17)
        check_path.lineTo(18, 8)

        total_length = check_path.length()
        if total_length <= 0:
            return

        pen = QPen(
            QColor('#FFFFFF'),
            self.CHECK_STROKE_WIDTH,
            Qt.SolidLine,
            Qt.RoundCap,
            Qt.RoundJoin,
        )
        # Qt 的 dash pattern 以笔宽为单位
        unit_length = total_length / self.CHECK_STROKE_WIDTH
        pen.setDashPattern([unit_length, unit_length])
        pen.setDashOffset(unit_length * (1.0 - self._check_progress))

        painter.save()
        painter.translate(box_rect.topLeft())
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(check_path)
        painter.restore()

    def _draw_text(self, painter: QPainter, box_rect: QRectF) -> None:
        """绘制复选框文本。"""
        text_rect = QRectF(
            box_rect.right() + self.BOX_TEXT_SPACING,
            0.0,
            self.width() - box_rect.right() - self.BOX_TEXT_SPACING,
            self.height(),
        )
        text_color = QColor('#212121') if self.isEnabled() else QColor(self._disabled_color)
        painter.setPen(text_color)
        painter.setFont(self.font())
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self._text)

    def _draw_ripples(self, painter: QPainter) -> None:
        """绘制所有活跃水波纹。"""
        if not self._ripples:
            return
        painter.save()
        painter.setPen(Qt.NoPen)
        for ripple in self._ripples:
            ripple.draw(painter)
        painter.restore()

    # ----- 内部方法 -----

    def _update_size(self) -> None:
        """根据是否有文本更新组件尺寸约束。"""
        fm = QFontMetrics(self.font())
        text_height = fm.height()
        height = max(self.BOX_SIZE, text_height)
        self.setMaximumHeight(height)

        if not self._text:
            self.setFixedSize(self.BOX_SIZE, self.BOX_SIZE)
            return

        text_width = fm.horizontalAdvance(self._text)
        width = self.BOX_SIZE + self.BOX_TEXT_SPACING + text_width
        self.setMinimumSize(width, height)
        # 清除仅勾选框模式下的固定宽度限制
        self.setMaximumWidth(16777215)

    def _start_state_animation(self) -> None:
        """启动填充与对勾动画。"""
        target_fill = 1.0 if self._checked else 0.0
        target_check = 1.0 if self._checked else 0.0

        self._fill_animation.stop()
        self._fill_animation.setStartValue(self._fill_progress)
        self._fill_animation.setEndValue(target_fill)
        self._fill_animation.start()

        self._check_animation.stop()
        self._check_animation.setStartValue(self._check_progress)
        self._check_animation.setEndValue(target_check)
        self._check_animation.start()

    def _start_ripple(self, pos) -> None:
        """在指定位置启动水波纹。"""
        center = QPointF(pos)
        max_radius = max(self.width(), self.height()) * 1.2
        ripple_color = QColor('#BDBDBD')
        ripple = _Ripple(center, max_radius, ripple_color)
        self._ripples.append(ripple)
        if not self._ripple_timer.isActive():
            self._ripple_timer.start()

    def _update_ripples(self) -> None:
        """更新水波纹动画帧。"""
        for ripple in self._ripples[:]:
            ripple.update()
            if ripple.finished:
                self._ripples.remove(ripple)
        self.update()
        if not self._ripples:
            self._ripple_timer.stop()

    @staticmethod
    def _fast_out_slow_in_easing() -> QEasingCurve:
        """返回 Material Design FastOutSlowIn 缓动曲线。

        该曲线对应 cubic-bezier(0.4, 0.0, 0.2, 1.0)。
        """
        curve = QEasingCurve(QEasingCurve.BezierSpline)
        curve.addCubicBezierSegment(
            QPointF(0.4, 0.0),
            QPointF(0.2, 1.0),
            QPointF(1.0, 1.0),
        )
        return curve
