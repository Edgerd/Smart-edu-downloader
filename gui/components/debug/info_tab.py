# -*- coding: utf-8 -*-
"""
信息标签页组件

以信息卡片形式展示系统信息、应用信息和依赖信息。
"""

import sys
import io

from core.i18n import _
import os
import platform
import sys as system_module
from datetime import datetime

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QSizePolicy
from PyQt5.QtCore import Qt
from PyQt5 import QtCore

# 静默导入 qfluentwidgets，避免其 Pro 提示输出到控制台
_old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    from qfluentwidgets import SettingCard, SettingCardGroup, FluentIcon as FIF
finally:
    sys.stdout = _old_stdout

from gui.fonts import body_font
from gui.styles import load_primary_color, load_background_color
from gui.pages.settings.components.setting_group import SettingGroup


class InfoItemCard(SettingCard):
    """单条信息展示卡片。

    左侧显示信息名称，右侧显示对应的值，支持值文本自动换行，
    并根据内容自适应卡片高度，避免长文本被截断。
    """

    def __init__(self, icon, title: str, value: str, parent: QWidget = None):
        super().__init__(icon, title, "", parent)
        self._value_label = QLabel(str(value))
        self._value_label.setFont(body_font())
        self._value_label.setWordWrap(True)
        self._value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self._value_label.setMinimumHeight(20)
        self.hBoxLayout.addWidget(
            self._value_label, 0, Qt.AlignRight | Qt.AlignVCenter
        )
        self.hBoxLayout.addSpacing(16)

        # 允许卡片高度随内容扩展
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.setMinimumHeight(64)
        self._update_height()

    def set_value(self, value: str):
        """更新卡片右侧显示的值，并重新计算卡片高度。"""
        self._value_label.setText(str(value))
        self._update_height()

    def _update_height(self):
        """根据值标签内容计算并设置卡片最小高度。"""
        self._value_label.adjustSize()
        value_height = self._value_label.height()
        # 固定标签高度为实际内容高度，避免布局分配额外空间导致垂直居中偏移
        self._value_label.setFixedHeight(max(20, value_height))
        # 保留标题区域与上下边距空间
        self.setMinimumHeight(max(64, value_height + 32))
        self.updateGeometry()

    def resizeEvent(self, event):
        """尺寸变化时重新调整高度，确保换行文本完整显示。"""
        super().resizeEvent(event)
        self._update_height()


class InfoTab(QWidget):
    """信息标签页

    以信息卡片形式展示系统信息、应用信息和依赖信息。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._accent_color = load_primary_color()
        self._background_color = load_background_color()
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 使用滚动区域承载信息分组，避免内容过多时显示不全
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(15, 15, 15, 15)
        scroll_layout.setSpacing(12)

        self.system_group, self.system_cards = self._build_info_group(
            _('debug.info.system_info'),
            self._get_system_info_items(),
            FIF.INFO,
        )
        self.app_group, self.app_cards = self._build_info_group(
            _('debug.info.app_info'),
            self._get_app_info_items(),
            FIF.INFO,
        )
        self.dependency_group, self.dependency_cards = self._build_info_group(
            _('debug.info.dependencies'),
            self._get_dependency_items(),
            FIF.LIBRARY,
        )

        scroll_layout.addWidget(self.system_group)
        scroll_layout.addWidget(self.app_group)
        scroll_layout.addWidget(self.dependency_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

    def _build_info_group(self, title: str, items: list, icon):
        """创建一个信息分组，并为每个信息项添加卡片。

        Args:
            title: 分组标题。
            items: (标签, 值, 图标) 元组列表；图标为 None 时使用传入的默认 icon。
            icon: 默认图标。

        Returns:
            (SettingGroup, list): 分组容器与卡片列表。
        """
        group = SettingGroup(title, self._accent_color, self)

        sys.stdout = io.StringIO()
        try:
            card_group = SettingCardGroup("", group)
        finally:
            sys.stdout = _old_stdout
        card_group.titleLabel.hide()
        group.add_widget(card_group)

        cards = []
        for label, value, item_icon in items:
            card = InfoItemCard(item_icon or icon, label, value)
            card_group.addSettingCard(card)
            cards.append((label, card))

        return group, cards

    def _get_system_info_items(self):
        """获取系统信息项列表。"""
        return [
            (_('gui.components.debug.info_tab.auto_002'), system_module.version.split()[0], FIF.COMMAND_PROMPT),
            (_('gui.components.debug.info_tab.auto_001'), QtCore.QT_VERSION_STR, FIF.APPLICATION),
            (_('gui.components.debug.info_tab.auto_003'), QtCore.QT_VERSION_STR, FIF.FONT),
            (_('gui.components.debug.info_tab.auto_008'), f'{platform.system()} {platform.release()}', FIF.INFO),
            (_('gui.components.debug.info_tab.auto_004'), platform.processor() or _('common.unknown'), FIF.INFO),
            (_('gui.components.debug.info_tab.auto_007'), datetime.now().strftime('%Y-%m-%d %H:%M:%S'), FIF.DATE_TIME),
        ]

    def _get_app_info_items(self):
        """获取应用信息项列表。"""
        from core.infrastructure.version import VERSION
        return [
            (_('gui.components.debug.info_tab.auto_009'), VERSION, FIF.TAG),
            (_('gui.components.debug.info_tab.auto_005'), os.getcwd(), FIF.FOLDER),
        ]

    def _get_dependency_items(self):
        """获取依赖信息项列表。

        依赖状态在刷新时动态检测，初始统一显示为加载中。
        """
        dependencies = [
            ('requests', 'requests'),
            ('psutil', 'psutil'),
            ('PyQt5', 'PyQt5'),
        ]
        items = []
        for name, module in dependencies:
            value = self._detect_dependency_value(module)
            items.append((name, value, FIF.LIBRARY))
        return items

    @staticmethod
    def _detect_dependency_value(module: str) -> str:
        """检测依赖模块版本或安装状态。"""
        try:
            mod = __import__(module)
            return getattr(mod, '__version__', _('gui.components.debug.info_tab.auto_006'))
        except ImportError:
            return _('debug.info.not_installed')

    def refresh_dependencies(self):
        """刷新依赖信息卡片显示。"""
        for label, card in self.dependency_cards:
            module_map = {'requests': 'requests', 'psutil': 'psutil', 'PyQt5': 'PyQt5'}
            module = module_map.get(label)
            if module:
                card.set_value(self._detect_dependency_value(module))

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新信息标签页视觉元素。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        self._accent_color = primary
        self._background_color = background
        self.setStyleSheet("background: transparent;")
        for group in (self.system_group, self.app_group, self.dependency_group):
            if group is not None and hasattr(group, 'update_accent_color'):
                group.update_accent_color(primary)
