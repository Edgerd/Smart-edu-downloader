# -*- coding: utf-8 -*-
"""基础设置标签页"""

from typing import Any, Dict

from PyQt5.QtWidgets import QHBoxLayout, QLabel

from qfluentwidgets import FluentIcon as FIF

from core.i18n import _
from gui.fonts import body_font, small_font
from gui.widgets import NoWheelSpinBox
from gui.pages.settings.base_tab import BaseSettingTab
from gui.pages.settings.components.switch_card import SwitchWithLabelSettingCard


class BasicSettingTab(BaseSettingTab):
    """基础设置标签页——赞赏码 / 基础功能开关 / 剪贴板监测"""

    # ── UI 创建 ───────────────────────────────────────────
    def _create_content(self, parent_layout):
        self._create_donation_group(parent_layout)
        self._create_basic_group(parent_layout)
        self._create_clipboard_group(parent_layout)

    def _create_donation_group(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.basic.donation_qr")
        )

        self.show_tips_switch = SwitchWithLabelSettingCard(
            FIF.INFO,
            _("settings.basic.show_donation_qr"),
            _("settings.basic.show_donation_qr_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.show_tips_switch)

        # launch_count 在 refresh_from 中补充，这里创建占位标签
        self.launch_info_label = QLabel("")
        self.launch_info_label.setFont(small_font())
        self.launch_info_label.setStyleSheet("color: #999;")
        group.add_widget(self.launch_info_label)

        parent_layout.addWidget(group)

    def _create_basic_group(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.basic.group_title")
        )

        cards = [
            (FIF.SYNC, _("settings.basic.restore_last_task_on_startup"),
             _("settings.basic.restore_last_task_on_startup_desc"), "auto_recover"),
            (FIF.MINIMIZE, _("settings.basic.minimize_to_tray"),
             _("settings.basic.minimize_to_tray_desc"), "minimize_to_tray"),
            (FIF.MESSAGE, _("settings.basic.system_tray_notification"),
             _("settings.basic.system_tray_notification_desc"), "tray_notifications"),
            (FIF.DOWNLOAD, _("settings.basic.tray_show_progress"),
             _("settings.basic.tray_show_progress_desc"), "tray_show_progress"),
            (FIF.VOLUME, _("settings.basic.enable_sound"),
             _("settings.basic.enable_sound_desc"), "sound_enabled"),
            (FIF.MUSIC, _("settings.basic.download_complete_sound"),
             _("settings.basic.download_complete_sound_desc"), "download_complete_sound"),
            (FIF.DATE_TIME, _("settings.basic.show_startup_time"),
             _("settings.basic.show_startup_time_desc"), "show_startup_time"),
            (FIF.BROOM, _("settings.basic.auto_cleanup_temp"),
             _("settings.basic.auto_cleanup_temp_desc"), "auto_clean_temp"),
        ]

        for icon, title, content, name in cards:
            card = SwitchWithLabelSettingCard(
                icon, title, content, checked=False
            )
            setattr(self, f"{name}_switch", card)
            card_group.addSettingCard(card)

        parent_layout.addWidget(group)

    def _create_clipboard_group(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.basic.clipboard_monitor_group")
        )

        self.clipboard_monitor_switch = SwitchWithLabelSettingCard(
            FIF.PASTE,
            _("settings.basic.clipboard_monitor"),
            _("settings.basic.clipboard_monitor_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.clipboard_monitor_switch)

        # 检测间隔保持行内 SpinBox
        interval_layout = QHBoxLayout()
        interval_layout.setSpacing(8)
        clipboard_interval_label = QLabel(
            _("settings.basic.clipboard_check_interval")
        )
        clipboard_interval_label.setFont(body_font())
        self.clipboard_interval_spin = NoWheelSpinBox()
        self.clipboard_interval_spin.setRange(500, 5000)
        self.clipboard_interval_spin.setSingleStep(500)
        self.clipboard_interval_spin.setValue(1000)
        interval_layout.addWidget(clipboard_interval_label)
        interval_layout.addWidget(self.clipboard_interval_spin)
        interval_layout.addStretch()
        interval_layout.setContentsMargins(16, 0, 16, 0)
        group.add_layout(interval_layout)

        parent_layout.addWidget(group)

    # ── 设置收集 ──────────────────────────────────────────
    def collect_settings(self, settings: Dict[str, Any]) -> None:
        settings["show_tips_switch"] = self.show_tips_switch.isChecked()
        settings["auto_recover_tasks"] = self.auto_recover_switch.isChecked()
        settings["minimize_to_tray"] = self.minimize_to_tray_switch.isChecked()
        settings["tray_notifications"] = self.tray_notifications_switch.isChecked()
        settings["tray_show_progress"] = self.tray_show_progress_switch.isChecked()
        settings["sound_enabled"] = self.sound_enabled_switch.isChecked()
        settings["download_complete_sound"] = self.download_complete_sound_switch.isChecked()
        settings["show_startup_time"] = self.show_startup_time_switch.isChecked()
        settings["auto_clean_temp"] = self.auto_clean_temp_switch.isChecked()
        settings["clipboard_monitor_enabled"] = self.clipboard_monitor_switch.isChecked()
        settings["clipboard_check_interval"] = self.clipboard_interval_spin.value()

    # ── UI 刷新 ───────────────────────────────────────────
    def refresh_from(self, settings: Dict[str, Any]) -> None:
        self.show_tips_switch.setChecked(settings.get("show_tips_switch", True))
        self.launch_info_label.setText(
            _("settings.basic.launch_count_template", count=settings.get('launch_count', 0))
        )
        self.auto_recover_switch.setChecked(settings.get("auto_recover_tasks", True))
        self.minimize_to_tray_switch.setChecked(settings.get("minimize_to_tray", False))
        self.tray_notifications_switch.setChecked(settings.get("tray_notifications", False))
        self.tray_show_progress_switch.setChecked(settings.get("tray_show_progress", False))
        self.sound_enabled_switch.setChecked(settings.get("sound_enabled", True))
        self.download_complete_sound_switch.setChecked(settings.get("download_complete_sound", False))
        self.show_startup_time_switch.setChecked(settings.get("show_startup_time", False))
        self.auto_clean_temp_switch.setChecked(settings.get("auto_clean_temp", False))
        self.clipboard_monitor_switch.setChecked(settings.get("clipboard_monitor_enabled", True))
        self.clipboard_interval_spin.setValue(settings.get("clipboard_check_interval", 1000))
