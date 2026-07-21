# -*- coding: utf-8 -*-
"""圆形导航按钮组件。

提供直径 48 dp 的圆形按钮，用于新手引导中的上一步、下一步与完成导航。
支持 SVG 图标、主题色/浅色两种背景样式、禁用状态与悬浮提示（QToolTip）。
桌面端按 1 dp = 1 px 处理。
"""

import os
import re
from typing import Optional

from PyQt5.QtCore import Qt, QSize, QRect, QRectF, QTimer, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QPixmap, QMouseEvent, QPaintEvent, QEnterEvent, QPainterPath
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import QPushButton, QWidget

from gui.fonts import body_font
from gui.styles import load_primary_color
from gui.utils.color_utils import mix, ripple_tint
from gui.widgets.ripple_effect import RippleEffect


class CircleNavButton(QPushButton):
    """圆形导航按钮。

    直径固定为 48 dp，支持主题色背景（下一步/完成）与浅色背景（上一步）
    两种视觉样式，支持 SVG 图标渲染与悬浮提示。

    信号:
        clicked(): 按钮被点击时发射（继承自 QPushButton）。

    属性:
        button_style: 按钮背景样式，``'accent'`` 或 ``'light'``。
        accent_color: 主题色，用于 ``accent`` 样式背景与焦点环。
    """

    # 尺寸常量（桌面端 1 dp = 1 px）
    DIAMETER = 48
    ICON_SIZE = 24
    SHADOW_OFFSET = 1

    STYLE_ACCENT = 'accent'
    STYLE_LIGHT = 'light'

    def __init__(
        self,
        icon_path: str = '',
        button_style: str = STYLE_ACCENT,
        tooltip: str = '',
        parent: Optional[QWidget] = None,
    ):
        """初始化圆形导航按钮。

        Args:
            icon_path: SVG 图标路径，支持绝对路径或相对于项目根目录的路径。
            button_style: 背景样式，``'accent'`` 为主题色背景，``'light'`` 为浅色背景。
            tooltip: 悬浮提示文本。
            parent: 父组件。
        """
        super().__init__(parent)
        self._button_style = button_style
        self._accent_color = load_primary_color()
        self._light_bg = '#F5F5F5'
        self._light_hover_bg = '#EEEEEE'
        self._disabled_bg = '#E0E0E0'
        self._disabled_icon_color = '#9E9E9E'
        self._light_icon_color = '#424242'
        self._icon_path = icon_path
        self._rendered_icon: Optional[QPixmap] = None
        self._pressed = False
        self._hovered = False
        self._ripples = []
        self._ripple_color = QColor(self._get_ripple_color())
        self._ripple_timer = QTimer(self)
        self._ripple_timer.timeout.connect(self._update_ripples)

        self.setFixedSize(self.DIAMETER, self.DIAMETER)
        self.setFont(body_font())
        self.setCursor(Qt.PointingHandCursor)
        self.setFlat(True)
        self.setStyleSheet('background: transparent; border: none;')
        self.setAttribute(Qt.WA_Hover, True)
        self.setFocusPolicy(Qt.NoFocus)

        if tooltip:
            self.setToolTip(tooltip)

        self._load_icon()

    # ----- 公共 API -----

    def setIcon(self, icon_path: str) -> None:
        """设置 SVG 图标路径。

        与 QPushButton 的原生 ``setIcon(QIcon)`` 不同，本组件仅接受 SVG 文件路径字符串，
        并在内部按当前样式渲染为指定颜色的位图。

        Args:
            icon_path: SVG 文件路径，支持绝对路径或相对于项目根目录的路径。
        """
        self._icon_path = icon_path
        self._load_icon()
        self.update()

    def setTooltip(self, tooltip: str) -> None:
        """设置悬浮提示文本。

        Args:
            tooltip: 提示文本。
        """
        self.setToolTip(tooltip)

    def setButtonStyle(self, style: str) -> None:
        """设置按钮背景样式。

        Args:
            style: ``'accent'`` 表示主题色背景（白色图标）；
                ``'light'`` 表示浅色背景（深色图标）。
        """
        if style not in (self.STYLE_ACCENT, self.STYLE_LIGHT):
            style = self.STYLE_ACCENT
        self._button_style = style
        self._ripple_color = QColor(self._get_ripple_color())
        self._load_icon()
        self.update()

    def setAccentColor(self, color: str) -> None:
        """设置主题色。

        Args:
            color: 十六进制颜色字符串，例如 ``'#2078DA'``。
        """
        self._accent_color = color
        self._ripple_color = QColor(self._get_ripple_color())
        self._load_icon()
        self.update()

    def setEnabled(self, enabled: bool) -> None:
        """设置启用状态。

        Args:
            enabled: 是否启用按钮。
        """
        super().setEnabled(enabled)
        self.setCursor(Qt.PointingHandCursor if enabled else Qt.ArrowCursor)
        self._load_icon()
        self.update()

    def sizeHint(self) -> QSize:
        """返回建议大小。"""
        return QSize(self.DIAMETER, self.DIAMETER)

    def minimumSizeHint(self) -> QSize:
        """返回最小建议大小。"""
        return QSize(self.DIAMETER, self.DIAMETER)

    # ----- 绘制 -----

    def paintEvent(self, event: QPaintEvent) -> None:
        """自定义绘制圆形按钮、图标、焦点指示器与投影。"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        try:
            self._draw_shadow(painter)

            bg_color = QColor(self._get_bg_color())
            if self.isEnabled():
                if self._pressed:
                    bg_color = QColor(mix(bg_color.name(), '#000000', 0.12))
                elif self._hovered and self._button_style == self.STYLE_LIGHT:
                    bg_color = QColor(self._light_hover_bg)
                elif self._hovered and self._button_style == self.STYLE_ACCENT:
                    bg_color = QColor(mix(bg_color.name(), '#FFFFFF', 0.08))

            painter.setPen(Qt.NoPen)
            painter.setBrush(bg_color)
            painter.drawEllipse(QRectF(self.rect().adjusted(0, 0, -1, -1)))

            # 绘制水波纹
            painter.save()
            clip_path = QPainterPath()
            clip_path.addEllipse(QRectF(self.rect().adjusted(0, 0, -1, -1)))
            painter.setClipPath(clip_path)
            for ripple in self._ripples:
                ripple.draw(painter)
            painter.restore()

            if self._rendered_icon:
                icon_rect = self._rendered_icon.rect()
                icon_rect.moveCenter(self.rect().center())
                painter.drawPixmap(icon_rect, self._rendered_icon)
        finally:
            if painter.isActive():
                painter.end()

    def _draw_shadow(self, painter: QPainter) -> None:
        """为主题色按钮绘制柔和的 1 dp 投影。"""
        if self._button_style != self.STYLE_ACCENT or not self.isEnabled():
            return
        shadow_color = QColor(0, 0, 0, 35)
        painter.setPen(Qt.NoPen)
        painter.setBrush(shadow_color)
        shadow_rect = QRect(
            1,
            self.SHADOW_OFFSET + 1,
            self.DIAMETER - 2,
            self.DIAMETER - 2,
        )
        painter.drawEllipse(QRectF(shadow_rect))

    # ----- 事件处理 -----

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """鼠标按下事件。"""
        if event.button() == Qt.LeftButton and self.isEnabled():
            self._pressed = True
            self._start_ripple(event.pos())
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """鼠标释放事件。"""
        if event.button() == Qt.LeftButton:
            self._pressed = False
            self.update()
            if not self.rect().contains(event.pos()):
                return
        super().mouseReleaseEvent(event)

    def enterEvent(self, event: QEnterEvent) -> None:
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

    # ----- 内部方法 -----

    def _get_icon_color(self) -> str:
        """返回当前应使用的图标颜色。"""
        if not self.isEnabled():
            return self._disabled_icon_color
        if self._button_style == self.STYLE_ACCENT:
            return '#FFFFFF'
        return self._light_icon_color

    def _get_bg_color(self) -> str:
        """返回当前应使用的背景颜色。"""
        if not self.isEnabled():
            return self._disabled_bg
        if self._button_style == self.STYLE_ACCENT:
            return self._accent_color
        return self._light_bg

    def _load_icon(self) -> None:
        """加载 SVG 图标并按当前颜色渲染为位图。"""
        self._rendered_icon = None
        resolved_path = self._resolve_icon_path(self._icon_path)
        if not resolved_path or not os.path.exists(resolved_path):
            return

        painter = None
        try:
            with open(resolved_path, 'r', encoding='utf-8') as f:
                svg_data = f.read()
            icon_color = self._get_icon_color()
            svg_data = self._replace_svg_fill(svg_data, icon_color)
            renderer = QSvgRenderer(bytes(svg_data, encoding='utf-8'))
            pixmap = QPixmap(self.ICON_SIZE, self.ICON_SIZE)
            pixmap.fill(Qt.transparent)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            renderer.render(painter)
            self._rendered_icon = pixmap
        except Exception:
            self._rendered_icon = None
        finally:
            if painter is not None and painter.isActive():
                painter.end()

    @classmethod
    def _resolve_icon_path(cls, icon_path: str) -> str:
        """解析图标路径。

        若路径不存在，则尝试以项目根目录为基准拼接。

        Args:
            icon_path: 原始图标路径。

        Returns:
            解析后的路径（可能仍然不存在）。
        """
        if not icon_path:
            return icon_path
        if os.path.isabs(icon_path) and os.path.exists(icon_path):
            return icon_path
        if os.path.exists(icon_path):
            return icon_path
        # gui/components/circle_nav_button.py -> 上 3 级为项目根目录
        project_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        candidate = os.path.join(project_root, icon_path)
        if os.path.exists(candidate):
            return candidate
        return icon_path

    def _get_ripple_color(self) -> str:
        """返回当前背景下的水波纹颜色。

        主题色背景使用淡白色，浅色背景使用淡黑色，确保水波纹可见且自然。
        """
        if self._button_style == self.STYLE_ACCENT and self.isEnabled():
            return mix(self._accent_color, '#FFFFFF', 0.28)
        return mix(self._light_bg, '#000000', 0.12)

    def _start_ripple(self, pos) -> None:
        """启动水波纹。"""
        max_radius = self.DIAMETER * 1.5
        ripple = RippleEffect(QPointF(pos), 0, self._ripple_color, max_radius)
        self._ripples.append(ripple)
        if not self._ripple_timer.isActive():
            self._ripple_timer.start(16)

    def _update_ripples(self) -> None:
        """更新水波纹动画。"""
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

    @staticmethod
    def _replace_svg_fill(svg_data: str, color: str) -> str:
        """将 SVG 中的 fill/stroke 颜色替换为指定颜色。

        处理 ``fill="..."``、``fill='...'``、``style="fill: ..."`` 形式，
        同时处理 ``stroke`` 描边属性（大小写不敏感）。若根 ``<svg>`` 未设置 fill，
        则注入 ``fill="{color}"`` 确保默认颜色可覆盖白色/黑色图标。

        Args:
            svg_data: 原始 SVG 文本。
            color: 目标颜色。

        Returns:
            替换后的 SVG 文本。
        """
        lower_data = svg_data.lower()
        has_fill = 'fill=' in lower_data or 'fill:' in lower_data
        has_stroke = 'stroke=' in lower_data or 'stroke:' in lower_data
        if not has_fill and not has_stroke:
            svg_data = re.sub(
                r'<svg([^>]*)>',
                rf'<svg\1 fill="{color}">',
                svg_data,
                count=1,
            )
        svg_data = re.sub(r'(?i)fill="[^"]*"', f'fill="{color}"', svg_data)
        svg_data = re.sub(r"(?i)fill='[^']*'", f'fill="{color}"', svg_data)
        svg_data = re.sub(r'(?i)fill:\s*[^;"\']*', f'fill:{color}', svg_data)
        svg_data = re.sub(r'(?i)stroke="[^"]*"', f'stroke="{color}"', svg_data)
        svg_data = re.sub(r"(?i)stroke='[^']*'", f'stroke="{color}"', svg_data)
        svg_data = re.sub(r'(?i)stroke:\s*[^;"\']*', f'stroke:{color}', svg_data)
        return svg_data
