# -*- coding: utf-8 -*-
"""数值范围设置卡片。

继承 qfluentwidgets.SettingCard，右侧使用项目内建的 NoWheelSpinBox，
用于展示需要输入整数值的设置项，同时禁用滚轮避免误操作。
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

from gui.widgets import NoWheelSpinBox


class RangeCard(SettingCard):
    """带禁用滚轮数值框的设置卡片。

    外观与 qfluentwidgets SettingCard 一致，内部数值控件使用
    ``NoWheelSpinBox``，避免滚动页面时因滚轮事件导致数值误变化。

    Args:
        icon: 卡片左侧图标，可使用 qfluentwidgets.FluentIcon。
        title: 卡片标题。
        content: 卡片副标题/说明，None 或空字符串时隐藏。
        parent: 父控件。
    """

    valueChanged = pyqtSignal(int)

    def __init__(self, icon, title: str, content: str = None,
                 parent: QWidget = None):
        super().__init__(icon, title, content, parent)
        self._spin = NoWheelSpinBox()
        self._spin.setMinimumWidth(120)
        self._spin.setAlignment(Qt.AlignCenter)
        self.hBoxLayout.addWidget(self._spin, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)
        self._spin.valueChanged.connect(self.valueChanged.emit)

    def setRange(self, minimum: int, maximum: int):
        """设置数值范围。"""
        self._spin.setRange(minimum, maximum)

    def setValue(self, value: int):
        """设置当前数值（不触发信号）。"""
        self._spin.blockSignals(True)
        self._spin.setValue(value)
        self._spin.blockSignals(False)

    def value(self) -> int:
        """返回当前数值。"""
        return self._spin.value()

    def setSingleStep(self, step: int):
        """设置步进值。"""
        self._spin.setSingleStep(step)

    def setSpecialValueText(self, text: str):
        """设置特殊值（通常为最小值）的显示文本。"""
        self._spin.setSpecialValueText(text)

    def setSuffix(self, suffix: str):
        """设置数值后缀。"""
        self._spin.setSuffix(suffix)

    def spin_box(self) -> NoWheelSpinBox:
        """返回内部数值框控件，便于外部进行特殊配置。"""
        return self._spin
