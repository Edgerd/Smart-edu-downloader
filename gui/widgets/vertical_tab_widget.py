# -*- coding: utf-8 -*-
"""
垂直标签页组件。

侧边栏标签按钮采用 Chrome 设置风格：左侧贴边（直角）、右侧圆角，
并带有 Material Design 水波纹与悬浮阴影效果。
"""

import os
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QStackedWidget, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPointF, QByteArray, pyqtProperty, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import (
    QPainter, QColor, QPainterPath, QFont, QMouseEvent,
    QPaintEvent, QEnterEvent, QPixmap, QPen
)
from PyQt5.QtSvg import QSvgRenderer

from gui.fonts import body_font
from gui.utils.color_utils import ripple_tint, mix, darken
from gui.widgets.ripple_effect import RippleEffect
from gui.styles import load_background_color, load_primary_color


class MaterialTabButton(QPushButton):
    """侧边栏标签按钮：左侧贴边、右侧圆角。"""

    def __init__(self, text: str = "", icon_path: str = "", parent: QWidget = None):
        super().__init__(text, parent)

        self._accent_color = load_primary_color()
        self._selected = False
        self._hovered = False
        self._pressed = False
        self._ripples = []
        self._ripple_color = QColor(ripple_tint(self._accent_color))
        self._ripple_timer = QTimer(self)
        self._ripple_timer.timeout.connect(self._update_ripples)

        # 选中状态过渡动画进度（0.0 ~ 1.0）
        self._selection_progress = 0.0
        self._selection_animation = QPropertyAnimation(self, b'selection_progress', self)
        self._selection_animation.setDuration(180)
        self._selection_animation.setEasingCurve(QEasingCurve.InOutCubic)

        self._icon_path = icon_path
        self._icon_size = 20
        self._icon_pixmap = None
        self._load_icon()

        self._shadow_effect = QGraphicsDropShadowEffect(self)
        self._shadow_effect.setBlurRadius(6)
        self._shadow_effect.setColor(QColor(0, 0, 0, 30))
        self._shadow_effect.setOffset(2, 0)
        self.setGraphicsEffect(self._shadow_effect)
        self._update_shadow()

        self.setCursor(Qt.PointingHandCursor)
        self.setFont(body_font())
        self.setFixedHeight(42)
        self.setAttribute(Qt.WA_Hover, True)

    @pyqtProperty(float)
    def selection_progress(self) -> float:
        """选中状态过渡进度（0.0 ~ 1.0）。"""
        return self._selection_progress

    @selection_progress.setter
    def selection_progress(self, value: float):
        self._selection_progress = max(0.0, min(1.0, value))
        try:
            self.update()
        except RuntimeError:
            # 控件可能已被销毁，忽略刷新请求
            pass

    def setAccentColor(self, color: str):
        """设置主题色"""
        self._accent_color = color
        self._update_ripple_color()
        self._load_icon()
        self.update()

    def setSelected(self, selected: bool):
        """设置选中状态并播放淡入淡出动画。"""
        if self._selected == selected:
            return
        self._selected = selected
        self._update_ripple_color()
        self._load_icon()

        # 停止可能正在进行的旧动画，并从当前进度平滑过渡到目标值
        self._selection_animation.stop()
        self._selection_animation.setStartValue(self._selection_progress)
        self._selection_animation.setEndValue(1.0 if selected else 0.0)
        self._selection_animation.start()

    def setIconPath(self, icon_path: str):
        """设置图标路径"""
        self._icon_path = icon_path
        self._load_icon()
        self.update()

    def _load_icon(self):
        """加载 SVG 图标并生成未选中/选中两种颜色的 pixmap。"""
        if not self._icon_path or not os.path.exists(self._icon_path):
            self._icon_pixmap_normal = None
            self._icon_pixmap_selected = None
            return

        self._icon_pixmap_normal = self._render_icon_with_color("#666666")
        self._icon_pixmap_selected = self._render_icon_with_color("#FFFFFF")

    def _render_icon_with_color(self, color: str) -> Optional[QPixmap]:
        """将 SVG 图标渲染为指定颜色的 pixmap。"""
        painter = None
        try:
            with open(self._icon_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()

            # 替换常见颜色占位符为当前颜色
            svg_content = svg_content.replace('fill="#1A82E2"', f'fill="{self._accent_color}"')
            svg_content = svg_content.replace('fill="#2078DA"', f'fill="{self._accent_color}"')
            svg_content = svg_content.replace('fill="white"', f'fill="{color}"')
            svg_content = svg_content.replace('fill="#FFFFFF"', f'fill="{color}"')

            renderer = QSvgRenderer(QByteArray(svg_content.encode('utf-8')))
            pixmap = QPixmap(self._icon_size, self._icon_size)
            pixmap.fill(Qt.transparent)

            painter = QPainter(pixmap)
            renderer.render(painter)
            return pixmap
        except Exception:
            return None
        finally:
            if painter is not None and painter.isActive():
                painter.end()

    def _update_ripple_color(self):
        """使用主题色淡化后的颜色作为水波纹颜色"""
        self._ripple_color = QColor(ripple_tint(self._accent_color))

    @staticmethod
    def _interpolate_color(start: QColor, end: QColor, t: float) -> QColor:
        """在两种颜色之间线性插值。"""
        t = max(0.0, min(1.0, t))
        return QColor(
            int(start.red() + (end.red() - start.red()) * t),
            int(start.green() + (end.green() - start.green()) * t),
            int(start.blue() + (end.blue() - start.blue()) * t),
            int(start.alpha() + (end.alpha() - start.alpha()) * t),
        )

    def _current_background_color(self) -> QColor:
        """获取当前背景色（已包含选中过渡插值）。"""
        if self._selected and self._selection_progress >= 1.0:
            bg = QColor(self._accent_color)
        else:
            if self._hovered:
                bg = QColor(mix("#FFFFFF", self._accent_color, 0.08))
            else:
                bg = QColor(self._accent_color)
                bg.setAlpha(0)
            target = QColor(self._accent_color)
            bg = self._interpolate_color(bg, target, self._selection_progress)
        if self._pressed and self.isEnabled():
            bg = QColor(darken(f"#{bg.red():02x}{bg.green():02x}{bg.blue():02x}", 12))
            bg.setAlpha(bg.alpha())
        return bg

    def _update_shadow(self):
        """阴影仅在悬浮且未选中时显示"""
        if self._hovered and not self._selected:
            self._shadow_effect.setEnabled(True)
        else:
            self._shadow_effect.setEnabled(False)

    def _shape_path(self) -> QPainterPath:
        """生成左方右圆的按钮形状路径"""
        path = QPainterPath()
        width = self.width()
        height = self.height()
        radius = min(20, height // 2)

        # 从左上角开始，顺时针绘制
        path.moveTo(0, 0)
        path.lineTo(width - radius, 0)
        path.arcTo(width - 2 * radius, 0, 2 * radius, 2 * radius, 90, -90)
        path.lineTo(width, height - radius)
        path.arcTo(width - 2 * radius, height - 2 * radius, 2 * radius, 2 * radius, 0, -90)
        path.lineTo(0, height)
        path.lineTo(0, 0)
        return path

    def paintEvent(self, event: QPaintEvent):
        """自定义绘制"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        try:
            height = self.height()

            # 背景色
            bg_color = self._current_background_color()

            # 绘制背景
            path = self._shape_path()
            if bg_color.alpha() > 0:
                painter.fillPath(path, bg_color)

            # 绘制水波纹
            painter.setClipPath(path)
            for ripple in self._ripples:
                ripple.draw(painter)
            painter.setClipping(False)

            # 计算图标和文字区域
            has_icon = bool(self._icon_pixmap_normal and self._icon_pixmap_selected)
            icon_width = self._icon_size + 8 if has_icon else 0
            progress = self._selection_progress
            text_color = self._interpolate_color(QColor("#666666"), QColor("#FFFFFF"), progress)

            # 绘制图标（带淡入淡出）
            icon_x = 12
            icon_y = (height - self._icon_size) // 2
            if has_icon:
                if progress <= 0.0:
                    painter.drawPixmap(icon_x, icon_y, self._icon_pixmap_normal)
                elif progress >= 1.0:
                    painter.drawPixmap(icon_x, icon_y, self._icon_pixmap_selected)
                else:
                    painter.drawPixmap(icon_x, icon_y, self._icon_pixmap_normal)
                    painter.save()
                    painter.setOpacity(progress)
                    painter.drawPixmap(icon_x, icon_y, self._icon_pixmap_selected)
                    painter.restore()

            # 绘制文字
            painter.setPen(text_color)
            font = self.font()
            font.setWeight(QFont.Medium)
            font.setPixelSize(13)
            painter.setFont(font)
            # 左侧留出边距，为图标腾出空间
            text_rect = self.rect().adjusted(12 + icon_width, 0, -12, 0)
            painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.text())

            # 水波纹所到之处文字与图标变白：在波纹覆盖区域以白色重绘
            if self._ripples:
                white_pen = QPen(QColor("#FFFFFF"))
                white_pen.setWidth(0)
                painter.setPen(white_pen)
                for ripple in self._ripples:
                    if ripple.alpha <= 0 or ripple.radius <= 0:
                        continue
                    # 设置裁剪区域为当前波纹的圆形范围
                    painter.save()
                    clip = QPainterPath()
                    clip.addEllipse(ripple.center, ripple.radius, ripple.radius)
                    painter.setClipPath(clip)
                    if has_icon:
                        painter.drawPixmap(icon_x, icon_y, self._icon_pixmap_selected)
                    painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, self.text())
                    painter.restore()
        finally:
            if painter.isActive():
                painter.end()

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

    def enterEvent(self, event: QEnterEvent):
        """鼠标进入"""
        self._hovered = True
        self._update_ripple_color()
        self._update_shadow()
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开"""
        self._hovered = False
        self._update_ripple_color()
        self._update_shadow()
        self.update()
        super().leaveEvent(event)

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


class VerticalTabWidget(QWidget):
    """垂直标签页组件"""
    tab_changed = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tabs = []
        self._current_index = -1
        self._accent_color = load_primary_color()
        self._background_color = load_background_color()
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self.tab_bar = QWidget()
        self.tab_bar.setFixedWidth(120)
        self.tab_bar.setStyleSheet(f"background-color: {self._background_color};")
        self.tab_layout = QVBoxLayout()
        self.tab_layout.setContentsMargins(0, 8, 0, 8)
        self.tab_layout.setSpacing(4)
        self.tab_layout.addStretch()
        self.tab_bar.setLayout(self.tab_layout)
        main_layout.addWidget(self.tab_bar)

        self.stacked_widget = QStackedWidget()
        self._update_stacked_widget_style()
        main_layout.addWidget(self.stacked_widget)

    def _update_stacked_widget_style(self):
        """根据当前背景色更新内容区样式"""
        self.stacked_widget.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {self._background_color};
                border: 1px solid {self._background_color};
                border-radius: 8px;
            }}
        """)

    def setAccentColor(self, color: str):
        """设置主题色，同步到所有标签按钮"""
        self._accent_color = color
        for tab_button, _ in self._tabs:
            tab_button.setAccentColor(color)

    def setBackgroundColor(self, color: str):
        """设置背景色，同步到侧边栏和内容区"""
        self._background_color = color
        self.tab_bar.setStyleSheet(f"background-color: {color};")
        self._update_stacked_widget_style()

    def addTab(self, widget, title, icon_path: str = ""):
        """添加标签页

        Args:
            widget: 标签页内容控件
            title: 标签标题
            icon_path: 标签图标路径（可选）
        """
        # 创建自定义侧边栏标签按钮
        tab_button = MaterialTabButton(title, icon_path)
        tab_button.setAccentColor(self._accent_color)

        # 保存当前标签数量
        tab_index = len(self._tabs)

        # 连接点击事件
        def on_tab_clicked():
            self.setCurrentIndex(tab_index)

        tab_button.clicked.connect(on_tab_clicked)

        # 插入到 stretch 之前
        self.tab_layout.insertWidget(self.tab_layout.count() - 1, tab_button)

        # 添加到内容区域
        self.stacked_widget.addWidget(widget)

        # 保存标签信息
        self._tabs.append((tab_button, title))

        # 如果是第一个标签，设置为当前标签
        if len(self._tabs) == 1:
            self.setCurrentIndex(0)

        return tab_index

    @staticmethod
    def _ripple_remaining_ms(button) -> int:
        """计算标签按钮上水波纹的最长剩余时长（毫秒）。"""
        if not hasattr(button, '_ripples') or not button._ripples:
            return 0
        return max(
            ripple.estimated_duration_ms(16) for ripple in button._ripples
        )

    def setCurrentIndex(self, index):
        """设置当前标签页。

        若目标按钮或当前按钮正在播放水波纹，则短暂延迟后启动选中
        状态淡入淡出动画，避免背景立即变色覆盖水波纹。
        """
        if 0 <= index < len(self._tabs):
            # 点击已选中的标签，保持当前状态并保留水波纹反馈
            if index == self._current_index:
                return

            delay = 150 if any(self._tabs[i][0]._ripples for i in range(len(self._tabs))) else 0

            # 更新之前的标签状态
            if self._current_index != -1:
                old_button = self._tabs[self._current_index][0]
                if delay > 0:
                    QTimer.singleShot(delay, lambda btn=old_button: btn.setSelected(False))
                else:
                    old_button.setSelected(False)

            # 更新当前标签状态（如有水波纹也延迟，避免背景立即变色覆盖动画）
            current_button = self._tabs[index][0]
            if delay > 0:
                QTimer.singleShot(delay, lambda btn=current_button: btn.setSelected(True))
            else:
                current_button.setSelected(True)

            # 更新内容区域
            self.stacked_widget.setCurrentIndex(index)
            self._current_index = index
            self.tab_changed.emit(index)

    def currentIndex(self):
        """获取当前标签页索引"""
        return self._current_index

    def count(self):
        """获取标签页数量"""
        return len(self._tabs)
