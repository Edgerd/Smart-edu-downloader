# -*- coding: utf-8 -*-
"""设置组组件"""

import sys
import io

from PyQt5.QtWidgets import QVBoxLayout, QLabel
from gui.fonts import bold_font
from gui.styles import load_primary_color

# 静默导入 qfluentwidgets，避免其 Pro 提示输出到控制台
_old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    from qfluentwidgets import CardWidget
finally:
    sys.stdout = _old_stdout


class SettingGroup(CardWidget):
    """设置组组件——封装单个设置分组的UI创建和控件管理"""

    def __init__(self, title: str, accent_color: str = None, parent=None):
        super().__init__(parent)
        self._accent_color = accent_color or load_primary_color()
        self._title_label = None
        self._init_ui(title)

    # ── 公开属性 ──────────────────────────────────────────
    @property
    def title_label(self):
        """分组标题 QLabel，外部可通过它动态更新颜色"""
        return self._title_label

    # ── 初始化 ─────────────────────────────────────────────
    def _init_ui(self, title: str):
        self.setObjectName("settingGroup")

        layout = QVBoxLayout()
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(10)
        self.setLayout(layout)

        self._title_label = QLabel(title)
        self._title_label.setFont(bold_font())
        self._title_label.setStyleSheet(f"color: {self._accent_color};")
        layout.addWidget(self._title_label)

    # ── 便捷添加方法 ──────────────────────────────────────
    def add_widget(self, widget):
        """向组内添加控件"""
        self.layout().addWidget(widget)

    def add_layout(self, layout):
        """向组内添加布局"""
        self.layout().addLayout(layout)

    # ── 辅助 ──────────────────────────────────────────────
    def update_accent_color(self, color: str):
        """更新标题颜色（外部主题切换时调用）"""
        self._accent_color = color
        if self._title_label:
            self._title_label.setStyleSheet(f"color: {color};")