# -*- coding: utf-8 -*-
"""文本输入设置卡片。

继承 qfluentwidgets.SettingCard，右侧使用 qfluentwidgets.LineEdit，
用于需要用户输入文本的设置项，如下载目录、音效文件路径等。
"""

import sys
import io

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QWidget

# 静默导入 qfluentwidgets，避免其 Pro 提示输出到控制台
_old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    from qfluentwidgets import SettingCard, LineEdit
finally:
    sys.stdout = _old_stdout

from gui.fonts import body_font
from gui.widgets import CustomContextMenu


class LineEditCard(SettingCard):
    """带文本输入框的设置卡片。

    外观与 qfluentwidgets SettingCard 一致，内部输入框使用
    ``qfluentwidgets.LineEdit``，并统一应用项目字体与右键菜单。

    Args:
        icon: 卡片左侧图标，可使用 qfluentwidgets.FluentIcon。
        title: 卡片标题。
        content: 卡片副标题/说明，None 或空字符串时隐藏。
        parent: 父控件。
    """

    textChanged = pyqtSignal(str)

    def __init__(self, icon, title: str, content: str = None,
                 parent: QWidget = None):
        super().__init__(icon, title, content, parent)
        self._line_edit = LineEdit()
        self._line_edit.setMinimumWidth(200)
        self._line_edit.setFont(body_font())
        CustomContextMenu.setup_for_line_edit(self._line_edit, body_font())
        self.hBoxLayout.addWidget(self._line_edit, 1, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self._line_edit.textChanged.connect(self.textChanged.emit)

    def text(self) -> str:
        """返回当前输入文本。"""
        return self._line_edit.text()

    def setText(self, text: str):
        """设置输入文本（不触发信号）。"""
        self._line_edit.blockSignals(True)
        self._line_edit.setText(text)
        self._line_edit.blockSignals(False)

    def setPlaceholderText(self, text: str):
        """设置占位提示文本。"""
        self._line_edit.setPlaceholderText(text)

    def setEchoMode(self, mode):
        """设置回显模式（如密码框）。"""
        self._line_edit.setEchoMode(mode)

    def setReadOnly(self, read_only: bool):
        """设置只读状态。"""
        self._line_edit.setReadOnly(read_only)

    def line_edit(self) -> LineEdit:
        """返回内部输入框控件，便于外部进行特殊配置。"""
        return self._line_edit
