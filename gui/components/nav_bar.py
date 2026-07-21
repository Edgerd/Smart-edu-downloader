# -*- coding: utf-8 -*-
"""导航栏组件"""

import os

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QPushButton, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QTimer, pyqtProperty, QPropertyAnimation, QEasingCurve, QEvent
from PyQt5.QtGui import (
    QPainter, QColor, QPainterPath, QMouseEvent,
    QPaintEvent, QEnterEvent, QFontMetrics
)

from gui.fonts import get_harmonyos_family
from gui.utils.color_utils import ripple_tint, mix
from gui.widgets.ripple_effect import RippleEffect
from gui.styles import load_primary_color
from core.ui.icon_manager import NAV_ICONS, IconManager


class NavButton(QPushButton):
    """带 Material 水波纹的导航按钮"""

    def __init__(self, active_color: str = None, radius: int = 20, parent: QWidget = None):
        super().__init__(parent)

        self._active_color = active_color or load_primary_color()
        self._radius = radius
        self._ripples = []
        self._ripple_color = QColor(ripple_tint(self._active_color))
        self._ripple_timer = QTimer(self)
        self._ripple_timer.timeout.connect(self._update_ripples)
        self.destroyed.connect(self._stop_ripple_timer)

        # 选中状态过渡动画进度（0.0 ~ 1.0）
        self._is_active = False
        self._hovered = False
        self._pressed = False
        self._active_progress = 0.0
        self._active_animation = QPropertyAnimation(self, b'active_progress', self)
        self._active_animation.setDuration(180)
        self._active_animation.setEasingCurve(QEasingCurve.InOutCubic)

        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)

    def set_active_color(self, color: str):
        """设置激活时的主题色"""
        self._active_color = color
        self._ripple_color = QColor(ripple_tint(color))
        self.update()

    def set_radius(self, radius: int):
        """设置按钮圆角半径"""
        self._radius = radius
        self.update()

    @pyqtProperty(float)
    def active_progress(self) -> float:
        """选中状态过渡进度（0.0 ~ 1.0）。"""
        return self._active_progress

    @active_progress.setter
    def active_progress(self, value: float):
        self._active_progress = max(0.0, min(1.0, value))
        try:
            self.update()
        except RuntimeError:
            # 控件可能已被销毁，忽略刷新请求
            pass

    def set_active(self, active: bool):
        """设置激活状态并播放淡入淡出动画。"""
        if self._is_active == active:
            return
        self._is_active = active
        self._ripple_color = self._ripple_color_for_state()
        self._active_animation.stop()
        self._active_animation.setStartValue(self._active_progress)
        self._active_animation.setEndValue(1.0 if active else 0.0)
        self._active_animation.start()

    def _ripple_color_for_state(self) -> QColor:
        """根据当前状态返回水波纹颜色：选中为主题色淡化，未选中为白色"""
        if self._is_active:
            return QColor(ripple_tint(self._active_color))
        return QColor(255, 255, 255, 150)

    def _shape_path(self) -> QPainterPath:
        """生成圆角矩形裁剪路径"""
        path = QPainterPath()
        rect = self.rect()
        path.addRoundedRect(rect.x(), rect.y(), rect.width(), rect.height(), self._radius, self._radius)
        return path

    def paintEvent(self, event: QPaintEvent):
        """自定义绘制：背景淡入淡出 + 水波纹。"""
        # 先让父类绘制子控件（图标和文字标签）
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        try:
            progress = self._active_progress

            # 基础背景（悬浮 / 按下 / 普通）
            if self._pressed:
                base_bg = QColor(255, 255, 255, 51)
            elif self._hovered:
                base_bg = QColor(255, 255, 255, 31)
            else:
                base_bg = QColor(255, 255, 255, 0)

            # 激活背景目标色（白色不透明）
            active_bg = QColor(255, 255, 255, 242)

            # 根据进度插值得到当前背景色
            bg = QColor(
                int(base_bg.red() + (active_bg.red() - base_bg.red()) * progress),
                int(base_bg.green() + (active_bg.green() - base_bg.green()) * progress),
                int(base_bg.blue() + (active_bg.blue() - base_bg.blue()) * progress),
                int(base_bg.alpha() + (active_bg.alpha() - base_bg.alpha()) * progress),
            )

            if bg.alpha() > 0:
                painter.fillRect(self.rect(), bg)

            painter.setClipPath(self._shape_path())
            for ripple in self._ripples:
                ripple.draw(painter)
        finally:
            if painter.isActive():
                painter.end()

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
        """鼠标按下时启动水波纹"""
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

    def _start_ripple(self, pos):
        """启动水波纹"""
        max_radius = max(self.width(), self.height()) * 1.5
        ripple = RippleEffect(QPointF(pos), 0, self._ripple_color_for_state(), max_radius)
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

    def _stop_ripple_timer(self):
        """停止水波纹动画定时器。"""
        if self._ripple_timer and self._ripple_timer.isActive():
            self._ripple_timer.stop()
        self._ripples.clear()

    def ripple_remaining_ms(self) -> int:
        """返回当前水波纹的最长剩余动画时长（毫秒）。"""
        if not self._ripples:
            return 0
        return max(ripple.estimated_duration_ms(16) for ripple in self._ripples)


class NavBar(QWidget):
    """导航栏组件"""

    page_switch_requested = pyqtSignal(int)

    # 导航配置常量 - 使用 SVG 图标
    NAV_CONFIG = NAV_ICONS

    # 颜色定义
    COLOR_INACTIVE = "#FFFFFF"  # 非激活状态 - 白色

    def __init__(self, add_nav_hover_effect_fn=None, add_hover_tooltip_fn=None, radius: int = 20, parent=None):
        """初始化导航栏

        Args:
            add_nav_hover_effect_fn: 外部传入的导航悬停动画函数
            add_hover_tooltip_fn: 外部传入的悬停提示函数
            radius: 导航按钮圆角半径
            parent: 父组件
        """
        super().__init__(parent)
        self._add_nav_hover_effect = add_nav_hover_effect_fn
        self._add_hover_tooltip = add_hover_tooltip_fn
        self._button_radius = radius

        # 从设置读取主题色
        self._accent_color = load_primary_color()

        # 初始化 SVG 图标管理器
        # nav_bar.py 在 gui/components/ -> 上3级 = 项目根目录
        app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.icon_manager = IconManager(app_root)

        self.setFixedHeight(55)
        self.setObjectName("navBar")
        self.setAttribute(Qt.WA_StyledBackground, True)

        # 设置初始默认背景，避免启动瞬间透明；主窗口后续会覆盖为渐变主题色。
        default_bg = load_primary_color()
        self.setStyleSheet(f"""
            QWidget#navBar {{
                background: {default_bg};
            }}
        """)

        self.nav_buttons = []
        self.nav_icon_labels = []
        self.nav_configs = []

        self._create_layout()
        self._create_nav_buttons()
    
    def _create_layout(self):
        """创建导航栏布局"""
        self.nav_layout = QHBoxLayout()
        self.nav_layout.setContentsMargins(20, 0, 20, 0)
        self.nav_layout.setSpacing(15)
        self.setLayout(self.nav_layout)
    
    def _load_svg_icon(self, icon_name, color, size=(30, 30)):
        """加载 SVG 图标并着色"""
        return self.icon_manager.load_colored_pixmap(icon_name, color, size)
    
    def _create_nav_buttons(self):
        """创建导航按钮"""
        for i, config in enumerate(self.NAV_CONFIG):
            btn = self._create_nav_button(i, config)
            
            if self._add_nav_hover_effect:
                self._add_nav_hover_effect(btn, i)
            if self._add_hover_tooltip:
                self._add_hover_tooltip(btn, config['tip'])
            
            btn.clicked.connect(lambda _, idx=i: self.page_switch_requested.emit(idx))
            
            self.nav_buttons.append(btn)
            self.nav_configs.append(config)
            self.nav_layout.addWidget(btn)
        
        self.nav_layout.addStretch()
    
    def _create_nav_button(self, index, config):
        """创建单个导航按钮

        Args:
            index: 按钮索引
            config: 按钮配置字典

        Returns:
            QPushButton: 导航按钮实例
        """
        btn = NavButton(active_color=self._accent_color, radius=self._button_radius)
        btn.setFixedHeight(40)
        btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        btn.setObjectName(f"navBtn_{index}")
        btn.setProperty("active", index == 0)
        btn.setContentsMargins(0, 0, 0, 0)

        # 创建水平布局用于图标和文字
        btn_layout = QHBoxLayout()
        margin_h = 15
        icon_size = 30
        font_size = 11
        btn_layout.setContentsMargins(margin_h, 0, margin_h, 0)
        btn_layout.setSpacing(6)
        btn_layout.setAlignment(Qt.AlignCenter)

        # 加载并添加 SVG 图标（带颜色）
        icon_color = self._accent_color if index == 0 else self.COLOR_INACTIVE
        icon_pixmap = self._load_svg_icon(config['icon_file'], icon_color, size=(icon_size, icon_size))

        icon_label = QLabel()
        icon_label.setFixedSize(icon_size, icon_size)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setObjectName(f"navIcon_{index}")
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)

        if icon_pixmap and not icon_pixmap.isNull():
            icon_label.setPixmap(icon_pixmap)

        btn_layout.addWidget(icon_label)
        self.nav_icon_labels.append(icon_label)

        # 添加文字标签
        from gui.fonts import nav_font
        name_label = QLabel(config['name'])
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setObjectName(f"navText_{index}")
        name_label.setProperty("active", index == 0)
        name_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        name_label.setWordWrap(False)
        name_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        name_label.setToolTip(config['tip'])

        font = nav_font()
        font.setPointSize(font_size)
        name_label.setFont(font)
        btn_layout.addWidget(name_label)

        btn.setLayout(btn_layout)

        # 手动计算按钮宽度
        font_metrics = QFontMetrics(font)
        text_width = font_metrics.horizontalAdvance(config['name'])
        calculated_width = margin_h * 2 + icon_size + 6 + text_width + 4
        btn.setMinimumWidth(calculated_width)

        btn.setStyleSheet(self._get_nav_button_style())

        return btn

    def set_active_button(self, index):
        """设置激活的导航按钮。

        若按钮正在播放水波纹，则延迟改变 active 状态，等水波纹动画
        基本结束后再改变背景色和图标颜色。

        Args:
            index: 要激活的按钮索引
        """
        for i, btn in enumerate(self.nav_buttons):
            is_active = (i == index)
            current_active = btn.property("active")

            # 只对状态改变的按钮进行样式更新
            if current_active != is_active:
                delay = 150 if btn._ripples else 0
                if delay > 0:
                    QTimer.singleShot(delay, lambda idx=i, active=is_active: self._update_button_state(idx, active))
                else:
                    # 没有水波纹，立即改变状态
                    self._update_button_state(i, is_active)

    def _update_button_state(self, index, is_active):
        """更新按钮的视觉状态。

        Args:
            index: 按钮索引
            is_active: 是否激活
        """
        if index >= len(self.nav_buttons):
            return

        btn = self.nav_buttons[index]

        # 播放背景淡入淡出动画
        btn.set_active(is_active)

        # 更新文字标签 active 属性
        text_label = btn.findChild(QLabel, f"navText_{index}")
        if text_label:
            text_label.setProperty("active", is_active)
            text_label.style().unpolish(text_label)
            text_label.style().polish(text_label)

        # 更新图标 - 重新加载 SVG 并设置新颜色
        icon_label = btn.findChild(QLabel, f"navIcon_{index}")
        if icon_label:
            new_color = self._accent_color if is_active else self.COLOR_INACTIVE
            config = self.nav_configs[index]
            new_pixmap = self._load_svg_icon(config['icon_file'], new_color)
            if new_pixmap and not new_pixmap.isNull():
                icon_label.setPixmap(new_pixmap)

    def get_button_by_index(self, index):
        """获取指定索引的导航按钮
        
        Args:
            index: 按钮索引
        
        Returns:
            QPushButton or None: 导航按钮实例
        """
        if 0 <= index < len(self.nav_buttons):
            return self.nav_buttons[index]
        return None
    
    def get_button_count(self):
        """获取导航按钮数量
        
        Returns:
            int: 按钮数量
        """
        return len(self.nav_buttons)

    def set_bar_background(self, background: str):
        """设置导航栏背景（支持纯色或渐变 CSS）。

        Args:
            background: CSS background 值，如 rgba(...) 或 qlineargradient(...)。
        """
        self.setStyleSheet(f"""
            QWidget#navBar {{
                background: {background};
            }}
        """)

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新导航栏按钮样式和图标

        Args:
            primary: 主题主色。
            background: 主题背景色。
        """
        self._accent_color = primary

        for i, btn in enumerate(self.nav_buttons):
            btn.set_active_color(primary)
            btn.set_radius(self._button_radius)
            # 重新生成并应用按钮样式表
            btn.setStyleSheet(self._get_nav_button_style())

            # 更新图标颜色
            icon_label = btn.findChild(QLabel, f"navIcon_{i}")
            if icon_label:
                is_active = btn.property("active") is True
                icon_color = primary if is_active else self.COLOR_INACTIVE
                config = self.nav_configs[i]
                icon_size = icon_label.width() or 30
                new_pixmap = self._load_svg_icon(config['icon_file'], icon_color, size=(icon_size, icon_size))
                if new_pixmap and not new_pixmap.isNull():
                    icon_label.setPixmap(new_pixmap)

    def _get_nav_button_style(self):
        """获取导航按钮样式表。

        背景完全由 NavButton.paintEvent 根据 active_progress 绘制，
        样式表仅保留透明底与文字颜色，避免与自定义绘制冲突。
        """
        font_family = get_harmonyos_family()
        radius = self._button_radius
        default_style = f"""
            QPushButton[objectName^="navBtn_"] {{
                background: transparent;
                border: none;
                border-radius: {radius}px;
            }}
            QLabel[objectName^="navText_"] {{
                color: #FFFFFF;
                font-family: "{font_family}";
                font-size: 11pt;
                font-weight: 500;
            }}
        """
        active_style = f"""
            QLabel[objectName^="navText_"][active="true"] {{
                color: {self._accent_color};
                font-weight: 600;
            }}
        """
        return default_style + active_style
