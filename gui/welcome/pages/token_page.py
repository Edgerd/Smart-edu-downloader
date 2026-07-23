# -*- coding: utf-8 -*-
"""Access Token 配置页面。

引导用户获取并填写智慧教育平台的 Access Token。
"""

import os
import webbrowser
from typing import Any, Dict, Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QGuiApplication
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFrame,
)

from core.i18n import _
from core.network.token_crypto import decrypt_token
from gui.fonts import body_font, small_font, title_font, subtitle_font
from gui.styles import load_primary_color
from gui.widgets.material_button import MaterialButton
from gui.components.circle_nav_button import CircleNavButton
from gui.welcome.pages.base_page import BaseWelcomePage


class TokenPage(BaseWelcomePage):
    """Access Token 配置页。

    收集用户输入的 Access Token，并提供云平台跳转与 JS 代码复制功能。

    属性:
        access_token: 当前输入框中的 Access Token 字符串。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化 Access Token 页。"""
        super().__init__(parent)
        self._create_content()

    def _create_title(self) -> QLabel:
        """页面标题，左对齐显示。"""
        title = QLabel(_("welcome_onboarding.access_token.title"))
        title.setFont(title_font())
        title.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        title.setStyleSheet("color: #212121;")
        return title

    def _create_subtitle(self) -> QLabel:
        """页面副标题，左对齐显示。"""
        subtitle = QLabel(_("welcome_onboarding.access_token.subtitle"))
        subtitle.setFont(subtitle_font())
        subtitle.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        subtitle.setStyleSheet("color: #666666;")
        return subtitle

    def _create_content(self) -> None:
        """创建 Access Token 页内容。"""
        self.title_label.setText(_("welcome_onboarding.access_token.title"))
        self.subtitle_label.setText(_("welcome_onboarding.access_token.subtitle"))

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 8px;
                border: none;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(16)
        card_layout.setContentsMargins(20, 20, 20, 20)

        # 输入框标签
        input_label = QLabel(_("welcome_onboarding.access_token.input_label"))
        input_label.setFont(body_font())
        input_label.setStyleSheet("color: #212121; font-weight: bold;")
        card_layout.addWidget(input_label)

        # Token 输入框
        self.token_input = QLineEdit()
        self.token_input.setFont(body_font())
        self.token_input.setPlaceholderText(_("settings.privacy.access_token_placeholder"))
        self.token_input.textChanged.connect(self._on_token_changed)
        self._refresh_input_style()
        card_layout.addWidget(self.token_input)

        # 提示信息
        self.tip_label = QLabel(_("welcome_onboarding.access_token.empty_tip"))
        self.tip_label.setFont(small_font())
        self.tip_label.setWordWrap(True)
        self.tip_label.setStyleSheet(f"color: {self._accent_color};")
        card_layout.addWidget(self.tip_label)

        # 操作按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        self.open_cloud_btn = MaterialButton(
            _("welcome_onboarding.access_token.open_cloud_platform")
        )
        self.open_cloud_btn.setFont(body_font())
        self.open_cloud_btn.setFixedHeight(32)
        self.open_cloud_btn.setAccentColor(self._accent_color)
        self.open_cloud_btn.clicked.connect(self._on_open_cloud_platform)
        btn_row.addWidget(self.open_cloud_btn)

        self.copy_code_btn = MaterialButton(
            _("welcome_onboarding.access_token.copy_code")
        )
        self.copy_code_btn.setFont(body_font())
        self.copy_code_btn.setFixedHeight(32)
        self.copy_code_btn.setVariant(MaterialButton.VARIANT_OUTLINED)
        self.copy_code_btn.setAccentColor(self._accent_color)
        self.copy_code_btn.clicked.connect(self._on_copy_code)
        btn_row.addWidget(self.copy_code_btn)
        btn_row.addStretch()

        card_layout.addLayout(btn_row)

        # 5 步教程
        self.tutorial_label = QLabel(self._build_tutorial_text())
        self.tutorial_label.setFont(small_font())
        self.tutorial_label.setWordWrap(True)
        self.tutorial_label.setStyleSheet("color: #555555; line-height: 1.6;")
        card_layout.addWidget(self.tutorial_label)

        self.add_centered_content(card, Qt.AlignCenter)

        # 导航按钮
        self.prev_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_l.svg"),
            button_style=CircleNavButton.STYLE_LIGHT,
            tooltip=_("welcome_onboarding.access_token.previous_tip"),
            parent=self,
        )
        self.next_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_r.svg"),
            button_style=CircleNavButton.STYLE_LIGHT,
            tooltip=_("welcome_onboarding.access_token.next_tip"),
            parent=self,
        )
        self.next_btn.setAccentColor(self._accent_color)
        self.next_btn.setEnabled(False)
        self.set_nav_buttons(self.prev_btn, self.next_btn)

    def _build_tutorial_text(self) -> str:
        """组装 5 步教程文本。"""
        steps = [
            _("welcome_onboarding.access_token.tutorial_step_1"),
            _("welcome_onboarding.access_token.tutorial_step_2"),
            _("welcome_onboarding.access_token.tutorial_step_3"),
            _("welcome_onboarding.access_token.tutorial_step_4"),
            _("welcome_onboarding.access_token.tutorial_step_5"),
        ]
        return "\n".join(steps)

    def _on_open_cloud_platform(self) -> None:
        """在默认浏览器打开国家中小学智慧教育平台。"""
        webbrowser.open("https://www.zxx.edu.cn/")

    def _on_copy_code(self) -> None:
        """复制 JS 代码片段到剪贴板并显示提示。"""
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(_("settings.privacy.token_js_code_snippet"))

        original_text = self.copy_code_btn.text()
        self.copy_code_btn.setText(_("welcome_onboarding.access_token.copy_success"))
        self.copy_code_btn.setEnabled(False)
        QTimer.singleShot(2000, lambda: self._restore_copy_button(original_text))

    def _restore_copy_button(self, text: str) -> None:
        """恢复复制按钮的原始文本和状态。"""
        if self.copy_code_btn:
            self.copy_code_btn.setText(text)
            self.copy_code_btn.setEnabled(True)

    def _on_token_changed(self, text: str) -> None:
        """输入框内容变化时更新提示与下一步按钮状态。"""
        has_token = bool(text.strip())
        self.next_btn.setEnabled(has_token)
        self.next_btn.setButtonStyle(
            CircleNavButton.STYLE_ACCENT if has_token else CircleNavButton.STYLE_LIGHT
        )
        self.tip_label.setVisible(not has_token)

    def _refresh_input_style(self) -> None:
        """刷新输入框样式以应用当前主题色。"""
        self.token_input.setStyleSheet(f"""
            QLineEdit {{
                border: 2px solid #E0E8F0;
                border-radius: 6px;
                padding: 8px 10px;
                background: #F8FAFC;
                outline: none;
            }}
            QLineEdit:focus {{
                border-color: {self._accent_color};
                background: white;
                outline: none;
            }}
        """)

    def set_initial_values(self, settings: Dict[str, Any]) -> None:
        """从已有设置加载已保存的 Access Token。

        Args:
            settings: 当前设置字典。
        """
        encrypted_token = settings.get("access_token", "")
        if encrypted_token:
            try:
                decrypted = decrypt_token(encrypted_token)
                self.token_input.setText(decrypted)
            except Exception:
                self.token_input.setText("")

    def set_accent_color(self, color: str) -> None:
        """更新页面主题色。

        Args:
            color: 新的主题色十六进制字符串。
        """
        super().set_accent_color(color)
        self._refresh_input_style()
        if hasattr(self, "open_cloud_btn") and self.open_cloud_btn:
            self.open_cloud_btn.setAccentColor(color)
        if hasattr(self, "copy_code_btn") and self.copy_code_btn:
            self.copy_code_btn.setAccentColor(color)
        if hasattr(self, "next_btn") and self.next_btn:
            self.next_btn.setAccentColor(color)
        if hasattr(self, "prev_btn") and self.prev_btn:
            self.prev_btn.setAccentColor(color)
        if hasattr(self, "tip_label") and self.tip_label:
            self.tip_label.setStyleSheet(f"color: {color};")

    def reload_texts(self) -> None:
        """重新加载页面翻译文本。"""
        self.title_label.setText(_("welcome_onboarding.access_token.title"))
        self.subtitle_label.setText(_("welcome_onboarding.access_token.subtitle"))
        if hasattr(self, "open_cloud_btn") and self.open_cloud_btn:
            self.open_cloud_btn.setText(
                _("welcome_onboarding.access_token.open_cloud_platform")
            )
        if hasattr(self, "copy_code_btn") and self.copy_code_btn:
            original_text = _("welcome_onboarding.access_token.copy_code")
            if self.copy_code_btn.isEnabled():
                self.copy_code_btn.setText(original_text)
        if hasattr(self, "tutorial_label") and self.tutorial_label:
            self.tutorial_label.setText(self._build_tutorial_text())
        if hasattr(self, "tip_label") and self.tip_label:
            self.tip_label.setText(_("welcome_onboarding.access_token.empty_tip"))

    def get_access_token(self) -> str:
        """返回当前输入框中的 Access Token。"""
        return self.token_input.text()
