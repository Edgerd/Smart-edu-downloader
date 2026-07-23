# -*- coding: utf-8 -*-
"""高级设置标签页"""

from typing import Any, Dict

from PyQt5.QtWidgets import QLabel, QLineEdit

from qfluentwidgets import FluentIcon as FIF

from core.i18n import _
from core.infrastructure.logger import (
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_ERROR,
)
from core.resource.search_engine import (
    SEARCH_MODE_APPROXIMATE,
    SEARCH_MODE_EXACT,
)
from gui.fonts import small_font
from gui.pages.settings.base_tab import BaseSettingTab
from gui.pages.settings.components.switch_card import SwitchWithLabelSettingCard
from gui.pages.settings.components.combo_box_card import ComboBoxCard
from gui.pages.settings.components.range_card import RangeCard
from gui.pages.settings.components.line_edit_card import LineEditCard


class AdvancedSettingTab(BaseSettingTab):
    """高级设置标签页——代理 / 缓存 / API / 日志 / 搜索 / 配置管理"""

    # ── UI 创建 ───────────────────────────────────────────
    def _create_content(self, parent_layout):
        self._create_proxy_section(parent_layout)
        self._create_cache_section(parent_layout)
        self._create_api_section(parent_layout)
        self._create_log_section(parent_layout)
        self._create_search_section(parent_layout)
        self._create_config_section(parent_layout)

    def _create_proxy_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.advanced.proxy_settings")
        )

        self.proxy_enabled_switch = SwitchWithLabelSettingCard(
            FIF.GLOBE,
            _("settings.advanced.enable_proxy"),
            _("settings.advanced.enable_proxy_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.proxy_enabled_switch)

        self.proxy_type_card = ComboBoxCard(
            FIF.GLOBE,
            _("settings.advanced.proxy_type"),
            _("settings.advanced.proxy_type_desc"),
        )
        self.proxy_type_card.addItems(["http", "https", "socks4", "socks5"])
        self.proxy_type_card.setCurrentText("http")
        card_group.addSettingCard(self.proxy_type_card)

        self.proxy_host_input = LineEditCard(
            FIF.LINK,
            _("settings.advanced.proxy_address"),
            _("settings.advanced.proxy_address_desc"),
        )
        self.proxy_host_input.setPlaceholderText(
            _("settings.advanced.proxy_host_hint")
        )
        card_group.addSettingCard(self.proxy_host_input)

        self.proxy_port_input = LineEditCard(
            FIF.EDIT,
            _("settings.advanced.proxy_port"),
            _("settings.advanced.proxy_port_desc"),
        )
        self.proxy_port_input.setPlaceholderText(
            _("settings.advanced.proxy_port_hint")
        )
        card_group.addSettingCard(self.proxy_port_input)

        self.proxy_user_input = LineEditCard(
            FIF.PEOPLE,
            _("settings.advanced.proxy_username"),
            _("settings.advanced.proxy_username_desc"),
        )
        card_group.addSettingCard(self.proxy_user_input)

        self.proxy_pass_input = LineEditCard(
            FIF.VPN,
            _("settings.advanced.proxy_password"),
            _("settings.advanced.proxy_password_desc"),
        )
        self.proxy_pass_input.setEchoMode(QLineEdit.Password)
        card_group.addSettingCard(self.proxy_pass_input)

        self.ssl_verify_switch = SwitchWithLabelSettingCard(
            FIF.CERTIFICATE,
            _("settings.advanced.ssl_verify"),
            _("settings.advanced.ssl_verify_desc"),
            checked=True,
        )
        self.ssl_verify_switch.toggled.connect(self._on_ssl_verify_toggled)
        card_group.addSettingCard(self.ssl_verify_switch)

        parent_layout.addWidget(group)

    @staticmethod
    def _on_ssl_verify_toggled(checked: bool):
        """SSL 验证开关状态变更时实时同步到 HTTP 客户端。"""
        try:
            from core.network.http_client import get_http_client
            get_http_client().set_ssl_verify(checked)
        except Exception as e:
            from core.infrastructure.logger import log
            log("WARNING", f"同步 SSL 验证设置失败: {e}")

    def _create_cache_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.advanced.cache_settings")
        )

        self.cache_enabled_switch = SwitchWithLabelSettingCard(
            FIF.SAVE,
            _("settings.advanced.enable_cache"),
            _("settings.advanced.enable_cache_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.cache_enabled_switch)

        self.cache_size_card = ComboBoxCard(
            FIF.SAVE_AS,
            _("settings.advanced.cache_size_limit"),
            _("settings.advanced.cache_size_limit_desc"),
        )
        self.cache_size_card.addItems([
            "100 MB", "200 MB", "300 MB", "500 MB",
            "1 GB", "2 GB", "3 GB", "5 GB",
        ])
        self.cache_size_card.setCurrentText("500 MB")
        card_group.addSettingCard(self.cache_size_card)

        self.cache_cleanup_card = ComboBoxCard(
            FIF.CALENDAR,
            _("settings.advanced.cache_cleanup_interval"),
            _("settings.advanced.cache_cleanup_interval_desc"),
        )
        self.cache_cleanup_card.addItems([
            _("common.every_day"),
            _("common.every_week"),
            _("common.every_month"),
            _("common.never"),
        ])
        self.cache_cleanup_card.setCurrentText(_("common.every_week"))
        card_group.addSettingCard(self.cache_cleanup_card)

        parent_layout.addWidget(group)

    def _create_api_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.advanced.api_settings")
        )

        self.api_timeout_card = RangeCard(
            FIF.SEND,
            _("settings.advanced.api_timeout"),
            _("settings.advanced.api_timeout_desc"),
        )
        self.api_timeout_card.setRange(5, 300)
        self.api_timeout_card.setValue(30)
        self.api_timeout_card.setSuffix(" s")
        card_group.addSettingCard(self.api_timeout_card)

        self.api_retry_card = RangeCard(
            FIF.SYNC,
            _("settings.advanced.api_retry_count"),
            _("settings.advanced.api_retry_count_desc"),
        )
        self.api_retry_card.setRange(0, 20)
        self.api_retry_card.setValue(3)
        card_group.addSettingCard(self.api_retry_card)

        parent_layout.addWidget(group)

    def _create_log_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.advanced.log_settings")
        )

        self.log_level_card = ComboBoxCard(
            FIF.DOCUMENT,
            _("settings.advanced.log_level"),
            _("settings.advanced.log_level_desc"),
        )
        self.log_level_card.addItem(_("settings.advanced.debug_label"), LOG_LEVEL_DEBUG)
        self.log_level_card.addItem(_("common.info_label"), LOG_LEVEL_INFO)
        self.log_level_card.addItem(_("common.warning_label"), LOG_LEVEL_WARNING)
        self.log_level_card.addItem(_("common.error_label"), LOG_LEVEL_ERROR)
        self.log_level_card.setCurrentIndex(
            self.log_level_card.findData(LOG_LEVEL_INFO)
        )
        card_group.addSettingCard(self.log_level_card)

        self.log_retention_card = ComboBoxCard(
            FIF.CALENDAR,
            _("settings.advanced.log_retention"),
            _("settings.advanced.log_retention_desc"),
        )
        self.log_retention_card.addItems([
            _("common.one_day"),
            _("common.three_days"),
            _("common.seven_days"),
            _("common.fourteen_days"),
            _("common.thirty_days"),
            _("common.forever"),
        ])
        self.log_retention_card.setCurrentText(_("common.seven_days"))
        card_group.addSettingCard(self.log_retention_card)

        self.log_cleanup_card = ComboBoxCard(
            FIF.DATE_TIME,
            _("settings.advanced.auto_cleanup_interval"),
            _("settings.advanced.auto_cleanup_interval_desc"),
        )
        self.log_cleanup_card.addItems([
            _("settings.advanced.every_startup"),
            _("common.every_day"),
            _("common.every_week"),
            _("common.every_month"),
        ])
        self.log_cleanup_card.setCurrentText(_("common.every_week"))
        card_group.addSettingCard(self.log_cleanup_card)

        self.debug_mode_switch = SwitchWithLabelSettingCard(
            FIF.INFO,
            _("settings.advanced.enable_debug_mode"),
            _("settings.advanced.enable_debug_mode_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.debug_mode_switch)

        parent_layout.addWidget(group)

    def _create_search_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.advanced.search_settings")
        )

        self.search_mode_card = ComboBoxCard(
            FIF.SEARCH,
            _("settings.advanced.search_mode"),
            _("settings.advanced.search_mode_desc"),
        )
        self.search_mode_card.addItem(
            _("common.approximate_match"), SEARCH_MODE_APPROXIMATE
        )
        self.search_mode_card.addItem(
            _("common.exact_match"), SEARCH_MODE_EXACT
        )
        self.search_mode_card.setCurrentIndex(
            self.search_mode_card.findData(SEARCH_MODE_APPROXIMATE)
        )
        card_group.addSettingCard(self.search_mode_card)

        self.search_suggestions_switch = SwitchWithLabelSettingCard(
            FIF.SEARCH,
            _("settings.advanced.enable_search_suggestions"),
            _("settings.advanced.enable_search_suggestions_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.search_suggestions_switch)

        self.search_max_results_card = RangeCard(
            FIF.LIBRARY,
            _("settings.advanced.max_search_results"),
            _("settings.advanced.max_search_results_desc"),
        )
        self.search_max_results_card.setRange(0, 1000)
        self.search_max_results_card.setValue(100)
        self.search_max_results_card.setSpecialValueText(_("common.unlimited"))
        card_group.addSettingCard(self.search_max_results_card)

        self.search_smart_repair_switch = SwitchWithLabelSettingCard(
            FIF.SEARCH,
            _("settings.advanced.smart_keyword_fix"),
            _("settings.advanced.smart_keyword_fix_desc"),
            checked=True,
        )
        card_group.addSettingCard(self.search_smart_repair_switch)

        mode_desc = QLabel(_("settings.advanced.search_mode_description"))
        mode_desc.setFont(small_font())
        mode_desc.setStyleSheet("color: #666;")
        mode_desc.setWordWrap(True)
        group.add_widget(mode_desc)

        max_results_desc = QLabel(_("settings.advanced.max_search_results_hint"))
        max_results_desc.setFont(small_font())
        max_results_desc.setStyleSheet("color: #666;")
        max_results_desc.setWordWrap(True)
        group.add_widget(max_results_desc)

        repair_desc = QLabel(_("settings.advanced.smart_keyword_fix_hint"))
        repair_desc.setFont(small_font())
        repair_desc.setStyleSheet("color: #666;")
        repair_desc.setWordWrap(True)
        group.add_widget(repair_desc)

        parent_layout.addWidget(group)

    def _create_config_section(self, parent_layout):
        group, card_group = self._create_card_group(
            _("settings.advanced.config_management")
        )

        self.auto_export_config_switch = SwitchWithLabelSettingCard(
            FIF.SYNC,
            _("settings.advanced.auto_export_config"),
            _("settings.advanced.auto_export_config_desc"),
            checked=False,
        )
        card_group.addSettingCard(self.auto_export_config_switch)

        self.export_interval_card = ComboBoxCard(
            FIF.CALENDAR,
            _("settings.advanced.export_interval"),
            _("settings.advanced.export_interval_desc"),
        )
        self.export_interval_card.addItems([
            _("common.every_day"),
            _("common.every_week"),
            _("common.every_month"),
        ])
        self.export_interval_card.setCurrentText(_("common.every_week"))
        card_group.addSettingCard(self.export_interval_card)

        parent_layout.addWidget(group)

    # ── 设置收集 ──────────────────────────────────────────
    def collect_settings(self, settings: Dict[str, Any]) -> None:
        settings["proxy_enabled"] = self.proxy_enabled_switch.isChecked()
        settings["proxy_type"] = self.proxy_type_card.currentText()
        settings["proxy_host"] = self.proxy_host_input.text()
        settings["proxy_port"] = self.proxy_port_input.text()
        settings["proxy_username"] = self.proxy_user_input.text()
        settings["proxy_password"] = self.proxy_pass_input.text()
        settings["ssl_verify"] = self.ssl_verify_switch.isChecked()

        settings["cache_enabled"] = self.cache_enabled_switch.isChecked()
        cache_map = {
            "100 MB": 100, "200 MB": 200, "300 MB": 300, "500 MB": 500,
            "1 GB": 1000, "2 GB": 2000, "3 GB": 3000, "5 GB": 5000,
        }
        settings["cache_size_limit"] = cache_map.get(
            self.cache_size_card.currentText(), 500
        )
        settings["cache_cleanup_period"] = self.cache_cleanup_card.currentText()

        settings["api_timeout"] = self.api_timeout_card.value()
        settings["api_retry_count"] = self.api_retry_card.value()

        settings["log_level"] = self.log_level_card.currentData()
        settings["debug_mode"] = self.debug_mode_switch.isChecked()
        retention_map = {
            _("common.one_day"): 1,
            _("common.three_days"): 3,
            _("common.seven_days"): 7,
            _("common.fourteen_days"): 14,
            _("common.thirty_days"): 30,
            _("common.forever"): 0,
        }
        settings["log_retention_days"] = retention_map.get(
            self.log_retention_card.currentText(), 7
        )
        settings["log_cleanup_period"] = self.log_cleanup_card.currentText()

        settings["search_mode"] = self.search_mode_card.currentData()
        settings["search_suggestions_enabled"] = self.search_suggestions_switch.isChecked()
        settings["search_max_results"] = self.search_max_results_card.value()
        settings["search_smart_repair"] = self.search_smart_repair_switch.isChecked()

        settings["auto_export_config"] = self.auto_export_config_switch.isChecked()
        settings["export_interval"] = self.export_interval_card.currentText()

    # ── UI 刷新 ───────────────────────────────────────────
    def refresh_from(self, settings: Dict[str, Any]) -> None:
        self.proxy_enabled_switch.setChecked(settings.get("proxy_enabled", False))
        self.proxy_type_card.setCurrentText(settings.get("proxy_type", "http"))
        self.proxy_host_input.setText(settings.get("proxy_host", ""))
        self.proxy_port_input.setText(settings.get("proxy_port", ""))
        self.proxy_user_input.setText(settings.get("proxy_username", ""))
        self.proxy_pass_input.setText(settings.get("proxy_password", ""))
        self.ssl_verify_switch.setChecked(settings.get("ssl_verify", True))

        self.cache_enabled_switch.setChecked(settings.get("cache_enabled", True))
        current_cache = settings.get("cache_size_limit", 500)
        cache_options = {
            "100 MB": 100, "200 MB": 200, "300 MB": 300, "500 MB": 500,
            "1 GB": 1000, "2 GB": 2000, "3 GB": 3000, "5 GB": 5000,
        }
        closest = min(cache_options, key=lambda x: abs(cache_options[x] - current_cache))
        self.cache_size_card.setCurrentText(closest)
        self.cache_cleanup_card.setCurrentText(
            settings.get("cache_cleanup_period", _("common.every_week"))
        )

        self.api_timeout_card.setValue(settings.get("api_timeout", 30))
        self.api_retry_card.setValue(settings.get("api_retry_count", 3))

        self.log_level_card.setCurrentIndex(
            self.log_level_card.findData(settings.get("log_level", LOG_LEVEL_INFO))
        )
        self.debug_mode_switch.setChecked(settings.get("debug_mode", False))
        ret_map = {
            1: _("common.one_day"),
            3: _("common.three_days"),
            7: _("common.seven_days"),
            14: _("common.fourteen_days"),
            30: _("common.thirty_days"),
            0: _("common.forever"),
        }
        self.log_retention_card.setCurrentText(
            ret_map.get(settings.get("log_retention_days", 7), _("common.seven_days"))
        )
        self.log_cleanup_card.setCurrentText(
            settings.get("log_cleanup_period", _("common.every_week"))
        )

        self.search_mode_card.setCurrentIndex(
            self.search_mode_card.findData(
                settings.get("search_mode", SEARCH_MODE_APPROXIMATE)
            )
        )
        self.search_suggestions_switch.setChecked(
            settings.get("search_suggestions_enabled", True)
        )
        self.search_max_results_card.setValue(settings.get("search_max_results", 100))
        self.search_smart_repair_switch.setChecked(
            settings.get("search_smart_repair", True)
        )

        self.auto_export_config_switch.setChecked(
            settings.get("auto_export_config", False)
        )
        self.export_interval_card.setCurrentText(
            settings.get("export_interval", _("common.every_week"))
        )
