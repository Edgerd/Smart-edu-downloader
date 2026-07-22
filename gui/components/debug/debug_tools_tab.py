# -*- coding: utf-8 -*-
"""
调试工具标签页组件

以信息卡片形式组织多个调试工具区块，包括通知测试、变量监控、
性能分析、错误捕获以及网络诊断、缓存管理、日志管理和快捷操作。
"""

import sys
import os
import platform
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QListWidget, QListWidgetItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QGridLayout, QCheckBox, QMessageBox, QFileDialog,
)
from PyQt5.QtCore import Qt, QTimer

from gui.fonts import body_font, bold_font, monospace_font
from gui.widgets.custom_controls import ChineseLineEdit
from gui.widgets.material_button import MaterialButton
from gui.styles import get_fluent_table_style, load_primary_color
from gui.pages.settings.components.setting_group import SettingGroup
from core.infrastructure.logger import log
from core.i18n import _
from .tools import (
    NetworkDiagnosticWidget, CacheManagerWidget,
    LogFileManagerWidget, QuickActionsWidget, CrashTesterWidget,
)


class DebugToolsTab(QWidget):
    """调试工具标签页

    以信息卡片形式组织多个调试工具区块，便于统一主题色管理与视觉层次。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.monitored_variables = []
        self.error_history = []
        self._accent_color = load_primary_color()
        self._background_color = "transparent"
        self._init_ui()
        self._init_timers()

    def _init_ui(self):
        """初始化UI"""
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(15, 15, 15, 15)
        scroll_layout.setSpacing(12)

        self.notification_group = self._create_group(
            _("debug.tools.notification_test"),
            _("debug.tools.notification_test_desc"),
        )
        self.notification_group.add_widget(self._build_notification_widget())
        scroll_layout.addWidget(self.notification_group)

        self.variable_group = self._create_group(
            _("debug.tools.variable_monitor"),
            _("debug.tools.variable_monitor_desc"),
        )
        self.variable_group.add_widget(self._build_variable_monitor_widget())
        scroll_layout.addWidget(self.variable_group)

        self.performance_group = self._create_group(
            _("debug.tools.performance"),
            _("debug.tools.performance_desc"),
        )
        self.performance_group.add_widget(self._build_performance_widget())
        scroll_layout.addWidget(self.performance_group)

        self.error_group = self._create_group(
            _("debug.tools.error_capture"),
            _("debug.tools.error_capture_desc"),
        )
        self.error_group.add_widget(self._build_error_capture_widget())
        scroll_layout.addWidget(self.error_group)

        self.crash_test_group = self._create_group(
            _("debug.tools.crash_tester_title"),
            _("debug.tools.crash_tester_desc"),
        )
        self.crash_tester = CrashTesterWidget(show_title=False)
        self.crash_test_group.add_widget(self.crash_tester)
        scroll_layout.addWidget(self.crash_test_group)

        self.network_group = self._create_group(
            _("debug.tools.network_diagnostic"),
            _("debug.tools.network_diagnostic_desc"),
        )
        self.network_diagnostic = NetworkDiagnosticWidget(show_title=False)
        self.network_group.add_widget(self.network_diagnostic)
        scroll_layout.addWidget(self.network_group)

        self.cache_group = self._create_group(
            _("debug.tools.cache_manager"),
            _("debug.tools.cache_manager_desc"),
        )
        self.cache_manager = CacheManagerWidget(show_title=False)
        self.cache_group.add_widget(self.cache_manager)
        scroll_layout.addWidget(self.cache_group)

        self.log_group = self._create_group(
            _("debug.tools.log_manager"),
            _("debug.tools.log_manager_desc"),
        )
        self.log_file_manager = LogFileManagerWidget(show_title=False)
        self.log_group.add_widget(self.log_file_manager)
        scroll_layout.addWidget(self.log_group)

        self.quick_group = self._create_group(
            _("debug.tools.quick_actions"),
            _("debug.tools.quick_actions_desc"),
        )
        self.quick_actions = QuickActionsWidget(show_title=False)
        self.quick_group.add_widget(self.quick_actions)
        scroll_layout.addWidget(self.quick_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        self._install_exception_hook()
        QTimer.singleShot(100, self._refresh_performance)

    def _create_group(self, title: str, desc: str = "") -> SettingGroup:
        """创建带描述的设置分组卡片。

        Args:
            title: 分组标题。
            desc: 分组简介，为空时不显示。

        Returns:
            SettingGroup: 创建好的分组容器。
        """
        group = SettingGroup(title, self._accent_color, self)
        if desc:
            desc_label = QLabel(desc)
            desc_label.setFont(body_font())
            desc_label.setStyleSheet("color: #888888; background: transparent;")
            desc_label.setWordWrap(True)
            group.add_widget(desc_label)
        return group

    def _init_timers(self):
        """初始化工具定时器"""
        self.var_monitor_timer = QTimer(self)
        self.var_monitor_timer.timeout.connect(self._refresh_variable_monitor)
        self.var_monitor_timer.setInterval(2000)
        self.perf_timer = QTimer(self)
        self.perf_timer.timeout.connect(self._refresh_performance)
        self.perf_timer.setInterval(3000)

    def _build_notification_widget(self):
        """构建通知测试内容"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(10)
        accent_color = self._accent_color

        self.notify_btn_tl = MaterialButton(
            _("debug.tools.notify_top_left"),
            variant=MaterialButton.VARIANT_OUTLINED,
        )
        self.notify_btn_tl.setAccentColor(accent_color)
        self.notify_btn_tl.setFixedHeight(40)
        self.notify_btn_tl.clicked.connect(
            lambda: self._test_notification(
                _("common.top_left"),
                _("gui.components.debug.debug_tools_tab.auto_012"),
                _("gui.components.debug.debug_tools_tab.auto_019"),
            )
        )
        grid_layout.addWidget(self.notify_btn_tl, 0, 0)

        self.notify_btn_tr = MaterialButton(
            _("debug.tools.notify_top_right"),
            variant=MaterialButton.VARIANT_OUTLINED,
        )
        self.notify_btn_tr.setAccentColor(accent_color)
        self.notify_btn_tr.setFixedHeight(40)
        self.notify_btn_tr.clicked.connect(
            lambda: self._test_notification(
                _("common.top_right"),
                _("gui.components.debug.debug_tools_tab.auto_010"),
                _("gui.components.debug.debug_tools_tab.auto_019"),
            )
        )
        grid_layout.addWidget(self.notify_btn_tr, 0, 1)

        self.notify_btn_bl = MaterialButton(
            _("debug.tools.notify_bottom_left"),
            variant=MaterialButton.VARIANT_OUTLINED,
        )
        self.notify_btn_bl.setAccentColor(accent_color)
        self.notify_btn_bl.setFixedHeight(40)
        self.notify_btn_bl.clicked.connect(
            lambda: self._test_notification(
                _("common.bottom_left"),
                _("gui.components.debug.debug_tools_tab.auto_013"),
                _("gui.components.debug.debug_tools_tab.auto_019"),
            )
        )
        grid_layout.addWidget(self.notify_btn_bl, 1, 0)

        self.notify_btn_br = MaterialButton(
            _("debug.tools.notify_bottom_right"),
            variant=MaterialButton.VARIANT_OUTLINED,
        )
        self.notify_btn_br.setAccentColor(accent_color)
        self.notify_btn_br.setFixedHeight(40)
        self.notify_btn_br.clicked.connect(
            lambda: self._test_notification(
                _("common.bottom_right"),
                _("gui.components.debug.debug_tools_tab.auto_011"),
                _("gui.components.debug.debug_tools_tab.auto_019"),
            )
        )
        grid_layout.addWidget(self.notify_btn_br, 1, 1)

        layout.addLayout(grid_layout)

        hint_label = QLabel(_("debug.tools.notification_hint"))
        hint_label.setFont(body_font())
        hint_label.setStyleSheet("color: #888;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        return container

    def _build_variable_monitor_widget(self):
        """构建变量监控内容"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        input_layout = QHBoxLayout()
        input_layout.setSpacing(10)
        accent_color = self._accent_color

        self.var_input = ChineseLineEdit()
        self.var_input.setFont(body_font())
        self.var_input.setPlaceholderText(_("debug.tools.variable_input_hint"))
        self.var_input.setStyleSheet(self._get_input_style(accent_color))
        input_layout.addWidget(self.var_input)

        self.add_var_btn = MaterialButton(_("debug.tools.add_monitor"))
        self.add_var_btn.setAccentColor(accent_color)
        self.add_var_btn.setFixedHeight(36)
        self.add_var_btn.clicked.connect(self._add_variable_to_monitor)
        input_layout.addWidget(self.add_var_btn)

        layout.addLayout(input_layout)

        self.var_monitor_list = QListWidget()
        self.var_monitor_list.setFont(body_font())
        self.var_monitor_list.setStyleSheet(self._get_list_style())
        self.var_monitor_list.setMaximumHeight(150)
        layout.addWidget(self.var_monitor_list)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        self.var_monitor_toggle_btn = MaterialButton(_("debug.tools.start_monitor"))
        self.var_monitor_toggle_btn.setAccentColor("#28A745")
        self.var_monitor_toggle_btn.setFixedHeight(32)
        self.var_monitor_toggle_btn.setCheckable(True)
        self.var_monitor_toggle_btn.setChecked(False)
        self.var_monitor_toggle_btn.clicked.connect(self._toggle_variable_monitor)

        remove_var_btn = MaterialButton(
            _("debug.tools.remove_selected"),
            variant=MaterialButton.VARIANT_OUTLINED,
        )
        remove_var_btn.setAccentColor("#DC3545")
        remove_var_btn.setFixedHeight(32)
        remove_var_btn.clicked.connect(self._remove_selected_variable)

        control_layout.addWidget(self.var_monitor_toggle_btn)
        control_layout.addWidget(remove_var_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        return container

    def _build_performance_widget(self):
        """构建性能分析内容"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.perf_table = QTableWidget()
        self.perf_table.setColumnCount(2)
        self.perf_table.setHorizontalHeaderLabels([
            _("debug.tools.performance_header_metric"),
            _("debug.tools.performance_header_current"),
        ])
        self.perf_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.perf_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.perf_table.verticalHeader().setVisible(False)
        self.perf_table.setAlternatingRowColors(True)
        self.perf_table.setFont(body_font())
        self.perf_table.setStyleSheet(get_fluent_table_style())
        self.perf_table.setMaximumHeight(200)
        from core.ui.scroll_isolation import install_scroll_isolation
        install_scroll_isolation(self.perf_table)
        layout.addWidget(self.perf_table)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        refresh_perf_btn = MaterialButton(
            _("debug.tools.refresh_now"),
            variant=MaterialButton.VARIANT_OUTLINED,
        )
        refresh_perf_btn.setAccentColor("#6C757D")
        refresh_perf_btn.setFixedHeight(32)
        refresh_perf_btn.clicked.connect(self._refresh_performance)

        self.perf_auto_toggle_btn = MaterialButton(
            _("debug.tools.auto_refresh_off"),
            variant=MaterialButton.VARIANT_OUTLINED,
        )
        self.perf_auto_toggle_btn.setAccentColor("#6C757D")
        self.perf_auto_toggle_btn.setFixedHeight(32)
        self.perf_auto_toggle_btn.setCheckable(True)
        self.perf_auto_toggle_btn.setChecked(False)
        self.perf_auto_toggle_btn.clicked.connect(self._toggle_perf_auto_refresh)

        control_layout.addWidget(refresh_perf_btn)
        control_layout.addWidget(self.perf_auto_toggle_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        return container

    def _build_error_capture_widget(self):
        """构建错误捕获内容"""
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self.error_count_label = QLabel(_("debug.tools.errors_zero"))
        self.error_count_label.setFont(bold_font())
        self.error_count_label.setStyleSheet("color: #EF5350;")
        layout.addWidget(self.error_count_label)

        self.error_list = QListWidget()
        self.error_list.setFont(body_font())
        self.error_list.setStyleSheet(self._get_list_style())
        self.error_list.setMaximumHeight(200)
        self.error_list.itemDoubleClicked.connect(self._show_error_detail)
        layout.addWidget(self.error_list)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        clear_errors_btn = MaterialButton(_("debug.tools.clear_history"))
        clear_errors_btn.setAccentColor("#DC3545")
        clear_errors_btn.setFixedHeight(32)
        clear_errors_btn.clicked.connect(self._clear_error_history)

        export_errors_btn = MaterialButton(_("debug.tools.export_error_title"))
        export_errors_btn.setAccentColor("#28A745")
        export_errors_btn.setFixedHeight(32)
        export_errors_btn.clicked.connect(self._export_error_history)

        control_layout.addWidget(clear_errors_btn)
        control_layout.addWidget(export_errors_btn)
        control_layout.addStretch()
        layout.addLayout(control_layout)
        return container

    def _get_input_style(self, accent_color: str) -> str:
        """返回统一输入框样式。"""
        return f"""
            QLineEdit {{
                background: #F8FAFC;
                border: 1px solid #E0E8F0;
                border-radius: 4px;
                padding: 8px;
            }}
            QLineEdit:focus {{
                border-color: {accent_color};
                background: white;
            }}
        """

    def _get_list_style(self) -> str:
        """返回统一列表样式。"""
        return """
            QListWidget {
                background: transparent;
                border: 1px solid #E0E8F0;
                border-radius: 4px;
                padding: 4px;
            }
        """

    def _test_notification(self, position, title, message):
        """测试通知弹窗"""
        from core.config.settings_manager import get_settings_manager
        sm = get_settings_manager()
        original_position = sm.get("notification_position", _("common.top_right"))
        sm.set("notification_position", position)
        duration_seconds = sm.get("notification_duration", 5)
        duration_ms = duration_seconds * 1000
        from gui.widgets.notification_widget import show_notification
        show_notification(title, message, duration_ms)
        restore_delay = duration_ms + 500
        QTimer.singleShot(restore_delay, lambda: sm.set("notification_position", original_position))

    def _add_variable_to_monitor(self):
        """添加变量到监控列表"""
        var_name = self.var_input.text().strip()
        if not var_name:
            QMessageBox.warning(self, _("common.tip"), _("debug.tools.enter_variable_name"))
            return
        if var_name in [v[0] for v in self.monitored_variables]:
            QMessageBox.warning(
                self, _("common.tip"),
                _("debug.tools.variable_already_monitored_template", var_name=var_name),
            )
            return
        self.monitored_variables.append((var_name, _("gui.components.debug.debug_tools_tab.auto_006")))
        self.var_input.clear()
        self._refresh_variable_monitor()

    def _refresh_variable_monitor(self):
        """刷新变量监控显示"""
        self.var_monitor_list.clear()
        for var_name, _unused in self.monitored_variables:
            try:
                var_value = self._evaluate_variable(var_name)
                value_str = str(var_value)[:100]
            except Exception as e:
                value_str = f"{_('gui.components.debug.debug_tools_tab.fstr_004')}{e}>"
            item_text = f"{var_name} = {value_str}"
            item = QListWidgetItem(item_text)
            self.var_monitor_list.addItem(item)

    def _evaluate_variable(self, var_name):
        """求值变量"""
        safe_globals = {
            "__builtins__": {
                "len": len, "str": str, "int": int, "float": float,
                "list": list, "dict": dict, "type": type, "print": print,
            }
        }
        try:
            from gui.main_window import get_main_window
            main_window = get_main_window()
            if main_window:
                safe_globals["main_window"] = main_window
                safe_globals["self"] = main_window
        except Exception:
            pass
        return eval(var_name, safe_globals)

    def _toggle_variable_monitor(self):
        """切换变量监控"""
        is_checked = self.var_monitor_toggle_btn.isChecked()
        if is_checked:
            self.var_monitor_timer.start()
            self.var_monitor_toggle_btn.setText(_("debug.tools.stop_monitor"))
            self.var_monitor_toggle_btn.setAccentColor("#DC3545")
        else:
            self.var_monitor_timer.stop()
            self.var_monitor_toggle_btn.setText(_("debug.tools.start_monitor"))
            self.var_monitor_toggle_btn.setAccentColor("#28A745")

    def _remove_selected_variable(self):
        """移除选中的监控变量"""
        current_row = self.var_monitor_list.currentRow()
        if current_row < 0 or current_row >= len(self.monitored_variables):
            QMessageBox.warning(self, _("common.tip"), _("debug.tools.select_variable_first"))
            return
        self.monitored_variables.pop(current_row)
        self.var_monitor_list.takeItem(current_row)

    def _refresh_performance(self):
        """刷新性能数据"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / (1024 * 1024)
            cpu_percent = process.cpu_percent(interval=0.1)
            threads = process.num_threads()
        except ImportError:
            memory_mb = 0
            cpu_percent = 0
            threads = 0
        try:
            import psutil
            system_memory = psutil.virtual_memory()
            system_memory_percent = system_memory.percent
            system_memory_available = system_memory.available / (1024 * 1024 * 1024)
        except ImportError:
            system_memory_percent = 0
            system_memory_available = 0

        self.perf_table.setRowCount(6)
        perf_data = [
            (_("gui.components.debug.debug_tools_tab.auto_022"), f"{memory_mb:.1f} MB"),
            (_("gui.components.debug.debug_tools_tab.auto_021"), f"{cpu_percent:.1f}%"),
            (_("gui.components.debug.debug_tools_tab.auto_018"), f"{threads}"),
            (_("gui.components.debug.debug_tools_tab.auto_016"), f"{system_memory_percent:.1f}%"),
            (_("gui.components.debug.debug_tools_tab.auto_017"), f"{system_memory_available:.1f} GB"),
            (_("gui.components.debug.debug_tools_tab.auto_009"), datetime.now().strftime("%H:%M:%S")),
        ]
        for row, (metric, value) in enumerate(perf_data):
            self.perf_table.setItem(row, 0, QTableWidgetItem(metric))
            self.perf_table.setItem(row, 1, QTableWidgetItem(value))
            if "CPU" in metric and float(value.replace("%", "")) > 80:
                self.perf_table.item(row, 1).setBackground(Qt.red)
            elif (
                _("gui.components.debug.debug_tools_tab.auto_005") in metric
                and _("gui.components.debug.debug_tools_tab.auto_020") in metric
                and (float(value.replace(" MB", "")) > 500)
            ):
                self.perf_table.item(row, 1).setBackground(Qt.yellow)

    def _toggle_perf_auto_refresh(self):
        """切换性能自动刷新"""
        is_checked = self.perf_auto_toggle_btn.isChecked()
        if is_checked:
            self.perf_timer.start()
            self.perf_auto_toggle_btn.setText(_("debug.tools.auto_refresh_on"))
            self.perf_auto_toggle_btn.setAccentColor("#28A745")
        else:
            self.perf_timer.stop()
            self.perf_auto_toggle_btn.setText(_("debug.tools.auto_refresh_off"))
            self.perf_auto_toggle_btn.setAccentColor("#6C757D")

    def _install_exception_hook(self):
        """安装全局异常钩子"""
        self._original_excepthook = sys.excepthook
        sys.excepthook = self._global_exception_handler

    def _global_exception_handler(self, exc_type, exc_value, exc_traceback):
        """全局异常处理"""
        import traceback
        if issubclass(exc_type, KeyboardInterrupt):
            self._original_excepthook(exc_type, exc_value, exc_traceback)
            return
        tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        error_entry = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "type": exc_type.__name__,
            "message": str(exc_value),
            "traceback": tb_str,
        }
        self.error_history.append(error_entry)
        self._update_error_display()
        self._original_excepthook(exc_type, exc_value, exc_traceback)

    def _update_error_display(self):
        """更新错误显示"""
        self.error_list.clear()
        for error in self.error_history:
            item_text = f"[{error['time']}] {error['type']}: {error['message'][:80]}"
            item = QListWidgetItem(item_text)
            item.setForeground(Qt.red)
            self.error_list.addItem(item)
        self.error_count_label.setText(_("debug.tools.errors_template", arg0=len(self.error_history)))

    def _show_error_detail(self, item):
        """显示错误详情"""
        row = self.error_list.row(item)
        if 0 <= row < len(self.error_history):
            error = self.error_history[row]
            detail = (
                f"{_('gui.components.debug.debug_tools_tab.fstr_006')}{error['time']}"
                f"{_('gui.components.debug.debug_tools_tab.fstr_003')}{error['type']}"
                f"{_('gui.components.debug.debug_tools_tab.fstr_002')}{error['message']}"
                f"{_('gui.components.debug.debug_tools_tab.fstr_001')}{error['traceback']}"
            )
            QMessageBox.information(self, _("debug.tools.error_details"), detail)

    def _clear_error_history(self):
        """清除错误历史"""
        self.error_history.clear()
        self.error_list.clear()

    def _export_error_history(self):
        """导出错误历史"""
        if not self.error_history:
            QMessageBox.information(self, _("common.tip"), _("debug.tools.no_errors_to_export"))
            return
        file_path, _unused = QFileDialog.getSaveFileName(
            self,
            _("debug.tools.export_errors"),
            f"error_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            _("debug.log_tab.text_filter"),
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    for error in self.error_history:
                        f.write("=" * 60 + "\n")
                        f.write(f"{_('gui.components.debug.debug_tools_tab.fstr_006')}{error['time']}\n")
                        f.write(f"{_('gui.components.debug.debug_tools_tab.fstr_008')}{error['type']}\n")
                        f.write(f"{_('gui.components.debug.debug_tools_tab.fstr_007')}{error['message']}\n")
                        f.write(f"{_('gui.components.debug.debug_tools_tab.fstr_005')}{error['traceback']}\n")
                        f.write("=" * 60 + "\n\n")
                QMessageBox.information(
                    self, _("common.success"),
                    _("debug.tools.errors_exported_to", file_path=file_path),
                )
            except Exception as e:
                QMessageBox.critical(self, _("common.error"), _("debug.tools.export_failed", error=str(e)))

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新调试工具标签页视觉元素。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        self._accent_color = primary
        self._background_color = background
        self.setStyleSheet("background: transparent;")

        for group in (
            self.notification_group, self.variable_group,
            self.performance_group, self.error_group,
            self.crash_test_group, self.network_group,
            self.cache_group, self.log_group, self.quick_group,
        ):
            if group is not None and hasattr(group, "update_accent_color"):
                group.update_accent_color(primary)

        for btn in (
            getattr(self, "notify_btn_tl", None),
            getattr(self, "notify_btn_tr", None),
            getattr(self, "notify_btn_bl", None),
            getattr(self, "notify_btn_br", None),
        ):
            if btn is not None:
                btn.setAccentColor(primary)

        if hasattr(self, "add_var_btn"):
            self.add_var_btn.setAccentColor(primary)

        if hasattr(self, "var_input"):
            self.var_input.setStyleSheet(self._get_input_style(primary))

        list_style = self._get_list_style()
        if hasattr(self, "var_monitor_list"):
            self.var_monitor_list.setStyleSheet(list_style)
        if hasattr(self, "error_list"):
            self.error_list.setStyleSheet(list_style)

        if hasattr(self, "perf_table"):
            self.perf_table.setStyleSheet(get_fluent_table_style(primary))

        for widget in (
            self.network_diagnostic, self.cache_manager,
            self.log_file_manager, self.quick_actions,
        ):
            if hasattr(widget, "update_theme_colors"):
                try:
                    widget.update_theme_colors(primary, background)
                except Exception as e:
                    log("WARNING", f"调试工具子控件 {type(widget).__name__} 主题色更新失败: {e}")
