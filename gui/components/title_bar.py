# -*- coding: utf-8 -*-
"""
标题栏组件
职责：标题栏 UI 创建、按钮事件信号发射
"""

import os

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QIcon

from gui.widgets.title_bar_button import TitleBarButton

from gui.fonts import title_font
from gui.styles import load_primary_color
from core.ui.icon_manager import IconManager
from core.i18n import _


class TitleBar(QWidget):
    """标题栏组件
    
    信号:
        minimize_requested: 最小化按钮被点击
        maximize_requested: 最大化按钮被点击
        close_requested: 关闭按钮被点击
    """
    
    minimize_requested = pyqtSignal()
    maximize_requested = pyqtSignal()
    close_requested = pyqtSignal()
    
    def __init__(self, title_text="SED - Smart-edu-downloader", add_hover_effect_fn=None, add_hover_tooltip_fn=None, parent=None):
        """初始化标题栏
        
        Args:
            title_text: 窗口标题文本
            add_hover_effect_fn: 外部传入的悬停动画函数
            add_hover_tooltip_fn: 外部传入的悬停提示函数
            parent: 父组件
        """
        super().__init__(parent)
        self._add_hover_effect = add_hover_effect_fn
        self._add_hover_tooltip = add_hover_tooltip_fn
        self._default_title = title_text or "SED - Smart-edu-downloader"

        # 初始化图标管理器
        self.icon_manager = IconManager()

        self.setFixedHeight(50)
        self.setObjectName("titleBar")
        self.setAttribute(Qt.WA_StyledBackground, True)  # 启用样式表背景支持

        # 标题栏背景由 SettingsHandler 根据渐变开关统一下发；
        # 这里仅设置初始默认背景，避免启动瞬间透明。
        self._default_accent = load_primary_color()
        self._bar_background = None
        self._corner_radius = 12
        self._update_style_sheet()

        self._create_layout()
        self._create_title_label(self._default_title)
        self._create_control_buttons()
    
    def _update_style_sheet(self):
        """根据当前圆角半径与下发背景更新样式表。"""
        radius = self._corner_radius
        bg = self._bar_background if self._bar_background is not None else self._default_accent
        self.setStyleSheet(f"""
            QWidget#titleBar {{
                background: {bg};
                border-top-left-radius: {radius}px;
                border-top-right-radius: {radius}px;
            }}
        """)

    def set_bar_background(self, background: str):
        """设置标题栏背景（支持纯色或渐变 CSS）。

        Args:
            background: CSS background 值，如 rgba(...) 或 qlineargradient(...)。
        """
        self._bar_background = background
        self._update_style_sheet()

    def setCornerRadius(self, radius: int):
        """设置标题栏顶部圆角半径

        Args:
            radius: 圆角半径，最大化时通常设为 0
        """
        self._corner_radius = radius
        self._update_style_sheet()

    def set_title_text(self, text: str):
        """更新标题标签文本。

        Args:
            text: 标题文本；为空时使用创建时传入的默认标题。
        """
        if self._text_label is None:
            return
        self._text_label.setText(text or self._default_title)

    def set_title_font_styles(self, styles: list):
        """根据样式列表设置标题字体加粗/倾斜。

        Args:
            styles: 字体样式列表，可包含 "bold"、"italic"。
        """
        if self._text_label is None:
            return
        font = title_font()
        if "bold" in styles:
            font.setBold(True)
        if "italic" in styles:
            font.setItalic(True)
        self._text_label.setFont(font)

    def update_theme_colors(self, primary: str, background: str):
        """使用主题主色更新标题栏背景并刷新样式表。

        Args:
            primary: 主题主色。
            background: 主题背景色（当前标题栏不使用）。
        """
        self._default_accent = primary
        self._update_style_sheet()

    def _create_layout(self):
        """创建标题栏布局"""
        self.title_bar_layout = QHBoxLayout()
        self.title_bar_layout.setContentsMargins(20, 0, 10, 0)
        self.title_bar_layout.setSpacing(10)
        self.setLayout(self.title_bar_layout)
    
    def _create_title_label(self, title_text):
        """创建标题标签（包含 SVG 图标和文本）"""
        title_layout = QHBoxLayout()
        title_layout.setSpacing(8)
        title_layout.setContentsMargins(0, 0, 0, 0)
        
        # 加载标题 SVG 图标
        icon_pixmap = self.icon_manager.load_title_svg("title_books.svg", "#FFFFFF", size=(24, 24))
        if icon_pixmap:
            icon_label = QLabel()
            icon_label.setPixmap(icon_pixmap)
            icon_label.setFixedSize(24, 24)
            title_layout.addWidget(icon_label)
        
        # 添加文本
        self._text_label = QLabel(title_text)
        self._text_label.setFont(title_font())
        self._text_label.setStyleSheet("color: white; background: transparent;")
        title_layout.addWidget(self._text_label)

        self.title_label = QWidget()
        self.title_label.setLayout(title_layout)
        self.title_bar_layout.addWidget(self.title_label)
        
        # 添加弹性空间
        self.title_bar_layout.addStretch()
    
    def _create_control_buttons(self):
        """创建窗口控制按钮（最小化、最大化、关闭）"""
        # title_bar.py 在 gui/components/ -> 上3级 = 项目根目录
        app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        resources_dir = os.path.join(app_root, "resources", "images")
        s_icon_path = os.path.join(resources_dir, "s.png")
        b_icon_path = os.path.join(resources_dir, "b.png")
        c_icon_path = os.path.join(resources_dir, "c.png")
        
        # 最小化按钮
        self.min_btn = self._create_control_button()
        if self._add_hover_effect:
            self._add_hover_effect(self.min_btn)
        if self._add_hover_tooltip:
            self._add_hover_tooltip(self.min_btn, _("core.status_bar.minimize_tooltip"))
        self.min_btn.clicked.connect(self.minimize_requested.emit)
        self._add_button_icon(self.min_btn, s_icon_path)
        
        # 最大化按钮
        self.max_btn = self._create_control_button()
        if self._add_hover_effect:
            self._add_hover_effect(self.max_btn)
        if self._add_hover_tooltip:
            self._add_hover_tooltip(self.max_btn, _("core.status_bar.maximize_tooltip"))
        self.max_btn.clicked.connect(self.maximize_requested.emit)
        self._add_button_icon(self.max_btn, b_icon_path)
        
        # 关闭按钮
        self.close_btn = self._create_control_button(close_button=True)
        if self._add_hover_effect:
            self._add_hover_effect(self.close_btn)
        if self._add_hover_tooltip:
            self._add_hover_tooltip(self.close_btn, _("core.status_bar.close_tooltip"))
        self.close_btn.clicked.connect(self.close_requested.emit)
        self._add_button_icon(self.close_btn, c_icon_path)
        
        # 添加到布局
        self.title_bar_layout.addWidget(self.min_btn)
        self.title_bar_layout.addWidget(self.max_btn)
        self.title_bar_layout.addWidget(self.close_btn)
    
    def _create_control_button(self, close_button=False):
        """创建控制按钮
        
        Args:
            close_button: 是否为关闭按钮（关闭按钮有红色悬停效果）
        """
        btn = TitleBarButton()
        btn.setCursor(Qt.PointingHandCursor)
        
        if close_button:
            btn.setHoverBackground('#E81123')
            btn.setPressedBackground('#B20E1C')
        else:
            btn.setHoverBackground('rgba(255, 255, 255, 40)')
            btn.setPressedBackground('rgba(255, 255, 255, 60)')
        
        return btn
    
    def _add_button_icon(self, button, icon_path):
        """为按钮添加图标
        
        Args:
            button: 目标按钮
            icon_path: 图标路径
        """
        if os.path.exists(icon_path):
            button.setIcon(QIcon(icon_path))
            button.setIconSize(QSize(20, 20))
