# -*- coding: utf-8 -*-
"""自动保存信号连接器模块

负责将设置页面中各类控件的变更信号统一连接到延迟保存回调，
实现配置变更后的自动持久化。
"""

from typing import Any, Callable


class AutoSaveConnector:
    """自动保存信号连接器

    遍历 SettingPage 的每个标签页，将控件变更信号统一连接到
    外部传入的延迟保存回调函数。
    """

    @staticmethod
    def connect(page: Any, schedule_save_callback: Callable[..., Any]) -> None:
        """连接所有标签页中控件的自动保存信号

        Args:
            page: SettingPage 实例
            schedule_save_callback: 延迟保存回调函数
        """
        tabs = getattr(page, "_tabs", None)
        if not tabs:
            return

        for tab_key, tab in tabs.items():
            AutoSaveConnector._connect_tab(tab, schedule_save_callback)

    @staticmethod
    def _connect_tab(tab: Any, cb: Callable[..., Any]) -> None:
        """连接单个标签页中控件的变更信号"""
        # 开关控件
        for switch in AutoSaveConnector._list_switches(tab):
            if hasattr(switch, 'toggled'):
                switch.toggled.connect(cb)
            elif hasattr(switch, 'stateChanged'):
                switch.stateChanged.connect(cb)
            elif hasattr(switch, 'clicked'):
                switch.clicked.connect(cb)

        # 下拉框
        for combo in AutoSaveConnector._list_combos(tab):
            if hasattr(combo, 'currentTextChanged'):
                combo.currentTextChanged.connect(cb)

        # 输入框
        for inp in AutoSaveConnector._list_inputs(tab):
            if hasattr(inp, 'textChanged'):
                inp.textChanged.connect(cb)

        # 数值输入框 / 滑块
        for spin in AutoSaveConnector._list_spins(tab):
            if hasattr(spin, 'valueChanged'):
                spin.valueChanged.connect(cb)

    # ── 按标签页列控件名 ──────────────────────────────────
    # 避免用 dir() 反射来匹配，保持显式可追踪

    @staticmethod
    def _list_switches(tab) -> list:
        """返回标签页中所有开关控件的列表"""
        names = [
            # basic tab
            'show_tips_switch', 'auto_recover_switch', 'minimize_to_tray_switch',
            'tray_notifications_switch', 'tray_show_progress_switch',
            'sound_enabled_switch', 'download_complete_sound_switch',
            'show_startup_time_switch', 'auto_clean_temp_switch',
            'clipboard_monitor_switch',
            # download tab
            'open_folder_switch',
            'auto_rename_switch', 'include_chapter_switch', 'include_timestamp_switch',
            'auto_categorize_switch',
            'resume_download_switch', 'auto_delete_failed_switch',
            'auto_verify_switch', 'retry_on_verify_fail_switch',
            'allow_any_domain_switch', 'confirm_non_whitelist_switch',
            # interface tab
            'animations_enabled_switch', 'show_details_switch',
            'show_status_bar_switch', 'window_shadow_switch',
            'notification_never_hide_switch',
            # advanced tab
            'proxy_enabled_switch', 'cache_enabled_switch',
            'debug_mode_switch', 'auto_export_config_switch',
            'search_suggestions_switch', 'search_smart_repair_switch',
            # privacy tab
            'auto_save_token_switch', 'auto_clear_history_switch',
            'privacy_protection_switch', 'safe_download_mode_switch',
        ]
        return [getattr(tab, n, None) for n in names if hasattr(tab, n)]

    @staticmethod
    def _list_combos(tab) -> list:
        names = [
            'naming_rule_card', 'categorize_rule_card',
            'interface_scale_card', 'animation_speed_card',
            'list_sort_card', 'list_view_card',
            'proxy_type_card', 'cache_size_card', 'cache_cleanup_card',
            'log_level_card', 'log_retention_card', 'log_cleanup_card',
            'export_interval_card', 'history_retention_card',
            'search_mode_card', 'notification_position_card',
            'notification_size_card', 'language_card',
        ]
        return [getattr(tab, n, None) for n in names if hasattr(tab, n)]

    @staticmethod
    def _list_inputs(tab) -> list:
        names = [
            'download_dir_input', 'proxy_host_input', 'proxy_port_input',
            'proxy_user_input', 'proxy_pass_input', 'token_input',
            'notification_sound_card', 'custom_domain_input',
        ]
        return [getattr(tab, n, None) for n in names if hasattr(tab, n)]

    @staticmethod
    def _list_spins(tab) -> list:
        names = [
            'max_concurrent_card', 'download_threads_card',
            'speed_limit_card', 'retry_count_card', 'retry_interval_card',
            'connect_timeout_card', 'read_timeout_card',
            'resume_threshold_card', 'api_timeout_card', 'api_retry_card',
            'clipboard_interval_spin', 'search_max_results_card',
            'notification_duration_card',
        ]
        return [getattr(tab, n, None) for n in names if hasattr(tab, n)]