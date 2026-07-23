# -*- coding: utf-8 -*-
"""
调试面板导航栏组件

提供顶部图标导航栏，用于切换不同的调试页面。
"""

import os
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import pyqtSignal, Qt, QSize
from PyQt5.QtGui import QIcon

from gui.widgets.material_button import MaterialButton
from gui.fonts import body_font, small_font
from gui.styles import load_primary_color
from gui.utils.color_utils import lighten
from core.i18n import _


class NavigationBar(QWidget):
    """调试面板导航栏
    
    提供图标导航按钮，支持切换不同的调试页面。
    """
    
    # 页面切换信号
    page_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 当前选中的页面索引
        self._current_page = 0
        
        # 导航按钮列表
        self._buttons = []
        
        # 页面配置：(图标文件, 标签文字)
        self._nav_items = [
            ("basic.svg", _("debug.panel.log_tab")),
            ("advanced.svg", _("debug.panel.console_tab")),
            ("privacy.svg", _("debug.panel.info_tab")),
            ("download.svg", _("debug.panel.tools_tab")),
            ("appearance.svg", _("debug.lab.title")),
        ]
        
        self._init_ui()
        self._update_button_states()
    
    def _init_ui(self):
        """初始化UI"""
        # 设置导航栏背景透明，与下方内容区颜色保持一致
        self.setStyleSheet("background-color: transparent;")
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)
        
        # 按钮容器
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        
        # 创建导航按钮
        for icon_file, label_text in self._nav_items:
            btn_widget = self._create_nav_button(icon_file, label_text)
            button_layout.addWidget(btn_widget)
        
        button_layout.addStretch()
        main_layout.addLayout(button_layout)
        
        # 分隔线
        separator = QWidget()
        separator.setFixedHeight(1)
        separator.setStyleSheet("background-color: #E0E0E0;")
        main_layout.addWidget(separator)
    
    def _create_nav_button(self, icon_file: str, label_text: str) -> QWidget:
        """创建导航按钮组件
        
        Args:
            icon_file: 图标文件名
            label_text: 按钮标签文字
            
        Returns:
            包含图标和文字的容器组件
        """
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(4)
        
        # 图标按钮
        icon_path = os.path.join("resources", "images", "setting", icon_file)
        btn = MaterialButton("", variant=MaterialButton.VARIANT_TEXT)
        btn.setIcon(QIcon(icon_path))
        btn.setIconSize(QSize(24, 24))
        btn.setFixedSize(60, 40)
        btn.setToolTip(label_text)
        btn.setCursor(Qt.PointingHandCursor)
        
        # 保存按钮引用
        self._buttons.append(btn)
        btn_index = len(self._buttons) - 1
        
        # 连接点击信号
        btn.clicked.connect(lambda checked, idx=btn_index: self._on_button_clicked(idx))
        
        container_layout.addWidget(btn, alignment=Qt.AlignCenter)
        
        # 标签文字
        label = QLabel(label_text)
        label.setObjectName(f"nav_label_{btn_index}")
        label.setFont(small_font())
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("color: #666666; background-color: transparent;")
        
        container_layout.addWidget(label, alignment=Qt.AlignCenter)
        
        return container
    
    def set_labels_visible(self, visible: bool):
        """设置图标标签文字是否可见
        
        Args:
            visible: 是否显示标签文字
        """
        labels = self.findChildren(QLabel)
        for label in labels:
            if label.objectName().startswith("nav_label_"):
                label.setVisible(visible)
    
    def _on_button_clicked(self, index: int):
        """按钮点击处理
        
        Args:
            index: 按钮索引
        """
        if index != self._current_page:
            self._current_page = index
            self._update_button_states()
            self.page_changed.emit(index)
    
    def _update_button_states(self):
        """更新按钮状态"""
        accent_color = load_primary_color()
        active_bg = lighten(accent_color, 88)
        active_hover_bg = lighten(accent_color, 80)
        for i, btn in enumerate(self._buttons):
            if i == self._current_page:
                # 选中状态
                btn.setAccentColor(accent_color)
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {active_bg};
                        border-radius: 8px;
                    }}
                    QPushButton:hover {{
                        background-color: {active_hover_bg};
                    }}
                """)
            else:
                # 未选中状态
                btn.setAccentColor("#6C757D")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        border-radius: 8px;
                    }
                    QPushButton:hover {
                        background-color: #F5F5F5;
                    }
                """)
    
    def set_current_page(self, index: int):
        """设置当前页面
        
        Args:
            index: 页面索引
        """
        if 0 <= index < len(self._buttons) and index != self._current_page:
            self._current_page = index
            self._update_button_states()
