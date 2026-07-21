# -*- coding: utf-8 -*-
"""欢迎向导页面基类。

提供统一的页面布局、标题/副标题样式、底部导航容器以及主题色获取接口，
供各引导页面复用。页面内容整体在窗口中垂直居中，导航按钮紧跟内容下方。
"""

from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from gui.fonts import title_font, subtitle_font
from gui.styles import load_primary_color


class BaseWelcomePage(QWidget):
    """欢迎向导页面基类。

    子类通常重写 ``_create_content()`` 向中间内容区添加控件，
    并通过 ``set_nav_buttons()`` 设置底部导航按钮。

    属性:
        accent_color: 当前主题色。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化页面基类。

        Args:
            parent: 父组件。
        """
        super().__init__(parent)
        self._accent_color = load_primary_color()
        self._init_ui()

    # ----- 公共 API -----

    def set_accent_color(self, color: str) -> None:
        """更新页面主题色。

        Args:
            color: 十六进制颜色字符串。
        """
        self._accent_color = color
        self._update_title_color()

    # ----- 子类可重写接口 -----

    def _create_title(self) -> QLabel:
        """创建页面标题标签，子类可重写文本。"""
        title = QLabel("")
        title.setFont(title_font())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #212121;")
        return title

    def _create_subtitle(self) -> QLabel:
        """创建页面副标题标签，子类可重写文本。"""
        subtitle = QLabel("")
        subtitle.setFont(subtitle_font())
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666666;")
        return subtitle

    # ----- UI 创建 -----

    def _init_ui(self) -> None:
        """初始化页面布局。

        标题、副标题、内容区与导航按钮作为一个整体在窗口中垂直居中，
        导航按钮紧贴内容区下方，避免被压到窗口底部。
        """
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(40, 30, 40, 20)
        layout.setAlignment(Qt.AlignCenter)
        self.setLayout(layout)

        self.title_label = self._create_title()
        self.subtitle_label = self._create_subtitle()
        if self.title_label.text() == "" and self.title_label.isHidden():
            self.title_label.setFixedHeight(0)
        if self.subtitle_label.text() == "" and self.subtitle_label.isHidden():
            self.subtitle_label.setFixedHeight(0)

        self.content_layout = QVBoxLayout()
        self.content_layout.setSpacing(12)
        self.content_layout.setAlignment(Qt.AlignCenter)

        self.nav_layout = QHBoxLayout()
        self.nav_layout.setSpacing(16)
        self.nav_layout.setAlignment(Qt.AlignCenter)

        self.bottom_layout = QHBoxLayout()
        self.bottom_layout.setSpacing(0)
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)
        self.bottom_layout.setAlignment(Qt.AlignRight | Qt.AlignBottom)

        # 整体垂直居中：上下 stretch 相等，中间依次排列标题/副标题/内容/按钮
        layout.addStretch(1)
        layout.addWidget(self.title_label, 0, Qt.AlignCenter)
        layout.addWidget(self.subtitle_label, 0, Qt.AlignCenter)
        layout.addLayout(self.content_layout, 0)
        layout.addSpacing(24)
        layout.addLayout(self.nav_layout)
        layout.addStretch(1)
        layout.addLayout(self.bottom_layout)

    def _update_title_color(self) -> None:
        """更新标题颜色（当前保持深灰，子类可按需调用）。"""
        if self.title_label:
            self.title_label.setStyleSheet("color: #212121;")

    def add_content(self, widget: QWidget, alignment: Qt.Alignment = Qt.AlignCenter, stretch: int = 0) -> None:
        """将控件添加到内容区。

        内容区本身已在主布局中居中，此处不再额外添加 stretch，
        避免子页面内容被不自然地推挤。

        Args:
            widget: 要添加的控件。
            alignment: 对齐方式。
            stretch: 控件的伸展因子。
        """
        self.content_layout.addWidget(widget, stretch, alignment)

    def add_centered_content(self, widget: QWidget, alignment: Qt.Alignment = Qt.AlignCenter, stretch: int = 0) -> None:
        """兼容旧接口：将控件添加到内容区。

        现在与 ``add_content`` 行为一致，均不添加额外 stretch。
        """
        self.add_content(widget, alignment, stretch)

    def set_nav_buttons(self, *buttons: QWidget) -> None:
        """设置底部导航按钮。

        先清空现有按钮，再将传入按钮居中排列。

        Args:
            buttons: 导航按钮组件序列。
        """
        while self.nav_layout.count():
            item = self.nav_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        for button in buttons:
            self.nav_layout.addWidget(button)

    def set_bottom_banner(self, widget: QWidget) -> None:
        """设置页面右下角横幅控件。

        横幅会固定在页面底部右侧，不与中间内容区重叠。

        Args:
            widget: 要显示的横幅控件。
        """
        while self.bottom_layout.count():
            item = self.bottom_layout.takeAt(0)
            existing = item.widget()
            if existing:
                existing.setParent(None)
        if widget:
            self.bottom_layout.addWidget(widget)
