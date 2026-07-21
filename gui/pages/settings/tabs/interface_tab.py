# -*- coding: utf-8 -*-
"""界面设置标签页"""

from typing import Any, Dict

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QMessageBox,
)

from qfluentwidgets import LineEdit, FluentIcon as FIF

from core.config.theme_config import (
    config_from_preset_key,
    config_from_preset_name,
    get_theme_config,
)
from core.i18n import _, get_available_languages
from gui.fonts import body_font, small_font
from gui.widgets import CustomContextMenu
from gui.widgets.material_button import MaterialButton
from gui.components.theme_selector import ThemeSelector
from gui.pages.settings.base_tab import BaseSettingTab
from gui.pages.settings.components.switch_card import SwitchWithLabelSettingCard
from gui.pages.settings.components.combo_box_card import ComboBoxCard
from gui.pages.settings.components.range_card import RangeCard
from gui.pages.settings.components.line_edit_card import LineEditCard
from gui.pages.settings.components.push_card import PushCard


class InterfaceSettingTab(BaseSettingTab):
    """界面设置标签页——界面缩放 / 列表 / 显示 / 主题 / 通知"""

    # ── UI 创建 ───────────────────────────────────────────
    def _create_content(self, parent_layout):
        self._theme_config = config_from_preset_key("jikelan")

        self._create_language_section(parent_layout)
        self._create_ui_scale_section(parent_layout)
        self._create_ui_elements_section(parent_layout)
        self._create_list_section(parent_layout)
        self._create_display_section(parent_layout)
        self._create_color_section(parent_layout)
        self._create_notification_section(parent_layout)

    def _create_language_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.interface.language_settings")
        )

        self.language_card = ComboBoxCard(
            FIF.LANGUAGE,
            _("settings.interface.language_label"),
            _("settings.interface.language_label_desc"),
        )
        for lang in get_available_languages():
            self.language_card.addItem(lang["name"], lang["code"])
        self.language_card.currentIndexChanged.connect(self._on_language_changed)
        card_group.addSettingCard(self.language_card)

        hint_label = QLabel(_("settings.interface.language_restart_hint"))
        hint_label.setFont(small_font())
        hint_label.setStyleSheet("color: #888888;")
        group.add_widget(hint_label)

        parent_layout.addWidget(group)

    def _create_ui_scale_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.interface.ui_scale_group")
        )

        self.interface_scale_card = ComboBoxCard(
            FIF.ZOOM,
            _("settings.interface.ui_scale"),
            _("settings.interface.ui_scale_desc"),
        )
        self.interface_scale_card.addItems(
            ["75%", "80%", "85%", "90%", "95%", "100%", "105%", "110%",
             "115%", "120%", "125%", "130%", "150%"]
        )
        self.interface_scale_card.setCurrentText("100%")
        card_group.addSettingCard(self.interface_scale_card)

        parent_layout.addWidget(group)

    def _create_ui_elements_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.interface.ui_elements")
        )

        self.animations_enabled_switch = SwitchWithLabelSettingCard(
            FIF.MOVIE,
            _("settings.interface.enable_animation"),
            _("settings.interface.enable_animation_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.animations_enabled_switch)

        self.animation_speed_card = ComboBoxCard(
            FIF.SPEED_MEDIUM,
            _("settings.interface.animation_speed"),
            _("settings.interface.animation_speed_desc"),
        )
        self.animation_speed_card.addItems([
            _("common.slow"),
            _("common.medium"),
            _("common.fast"),
        ])
        self.animation_speed_card.setCurrentText(_("common.medium"))
        card_group.addSettingCard(self.animation_speed_card)

        parent_layout.addWidget(group)

    def _create_list_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.interface.list_settings")
        )

        self.show_details_switch = SwitchWithLabelSettingCard(
            FIF.LIBRARY,
            _("settings.interface.show_detailed_info"),
            _("settings.interface.show_detailed_info_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.show_details_switch)

        self.list_sort_card = ComboBoxCard(
            FIF.ALIGNMENT,
            _("settings.interface.list_sort"),
            _("settings.interface.list_sort_desc"),
        )
        self.list_sort_card.addItems([
            _("common.by_time"),
            _("common.by_name"),
            _("common.by_size"),
        ])
        self.list_sort_card.setCurrentText(_("common.by_time"))
        card_group.addSettingCard(self.list_sort_card)

        self.list_view_card = ComboBoxCard(
            FIF.TILES,
            _("settings.interface.list_view"),
            _("settings.interface.list_view_desc"),
        )
        self.list_view_card.addItems([
            _("settings.interface.detailed_list"),
            _("settings.interface.compact_list"),
        ])
        self.list_view_card.setCurrentText(_("settings.interface.detailed_list"))
        card_group.addSettingCard(self.list_view_card)

        parent_layout.addWidget(group)

    def _create_display_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.interface.display_settings")
        )

        self.show_status_bar_switch = SwitchWithLabelSettingCard(
            FIF.VIEW,
            _("settings.interface.show_status_bar"),
            _("settings.interface.show_status_bar_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.show_status_bar_switch)

        self.window_shadow_switch = SwitchWithLabelSettingCard(
            FIF.FULL_SCREEN,
            _("settings.interface.show_window_shadow"),
            _("settings.interface.show_window_shadow_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.window_shadow_switch)

        parent_layout.addWidget(group)

    def _create_color_section(self, parent_layout):
        group = self._create_group(_("settings.interface.theme_settings"))

        self.theme_selector = ThemeSelector(self, self._theme_config, show_title=False)
        self.theme_selector.theme_changed.connect(self._on_theme_changed)
        group.add_widget(self.theme_selector)

        parent_layout.addWidget(group)

    def _on_theme_changed(self, config: dict) -> None:
        """主题选择器配置变化回调。"""
        self._theme_config = config
        cb = self._callbacks.get("theme_preset_selected")
        if cb:
            cb(self._theme_config.copy())
        cb = self._callbacks.get("custom_theme_changed")
        if cb:
            cb(self._theme_config.copy())

    def _create_notification_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.interface.notification_settings")
        )

        self.notification_position_card = ComboBoxCard(
            FIF.MESSAGE,
            _("settings.interface.notification_position"),
            _("settings.interface.notification_position_desc"),
        )
        self.notification_position_card.addItems([
            _("common.top_left"),
            _("common.top_right"),
            _("common.bottom_left"),
            _("common.bottom_right"),
        ])
        self.notification_position_card.setCurrentText(_("common.bottom_right"))
        card_group.addSettingCard(self.notification_position_card)

        self.notification_size_card = ComboBoxCard(
            FIF.FIT_PAGE,
            _("settings.interface.notification_size"),
            _("settings.interface.notification_size_desc"),
        )
        self.notification_size_card.addItems([
            _("common.small"),
            _("common.medium"),
            _("common.large"),
        ])
        self.notification_size_card.setCurrentText(_("common.large"))
        card_group.addSettingCard(self.notification_size_card)

        self.notification_duration_card = RangeCard(
            FIF.STOP_WATCH,
            _("settings.interface.notification_duration"),
            _("settings.interface.notification_duration_desc"),
        )
        self.notification_duration_card.setRange(1, 60)
        self.notification_duration_card.setValue(19)
        self.notification_duration_card.setSuffix(" s")
        card_group.addSettingCard(self.notification_duration_card)

        self.notification_never_hide_switch = SwitchWithLabelSettingCard(
            FIF.PIN,
            _("settings.interface.notification_never_hide"),
            _("settings.interface.notification_never_hide_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.notification_never_hide_switch)

        # 自定义音效：输入框卡片 + 浏览按钮卡片
        self.notification_sound_card = LineEditCard(
            FIF.MUSIC,
            _("settings.interface.notification_sound_placeholder"),
            _("settings.interface.notification_sound_desc"),
        )
        self.notification_sound_card.setPlaceholderText(
            _("settings.interface.notification_sound_placeholder")
        )
        card_group.addSettingCard(self.notification_sound_card)

        self.browse_sound_card = PushCard(
            FIF.FOLDER,
            _("settings.interface.notification_sound_placeholder"),
            _("settings.interface.browse_sound_desc"),
            button_text=_("common.browse"),
        )
        self.browse_sound_card.setAccentColor("#6C757D")
        self.browse_sound_card.clicked.connect(self._on_browse_sound)
        card_group.addSettingCard(self.browse_sound_card)

        parent_layout.addWidget(group)

    def _on_browse_sound(self):
        cb = self._callbacks.get("browse_notification_sound")
        if cb:
            cb()

    def _on_language_changed(self, index: int) -> None:
        """语言选择变更时切换语言并提示重启生效。"""
        code = self.language_card.currentData()
        if not code:
            return

        # 首次加载或恢复到初始语言时不弹窗
        if code == getattr(self, '_initial_language', None):
            return

        from core.config.settings_manager import set_setting
        from core.i18n import set_language

        set_setting("language", code)
        set_language(code)

        QMessageBox.information(
            self,
            _("settings.interface.language_changed_title"),
            _("settings.interface.language_changed_message"),
        )

    # ── 设置收集 ──────────────────────────────────────────
    def collect_settings(self, settings: Dict[str, Any]) -> None:
        settings["language"] = self.language_card.currentData()
        scale_text = self.interface_scale_card.currentText()
        settings["interface_scale"] = int(scale_text.replace('%', ''))
        settings["animations_enabled"] = self.animations_enabled_switch.isChecked()
        settings["animation_speed"] = self.animation_speed_card.currentText()
        settings["show_details"] = self.show_details_switch.isChecked()
        settings["list_sort"] = self.list_sort_card.currentText()
        settings["list_view"] = self.list_view_card.currentText()
        settings["show_status_bar"] = self.show_status_bar_switch.isChecked()
        settings["window_shadow"] = self.window_shadow_switch.isChecked()
        settings["notification_position"] = self.notification_position_card.currentText()
        settings["notification_size"] = self.notification_size_card.currentText()
        settings["notification_duration"] = self.notification_duration_card.value()
        settings["notification_never_hide"] = self.notification_never_hide_switch.isChecked()
        settings["notification_custom_sound"] = self.notification_sound_card.text()
        settings["theme_color"] = self.theme_selector.get_theme_config()

    # ── UI 刷新 ───────────────────────────────────────────
    def refresh_from(self, settings: Dict[str, Any]) -> None:
        current_language = settings.get("language", "zh_CN")
        # 记录当前语言作为初始值，用于区分用户主动变更与首次加载
        self._initial_language = current_language
        for i in range(self.language_card.combo_box().count()):
            if self.language_card.combo_box().itemData(i) == current_language:
                self.language_card.setCurrentIndex(i)
                break

        scale = str(settings.get("interface_scale", 100)) + "%"
        self.interface_scale_card.setCurrentText(scale)
        self.animations_enabled_switch.setChecked(settings.get("animations_enabled", True))
        self.animation_speed_card.setCurrentText(settings.get("animation_speed", _("common.medium")))
        self.show_details_switch.setChecked(settings.get("show_details", False))
        self.list_sort_card.setCurrentText(settings.get("list_sort", _("common.by_time")))
        self.list_view_card.setCurrentText(settings.get("list_view", _("settings.interface.detailed_list")))
        self.show_status_bar_switch.setChecked(settings.get("show_status_bar", True))
        self.window_shadow_switch.setChecked(settings.get("window_shadow", True))
        self.notification_position_card.setCurrentText(
            settings.get("notification_position", _("common.top_right"))
        )
        self.notification_size_card.setCurrentText(
            settings.get("notification_size", _("common.medium"))
        )
        self.notification_duration_card.setValue(
            settings.get("notification_duration", 5)
        )
        self.notification_never_hide_switch.setChecked(settings.get("notification_never_hide", False))
        self.notification_sound_card.setText(
            settings.get("notification_custom_sound", "")
        )

        # 恢复主题配置
        self._theme_config = get_theme_config(settings)
        self.theme_selector.set_theme_config(self._theme_config)
