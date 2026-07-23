# -*- coding: utf-8 -*-
"""设置页面"""

import os
from typing import Any, Dict

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QFileDialog,
                             QMessageBox, QSlider, QColorDialog)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor

from core.settings import (TokenManager, SettingsCollector, SettingsSaver,
                           SettingsExporter, DomainManager, HistoryCleaner,
                           SettingsRefresher, AutoSaveConnector)
from core.i18n import _, get_available_languages
from core.infrastructure.default_settings import get_all_default_settings, get_default_download_dir
from core.infrastructure.logger import log
from core.ui.icon_manager import IconManager
from core.config.theme_config import get_theme_config, primary_color

from gui.widgets import (SwitchWithLabel, NoWheelSpinBox, NoWheelComboBox,
                         VerticalTabWidget, CustomContextMenu)
from gui.widgets.material_button import MaterialButton
from gui.fonts import body_font, small_font, bold_font, monospace_font
from gui.styles import load_theme_color, load_primary_color

from gui.pages.settings.tabs.basic_tab import BasicSettingTab
from gui.pages.settings.tabs.download_tab import DownloadSettingTab
from gui.pages.settings.tabs.interface_tab import InterfaceSettingTab
from gui.pages.settings.tabs.advanced_tab import AdvancedSettingTab
from gui.pages.settings.tabs.privacy_tab import PrivacySettingTab


class SettingPage(QWidget):
    """设置页面类 - 重构版

    职责：
    - 组装标签页、协调全局 UI 元素（头部、保存按钮、主题色）
    - 持有回调方法供标签页按钮使用
    - 委托标签页各自的 ``collect_settings()`` / ``refresh_from()``
    """

    settings_saved = pyqtSignal()

    # 设置页标签图标路径
    SETTING_ICONS = {
        "basic": "resources/images/setting/basic.svg",
        "download": "resources/images/setting/download.svg",
        "appearance": "resources/images/setting/appearance.svg",
        "advanced": "resources/images/setting/advanced.svg",
        "privacy": "resources/images/setting/privacy.svg",
    }

    @staticmethod
    def _get_setting_icon_path(name: str) -> str:
        """获取设置页标签图标的绝对路径"""
        app_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        return os.path.join(app_root, SettingPage.SETTING_ICONS[name])

    def __init__(self, parent=None, downloader=None):
        super().__init__(parent)
        self.downloader = downloader
        self.settings = SettingPage.load_settings()
        self._auto_save_timer = QTimer()
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._auto_save_settings)
        self._theme_config = get_theme_config(self.settings)

        # 初始化图标管理器
        self.icon_manager = IconManager()

        # 初始化设置收集器
        self._settings_collector = SettingsCollector(self.settings)

        # 标签页实例字典
        self._tabs: Dict[str, object] = {}

        self._init_ui()

    # ═══════════════════════════════════════════════════════
    #  UI 组装
    # ═══════════════════════════════════════════════════════

    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 10, 15, 10)
        main_layout.setSpacing(15)
        self.setLayout(main_layout)

        self._create_header(main_layout)

        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.tab_widget = VerticalTabWidget()

        # 构建 callbacks 字典（按钮动作 → SettingPage 方法）
        callbacks = self._build_callbacks()

        # 创建标签页
        self._tabs["basic"] = BasicSettingTab(callbacks)
        self._tabs["download"] = DownloadSettingTab(callbacks)
        self._tabs["interface"] = InterfaceSettingTab(callbacks)
        self._tabs["advanced"] = AdvancedSettingTab(callbacks)
        self._tabs["privacy"] = PrivacySettingTab(callbacks)

        # 添加到标签页控件
        tab_configs = [
            ("basic", _("settings.tabs.basic"), self._get_setting_icon_path("basic")),
            ("download", _("settings.tabs.download"), self._get_setting_icon_path("download")),
            ("interface", _("settings.tabs.interface"), self._get_setting_icon_path("appearance")),
            ("advanced", _("settings.tabs.advanced"), self._get_setting_icon_path("advanced")),
            ("privacy", _("settings.tabs.privacy"), self._get_setting_icon_path("privacy")),
        ]
        for key, label, icon in tab_configs:
            self.tab_widget.addTab(self._tabs[key], label, icon)

        content_layout.addWidget(self.tab_widget)
        main_layout.addLayout(content_layout)

        # 刷新各标签页 UI（从 settings 字典同步）
        self._refresh_all_tabs()

        self._connect_auto_save_signals()
        self._create_save_buttons(main_layout)

    def _build_callbacks(self) -> dict:
        """构建按钮动作回调字典，供标签页按钮绑定"""
        return {
            "browse_download_dir": self._browse_download_dir,
            "add_custom_domain": self._on_add_custom_domain,
            "remove_custom_domain": self._on_remove_custom_domain,
            "clear_custom_domains": self._on_clear_custom_domains,
            "theme_preset_selected": self._on_theme_preset_selected,
            "custom_theme_changed": self._on_custom_theme_changed,
            "browse_notification_sound": self._browse_notification_sound,
            "open_cloud_platform": self._open_cloud_platform,
            "clear_history": self._clear_history,
        }

    # ═══════════════════════════════════════════════════════
    #  头部 / 保存按钮
    # ═══════════════════════════════════════════════════════

    def _create_header(self, parent_layout):
        from gui.widgets.page_header import PageHeader

        header_container = QWidget()
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(15, 0, 0, 0)
        header_layout.setSpacing(0)
        header_container.setLayout(header_layout)

        self.header_widget, self.header_title, self.header_subtitle = PageHeader.create_header(
            parent_layout=header_layout,
            icon_manager=self.icon_manager,
            accent_color=primary_color(self._theme_config),
            icon_name="title_settings.svg",
            title_text=_("settings.title"),
            subtitle_text=_("settings.subtitle"),
            return_labels=True,
        )

        parent_layout.addWidget(header_container)

    def _create_save_buttons(self, parent_layout):
        button_frame = QWidget()
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(15, 5, 0, 5)
        button_frame.setLayout(button_layout)

        button_layout.addStretch()

        import_btn = MaterialButton(_("settings.common.import_button"), variant=MaterialButton.VARIANT_TONAL)
        import_btn.setAccentColor("#6C757D")
        import_btn.setFixedHeight(28)
        import_btn.setFixedWidth(100)
        import_btn.clicked.connect(self._import_config)
        button_layout.addWidget(import_btn)

        export_btn = MaterialButton(_("settings.common.export_button"), variant=MaterialButton.VARIANT_TONAL)
        export_btn.setAccentColor(primary_color(self._theme_config))
        export_btn.setFixedHeight(28)
        export_btn.setFixedWidth(100)
        export_btn.clicked.connect(self._export_config)
        button_layout.addWidget(export_btn)

        reset_btn = MaterialButton(_("settings.common.reset_button"), variant=MaterialButton.VARIANT_OUTLINED)
        reset_btn.setAccentColor("#DC3545")
        reset_btn.setFixedHeight(28)
        reset_btn.setFixedWidth(100)
        reset_btn.clicked.connect(self._reset_settings)
        button_layout.addWidget(reset_btn)

        self.save_btn = MaterialButton(_("settings.common.save_button"))
        self.save_btn.setAccentColor(primary_color(self._theme_config))
        self.save_btn.setFixedHeight(30)
        self.save_btn.setFixedWidth(110)
        self.save_btn.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_btn)

        parent_layout.addWidget(button_frame)

    # ═══════════════════════════════════════════════════════
    #  设置收集 / 保存 / 刷新
    # ═══════════════════════════════════════════════════════

    def _collect_settings(self):
        """遍历所有标签页收集设置"""
        # 先收集标签页的设置
        for tab in self._tabs.values():
            tab.collect_settings(self.settings)
        # 补充主题配置（由 SettingPage 管理）
        self.settings["theme_color"] = self._theme_config

    def _refresh_all_tabs(self):
        """遍历所有标签页刷新 UI"""
        for tab in self._tabs.values():
            tab.refresh_from(self.settings)
        # 更新分组标题颜色
        accent = primary_color(self._theme_config)
        if hasattr(self, "header_title"):
            self.header_title.setStyleSheet(f"color: {accent};")
        for tab in self._tabs.values():
            if hasattr(tab, "set_accent_color"):
                tab.set_accent_color(accent)
        # 同步侧边栏标签按钮主题色
        if hasattr(self, "tab_widget"):
            self.tab_widget.setAccentColor(accent)

    def _save_settings(self):
        """保存设置"""
        self._collect_settings()

        try:
            SettingsSaver.save_settings(self.settings)

            token = self.settings.get("access_token", "")
            save_msg = TokenManager.get_display_info(token)

            SettingsSaver.update_download_dir(self.settings, self.downloader)
            SettingsSaver.apply_proxy_to_downloader(self.settings, self.downloader)
            SettingsSaver.apply_clipboard_monitor_settings(self.settings)

            SettingsExporter.check_and_auto_export(self.settings)

            self.settings_saved.emit()
            QMessageBox.information(
                self, _("common.success"),
                _("settings.common.save_success").replace("{...}", "{}").format(save_msg)
            )
        except (IOError, OSError) as e:
            log("ERROR", f"保存设置失败（磁盘/权限错误）: {e}")
            QMessageBox.critical(
                self, _("settings.common.save_failed_title"),
                _("settings.common.save_disk_failed").replace("{...}", "{}").format(str(e))
            )
        except Exception as e:
            log("ERROR", f"保存设置失败: {e}")
            QMessageBox.critical(
                self, _("settings.common.save_failed_title"),
                _("settings.common.save_failed_message").replace("{...}", "{}").format(str(e))
            )

    def _auto_save_settings(self):
        """自动保存设置（由定时器调用）"""
        try:
            self._collect_settings()
            SettingsSaver.save_settings(self.settings)
            SettingsSaver.apply_proxy_to_downloader(self.settings, self.downloader)
            SettingsExporter.check_and_auto_export(self.settings)
            log("DEBUG", "设置已自动保存")
        except Exception as e:
            log("ERROR", f"自动保存失败: {e}")

    def _connect_auto_save_signals(self):
        """连接自动保存信号"""
        AutoSaveConnector.connect(self, lambda: self._auto_save_timer.start(2000))

    @staticmethod
    def load_settings() -> Dict[str, Any]:
        """加载设置"""
        from core.config.settings_manager import get_settings_manager
        return get_settings_manager().get_all()

    @staticmethod
    def load_access_token() -> str:
        """加载 Access Token"""
        return TokenManager.load_token()

    def _refresh_ui(self):
        """刷新 UI（重置等操作使用）"""
        self._refresh_all_tabs()

    # ═══════════════════════════════════════════════════════
    #  回调方法（供标签页按钮使用）
    # ═══════════════════════════════════════════════════════

    def _browse_download_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self, _("settings.common.select_download_dir"),
            self._tabs["download"].download_dir_input.text()
        )
        if dir_path:
            self._tabs["download"].download_dir_input.setText(dir_path)

    def _on_add_custom_domain(self):
        raw = self._tabs["download"].custom_domain_input.text() if hasattr(self._tabs["download"], "custom_domain_input") else ""
        domain = DomainManager.add_domain(raw, self._tabs["download"].custom_domain_list_widget)
        if domain is None:
            normalized = DomainManager.normalize_domain(raw)
            if not normalized or not DomainManager.is_valid_domain(normalized):
                QMessageBox.warning(self, _("common.tip"), _("settings.common.invalid_domain"))
            else:
                QMessageBox.information(
                    self, _("common.tip"),
                    _("settings.common.domain_already_exists_template").replace("{...}", "{}").format(normalized)
                )
            return
        self._tabs["download"].custom_domain_input.clear()
        log("INFO", f"已添加自定义下载域名: {domain}")

    def _on_remove_custom_domain(self):
        if not hasattr(self._tabs["download"], "custom_domain_list_widget"):
            return
        count = DomainManager.remove_selected(self._tabs["download"].custom_domain_list_widget)
        if count == 0:
            QMessageBox.information(self, _("common.tip"), _("settings.common.select_domain_first"))
        else:
            log("INFO", f"已移除 {count} 个自定义下载域名")

    def _on_clear_custom_domains(self):
        if not hasattr(self._tabs["download"], "custom_domain_list_widget"):
            return
        if self._tabs["download"].custom_domain_list_widget.count() == 0:
            return
        reply = QMessageBox.question(
            self, _("common.confirm"), _("settings.common.confirm_clear_custom_domains"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            DomainManager.clear_all(self._tabs["download"].custom_domain_list_widget)
            log("INFO", "已清空自定义下载域名列表")

    def _on_theme_preset_selected(self, config: Dict[str, Any]):
        """用户选择了某个主题预设"""
        self._theme_config = config
        self._apply_theme_config()

    def _on_custom_theme_changed(self, config: Dict[str, Any]):
        """用户调节了自定义主题参数"""
        self._theme_config = config
        self._apply_theme_config()

    def _apply_theme_config(self):
        """将当前主题配置应用到主窗口（避免重复调用）"""
        try:
            from core.config.settings_manager import get_settings_manager
            from core.config.theme_config import background_color

            # 静默保存设置（不触发信号，避免重复应用主题）
            mgr = get_settings_manager()
            mgr._settings["theme_color"] = self._theme_config
            mgr._pending_save = True
            mgr._save_timer.start(mgr._SAVE_DELAY_MS)

            # 直接应用主题色
            main_window = self.window()
            if main_window and hasattr(main_window, "settings_handler"):
                main_window.settings_handler.apply_theme_colors(
                    {"theme_color": self._theme_config}
                )

            accent = primary_color(self._theme_config)
            bg = background_color(self._theme_config)
            self.update_theme_colors(accent, bg)
        except Exception as e:
            log("ERROR", f"应用主题配置失败: {e}")

    def update_theme_colors(self, primary: str, background: str):
        """响应外部主题色变化，刷新设置页所有视觉元素。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        try:
            from gui.widgets.page_header import PageHeader

            if hasattr(self, "header_widget"):
                PageHeader.update_header(
                    self.header_widget,
                    self.icon_manager,
                    primary,
                    "title_settings.svg",
                )

            if hasattr(self, "tab_widget"):
                self.tab_widget.setAccentColor(primary)
                self.tab_widget.setBackgroundColor(background)

            if hasattr(self, "save_btn"):
                self.save_btn.setAccentColor(primary)
            if hasattr(self, "export_btn"):
                self.export_btn.setAccentColor(primary)

            for tab in self._tabs.values():
                if hasattr(tab, "update_theme_colors"):
                    tab.update_theme_colors(primary, background)
                elif hasattr(tab, "set_accent_color"):
                    tab.set_accent_color(primary)
        except Exception as e:
            log("ERROR", f"刷新设置页主题色失败: {e}")

    def _browse_notification_sound(self):
        file_path, _unused = QFileDialog.getOpenFileName(
            self, _("settings.common.select_sound_file"), "",
            _("settings.common.audio_filter")
        )
        if file_path:
            self._tabs["interface"].notification_sound_card.setText(file_path)

    def _open_cloud_platform(self):
        import webbrowser
        webbrowser.open("https://auth.smartedu.cn/uias/login")

    def _clear_history(self):
        reply = QMessageBox.question(
            self, _("common.confirm"), _("settings.common.confirm_clear_browsing_history"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            HistoryCleaner.clean_all()
            QMessageBox.information(
                self, _("common.success"), _("settings.common.history_cleared")
            )

    def _import_config(self):
        file_path, _unused = QFileDialog.getOpenFileName(
            self, _("settings.common.import_dialog_title"), "",
            _("settings.common.json_filter")
        )
        if file_path:
            if SettingsExporter.import_config(file_path, self.settings):
                self._refresh_ui()
                QMessageBox.information(
                    self, _("common.success"), _("settings.common.import_success")
                )
            else:
                QMessageBox.warning(
                    self, _("common.error"), _("settings.common.import_failed")
                )

    def _export_config(self):
        file_path, _unused = QFileDialog.getSaveFileName(
            self, _("settings.common.export_dialog_title"),
            "settings_backup.json", _("settings.common.json_filter")
        )
        if file_path:
            if SettingsExporter.export_config(file_path, self.settings):
                QMessageBox.information(
                    self, _("common.success"), _("settings.common.export_success")
                )
            else:
                QMessageBox.warning(
                    self, _("common.error"), _("settings.common.export_failed")
                )

    def _reset_settings(self):
        reply = QMessageBox.question(
            self, _("common.confirm"), _("settings.common.confirm_reset"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.settings = get_all_default_settings()
            self._refresh_ui()
            log("INFO", "设置已重置为默认值")
            QMessageBox.information(
                self, _("common.success"), _("settings.common.reset_success")
            )

    def save_access_token(self, token: str) -> str:
        """保存 Access Token"""
        return TokenManager.get_display_info(token)

    # ═══════════════════════════════════════════════════════
    #  Token 高亮（外部 navigation_manager 使用）
    # ═══════════════════════════════════════════════════════

    def highlight_token_input(self):
        """高亮 Access Token 输入框，引导用户输入"""
        privacy_tab = self._tabs.get("privacy")
        if not privacy_tab or not hasattr(privacy_tab, "token_input"):
            log("WARNING", "token_input 控件不存在")
            return

        # 切换到隐私与安全标签页
        if hasattr(self, "tab_widget"):
            self.tab_widget.setCurrentIndex(4)
            log("INFO", "已切换到隐私与安全标签页")

        token_input = privacy_tab.token_input.line_edit()

        # 高亮边框样式
        original_style = token_input.styleSheet()
        highlight_style = """
            LineEdit {
                border: 3px solid #FF6B35;
                border-radius: 6px;
                padding: 6px 10px;
                background: #FFF3E0;
            }
            LineEdit:focus {
                border-color: #FF6B35;
                background: #FFE0B2;
            }
        """
        token_input.setStyleSheet(highlight_style)
        token_input.setFocus()
        token_input.selectAll()

        self._token_input_original_style = original_style
        QTimer.singleShot(2000, self._restore_token_input_style)
        log("INFO", "已高亮 Access Token 输入框")

    def _restore_token_input_style(self):
        """恢复 Token 输入框的原始样式"""
        try:
            if not self or not self.isVisible():
                return
        except RuntimeError:
            return

        original_style = getattr(self, "_token_input_original_style", "")
        privacy_tab = self._tabs.get("privacy")
        if privacy_tab and hasattr(privacy_tab, "token_input"):
            privacy_tab.token_input.line_edit().setStyleSheet(original_style)
            log("DEBUG", "Token 输入框样式已恢复")

    # ═══════════════════════════════════════════════════════
    #  颜色按钮工具（供 interface tab 使用）
    # ═══════════════════════════════════════════════════════

    @staticmethod
    def _update_color_button(button, color):
        accent = load_primary_color()
        button.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                border-radius: 6px;
            }}
            QPushButton:hover {{
                border: 2px solid {accent};
            }}
        """)