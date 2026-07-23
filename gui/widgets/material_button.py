"""Material Design 3 风格按钮组件"""
from PyQt5.QtWidgets import QPushButton, QWidget, QGraphicsDropShadowEffect, QSizePolicy
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QPointF, QSize, QRect, QRectF, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QPen, QColor, QPainterPath, QFont, QMouseEvent, QPaintEvent, QEnterEvent, QKeyEvent, QIcon, QFontMetrics
from gui.fonts import body_font
from gui.utils.color_utils import ripple_tint, mix
from gui.widgets.ripple_effect import RippleEffect
from core.i18n import _
from gui.styles import load_primary_color

class MaterialButton(QPushButton):
    """Material Design 3 风格按钮。

    特性:
    - 12dp 圆角（紧凑、现代）
    - 基于主题色淡化的点击水波纹动效
    - 阴影仅在鼠标悬浮时显示
    - 完整的 hover/pressed/disabled/checked 状态
    - 主题色系统支持
    """
    VARIANT_FILLED = 'filled'
    VARIANT_TONAL = 'tonal'
    VARIANT_OUTLINED = 'outlined'
    VARIANT_TEXT = 'text'
    VARIANT_ELEVATED = 'elevated'

    def __init__(self, text: str='', parent: QWidget=None, variant: str=VARIANT_FILLED):
        super().__init__(text, parent)
        self._variant = variant
        self._accent_color = load_primary_color()
        self._on_accent_color = '#FFFFFF'
        self._container_color = '#E8F4FD'
        self._on_container_color = '#082032'
        self._fixed_height = 36
        self._corner_radius = 12
        self._hover_elevation = 2
        self._disabled_elevation = 0
        self._hovered = False
        self._pressed = False
        self._checked = False
        self._checked_progress = 0.0
        self._checked_animation = QPropertyAnimation(self, b'checked_progress', self)
        self._checked_animation.setDuration(180)
        self._checked_animation.setEasingCurve(QEasingCurve.InOutCubic)
        self._icon_mode = False
        self._ripples = []
        self._ripple_color = QColor(ripple_tint(self._accent_color))
        self._ripple_timer = QTimer(self)
        self._ripple_timer.timeout.connect(self._update_ripples)
        self._shadow_effect = QGraphicsDropShadowEffect(self)
        self._shadow_effect.setBlurRadius(8)
        self._shadow_effect.setColor(QColor(0, 0, 0, 40))
        self._shadow_effect.setOffset(0, 2)
        self.setGraphicsEffect(self._shadow_effect)
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(body_font())
        self.setFixedHeight(self._fixed_height)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.setCheckable(False)
        self.setAttribute(Qt.WA_Hover, True)
        self.setStyleSheet("QPushButton { outline: none; }")
        self._update_style()

    def setVariant(self, variant: str):
        """设置按钮变体类型"""
        self._variant = variant
        self._update_style()
        self.update()

    def setAccentColor(self, color: str):
        """设置主题色"""
        self._accent_color = color
        self._update_style()
        self.update()

    def setOnAccentColor(self, color: str):
        """设置主题色上的文字颜色"""
        self._on_accent_color = color
        self.update()

    def setContainerColor(self, color: str):
        """设置容器颜色（用于 tonal 变体）"""
        self._container_color = color
        self._update_style()
        self.update()

    def setOnContainerColor(self, color: str):
        """设置容器上的文字颜色"""
        self._on_container_color = color
        self.update()

    def setFixedHeight(self, height: int):
        """设置固定高度"""
        super().setFixedHeight(height)
        self._fixed_height = height

    def sizeHint(self) -> QSize:
        """根据自定义绘制逻辑返回建议大小，避免文本被截断。"""
        base = super().sizeHint()
        if self._icon_mode:
            return QSize(max(base.width(), self._fixed_height), self._fixed_height)

        font = self.font()
        font.setWeight(QFont.Medium)
        if self._fixed_height >= 40:
            font_size = 14
            h_padding = 12
        elif self._fixed_height >= 32:
            font_size = 12
            h_padding = 10
        else:
            font_size = 10
            h_padding = 8
        font.setPixelSize(font_size)
        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(self.text())
        extra = 0
        if not self.icon().isNull() and self.text():
            extra = self.iconSize().width() + 6
        width = max(base.width(), text_width + h_padding * 2 + extra)
        return QSize(width, self._fixed_height)

    def minimumSizeHint(self) -> QSize:
        """返回最小建议大小。"""
        return self.sizeHint()

    def setCornerRadius(self, radius: int):
        """设置圆角半径"""
        self._corner_radius = radius
        self.update()

    def setIcon(self, icon: QIcon):
        """设置按钮图标"""
        super().setIcon(icon)
        self._icon_mode = not bool(self.text())
        self.update()

    def setText(self, text: str):
        """设置按钮文字"""
        super().setText(text)
        self._icon_mode = not bool(text)
        self.update()

    def setIconMode(self, icon_mode: bool):
        """设置是否强制使用图标模式"""
        self._icon_mode = icon_mode
        self.update()

    def setElevation(self, hover: int, disabled: int=0):
        """设置阴影高度。

        阴影仅在悬浮时显示，因此只需要设置悬浮高度与禁用高度。
        """
        self._hover_elevation = hover
        self._disabled_elevation = disabled
        self._update_shadow()

    def _update_style(self):
        """根据变体更新样式参数"""
        if self._variant == self.VARIANT_FILLED:
            self._ripple_color = QColor(ripple_tint(self._accent_color))
        elif self._variant == self.VARIANT_TONAL:
            self._ripple_color = QColor(ripple_tint(self._container_color))
        elif self._variant == self.VARIANT_OUTLINED:
            self._ripple_color = QColor(ripple_tint(self._accent_color))
        elif self._variant == self.VARIANT_TEXT:
            self._ripple_color = QColor(ripple_tint(self._accent_color))
        elif self._variant == self.VARIANT_ELEVATED:
            self._ripple_color = QColor(ripple_tint(self._accent_color))
        self._update_shadow()

    def _update_shadow(self):
        """更新阴影效果：仅在悬浮时显示"""
        if not self.isEnabled():
            self._apply_shadow(self._disabled_elevation)
        elif self._hovered:
            self._apply_shadow(self._hover_elevation)
        else:
            self._apply_shadow(0)

    def _apply_shadow(self, elevation: int):
        """应用指定高度的阴影"""
        if elevation <= 0:
            self._shadow_effect.setEnabled(False)
            return
        self._shadow_effect.setEnabled(True)
        alpha = min(60, 20 + elevation * 8)
        blur = elevation * 4 + 4
        offset_y = elevation
        self._shadow_effect.setColor(QColor(0, 0, 0, alpha))
        self._shadow_effect.setBlurRadius(blur)
        self._shadow_effect.setOffset(0, offset_y)

    def _get_state_opacity(self) -> float:
        """根据状态获取不透明度"""
        if not self.isEnabled():
            return 0.38
        return 1.0

    def paintEvent(self, event: QPaintEvent):
        """自定义绘制按钮"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        try:
            width = self.width()
            height = self.height()
            opacity = self._get_state_opacity()
            bg_color = self._get_background_color()
            border_color = self._get_border_color()
            text_color = self._get_text_color()
            if self._hovered and self.isEnabled():
                if self._variant in [self.VARIANT_FILLED, self.VARIANT_TONAL]:
                    bg_color = mix(bg_color, '#FFFFFF', 0.08)
                else:
                    bg_color = mix(bg_color, '#000000', 0.04)
            if self._pressed and self.isEnabled():
                if self._variant in [self.VARIANT_FILLED, self.VARIANT_TONAL]:
                    bg_color = mix(bg_color, '#000000', 0.12)
                else:
                    bg_color = mix(bg_color, '#000000', 0.08)
            if self._checked_progress > 0.0 and self.isEnabled():
                checked_bg = mix(bg_color, self._accent_color, 0.12 * self._checked_progress)
                bg_color = checked_bg
            painter.setOpacity(opacity)
            path = QPainterPath()
            path.addRoundedRect(0, 0, width, height, self._corner_radius, self._corner_radius)
            painter.fillPath(path, QColor(bg_color))
            if self._variant == self.VARIANT_OUTLINED:
                pen_color = QColor(border_color)
                if not self.isEnabled():
                    pen_color = QColor('#E0E0E0')
                painter.setPen(pen_color)
                painter.setBrush(Qt.NoBrush)
                border_rect = QRectF(0.5, 0.5, width - 1, height - 1)
                painter.drawRoundedRect(border_rect, self._corner_radius, self._corner_radius)
            painter.setOpacity(1.0)
            painter.setClipPath(path)
            for ripple in self._ripples:
                ripple.draw(painter)
            painter.setClipping(False)
            painter.setOpacity(opacity)
            icon = self.icon()
            has_icon = not icon.isNull()
            has_text = bool(self.text())
            font = self.font()
            font.setWeight(QFont.Medium)
            if self._icon_mode:
                h_padding = 0
                if height >= 48:
                    font_size = 24
                elif height >= 40:
                    font_size = 20
                elif height >= 32:
                    font_size = 16
                else:
                    font_size = 12
            elif height >= 40:
                font_size = 14
                h_padding = 12
            elif height >= 32:
                font_size = 12
                h_padding = 10
            else:
                font_size = 10
                h_padding = 8
            font.setPixelSize(font_size)
            painter.setFont(font)

            if self._icon_mode and has_icon:
                pixmap = icon.pixmap(self.iconSize())
                if not pixmap.isNull():
                    pixmap_rect = pixmap.rect()
                    pixmap_rect.moveCenter(self.rect().center())
                    painter.drawPixmap(pixmap_rect, pixmap)
            elif has_icon and has_text:
                self._draw_icon_and_text(painter, icon, text_color, font, height, h_padding)
            elif has_text:
                painter.setPen(QColor(text_color))
                text_rect = self.rect().adjusted(h_padding, 0, -h_padding, 0)
                painter.drawText(text_rect, Qt.AlignCenter | Qt.AlignVCenter, self.text())

                # 水波纹所到之处文字变白：在波纹覆盖区域以白色重绘文字
                if self._ripples:
                    white_pen = QPen(QColor("#FFFFFF"))
                    white_pen.setWidth(0)
                    painter.setPen(white_pen)
                    for ripple in self._ripples:
                        if ripple.alpha <= 0 or ripple.radius <= 0:
                            continue
                        painter.save()
                        clip = QPainterPath()
                        clip.addEllipse(ripple.center, ripple.radius, ripple.radius)
                        painter.setClipPath(clip)
                        painter.drawText(text_rect, Qt.AlignCenter | Qt.AlignVCenter, self.text())
                        painter.restore()
        finally:
            if painter.isActive():
                painter.end()

    def _get_background_color(self) -> str:
        """获取背景色"""
        if not self.isEnabled():
            return '#E0E0E0'
        if self._variant == self.VARIANT_FILLED:
            return self._accent_color
        elif self._variant == self.VARIANT_TONAL:
            return self._container_color
        elif self._variant == self.VARIANT_OUTLINED:
            return '#FFFFFF'
        elif self._variant == self.VARIANT_TEXT:
            return 'transparent'
        elif self._variant == self.VARIANT_ELEVATED:
            return '#FFFFFF'
        return self._accent_color

    def _get_text_color(self) -> str:
        """获取文字颜色"""
        if not self.isEnabled():
            return '#9E9E9E'
        if self._variant == self.VARIANT_FILLED:
            return self._on_accent_color
        elif self._variant == self.VARIANT_TONAL:
            return self._on_container_color
        elif self._variant == self.VARIANT_OUTLINED:
            return self._accent_color
        elif self._variant == self.VARIANT_TEXT:
            return self._accent_color
        elif self._variant == self.VARIANT_ELEVATED:
            return self._accent_color
        return self._on_accent_color

    def _get_border_color(self) -> str:
        """获取边框颜色"""
        return mix('#FFFFFF', self._accent_color, 0.3)

    def _draw_icon_and_text(self, painter, icon, text_color, font, height, h_padding):
        """绘制图标与文字并排的按钮内容。

        图标居左，文字紧随其后，整体在按钮中水平居中。水波纹覆盖区域会
        以白色重绘图标和文字。

        Args:
            painter: 当前 QPainter。
            icon: 按钮图标。
            text_color: 文字颜色。
            font: 当前使用的字体。
            height: 按钮高度。
            h_padding: 水平内边距。
        """
        from PyQt5.QtGui import QFontMetrics

        pixmap = icon.pixmap(self.iconSize())
        if pixmap.isNull():
            painter.setPen(QColor(text_color))
            text_rect = self.rect().adjusted(h_padding, 0, -h_padding, 0)
            painter.drawText(text_rect, Qt.AlignCenter | Qt.AlignVCenter, self.text())
            return

        metrics = QFontMetrics(font)
        text_width = metrics.horizontalAdvance(self.text())
        icon_size = pixmap.rect().size()
        spacing = 6
        total_width = icon_size.width() + spacing + text_width
        start_x = (self.width() - total_width) // 2
        icon_y = (height - icon_size.height()) // 2

        pixmap_rect = pixmap.rect()
        pixmap_rect.moveTopLeft(QPoint(start_x, icon_y))
        painter.drawPixmap(pixmap_rect, pixmap)

        painter.setPen(QColor(text_color))
        text_rect = QRect(
            start_x + icon_size.width() + spacing,
            0,
            text_width,
            height,
        )
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.text())

        if not self._ripples:
            return

        for ripple in self._ripples:
            if ripple.alpha <= 0 or ripple.radius <= 0:
                continue
            painter.save()
            clip = QPainterPath()
            clip.addEllipse(ripple.center, ripple.radius, ripple.radius)
            painter.setClipPath(clip)

            white_pen = QPen(QColor("#FFFFFF"))
            white_pen.setWidth(0)
            painter.setPen(white_pen)
            painter.drawPixmap(pixmap_rect, pixmap)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.text())
            painter.restore()

    def mousePressEvent(self, event: QMouseEvent):
        """鼠标按下事件"""
        if event.button() == Qt.LeftButton and self.isEnabled():
            self._pressed = True
            self._start_ripple(event.pos())
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent):
        """鼠标释放事件"""
        if event.button() == Qt.LeftButton:
            self._pressed = False
            self.update()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event: QEnterEvent):
        """鼠标进入"""
        self._hovered = True
        self._update_shadow()
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        self._hovered = False
        self._update_shadow()
        self.update()
        super().leaveEvent(event)

    def setEnabled(self, enabled: bool):
        """设置启用状态"""
        super().setEnabled(enabled)
        self._update_shadow()
        self.update()

    @pyqtProperty(float)
    def checked_progress(self) -> float:
        """选中状态过渡进度（0.0 ~ 1.0）。"""
        return self._checked_progress

    @checked_progress.setter
    def checked_progress(self, value: float):
        self._checked_progress = max(0.0, min(1.0, value))
        try:
            self.update()
        except RuntimeError:
            # 控件可能已被销毁，忽略刷新请求
            pass

    def setChecked(self, checked: bool):
        """设置选中状态并播放淡入淡出动画。"""
        if self.isChecked() == checked:
            return
        super().setChecked(checked)
        delay = 150 if self._ripples else 0
        if delay > 0:
            QTimer.singleShot(delay, lambda: self._start_checked_animation(checked))
        else:
            self._start_checked_animation(checked)

    def _start_checked_animation(self, checked: bool):
        """启动选中状态淡入淡出动画。"""
        self._checked = checked
        self._checked_animation.stop()
        self._checked_animation.setStartValue(self._checked_progress)
        self._checked_animation.setEndValue(1.0 if checked else 0.0)
        self._checked_animation.start()

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

    def ripple_remaining_ms(self) -> int:
        """返回当前水波纹的最长剩余动画时长（毫秒）。"""
        if not self._ripples:
            return 0
        return max(ripple.estimated_duration_ms(16) for ripple in self._ripples)

class MaterialIconButton(QPushButton):
    """Material Design 3 图标按钮"""

    def __init__(self, icon_text: str='', parent: QWidget=None, variant: str=MaterialButton.VARIANT_FILLED):
        super().__init__(icon_text, parent)
        self._base_button = MaterialButton(icon_text, self, variant)
        self._base_button.setFixedHeight(36)
        self._base_button.setFixedWidth(36)
        self._base_button.setCornerRadius(10)
        self._base_button.setElevation(2, 0)
        self._base_button._icon_mode = True
        self.setFixedSize(36, 36)
        self.setFlat(True)
        self.setStyleSheet('background: transparent; border: none;')
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(body_font())
        self._base_button.clicked.connect(self.clicked.emit)

    def setVariant(self, variant: str):
        """设置变体类型"""
        self._base_button.setVariant(variant)

    def setAccentColor(self, color: str):
        """设置主题色"""
        self._base_button.setAccentColor(color)

    def setFixedSize(self, width: int, height: int):
        """设置固定大小"""
        super().setFixedSize(width, height)
        self._base_button.setFixedSize(width, height)
        if width <= 28 or height <= 28:
            self._base_button.setCornerRadius(min(width, height) // 2)
        else:
            self._base_button.setCornerRadius(10)

    def resizeEvent(self, event):
        """调整子按钮大小"""
        super().resizeEvent(event)
        self._base_button.setFixedSize(self.size())

    def paintEvent(self, event: QPaintEvent):
        """不绘制，由子按钮处理"""
        pass

    def setEnabled(self, enabled: bool):
        """设置启用状态"""
        super().setEnabled(enabled)
        self._base_button.setEnabled(enabled)

    def setIcon(self, icon: QIcon):
        """设置按钮图标"""
        super().setIcon(icon)
        self._base_button.setIcon(icon)

    def setIconSize(self, size: QSize):
        """设置图标大小"""
        super().setIconSize(size)
        self._base_button.setIconSize(size)

    def setText(self, text: str):
        """设置按钮文字"""
        super().setText(text)
        self._base_button.setText(text)

class MaterialFAB(QPushButton):
    """Material Design 3 悬浮操作按钮（FAB）"""

    def __init__(self, icon_text: str='', parent: QWidget=None):
        super().__init__(icon_text, parent)
        self._base_button = MaterialButton(icon_text, self, MaterialButton.VARIANT_FILLED)
        self._base_button.setFixedHeight(56)
        self._base_button.setFixedWidth(56)
        self._base_button.setCornerRadius(16)
        self._base_button.setElevation(4, 0)
        self._base_button._icon_mode = True
        self.setFixedSize(56, 56)
        self.setFlat(True)
        self.setStyleSheet('background: transparent; border: none;')
        self.setCursor(Qt.PointingHandCursor)
        self.setFont(body_font())
        self._base_button.clicked.connect(self.clicked.emit)

    def setAccentColor(self, color: str):
        """设置主题色"""
        self._base_button.setAccentColor(color)

    def resizeEvent(self, event):
        """调整子按钮大小"""
        super().resizeEvent(event)
        self._base_button.setFixedSize(self.size())

    def paintEvent(self, event: QPaintEvent):
        """不绘制，由子按钮处理"""
        pass

    def setEnabled(self, enabled: bool):
        """设置启用状态"""
        super().setEnabled(enabled)
        self._base_button.setEnabled(enabled)

    def setIcon(self, icon: QIcon):
        """设置按钮图标"""
        super().setIcon(icon)
        self._base_button.setIcon(icon)

    def setIconSize(self, size: QSize):
        """设置图标大小"""
        super().setIconSize(size)
        self._base_button.setIconSize(size)

    def setText(self, text: str):
        """设置按钮文字"""
        super().setText(text)
        self._base_button.setText(text)
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout, QWidget, QLabel
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle(_('widgets.material_button.demo_title'))
    window.setMinimumWidth(500)
    window.setStyleSheet('background: #FAFAFA;')
    layout = QVBoxLayout(window)
    layout.setSpacing(20)
    layout.setContentsMargins(30, 30, 30, 30)
    title = QLabel(_('widgets.material_button.title'))
    title.setStyleSheet('font-size: 20px; font-weight: bold; color: #333;')
    layout.addWidget(title)
    variants = [(_('gui.widgets.material_button.auto_002'), MaterialButton.VARIANT_FILLED), (_('gui.widgets.material_button.auto_005'), MaterialButton.VARIANT_TONAL), (_('gui.widgets.material_button.auto_003'), MaterialButton.VARIANT_OUTLINED), (_('gui.widgets.material_button.auto_004'), MaterialButton.VARIANT_TEXT), (_('gui.widgets.material_button.auto_001'), MaterialButton.VARIANT_ELEVATED)]
    for text, variant in variants:
        label = QLabel(text)
        label.setStyleSheet('font-size: 12px; color: #666;')
        layout.addWidget(label)
        btn = MaterialButton(_('widgets.material_button.ok_example'))
        btn.setVariant(variant)
        layout.addWidget(btn)
    icon_layout = QHBoxLayout()
    icon_btn = MaterialIconButton('+')
    icon_btn.setVariant(MaterialButton.VARIANT_TONAL)
    icon_layout.addWidget(icon_btn)
    fab = MaterialFAB('+')
    icon_layout.addWidget(fab)
    icon_layout.addStretch()
    layout.addLayout(icon_layout)
    disabled_btn = MaterialButton(_('widgets.material_button.disabled_example'))
    disabled_btn.setEnabled(False)
    layout.addWidget(disabled_btn)
    layout.addStretch()
    window.show()
    sys.exit(app.exec())