# -*- coding: utf-8 -*-
"""开关按钮与主题色演示。

展示项目自定义 SwitchButton 在不同主题色下的开关效果，
支持 iOS 与 Fluent 两种风格切换，便于验证主题热重载。
"""

import sys
import io

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt

# 静默导入，避免 Pro 提示输出到控制台
_old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    import qfluentwidgets
finally:
    sys.stdout = _old_stdout

from gui.fonts import init_fonts, body_font, bold_font
from gui.styles import load_primary_color
from gui.widgets.switch_button import SwitchWithLabel


class DemoWindow(QWidget):
    """开关按钮主题演示窗口"""

    def __init__(self):
        super().__init__()
        self._accent_color = load_primary_color()
        self._init_ui()

    def _init_ui(self):
        """初始化界面"""
        self.setWindowTitle("开关按钮主题演示")
        self.resize(500, 300)
        self.setFont(body_font())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("SwitchButton 主题演示")
        title.setFont(bold_font())
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        desc = QLabel(f"当前主题色: {self._accent_color}")
        desc.setFont(body_font())
        desc.setAlignment(Qt.AlignCenter)
        layout.addWidget(desc)

        row = QHBoxLayout()
        row.setSpacing(30)

        ios_switch = SwitchWithLabel("iOS 风格", checked=True)
        ios_switch.setFont(body_font())
        row.addWidget(ios_switch)

        fluent_switch = SwitchWithLabel("Fluent 风格", style="fluent")
        fluent_switch.setFont(body_font())
        row.addWidget(fluent_switch)

        row.addStretch()
        layout.addLayout(row)

        layout.addStretch()


def run_demo():
    """运行开关按钮主题演示"""
    app = QApplication(sys.argv)
    init_fonts()
    app.setFont(body_font())

    window = DemoWindow()
    window.show()
    sys.exit(app.exec())
