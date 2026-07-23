# -*- coding: utf-8 -*-
"""历史记录组件 - 封装历史记录标签页的创建和管理逻辑"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QTableWidget, QHeaderView, QAbstractItemView
from PyQt5.QtCore import Qt, QTimer
from gui.fonts import body_font, bold_font, small_font, get_harmonyos_family
from gui.styles import get_fluent_table_style, load_primary_color
from core.ui.scroll_isolation import install_scroll_isolation
from core.ui.table_column_manager import restore_table_widths_from_settings
from core.i18n import _


class HistorySection(QWidget):
    """历史记录组件
    
    封装三标签页（下载/链接/搜索）历史记录的创建和管理逻辑，
    提供统一的表格样式、滚动隔离和列宽恢复功能。
    """
    
    def __init__(self, parent=None, accent_color=None, downloader=None):
        """初始化历史记录组件
        
        Args:
            parent: 父控件
            accent_color: 主题色（十六进制颜色字符串）
            downloader: 下载器实例（用于获取历史记录数据）
        """
        super().__init__(parent)
        self._accent_color = accent_color or load_primary_color()
        self.downloader = downloader
        
        # 表格引用（供外部访问）
        self.download_history_table = None
        self.link_history_table = None
        self.search_history_table = None
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)
        
        # 创建标签页控件
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(body_font())
        self.tab_widget.setStyleSheet(self._get_tab_style())
        
        # 创建三个标签页
        download_tab = self._create_history_tab('download')
        self.tab_widget.addTab(download_tab, _('more.download_record_tab'))
        
        link_tab = self._create_history_tab('link')
        self.tab_widget.addTab(link_tab, _('more.link_process_tab'))
        
        search_tab = self._create_history_tab('search')
        self.tab_widget.addTab(search_tab, _('more.search_record_tab'))
        
        layout.addWidget(self.tab_widget)
    
    def _get_tab_style(self):
        """获取标签页样式表
        
        Returns:
            str: 标签页样式表
        """
        return f'''
            QTabWidget::pane {{
                border: 1px solid #E0E8F0;
                border-radius: 6px;
                background: white;
            }}
            QTabBar::tab {{
                background: #F0F4F8;
                padding: 6px 18px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background: {self._accent_color};
                color: white;
            }}
            QTabBar::tab:hover:!selected {{
                background: #E0E8F0;
            }}
        '''
    
    def _create_history_tab(self, tab_type):
        """创建历史记录标签页
        
        Args:
            tab_type: 标签页类型（'download'/'link'/'search'）
        
        Returns:
            QWidget: 标签页控件
        """
        tab_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        tab_widget.setLayout(layout)
        
        # 创建表格
        table = QTableWidget()
        table.setFont(body_font())
        table.horizontalHeader().setFont(bold_font())
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setMinimumHeight(350)
        table.setStyleSheet(get_fluent_table_style(self._accent_color))
        
        # 安装滚动隔离
        install_scroll_isolation(table)
        
        # 根据类型设置表格
        if tab_type == 'download':
            self.download_history_table = table
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels([
                _('home.history.header_filename'),
                _('home.history.header_download_time'),
                _('home.history.header_status')
            ])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
            table_key = 'table_width_home_download_history'
        elif tab_type == 'link':
            self.link_history_table = table
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels([
                _('home.history.header_original_link'),
                _('home.history.header_process_time'),
                _('home.history.header_status')
            ])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
            table_key = 'table_width_home_link_history'
        elif tab_type == 'search':
            self.search_history_table = table
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels([
                _('home.history.header_search_keyword'),
                _('home.history.header_search_time'),
                _('home.history.header_result_count')
            ])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
            table_key = 'table_width_home_search_history'
        
        # 延迟恢复列宽
        QTimer.singleShot(100, lambda t=table, k=table_key: restore_table_widths_from_settings(t, k))
        
        layout.addWidget(table)
        return tab_widget
    
    def set_accent_color(self, color):
        """设置主题色
        
        Args:
            color: 主题色（十六进制颜色字符串）
        """
        self._accent_color = color
        self.tab_widget.setStyleSheet(self._get_tab_style())
        
        # 更新所有表格样式
        for table in [self.download_history_table, self.link_history_table, self.search_history_table]:
            if table:
                table.setStyleSheet(get_fluent_table_style(color))
