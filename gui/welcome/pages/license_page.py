# -*- coding: utf-8 -*-
"""许可条款页面。

包含隐私政策同意复选框以及进入下一步的导航。
"""

import os
from typing import Optional

from PyQt5.QtCore import Qt
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

    通过 MaterialCheckBox 要求用户同意隐私政策。

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

        # 复选框与隐私政策链接
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
        self.agree_label.setText(
            _("welcome_onboarding.license.agree_privacy_policy").replace(
                _("welcome_onboarding.license.privacy_policy"),
                f'<a href="#privacy" style="color: {self._accent_color}; text-decoration: none;">'
                f'{_("welcome_onboarding.license.privacy_policy")}</a>'
            )
        )
        self.agree_label.setStyleSheet("color: #333333;")
        self.agree_label.setCursor(Qt.PointingHandCursor)
        self.agree_label.linkActivated.connect(self._on_privacy_link_clicked)
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

    def _on_agreement_changed(self) -> None:
        """勾选状态变化时更新下一步按钮可用性。"""
        self._update_next_btn_state()

    def _update_next_btn_state(self) -> None:
        """根据隐私政策同意状态更新下一步按钮。"""
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
            self.agree_label.setText(
                _("welcome_onboarding.license.agree_privacy_policy").replace(
                    _("welcome_onboarding.license.privacy_policy"),
                    f'<a href="#privacy" style="color: {color}; text-decoration: none;'
                    f'">{_("welcome_onboarding.license.privacy_policy")}</a>'
                )
            )
        if hasattr(self, "next_btn") and self.next_btn:
            self.next_btn.setAccentColor(color)
            if self.next_btn.isEnabled():
                self.next_btn.setButtonStyle(CircleNavButton.STYLE_ACCENT)

    def reload_texts(self) -> None:
        """重新加载页面翻译文本。"""
        self.title_label.setText(_("welcome_onboarding.license.title"))
        self.subtitle_label.setText(_("welcome_onboarding.license.subtitle"))
        if hasattr(self, "agree_label") and self.agree_label:
            self.agree_label.setText(
                _("welcome_onboarding.license.agree_privacy_policy").replace(
                    _("welcome_onboarding.license.privacy_policy"),
                    f'<a href="#privacy" style="color: {self._accent_color}; text-decoration: none;'
                    f'">{_("welcome_onboarding.license.privacy_policy")}</a>'
                )
            )

    def _on_privacy_link_clicked(self, link: str = "") -> None:
        """点击隐私政策链接时打开隐私政策对话框。"""
        from gui.welcome.pages.privacy_policy_dialog import PrivacyPolicyDialog
        dialog = PrivacyPolicyDialog(self._accent_color, self)
        dialog.exec()
