# -*- coding: utf-8 -*-
"""统一页面头部组件"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel

from gui.fonts import title_font, body_font, get_harmonyos_family


class PageHeader:
    """统一的页面头部组件"""

    @staticmethod
    def create_header(parent_layout, icon_manager, accent_color, icon_name, title_text, subtitle_text, return_labels=False):
        """创建页面头部

        Args:
            title_text: 标题文本
            subtitle_text: 副标题文本
            return_labels: 是否返回 (title_label, subtitle_label) 元组，默认 False

        Returns:
            如果 return_labels=True，返回 (header_widget, title_label, subtitle_label) 元组
            否则返回 header_widget
        """
        header_widget = QWidget()
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 5)
        header_layout.setSpacing(2)
        header_widget.setLayout(header_layout)

        title_row_layout = QHBoxLayout()
        title_row_layout.setSpacing(8)
        title_row_layout.setContentsMargins(0, 0, 0, 0)

        icon_label = QLabel()
        icon_label.setObjectName("headerIcon")
        icon_pixmap = icon_manager.load_title_svg(icon_name, accent_color, size=(28, 28))
        if icon_pixmap:
            icon_label.setPixmap(icon_pixmap)
            icon_label.setFixedSize(28, 28)
            title_row_layout.addWidget(icon_label)

        title = QLabel(title_text)
        title.setObjectName("headerTitle")
        title.setFont(title_font())
        title.setStyleSheet(f"color: {accent_color}; font-family: '{get_harmonyos_family()}'; background: transparent;")
        title_row_layout.addWidget(title)
        title_row_layout.addStretch()

        header_layout.addLayout(title_row_layout)

        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("headerSubtitle")
        subtitle.setFont(body_font())
        subtitle.setStyleSheet(f"color: #666; font-family: '{get_harmonyos_family()}'; background: transparent;")

        header_layout.addWidget(subtitle)
        parent_layout.addWidget(header_widget)

        if return_labels:
            return header_widget, title, subtitle
        return header_widget

    @staticmethod
    def update_header(header_widget, icon_manager, accent_color, icon_name, title_text=None, subtitle_text=None):
        """刷新页面头部主题色

        Args:
            header_widget: create_header 返回的头部控件
            icon_manager: 图标管理器
            accent_color: 新的主题色
            icon_name: 标题图标文件名
            title_text: 新的标题文本（为 None 时保持不变）
            subtitle_text: 新的副标题文本（为 None 时保持不变）
        """
        if header_widget is None:
            return

        labels = header_widget.findChildren(QLabel)
        title = None
        subtitle = None
        icon_label = None
        for label in labels:
            if label.objectName() == "headerTitle":
                title = label
            elif label.objectName() == "headerSubtitle":
                subtitle = label
            elif label.objectName() == "headerIcon":
                icon_label = label

        if title is None:
            return

        icon_pixmap = icon_manager.load_title_svg(icon_name, accent_color, size=(28, 28))
        if icon_label is not None and icon_pixmap:
            icon_label.setPixmap(icon_pixmap)

        title.setStyleSheet(f"color: {accent_color}; font-family: '{get_harmonyos_family()}'; background: transparent;")
        if title_text is not None:
            title.setText(title_text)
        if subtitle is not None and subtitle_text is not None:
            subtitle.setText(subtitle_text)
