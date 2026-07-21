# -*- coding: utf-8 -*-
"""下载设置标签页"""

from typing import Any, Dict

from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QFormLayout, QLabel, QListWidget
from PyQt5.QtCore import Qt

from qfluentwidgets import LineEdit, FluentIcon as FIF

from core.i18n import _
from core.download.file_categorizer import (
    CATEGORIZE_BY_SUBJECT,
    CATEGORIZE_BY_GRADE,
    CATEGORIZE_BY_VERSION,
    CATEGORIZE_BY_SUBJECT_AND_GRADE,
)
from core.download.file_naming import (
    FILE_NAMING_DEFAULT,
    FILE_NAMING_TEXTBOOK_NAME,
    FILE_NAMING_TIMESTAMP,
    FILE_NAMING_TEXTBOOK_NAME_TIMESTAMP,
)
from gui.fonts import body_font, monospace_font
from gui.widgets import CustomContextMenu
from gui.widgets.material_button import MaterialButton
from gui.pages.settings.base_tab import BaseSettingTab
from gui.pages.settings.components.switch_card import SwitchWithLabelSettingCard
from gui.pages.settings.components.combo_box_card import ComboBoxCard
from gui.pages.settings.components.range_card import RangeCard
from gui.pages.settings.components.line_edit_card import LineEditCard
from gui.pages.settings.components.push_card import PushCard
from core.infrastructure.default_settings import get_default_download_dir


class DownloadSettingTab(BaseSettingTab):
    """下载设置标签页——下载目录 / 下载参数 / 文件命名 / 分类 / 域名白名单"""

    # ── UI 创建 ───────────────────────────────────────────
    def _create_content(self, parent_layout):
        self._create_download_dir_section(parent_layout)
        self._create_download_params_section(parent_layout)
        self._create_naming_section(parent_layout)
        self._create_categorize_section(parent_layout)
        self._create_advanced_download_section(parent_layout)
        self._create_domain_whitelist_section(parent_layout)

    def _create_download_dir_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.download.download_dir")
        )

        self.download_dir_input = LineEditCard(
            FIF.FOLDER,
            _("settings.download.download_dir"),
            _("settings.download.download_dir_desc"),
        )
        self.download_dir_input.setText(get_default_download_dir())
        card_group.addSettingCard(self.download_dir_input)

        self.browse_dir_card = PushCard(
            FIF.FOLDER_ADD,
            _("settings.download.download_dir"),
            _("settings.download.browse_dir_desc"),
            button_text=_("common.browse") + "...",
        )
        self.browse_dir_card.setAccentColor("#6C757D")
        self.browse_dir_card.clicked.connect(self._on_browse_dir)
        card_group.addSettingCard(self.browse_dir_card)

        self.ask_download_dir_switch = SwitchWithLabelSettingCard(
            FIF.QUESTION,
            _("settings.download.ask_download_location"),
            _("settings.download.ask_download_location_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.ask_download_dir_switch)

        parent_layout.addWidget(group)

    def _create_download_params_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.download.download_params")
        )

        self.open_folder_switch = SwitchWithLabelSettingCard(
            FIF.FOLDER,
            _("settings.download.open_folder_after_download"),
            _("settings.download.open_folder_after_download_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.open_folder_switch)

        self.max_concurrent_card = RangeCard(
            FIF.SPEED_HIGH,
            _("settings.download.max_concurrent_downloads"),
            _("settings.download.max_concurrent_downloads_desc"),
        )
        self.max_concurrent_card.setRange(1, 20)
        self.max_concurrent_card.setValue(5)
        card_group.addSettingCard(self.max_concurrent_card)

        self.download_threads_card = RangeCard(
            FIF.SPEED_MEDIUM,
            _("settings.download.download_threads"),
            _("settings.download.download_threads_desc"),
        )
        self.download_threads_card.setRange(1, 10)
        self.download_threads_card.setValue(3)
        card_group.addSettingCard(self.download_threads_card)

        self.speed_limit_card = RangeCard(
            FIF.SPEED_OFF,
            _("settings.download.speed_limit"),
            _("settings.download.speed_limit_desc"),
        )
        self.speed_limit_card.setRange(0, 100000)
        self.speed_limit_card.setValue(0)
        card_group.addSettingCard(self.speed_limit_card)

        self.retry_count_card = RangeCard(
            FIF.ROTATE,
            _("settings.download.retry_count"),
            _("settings.download.retry_count_desc"),
        )
        self.retry_count_card.setRange(0, 20)
        self.retry_count_card.setValue(3)
        card_group.addSettingCard(self.retry_count_card)

        self.retry_interval_card = RangeCard(
            FIF.STOP_WATCH,
            _("settings.download.retry_interval"),
            _("settings.download.retry_interval_desc"),
        )
        self.retry_interval_card.setRange(1, 300)
        self.retry_interval_card.setValue(5)
        card_group.addSettingCard(self.retry_interval_card)

        self.connect_timeout_card = RangeCard(
            FIF.CALENDAR,
            _("settings.download.connect_timeout"),
            _("settings.download.connect_timeout_desc"),
        )
        self.connect_timeout_card.setRange(5, 300)
        self.connect_timeout_card.setValue(30)
        card_group.addSettingCard(self.connect_timeout_card)

        self.read_timeout_card = RangeCard(
            FIF.CALENDAR,
            _("settings.download.read_timeout"),
            _("settings.download.read_timeout_desc"),
        )
        self.read_timeout_card.setRange(5, 600)
        self.read_timeout_card.setValue(60)
        card_group.addSettingCard(self.read_timeout_card)

        parent_layout.addWidget(group)

    def _create_naming_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.download.file_naming")
        )

        self.auto_rename_switch = SwitchWithLabelSettingCard(
            FIF.EDIT,
            _("settings.download.auto_rename_duplicate"),
            _("settings.download.auto_rename_duplicate_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.auto_rename_switch)

        self.naming_rule_card = ComboBoxCard(
            FIF.LABEL,
            _("settings.download.naming_rule_label"),
            _("settings.download.naming_rule_label_desc"),
        )
        self.naming_rule_card.addItem("default", FILE_NAMING_DEFAULT)
        self.naming_rule_card.addItem(
            _("settings.download.naming_textbook_name"), FILE_NAMING_TEXTBOOK_NAME
        )
        self.naming_rule_card.addItem(
            _("settings.download.naming_timestamp"), FILE_NAMING_TIMESTAMP
        )
        self.naming_rule_card.addItem(
            _("settings.download.naming_textbook_name_timestamp"),
            FILE_NAMING_TEXTBOOK_NAME_TIMESTAMP,
        )
        self.naming_rule_card.setCurrentIndex(
            self.naming_rule_card.findData(FILE_NAMING_DEFAULT)
        )
        card_group.addSettingCard(self.naming_rule_card)

        self.include_chapter_switch = SwitchWithLabelSettingCard(
            FIF.DOCUMENT,
            _("settings.download.include_chapter_info"),
            _("settings.download.include_chapter_info_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.include_chapter_switch)

        self.include_timestamp_switch = SwitchWithLabelSettingCard(
            FIF.DATE_TIME,
            _("settings.download.include_timestamp"),
            _("settings.download.include_timestamp_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.include_timestamp_switch)

        parent_layout.addWidget(group)

    def _create_categorize_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.download.categorize_save_group")
        )

        self.auto_categorize_switch = SwitchWithLabelSettingCard(
            FIF.FOLDER_ADD,
            _("settings.download.auto_categorize"),
            _("settings.download.auto_categorize_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.auto_categorize_switch)

        self.categorize_rule_card = ComboBoxCard(
            FIF.LIBRARY,
            _("settings.download.categorize_rule_label"),
            _("settings.download.categorize_rule_label_desc"),
        )
        self.categorize_rule_card.addItem(
            _("common.by_subject"), CATEGORIZE_BY_SUBJECT
        )
        self.categorize_rule_card.addItem(
            _("common.by_grade"), CATEGORIZE_BY_GRADE
        )
        self.categorize_rule_card.addItem(
            _("common.by_version"), CATEGORIZE_BY_VERSION
        )
        self.categorize_rule_card.addItem(
            _("common.by_subject_and_grade"), CATEGORIZE_BY_SUBJECT_AND_GRADE
        )
        self.categorize_rule_card.setCurrentIndex(
            self.categorize_rule_card.findData(CATEGORIZE_BY_SUBJECT)
        )
        card_group.addSettingCard(self.categorize_rule_card)

        parent_layout.addWidget(group)

    def _create_advanced_download_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.download.advanced_download")
        )

        self.resume_download_switch = SwitchWithLabelSettingCard(
            FIF.CLOUD_DOWNLOAD,
            _("settings.download.enable_resume"),
            _("settings.download.enable_resume_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.resume_download_switch)

        self.resume_threshold_card = RangeCard(
            FIF.STOP_WATCH,
            _("settings.download.resume_threshold"),
            _("settings.download.resume_threshold_desc"),
        )
        self.resume_threshold_card.setRange(1, 1000)
        self.resume_threshold_card.setValue(10)
        card_group.addSettingCard(self.resume_threshold_card)

        self.auto_delete_failed_switch = SwitchWithLabelSettingCard(
            FIF.DELETE,
            _("settings.download.auto_delete_failed"),
            _("settings.download.auto_delete_failed_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.auto_delete_failed_switch)

        self.auto_verify_switch = SwitchWithLabelSettingCard(
            FIF.ACCEPT,
            _("settings.download.auto_verify_after_download"),
            _("settings.download.auto_verify_after_download_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.auto_verify_switch)

        self.retry_on_verify_fail_switch = SwitchWithLabelSettingCard(
            FIF.ROTATE,
            _("settings.download.auto_retry_on_verify_fail"),
            _("settings.download.auto_retry_on_verify_fail_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.retry_on_verify_fail_switch)

        parent_layout.addWidget(group)

    def _create_domain_whitelist_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.download.domain_whitelist")
        )

        self.allow_any_domain_switch = SwitchWithLabelSettingCard(
            FIF.GLOBE,
            _("settings.download.allow_any_domain"),
            _("settings.download.allow_any_domain_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.allow_any_domain_switch)

        self.confirm_non_whitelist_switch = SwitchWithLabelSettingCard(
            FIF.HELP,
            _("settings.download.confirm_outside_whitelist"),
            _("settings.download.confirm_outside_whitelist_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.confirm_non_whitelist_switch)

        parent_layout.addWidget(group)

        # 自定义域名列表保持复杂布局，外层用 SettingGroup(CardWidget) 包裹
        list_group = self._create_group(_("settings.download.custom_domain_list"))

        self.custom_domain_list_widget = QListWidget()
        self.custom_domain_list_widget.setFont(monospace_font())
        self.custom_domain_list_widget.setMaximumHeight(120)
        self.custom_domain_list_widget.setStyleSheet("""
            QListWidget {
                background: #F8FAFC;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        list_group.add_widget(self.custom_domain_list_widget)

        # 操作按钮行
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self.custom_domain_input = LineEdit()
        self.custom_domain_input.setFont(monospace_font())
        self.custom_domain_input.setPlaceholderText(
            _("settings.download.domain_input_hint")
        )
        CustomContextMenu.setup_for_line_edit(self.custom_domain_input, body_font())
        btn_row.addWidget(self.custom_domain_input)

        add_btn = MaterialButton(_("common.add"), variant=MaterialButton.VARIANT_TONAL)
        add_btn.setAccentColor(self._accent_color)
        add_btn.setFixedHeight(28)
        add_btn.setFixedWidth(60)
        add_btn.clicked.connect(self._on_add_domain)
        btn_row.addWidget(add_btn)
        self.register_accent_button(add_btn)

        remove_btn = MaterialButton(
            _("common.delete"), variant=MaterialButton.VARIANT_OUTLINED
        )
        remove_btn.setAccentColor("#6C757D")
        remove_btn.setFixedHeight(28)
        remove_btn.setFixedWidth(60)
        remove_btn.clicked.connect(self._on_remove_domain)
        btn_row.addWidget(remove_btn)

        clear_btn = MaterialButton(
            _("common.clear"), variant=MaterialButton.VARIANT_OUTLINED
        )
        clear_btn.setAccentColor("#DC3545")
        clear_btn.setFixedHeight(28)
        clear_btn.setFixedWidth(60)
        clear_btn.clicked.connect(self._on_clear_domains)
        btn_row.addWidget(clear_btn)

        list_group.add_layout(btn_row)
        parent_layout.addWidget(list_group)

    # ── 回调（由 SettingPage 传入 callbacks 提供） ──────
    def _on_browse_dir(self):
        cb = self._callbacks.get("browse_download_dir")
        if cb:
            cb()

    def _on_add_domain(self):
        cb = self._callbacks.get("add_custom_domain")
        if cb:
            cb()

    def _on_remove_domain(self):
        cb = self._callbacks.get("remove_custom_domain")
        if cb:
            cb()

    def _on_clear_domains(self):
        cb = self._callbacks.get("clear_custom_domains")
        if cb:
            cb()

    # ── 设置收集 ──────────────────────────────────────────
    def collect_settings(self, settings: Dict[str, Any]) -> None:
        settings["download_dir"] = self.download_dir_input.text()
        settings["ask_download_dir"] = self.ask_download_dir_switch.isChecked()
        settings["open_folder_after_download"] = self.open_folder_switch.isChecked()
        settings["max_concurrent_downloads"] = self.max_concurrent_card.value()
        settings["download_threads"] = self.download_threads_card.value()
        settings["speed_limit"] = self.speed_limit_card.value()
        settings["retry_count"] = self.retry_count_card.value()
        settings["retry_interval"] = self.retry_interval_card.value()
        settings["connect_timeout"] = self.connect_timeout_card.value()
        settings["read_timeout"] = self.read_timeout_card.value()
        settings["auto_rename_duplicates"] = self.auto_rename_switch.isChecked()
        settings["file_naming_rule"] = self.naming_rule_card.currentData()
        settings["include_chapter_info"] = self.include_chapter_switch.isChecked()
        settings["include_timestamp"] = self.include_timestamp_switch.isChecked()
        settings["auto_categorize"] = self.auto_categorize_switch.isChecked()
        settings["categorize_rule"] = self.categorize_rule_card.currentData()
        settings["resume_download"] = self.resume_download_switch.isChecked()
        settings["resume_threshold"] = self.resume_threshold_card.value()
        settings["auto_delete_failed"] = self.auto_delete_failed_switch.isChecked()
        settings["auto_verify"] = self.auto_verify_switch.isChecked()
        settings["retry_on_verify_fail"] = self.retry_on_verify_fail_switch.isChecked()
        settings["allow_any_domain_download"] = self.allow_any_domain_switch.isChecked()
        settings["confirm_non_whitelist_download"] = self.confirm_non_whitelist_switch.isChecked()
        # 自定义域名列表
        domains = []
        for i in range(self.custom_domain_list_widget.count()):
            text = self.custom_domain_list_widget.item(i).text().strip()
            if text:
                domains.append(text)
        settings["custom_allowed_domains"] = domains

    # ── UI 刷新 ───────────────────────────────────────────
    def refresh_from(self, settings: Dict[str, Any]) -> None:
        self.download_dir_input.setText(settings.get("download_dir", ""))
        self.ask_download_dir_switch.setChecked(settings.get("ask_download_dir", True))
        self.open_folder_switch.setChecked(
            settings.get("open_folder_after_download", False)
        )
        self.max_concurrent_card.setValue(settings.get("max_concurrent_downloads", 5))
        self.download_threads_card.setValue(settings.get("download_threads", 3))
        self.speed_limit_card.setValue(settings.get("speed_limit", 0))
        self.retry_count_card.setValue(settings.get("retry_count", 3))
        self.retry_interval_card.setValue(settings.get("retry_interval", 5))
        self.connect_timeout_card.setValue(settings.get("connect_timeout", 30))
        self.read_timeout_card.setValue(settings.get("read_timeout", 60))
        self.auto_rename_switch.setChecked(settings.get("auto_rename_duplicates", True))
        self.naming_rule_card.setCurrentIndex(
            self.naming_rule_card.findData(settings.get("file_naming_rule", FILE_NAMING_DEFAULT))
        )
        self.include_chapter_switch.setChecked(settings.get("include_chapter_info", False))
        self.include_timestamp_switch.setChecked(settings.get("include_timestamp", False))
        self.auto_categorize_switch.setChecked(settings.get("auto_categorize", False))
        self.categorize_rule_card.setCurrentIndex(
            self.categorize_rule_card.findData(settings.get("categorize_rule", CATEGORIZE_BY_SUBJECT))
        )
        self.resume_download_switch.setChecked(settings.get("resume_download", True))
        self.resume_threshold_card.setValue(settings.get("resume_threshold", 10))
        self.auto_delete_failed_switch.setChecked(settings.get("auto_delete_failed", False))
        self.auto_verify_switch.setChecked(settings.get("auto_verify", False))
        self.retry_on_verify_fail_switch.setChecked(
            settings.get("retry_on_verify_fail", False)
        )
        self.allow_any_domain_switch.setChecked(settings.get("allow_any_domain_download", True))
        self.confirm_non_whitelist_switch.setChecked(
            settings.get("confirm_non_whitelist_download", True)
        )
        self._refresh_domain_list(settings)

    def _refresh_domain_list(self, settings):
        domains = settings.get("custom_allowed_domains", []) or []
        self.custom_domain_list_widget.clear()
        for d in domains:
            self.custom_domain_list_widget.addItem(d)
