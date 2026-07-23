# -*- coding: utf-8 -*-
"""许可条款页面。

包含用户协议同意复选框以及进入下一步的导航。
"""

import os
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QMouseEvent
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)

from core.i18n import _
from gui.fonts import body_font, title_font, subtitle_font
from gui.components.material_checkbox import MaterialCheckBox
from gui.components.circle_nav_button import CircleNavButton
from gui.welcome.pages.base_page import BaseWelcomePage


class LicensePage(BaseWelcomePage):
    """许可条款页。

    通过 MaterialCheckBox 要求用户同意用户协议。

    属性:
        agreed: 用户是否已勾选同意框。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化许可条款页。"""
        super().__init__(parent)
        self._create_content()

    def _create_title(self) -> QLabel:
        """页面标题。"""
        title = QLabel(_("welcome_onboarding.license.title"))
        title.setFont(title_font())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #212121;")
        return title

    def _create_subtitle(self) -> QLabel:
        """页面副标题。"""
        subtitle = QLabel(_("welcome_onboarding.license.subtitle"))
        subtitle.setFont(subtitle_font())
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #666666;")
        return subtitle

    def _create_content(self) -> None:
        """创建许可条款页内容。"""
        self.title_label.setText(_("welcome_onboarding.license.title"))
        self.subtitle_label.setText(_("welcome_onboarding.license.subtitle"))

        # 复选框与用户协议链接
        checkbox_row = QHBoxLayout()
        checkbox_row.setSpacing(8)
        checkbox_row.setAlignment(Qt.AlignCenter)

        self.agree_checkbox = MaterialCheckBox()
        self.agree_checkbox.setFixedSize(24, 24)
        self.agree_checkbox.setAccentColor(self._accent_color)
        self.agree_checkbox.clicked.connect(self._on_agreement_changed)
        checkbox_row.addWidget(self.agree_checkbox)

        self.agree_label = QLabel()
        self.agree_label.setFont(body_font())
        self.agree_label.setTextFormat(Qt.RichText)
        self.agree_label.setText(self._build_agreement_text(self._accent_color))
        self.agree_label.setStyleSheet("color: #333333;")
        self.agree_label.setCursor(Qt.PointingHandCursor)
        self.agree_label.setToolTip(_("welcome_onboarding.license.user_agreement"))
        self.agree_label.mousePressEvent = self._on_agreement_label_clicked
        checkbox_row.addWidget(self.agree_label)

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.addLayout(checkbox_row)
        self.content_layout.addWidget(content_widget, 0, Qt.AlignCenter)

        # 下一步按钮
        self.next_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_r.svg"),
            button_style=CircleNavButton.STYLE_LIGHT,
            tooltip=_("welcome_onboarding.license.next_tip"),
            parent=self,
        )
        self.next_btn.setEnabled(False)
        self.next_btn.setAccentColor(self._accent_color)
        self.set_nav_buttons(self.next_btn)

    def _build_agreement_text(self, color: str) -> str:
        """构建带超链接的用户协议同意文本。

        Args:
            color: 链接颜色十六进制字符串。

        Returns:
            str: 可供 QLabel 以富文本渲染的 HTML 字符串。
        """
        agreement_key = "welcome_onboarding.license.agree_user_agreement"
        link_key = "welcome_onboarding.license.user_agreement"
        agreement_text = _(agreement_key)
        link_text = _(link_key)
        # 防止翻译缺失时占位符裸露，使用中文兜底
        if agreement_text == agreement_key:
            agreement_text = "我已阅读并同意《{user_agreement}》"
        display_text = link_text if link_text != link_key else "用户协议"
        link_html = (
            f'<a href="#user_agreement" style="color: {color}; '
            f'text-decoration: underline; font-weight: bold;">{display_text}</a>'
        )
        return agreement_text.replace("{user_agreement}", link_html)

    def _on_agreement_changed(self) -> None:
        """勾选状态变化时更新下一步按钮可用性。"""
        self._update_next_btn_state()

    def _update_next_btn_state(self) -> None:
        """根据用户协议同意状态更新下一步按钮。"""
        checked = self.agree_checkbox.isChecked()
        self.next_btn.setEnabled(checked)
        if checked:
            self.next_btn.setButtonStyle(CircleNavButton.STYLE_ACCENT)
            self.next_btn.setAccentColor(self._accent_color)
        else:
            self.next_btn.setButtonStyle(CircleNavButton.STYLE_LIGHT)

    def set_accent_color(self, color: str) -> None:
        """更新页面主题色。

        Args:
            color: 新的主题色十六进制字符串。
        """
        super().set_accent_color(color)
        if hasattr(self, "agree_checkbox") and self.agree_checkbox:
            self.agree_checkbox.setAccentColor(color)
        if hasattr(self, "agree_label") and self.agree_label:
            self.agree_label.setText(self._build_agreement_text(color))
            self.agree_label.setToolTip(_("welcome_onboarding.license.user_agreement"))
        if hasattr(self, "next_btn") and self.next_btn:
            self.next_btn.setAccentColor(color)
            if self.next_btn.isEnabled():
                self.next_btn.setButtonStyle(CircleNavButton.STYLE_ACCENT)

    def reload_texts(self) -> None:
        """重新加载页面翻译文本。"""
        self.title_label.setText(_("welcome_onboarding.license.title"))
        self.subtitle_label.setText(_("welcome_onboarding.license.subtitle"))
        if hasattr(self, "agree_label") and self.agree_label:
            self.agree_label.setText(self._build_agreement_text(self._accent_color))
            self.agree_label.setToolTip(_("welcome_onboarding.license.user_agreement"))

    def _on_agreement_label_clicked(self, event: QMouseEvent) -> None:
        """点击用户协议文本时打开用户协议对话框。

        Args:
            event: 鼠标按下事件。
        """
        if event.button() == Qt.LeftButton:
            self._open_user_agreement_dialog()
        event.accept()

    def _open_user_agreement_dialog(self) -> None:
        """打开用户协议对话框。"""
        from gui.welcome.pages.user_agreement_dialog import UserAgreementDialog
        dialog = UserAgreementDialog(self._accent_color, self)
        dialog.exec()
