# -*- coding: utf-8 -*-
"""设置标签页基类"""

from typing import Any, Dict

import sys
import io

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QFrame,
    QHBoxLayout, QLabel, QSlider,
)

# 静默导入 qfluentwidgets，避免其 Pro 提示输出到控制台
_old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    from qfluentwidgets import SettingCardGroup
finally:
    sys.stdout = _old_stdout

from gui.pages.settings.components.setting_group import SettingGroup
from gui.styles import load_primary_color
from gui.fonts import body_font


class BaseSettingTab(QWidget):
    """设置标签页基类

    职责：
    - 封装滚动容器创建、布局管理
    - 提供 ``_create_group()`` 便捷方法
    - 强制子类实现 ``_create_content()`` / ``collect_settings()`` / ``refresh_from()``

    子类只需实现：
        1. ``_create_content(parent_layout)`` —— 创建本页所有 UI 控件
        2. ``collect_settings(settings)`` —— 从控件收集值到字典
        3. ``refresh_from(settings)`` —— 从字典刷新控件值（静态方法或实例方法均可）

    使用示例：:

        class BasicSettingTab(BaseSettingTab):
            def _create_content(self, layout):
                group = self._create_group(_("settings.basic.donation_qr"))
                self.show_tips_switch = SwitchWithLabel(
                    _("settings.basic.show_donation_qr"), checked=True
                )
                group.add_widget(self.show_tips_switch)
                layout.addWidget(group)

            def collect_settings(self, settings):
                settings["show_tips_switch"] = self.show_tips_switch.isChecked()

            def refresh_from(self, settings):
                self.show_tips_switch.setChecked(settings.get("show_tips_switch", True))
    """

    def __init__(self, callbacks: dict = None, parent=None):
        self._callbacks = callbacks or {}
        super().__init__(parent)
        self._accent_color = load_primary_color()
        self._group_titles = []  # 保存对分组标题的引用，用于主题色更新
        self._accent_buttons = []  # 保存需要跟随主题色的按钮引用
        self._init_ui()

    # ── 公开属性 ──────────────────────────────────────────
    @property
    def accent_color(self) -> str:
        return self._accent_color

    def register_accent_button(self, button):
        """注册需要跟随主题色更新的按钮。"""
        self._accent_buttons.append(button)

    def set_accent_color(self, color: str):
        """更新本页所有分组标题及注册按钮的主题色"""
        self._accent_color = color
        for group in self._group_titles:
            group.update_accent_color(color)
        for button in self._accent_buttons:
            if button and hasattr(button, 'setAccentColor'):
                button.setAccentColor(color)

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新本页分组标题、按钮及开关控件。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        self.set_accent_color(primary)

        # 刷新所有 SwitchWithLabel 开关控件
        from gui.widgets.switch_button import SwitchWithLabel
        for switch in self.findChildren(SwitchWithLabel):
            switch.update_theme_colors(primary, background)

    # ── 子类接口 ──────────────────────────────────────────
    def _create_content(self, parent_layout: QVBoxLayout) -> None:
        """创建标签页内容，由子类实现"""
        raise NotImplementedError

    def collect_settings(self, settings: Dict[str, Any]) -> None:
        """从本页控件收集设置值到 settings 字典"""
        raise NotImplementedError

    def refresh_from(self, settings: Dict[str, Any]) -> None:
        """从 settings 字典刷新本页所有控件"""
        raise NotImplementedError

    # ── 初始化 ─────────────────────────────────────────────
    def _init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.viewport().setStyleSheet("background: transparent;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        container.setFont(body_font())
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(15, 15, 15, 15)
        container.setLayout(layout)

        self._create_content(layout)

        layout.addStretch()
        scroll.setWidget(container)

        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        self.setLayout(page_layout)

    # ── 便捷方法 ──────────────────────────────────────────
    def _create_group(self, title: str) -> SettingGroup:
        """创建设置分组框"""
        group = SettingGroup(title, self._accent_color)
        self._group_titles.append(group)
        return group

    def _create_card_group(self, title: str):
        """创建带 SettingCardGroup 的分组容器。

        Returns:
            (SettingGroup, SettingCardGroup): 外层卡片容器与内部卡片组。
        """
        group = self._create_group(title)
        card_group = SettingCardGroup("", group)
        card_group.titleLabel.hide()
        group.add_widget(card_group)
        return group, card_group

    def _create_slider(self, label_text: str, min_value: int, max_value: int):
        """创建带标签和当前值显示的滑动条。

        Args:
            label_text: 滑动条左侧标签文本。
            min_value: 最小值。
            max_value: 最大值。

        Returns:
            (QLabel, QSlider, QLabel) 三元组，分别为标签、滑动条、数值标签。
        """
        label = QLabel(label_text)
        label.setFont(body_font())

        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_value, max_value)
        slider.setFixedWidth(160)

        value_label = QLabel(str(min_value))
        value_label.setFont(body_font())
        value_label.setFixedWidth(30)
        value_label.setAlignment(Qt.AlignCenter)

        return label, slider, value_label

    def on_accent_color_changed(self, color: str):
        """外部调用：主题色改变时刷新所有分组标题颜色"""
        self.set_accent_color(color)