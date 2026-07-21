# -*- coding: utf-8 -*-
"""
日志标签页组件

提供日志显示、过滤和导出功能。
"""

from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QCheckBox, QFileDialog, QMessageBox)
from PyQt5.QtCore import Qt

from gui.fonts import monospace_font, body_font
from gui.styles import load_primary_color
from gui.widgets.material_button import MaterialButton
from gui.widgets import CustomContextMenu
from core.i18n import _


class LogTab(QWidget):
    """日志标签页
    
    提供日志显示、过滤和导出功能。
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 日志数据
        self.logs = []
        self.max_logs = 1000
        self.auto_scroll = True
        self.log_filters = {}
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # 工具栏
        toolbar_layout = QHBoxLayout()
        
        # 清空按钮
        self.clear_btn = MaterialButton(_("common.clear"))
        self.clear_btn.setAccentColor("#DC3545")
        self.clear_btn.setFixedHeight(32)
        self.clear_btn.clicked.connect(self.clear_logs)
        toolbar_layout.addWidget(self.clear_btn)
        
        # 导出按钮
        self.export_btn = MaterialButton(_("debug.log_tab.export_log"))
        self.export_btn.setAccentColor(self._accent_color if hasattr(self, '_accent_color') else load_primary_color())
        self.export_btn.setFixedHeight(32)
        self.export_btn.clicked.connect(self.export_logs)
        toolbar_layout.addWidget(self.export_btn)
        
        # 自动滚动按钮
        self.toggle_auto_scroll_btn = MaterialButton(_("debug.log_tab.auto_scroll_on"))
        self.toggle_auto_scroll_btn.setAccentColor("#6C757D")
        self.toggle_auto_scroll_btn.setFixedHeight(32)
        self.toggle_auto_scroll_btn.setCheckable(True)
        self.toggle_auto_scroll_btn.setChecked(True)
        self.toggle_auto_scroll_btn.clicked.connect(self._toggle_auto_scroll)
        toolbar_layout.addWidget(self.toggle_auto_scroll_btn)
        
        toolbar_layout.addStretch()
        layout.addLayout(toolbar_layout)
        
        # 日志过滤区域
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(15)
        
        # 日志级别复选框
        self.log_filters = {
            "INFO": QCheckBox("INFO"),
            "WARNING": QCheckBox("WARNING"),
            "ERROR": QCheckBox("ERROR"),
            "DEBUG": QCheckBox("DEBUG"),
            "SUCCESS": QCheckBox("SUCCESS")
        }
        
        filter_colors = {
            "INFO": "#4FC3F7",
            "WARNING": "#FFB74D",
            "ERROR": "#EF5350",
            "DEBUG": "#BDBDBD",
            "SUCCESS": "#66BB6A"
        }
        
        for level, checkbox in self.log_filters.items():
            checkbox.setFont(body_font())
            checkbox.setChecked(True)
            color = filter_colors[level]
            checkbox.setStyleSheet(f"""
                QCheckBox {{ color: {color}; }}
                QCheckBox::indicator {{
                    width: 16px;
                    height: 16px;
                    border: 2px solid {color};
                    border-radius: 3px;
                }}
                QCheckBox::indicator:checked {{
                    background: {color};
                }}
            """)
            checkbox.stateChanged.connect(self._apply_log_filter)
            filter_layout.addWidget(checkbox)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # 快捷操作按钮
        quick_btn_layout = QHBoxLayout()
        quick_btn_layout.setSpacing(10)
        
        select_all_btn = MaterialButton(_("widgets.controls.select_all"))
        select_all_btn.setAccentColor("#28A745")
        select_all_btn.setFixedHeight(30)
        select_all_btn.clicked.connect(self._select_all_log_levels)
        quick_btn_layout.addWidget(select_all_btn)
        
        deselect_all_btn = MaterialButton(_("common.select_none"), variant=MaterialButton.VARIANT_OUTLINED)
        deselect_all_btn.setAccentColor("#6C757D")
        deselect_all_btn.setFixedHeight(30)
        deselect_all_btn.clicked.connect(self._deselect_all_log_levels)
        quick_btn_layout.addWidget(deselect_all_btn)
        
        error_only_btn = MaterialButton(_("debug.log_tab.only_error"))
        error_only_btn.setAccentColor("#EF5350")
        error_only_btn.setFixedHeight(30)
        error_only_btn.clicked.connect(self._error_only_log_level)
        quick_btn_layout.addWidget(error_only_btn)
        
        quick_btn_layout.addStretch()
        layout.addLayout(quick_btn_layout)
        
        # 日志显示区域
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(monospace_font())
        self.log_text.setStyleSheet("""
            QTextEdit {
                background: #1E1E1E;
                color: #D4D4D4;
                border: 1px solid #3D3D3D;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        CustomContextMenu.setup_for_text_edit(self.log_text, monospace_font())
        
        layout.addWidget(self.log_text)
    
    def log(self, message: str, level: str = "INFO"):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        colors = {
            "INFO": "#4FC3F7",
            "WARNING": "#FFB74D",
            "ERROR": "#EF5350",
            "SUCCESS": "#66BB6A",
            "DEBUG": "#BDBDBD"
        }
        color = colors.get(level, "#D4D4D4")
        
        self.logs.append({
            "timestamp": timestamp,
            "level": level,
            "message": message,
            "full": f"[{timestamp}] [{level}] {message}"
        })
        
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)
        
        # 检查是否启用过滤
        if self.log_filters:
            active_levels = {lvl for lvl, cb in self.log_filters.items() if cb.isChecked()}
            if level not in active_levels:
                return
        
        formatted_msg = f'<span style="color: #888;">[{timestamp}]</span> <span style="color: {color};">[{level}]</span> {message}'
        self.log_text.append(formatted_msg)
        
        if self.auto_scroll:
            self.log_text.ensureCursorVisible()
    
    def clear_logs(self):
        """清空日志"""
        self.logs.clear()
        self.log_text.clear()
        self.log(_('gui.pages.log_tab.log_cleared'), "INFO")
    
    def export_logs(self):
        """导出日志"""
        if not self.logs:
            QMessageBox.warning(self, _("common.tip"), _("debug.log_tab.no_log_to_export"))
            return
        
        file_path, _unused = QFileDialog.getSaveFileName(
            self, _("debug.log_tab.export_log"),
            f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            _("debug.log_tab.text_filter")
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for log in self.logs:
                        f.write(log["full"] + "\n")
                QMessageBox.information(self, _("common.success"), _("debug.log_tab.exported_to", file_path=(file_path)))
                self.log(f"日志已导出到: {file_path}", "SUCCESS")
            except Exception as e:
                QMessageBox.critical(self, _("common.error"), _("debug.log_tab.export_failed", error=str(e)))
                self.log(f"导出日志失败: {e}", "ERROR")
    
    def _toggle_auto_scroll(self):
        """切换自动滚动"""
        self.auto_scroll = not self.auto_scroll
        self.toggle_auto_scroll_btn.setText(_("debug.log_tab.auto_scroll_template", arg0=('开' if self.auto_scroll else '关')))
    
    def _apply_log_filter(self):
        """应用日志过滤"""
        active_levels = {level for level, cb in self.log_filters.items() if cb.isChecked()}
        
        self.log_text.clear()
        for log_entry in self.logs:
            if log_entry["level"] in active_levels:
                colors = {
                    "INFO": "#4FC3F7",
                    "WARNING": "#FFB74D",
                    "ERROR": "#EF5350",
                    "SUCCESS": "#66BB6A",
                    "DEBUG": "#BDBDBD"
                }
                color = colors.get(log_entry["level"], "#D4D4D4")
                formatted_msg = (
                    f'<span style="color: #888;">[{log_entry["timestamp"]}]</span> '
                    f'<span style="color: {color};">[{log_entry["level"]}]</span> '
                    f'{log_entry["message"]}'
                )
                self.log_text.append(formatted_msg)
        
        if self.auto_scroll:
            self.log_text.ensureCursorVisible()
    
    def _select_all_log_levels(self):
        """全选所有日志级别"""
        for cb in self.log_filters.values():
            cb.setChecked(True)
        self._apply_log_filter()
    
    def _deselect_all_log_levels(self):
        """取消全选日志级别"""
        for cb in self.log_filters.values():
            cb.setChecked(False)
        self._apply_log_filter()
    
    def _error_only_log_level(self):
        """仅显示ERROR"""
        for level, cb in self.log_filters.items():
            cb.setChecked(level == "ERROR")
        self._apply_log_filter()
