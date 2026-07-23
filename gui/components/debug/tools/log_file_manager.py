# -*- coding: utf-8 -*-
"""
日志文件管理工具组件

提供日志文件查看、打开目录、归档日志和设置日志级别功能。
"""
from core.i18n import _
from core.infrastructure.logger import LOG_LEVEL_DEBUG, LOG_LEVEL_INFO, LOG_LEVEL_WARNING, LOG_LEVEL_ERROR

import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QMessageBox
from PyQt5.QtCore import Qt

from gui.fonts import body_font
from gui.widgets import NoWheelComboBox
from gui.widgets.material_button import MaterialButton
from gui.styles import load_primary_color
from core.infrastructure.path_resolver import get_logs_dir
from core.infrastructure.platform_utils import open_directory


class LogFileManagerWidget(QWidget):
    """日志文件管理工具组件"""

    def __init__(self, parent=None, show_title: bool = True):
        super().__init__(parent)
        self._show_title = show_title
        self._init_ui()
        self._refresh_log_info()

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        # 标题
        if self._show_title:
            title = QLabel(_("debug.tools.log.title"))
            title.setFont(body_font())
            title.setStyleSheet("font-weight: bold; color: #333;")
            layout.addWidget(title)

        # 日志大小显示
        self.log_size_label = QLabel(_("debug.tools.log.size_calculating"))
        self.log_size_label.setFont(body_font())
        self.log_size_label.setStyleSheet("color: #666;")
        layout.addWidget(self.log_size_label)

        # 日志级别设置
        level_layout = QHBoxLayout()
        level_layout.setSpacing(10)

        level_label = QLabel(_("settings.advanced.log_level"))
        level_label.setFont(body_font())
        level_layout.addWidget(level_label)

        self.level_combo = NoWheelComboBox()
        self.level_combo.setFont(body_font())
        self.level_combo.addItem(_("settings.advanced.debug_label"), LOG_LEVEL_DEBUG)
        self.level_combo.addItem(_("common.info_label"), LOG_LEVEL_INFO)
        self.level_combo.addItem(_("common.warning_label"), LOG_LEVEL_WARNING)
        self.level_combo.addItem(_("common.error_label"), LOG_LEVEL_ERROR)
        self.level_combo.setMinimumWidth(120)
        self.level_combo.currentIndexChanged.connect(self._on_level_changed)
        level_layout.addWidget(self.level_combo)
        level_layout.addStretch()

        layout.addLayout(level_layout)
        
        # 从设置读取主题色
        accent_color = load_primary_color()

        # 控制按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        open_dir_btn = MaterialButton(_("debug.tools.open_log_dir"), variant=MaterialButton.VARIANT_OUTLINED)
        open_dir_btn.setAccentColor(accent_color)
        open_dir_btn.setFixedHeight(32)
        open_dir_btn.clicked.connect(self._open_log_directory)

        archive_btn = MaterialButton(_("debug.tools.log.archive_current"), variant=MaterialButton.VARIANT_OUTLINED)
        archive_btn.setAccentColor("#28A745")
        archive_btn.setFixedHeight(32)
        archive_btn.clicked.connect(self._archive_log)

        refresh_btn = MaterialButton(_("common.refresh"), variant=MaterialButton.VARIANT_OUTLINED)
        refresh_btn.setAccentColor("#6C757D")
        refresh_btn.setFixedHeight(32)
        refresh_btn.clicked.connect(self._refresh_log_info)
        
        btn_layout.addWidget(open_dir_btn)
        btn_layout.addWidget(archive_btn)
        btn_layout.addWidget(refresh_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _refresh_log_info(self):
        """刷新日志信息"""
        try:
            log_dir = get_logs_dir()
            if not os.path.exists(log_dir):
                self.log_size_label.setText(_("debug.tools.log.size_no_dir"))
                return

            total_size = 0
            file_count = 0

            for item in os.listdir(log_dir):
                item_path = os.path.join(log_dir, item)
                if os.path.isfile(item_path):
                    try:
                        total_size += os.path.getsize(item_path)
                        file_count += 1
                    except OSError:
                        pass

            size_str = self._format_size(total_size)
            self.log_size_label.setText(_("debug.tools.log.size_template", size_str=size_str, file_count=file_count))

        except Exception as e:
            self.log_size_label.setText(_("debug.tools.log.size_failed_template", arg0=str(e)))
    
    def _format_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB']
        unit_index = 0
        size = float(size_bytes)
        
        while size >= 1024 and unit_index < len(units) - 1:
            size /= 1024
            unit_index += 1
        
        return f"{size:.2f} {units[unit_index]}"
    
    def _on_level_changed(self, _index):
        """日志级别改变"""
        try:
            from core.config.settings_manager import get_settings_manager
            sm = get_settings_manager()
            level = self.level_combo.currentData()
            sm.set("log_level", level)
            QMessageBox.information(self, _("common.success"), _("debug.tools.log.level_set_template", level=level))
        except Exception as e:
            QMessageBox.critical(self, _("common.error"), _("debug.tools.log.set_level_failed", error=str(e)))
    
    def _open_log_directory(self):
        """打开日志目录"""
        try:
            log_dir = get_logs_dir()
            if not open_directory(log_dir):
                QMessageBox.critical(
                    self,
                    _("common.error"),
                    _("debug.tools.log.open_log_dir_failed", error=_("common.open_failed")),
                )
        except Exception as e:
            QMessageBox.critical(self, _("common.error"), _("debug.tools.log.open_log_dir_failed", error=str(e)))

    def _archive_log(self):
        """归档当前日志"""
        try:
            log_dir = get_logs_dir()
            archive_dir = os.path.join(log_dir, 'archive')

            if not os.path.exists(archive_dir):
                os.makedirs(archive_dir)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"log_archive_{timestamp}"
            archive_path = os.path.join(archive_dir, archive_name)

            if os.path.exists(log_dir):
                shutil.copytree(log_dir, archive_path, ignore=shutil.ignore_patterns("archive"))
                QMessageBox.information(self, _("common.success"), _("debug.tools.log.archived_to", archive_path=archive_path))
                self._refresh_log_info()
            else:
                QMessageBox.warning(self, _("common.tip"), _("debug.tools.log.dir_not_exist"))

        except Exception as e:
            QMessageBox.critical(self, _("common.error"), _("debug.tools.log.archive_failed", error=str(e)))
