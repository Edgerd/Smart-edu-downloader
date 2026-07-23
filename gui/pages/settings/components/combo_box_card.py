# -*- coding: utf-8 -*-
"""下拉选项设置卡片。

继承 qfluentwidgets.SettingCard，右侧使用项目内建的 NoWheelComboBox，
在保持 Fluent 卡片外观的同时禁用滚轮切换，避免鼠标悬停时误操作。
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

from gui.widgets import NoWheelComboBox


class ComboBoxCard(SettingCard):
    """带禁用滚轮下拉框的设置卡片。

    外观与 qfluentwidgets SettingCard 一致，内部下拉控件使用
    ``NoWheelComboBox``，避免在滚动设置页时因滚轮事件导致选项误切换。

    Args:
        icon: 卡片左侧图标，可使用 qfluentwidgets.FluentIcon。
        title: 卡片标题。
        content: 卡片副标题/说明，None 或空字符串时隐藏。
        parent: 父控件。
    """

    currentIndexChanged = pyqtSignal(int)

    def __init__(self, icon, title: str, content: str = None,
                 parent: QWidget = None):
        super().__init__(icon, title, content, parent)
        self._combo = NoWheelComboBox()
        self._combo.setMinimumWidth(140)
        self.hBoxLayout.addWidget(self._combo, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self._combo.currentIndexChanged.connect(self.currentIndexChanged.emit)

    def addItem(self, text: str, user_data=None, icon=None):
        """向下拉框添加一个选项。

        Args:
            text: 选项显示文本。
            user_data: 选项关联数据，默认 None。
            icon: 选项图标，默认 None。qfluentwidgets 的 addItem 签名为
                ``addItem(text, icon=None, userData=None)``，因此必须通过
                关键字参数传入 user_data，避免被识别为图标。
        """
        self._combo.addItem(text, icon=icon, userData=user_data)

    def addItems(self, texts: list):
        """向下拉框批量添加文本选项。"""
        self._combo.addItems(texts)

    def currentIndex(self) -> int:
        """返回当前选中索引。"""
        return self._combo.currentIndex()

    def setCurrentIndex(self, index: int):
        """设置当前选中索引（不触发信号）。

        当传入的索引无效且下拉框存在选项时，默认选中第一项，
        避免旧配置中保存了异常值（如 ``None``）导致保存时再次写入空值。
        """
        if index < 0 and self._combo.count() > 0:
            index = 0
        self._combo.blockSignals(True)
        self._combo.setCurrentIndex(index)
        self._combo.blockSignals(False)

    def currentText(self) -> str:
        """返回当前选中文本。"""
        return self._combo.currentText()

    def setCurrentText(self, text: str):
        """按文本设置当前选项。"""
        self._combo.blockSignals(True)
        self._combo.setCurrentText(text)
        self._combo.blockSignals(False)

    def currentData(self, role=Qt.UserRole):
        """返回当前选项关联数据。

        注意：qfluentwidgets.ComboBox 的 currentData 不接受 role 参数，
        内部默认使用 Qt.UserRole，因此这里忽略 role 直接返回数据。
        """
        return self._combo.currentData()

    def findData(self, data) -> int:
        """查找指定数据对应的索引。"""
        return self._combo.findData(data)

    def findText(self, text: str) -> int:
        """查找指定文本对应的索引。"""
        return self._combo.findText(text)

    def setMinimumWidth(self, width: int):
        """设置下拉框最小宽度。"""
        self._combo.setMinimumWidth(width)

    def combo_box(self) -> NoWheelComboBox:
        """返回内部下拉框控件，便于外部进行特殊配置。"""
        return self._combo
