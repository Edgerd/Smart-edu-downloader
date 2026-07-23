# -*- coding: utf-8 -*-
"""按钮操作设置卡片。

继承 qfluentwidgets.SettingCard，右侧使用项目统一的 MaterialButton，
用于需要触发一个操作的设置项，如浏览目录、打开网页、复制代码等。
"""

import sys
import io

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget

# 静默导入 qfluentwidgets，避免其 Pro 提示输出到控制台
_old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    from qfluentwidgets import SettingCard
finally:
    sys.stdout = _old_stdout

from gui.fonts import body_font
from gui.widgets.material_button import MaterialButton


class PushCard(SettingCard):
    """带操作按钮的设置卡片。

    外观与 qfluentwidgets SettingCard 一致，右侧放置 MaterialButton，
    点击后发射 ``clicked`` 信号，由外部处理具体操作。

    Args:
        icon: 卡片左侧图标，可使用 qfluentwidgets.FluentIcon。
        title: 卡片标题。
        content: 卡片副标题/说明，None 或空字符串时隐藏。
        button_text: 按钮显示文本。
        parent: 父控件。
    """

    clicked = pyqtSignal()

    def __init__(self, icon, title: str, content: str = None,
                 button_text: str = "", parent: QWidget = None):
        super().__init__(icon, title, content, parent)
        self._button = MaterialButton(button_text)
        self._button.setFont(body_font())
        self._button.setFixedHeight(32)
        self._button.clicked.connect(self.clicked.emit)
        self.hBoxLayout.addWidget(self._button, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

    def setButtonText(self, text: str):
        """设置按钮文本。"""
        self._button.setText(text)

    def setAccentColor(self, color: str):
        """设置按钮主题色。"""
        self._button.setAccentColor(color)

    def button(self) -> MaterialButton:
        """返回内部按钮控件，便于外部进行特殊配置。"""
        return self._button
