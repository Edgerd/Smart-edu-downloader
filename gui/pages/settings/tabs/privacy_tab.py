# -*- coding: utf-8 -*-
"""隐私与安全标签页"""

from typing import Any, Dict
import webbrowser

from PyQt5.QtWidgets import QApplication, QMessageBox, QLineEdit, QLabel
from PyQt5.QtGui import QClipboard

from qfluentwidgets import FluentIcon as FIF

from core.i18n import _
from gui.fonts import body_font, small_font, monospace_font
from gui.styles import load_background_color
from gui.pages.settings.base_tab import BaseSettingTab
from gui.pages.settings.components.switch_card import SwitchWithLabelSettingCard
from gui.pages.settings.components.combo_box_card import ComboBoxCard
from gui.pages.settings.components.line_edit_card import LineEditCard
from gui.pages.settings.components.push_card import PushCard


class PrivacySettingTab(BaseSettingTab):
    """隐私与安全标签页——Access Token / 历史记录 / 安全设置"""

    # ── UI 创建 ───────────────────────────────────────────
    def _create_content(self, parent_layout):
        self._create_token_section(parent_layout)
        self._create_history_section(parent_layout)
        self._create_security_section(parent_layout)

    def _create_token_section(self, parent_layout):
        group = self._create_group(_("settings.privacy.access_token_group"))

        self.token_input = LineEditCard(
            FIF.FINGERPRINT,
            _("settings.privacy.access_token_label"),
            _("settings.privacy.access_token_label_desc"),
        )
        self.token_input.setPlaceholderText(
            _("settings.privacy.access_token_placeholder")
        )
        self.token_input.setEchoMode(QLineEdit.Password)
        group.add_widget(self.token_input)

        self.auto_save_token_switch = SwitchWithLabelSettingCard(
            FIF.SAVE,
            _("settings.privacy.auto_save_token"),
            _("settings.privacy.auto_save_token_desc"),
            checked=True,
        )
        group.add_widget(self.auto_save_token_switch)

        self.open_cloud_card = PushCard(
            FIF.GLOBE,
            _("settings.privacy.open_cloud_platform_token"),
            _("settings.privacy.open_cloud_platform_token_desc"),
            button_text=_("settings.privacy.open_cloud_platform_token"),
        )
        self.open_cloud_card.setAccentColor(self._accent_color)
        self.open_cloud_card.clicked.connect(self._on_open_cloud)
        group.add_widget(self.open_cloud_card)
        self.register_accent_button(self.open_cloud_card.button())

        self.copy_js_card = PushCard(
            FIF.COPY,
            _("settings.privacy.copy_code_button"),
            _("settings.privacy.copy_code_button_desc"),
            button_text=_("settings.privacy.copy_code_button"),
        )
        self.copy_js_card.setAccentColor("#17A2B8")
        self.copy_js_card.clicked.connect(self._on_copy_js)
        group.add_widget(self.copy_js_card)

        bg_color = load_background_color()

        self.help_label = QLabel(_("settings.privacy.token_help"))
        self.help_label.setFont(small_font())
        self.help_label.setStyleSheet(
            f"color: #666; background: {bg_color}; padding: 8px; border-radius: 4px;"
        )
        self.help_label.setWordWrap(True)
        group.add_widget(self.help_label)

        js_code = _("settings.privacy.token_js_code")
        self.js_code_label = QLabel(js_code)
        self.js_code_label.setFont(monospace_font())
        self.js_code_label.setStyleSheet(
            f"color: {self._accent_color}; background: {bg_color}; padding: 8px; "
            f"border-radius: 4px; border: 1px solid #B8D4F0;"
        )
        self.js_code_label.setWordWrap(True)
        group.add_widget(self.js_code_label)

        parent_layout.addWidget(group)

    def _create_history_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.privacy.history")
        )

        self.clear_history_card = PushCard(
            FIF.DELETE,
            _("settings.privacy.clear_browsing_history"),
            _("settings.privacy.clear_browsing_history_desc"),
            button_text=_("settings.privacy.clear_browsing_history"),
        )
        self.clear_history_card.setAccentColor("#DC3545")
        self.clear_history_card.clicked.connect(self._on_clear_history)
        card_group.addSettingCard(self.clear_history_card)

        self.history_retention_card = ComboBoxCard(
            FIF.CALENDAR,
            _("settings.privacy.history_retention"),
            _("settings.privacy.history_retention_desc"),
        )
        self.history_retention_card.addItems([
            _("common.seven_days"),
            _("common.thirty_days"),
            _("common.ninety_days"),
            _("common.forever"),
        ])
        self.history_retention_card.setCurrentText(_("common.thirty_days"))
        card_group.addSettingCard(self.history_retention_card)

        self.auto_clear_history_switch = SwitchWithLabelSettingCard(
            FIF.SAVE,
            _("settings.privacy.auto_clear_history"),
            _("settings.privacy.auto_clear_history_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.auto_clear_history_switch)

        parent_layout.addWidget(group)

    def _create_security_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.privacy.security_settings")
        )

        self.privacy_protection_switch = SwitchWithLabelSettingCard(
            FIF.INFO,
            _("settings.privacy.network_privacy"),
            _("settings.privacy.network_privacy_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.privacy_protection_switch)

        self.safe_download_mode_switch = SwitchWithLabelSettingCard(
            FIF.HELP,
            _("settings.privacy.safe_download_mode"),
            _("settings.privacy.safe_download_mode_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.safe_download_mode_switch)

        parent_layout.addWidget(group)

    # ── 回调 ──────────────────────────────────────────────
    def _on_open_cloud(self):
        cb = self._callbacks.get("open_cloud_platform")
        if cb:
            cb()
        else:
            webbrowser.open("https://auth.smartedu.cn/uias/login")

    def _on_copy_js(self):
        clipboard = QApplication.clipboard()
        js_code = _("settings.privacy.token_js_code_snippet")
        clipboard.setText(js_code)
        QMessageBox.information(self, _("common.tip"), _("settings.privacy.copy_code_success"))

    def _on_clear_history(self):
        cb = self._callbacks.get("clear_history")
        if cb:
            cb()

    # ── 设置收集 ──────────────────────────────────────────
    def collect_settings(self, settings: Dict[str, Any]) -> None:
        from core.settings.token_manager import TokenManager

        raw_token = self.token_input.text().strip()
        if raw_token:
            is_already_encrypted = (
                raw_token.startswith("gAAAAA") or raw_token.startswith("xor:")
            )
            if is_already_encrypted:
                from core.infrastructure.logger import log
                log("INFO", "检测到输入框内容为密文格式，保持原有 token 不变")
            else:
                settings["access_token"] = TokenManager.encrypt(raw_token)
        else:
            settings["access_token"] = ""

        settings["auto_save_token"] = self.auto_save_token_switch.isChecked()
        settings["history_retention"] = self.history_retention_card.currentText()
        settings["auto_clear_history"] = self.auto_clear_history_switch.isChecked()
        settings["privacy_protection"] = self.privacy_protection_switch.isChecked()
        settings["safe_download_mode"] = self.safe_download_mode_switch.isChecked()

    def set_accent_color(self, color: str):
        """主题色变化时同步更新强调色与背景色。"""
        super().set_accent_color(color)
        bg_color = load_background_color()
        if hasattr(self, "js_code_label"):
            self.js_code_label.setStyleSheet(
                f"color: {color}; background: {bg_color}; padding: 8px; "
                f"border-radius: 4px; border: 1px solid #B8D4F0;"
            )
        if hasattr(self, "help_label"):
            self.help_label.setStyleSheet(
                f"color: #666; background: {bg_color}; padding: 8px; border-radius: 4px;"
            )

    # ── UI 刷新 ───────────────────────────────────────────
    def refresh_from(self, settings: Dict[str, Any]) -> None:
        from core.settings.token_manager import TokenManager

        encrypted_token = settings.get("access_token", "")
        decrypted_token = TokenManager.decrypt(encrypted_token)
        self.token_input.setText(decrypted_token)
        self.auto_save_token_switch.setChecked(settings.get("auto_save_token", True))
        self.history_retention_card.setCurrentText(
            settings.get("history_retention", _("common.thirty_days"))
        )
        self.auto_clear_history_switch.setChecked(
            settings.get("auto_clear_history", False)
        )
        self.privacy_protection_switch.setChecked(
            settings.get("privacy_protection", False)
        )
        self.safe_download_mode_switch.setChecked(
            settings.get("safe_download_mode", False)
        )
