# -*- coding: utf-8 -*-
"""
缓存管理工具组件

提供缓存大小查看、清除缓存、缓存文件列表和缓存配置功能。
"""

import os
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QGroupBox, QListWidget, QListWidgetItem,
                             QMessageBox)
from PyQt5.QtCore import Qt, QTimer

from gui.fonts import body_font, small_font
from gui.widgets.material_button import MaterialButton
from core.i18n import _
from core.infrastructure.path_resolver import get_cache_dir, get_temp_dir


class CacheManagerWidget(QWidget):
    """缓存管理工具组件"""
    
    def __init__(self, parent=None, show_title: bool = True):
        super().__init__(parent)
        self._show_title = show_title
        self._init_ui()
        QTimer.singleShot(100, self._refresh_cache_info)
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 标题
        if self._show_title:
            title = QLabel(_("debug.tools.cache.title"))
            title.setFont(body_font())
            title.setStyleSheet("font-weight: bold; color: #333;")
            layout.addWidget(title)
        
        # 缓存大小显示
        self.cache_size_label = QLabel(_("debug.tools.cache.size_calculating"))
        self.cache_size_label.setFont(body_font())
        self.cache_size_label.setStyleSheet("color: #666;")
        layout.addWidget(self.cache_size_label)
        
        # 缓存文件列表
        self.cache_list = QListWidget()
        self.cache_list.setFont(small_font())
        self.cache_list.setStyleSheet("""
            QListWidget {
                background: transparent;
                border: 1px solid #E0E8F0;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        self.cache_list.setMaximumHeight(200)
        layout.addWidget(self.cache_list)
        
        # 控制按钮
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        refresh_btn = MaterialButton(_("common.refresh"), variant=MaterialButton.VARIANT_OUTLINED)
        refresh_btn.setAccentColor("#6C757D")
        refresh_btn.setFixedHeight(32)
        refresh_btn.clicked.connect(self._refresh_cache_info)
        
        clear_btn = MaterialButton(_("debug.tools.cache.clear_button"))
        clear_btn.setAccentColor("#DC3545")
        clear_btn.setFixedHeight(32)
        clear_btn.clicked.connect(self._clear_cache)
        
        btn_layout.addWidget(refresh_btn)
        btn_layout.addWidget(clear_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
    
    def _refresh_cache_info(self):
        """刷新缓存信息"""
        try:
            cache_dirs = self._get_cache_directories()
            total_size = 0
            file_count = 0
            
            self.cache_list.clear()
            
            for cache_dir in cache_dirs:
                if os.path.exists(cache_dir):
                    dir_size, dir_files = self._calculate_dir_size(cache_dir)
                    total_size += dir_size
                    file_count += dir_files
                    
                    if dir_files > 0:
                        item = QListWidgetItem(_("debug.tools.cache.file_item_template", cache_dir=cache_dir, arg1=self._format_size(dir_size), dir_files=dir_files))
                        self.cache_list.addItem(item)
            
            self.cache_size_label.setText(_("debug.tools.cache.size_template", arg0=self._format_size(total_size), file_count=file_count))
            
        except Exception as e:
            self.cache_size_label.setText(_("debug.tools.cache.size_failed_template", arg0=str(e)))
    
    def _get_cache_directories(self):
        """获取缓存目录列表"""
        cache_dirs = []

        # 封面缓存
        cover_cache = os.path.join(get_temp_dir(), 'covers')
        if os.path.exists(cover_cache):
            cache_dirs.append(cover_cache)

        # 资源缓存
        resource_cache = get_cache_dir()
        if os.path.exists(resource_cache):
            cache_dirs.append(resource_cache)

        # 临时文件
        temp_dir = get_temp_dir()
        if os.path.exists(temp_dir):
            cache_dirs.append(temp_dir)

        return cache_dirs
    
    def _calculate_dir_size(self, directory):
        """计算目录大小和文件数"""
        total_size = 0
        file_count = 0
        
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        total_size += os.path.getsize(fp)
                        file_count += 1
                    except OSError:
                        pass
        except Exception:
            pass
        
        return total_size, file_count
    
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
    
    def _clear_cache(self):
        """清除缓存"""
        reply = QMessageBox.question(
            self, _("debug.tools.cache.confirm_clear_title"),
            _("debug.tools.cache.confirm_clear_message"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                cache_dirs = self._get_cache_directories()
                cleared_count = 0
                
                for cache_dir in cache_dirs:
                    if os.path.exists(cache_dir):
                        for item in os.listdir(cache_dir):
                            item_path = os.path.join(cache_dir, item)
                            try:
                                if os.path.isfile(item_path):
                                    os.remove(item_path)
                                    cleared_count += 1
                                elif os.path.isdir(item_path):
                                    shutil.rmtree(item_path)
                                    cleared_count += 1
                            except Exception:
                                pass
                
                QMessageBox.information(self, _("common.success"), _("debug.tools.cache.cleared_template", cleared_count=cleared_count))
                self._refresh_cache_info()
                
            except Exception as e:
                QMessageBox.critical(self, _("common.error"), _("debug.tools.cache.clear_failed", error=str(e)))
