# -*- coding: utf-8 -*-
"""自定义开关设置卡片。

继承 qfluentwidgets.SettingCard，右侧使用项目内建的 SwitchWithLabel，
从而支持 iOS / Fluent 两种开关风格切换，并默认以 iOS 风格展示。
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

from gui.widgets.switch_button import SwitchWithLabel


class SwitchWithLabelSettingCard(SettingCard):
    """带程序内建开关的设置卡片。

    该卡片外观与 qfluentwidgets SettingCard 一致，但右侧开关使用
    ``SwitchWithLabel``，因此能够跟随全局 ``switch_button_style`` 设置
    在 iOS 风格与 Fluent 风格之间切换。

    Args:
        icon: 卡片左侧图标，可使用 qfluentwidgets.FluentIcon。
        title: 卡片标题。
        content: 卡片副标题/说明，None 或空字符串时隐藏。
        checked: 初始选中状态。
        parent: 父控件。
    """

    toggled = pyqtSignal(bool)

    def __init__(self, icon, title: str, content: str = None,
                 checked: bool = False, parent: QWidget = None):
        super().__init__(icon, title, content, parent)
        self._switch = SwitchWithLabel(text="", checked=checked)
        # 开关卡片不需要文本标签，仅使用开关本体
        self._switch.label.hide()

        self.hBoxLayout.addWidget(self._switch, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

        self._switch.toggled.connect(self.toggled.emit)

    def isChecked(self) -> bool:
        """返回开关当前状态。"""
        return self._switch.isChecked()

    def setChecked(self, checked: bool):
        """设置开关状态。"""
        self._switch.setChecked(checked)

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新内部开关颜色。

        Args:
            primary: 主题主色。
            background: 内容区背景色。
        """
        self._switch.update_theme_colors(primary, background)
