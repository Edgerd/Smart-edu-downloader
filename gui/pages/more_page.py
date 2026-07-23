# -*- coding: utf-8 -*-
"""
更多功能页面模块
实现额外的功能模块
适配小屏幕设备
"""
from core.i18n import _

import json
import webbrowser
import os
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QMessageBox, QScrollArea,
                             QTabWidget, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QFontMetrics

from gui.fonts import title_font, body_font, small_font, bold_font, get_harmonyos_family
from gui.widgets.hover_tooltip_mixin import HoverTooltipMixin
from gui.utils.svg_icon_loader import load_svg_library_icon
from core.ui.icon_manager import IconManager

from core.url.url_modifier import URLModifier
from core.infrastructure.logger import log
from core.infrastructure.platform_utils import open_file
from gui.styles import get_button_style, load_primary_color, create_styled_button
from gui.welcome.wizard import WelcomeWizard


AFDIAN_URL = "https://ifdian.net/a/edgerd"


class MorePage(QWidget, HoverTooltipMixin):
    """更多功能页面类"""

    _hover_tooltips = {
        'clear_history_btn': 'clear_history_more',
        'open_log_btn': 'view_log',
        'donation_btn': 'donation',
        'bilibili_btn': 'bilibili',
        'afdian_btn': 'afdian',
        'download_history_table': 'download_history_table',
        'link_history_table': 'link_history_table',
        'search_history_table': 'search_history_table',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.url_modifier = URLModifier()
        self._accent_color = load_primary_color()
        self.downloader = None

        # 初始化图标管理器
        self.icon_manager = IconManager()

        # 初始化状态栏管理器
        from core.ui.status_bar import get_status_manager
        self.status_manager = get_status_manager()

        self._init_ui()
        self._init_mouse_hover_events()

    def set_downloader(self, downloader):
        """注入下载器实例"""
        self.downloader = downloader
        # 下载器注入后，刷新历史记录（如果页面已初始化）
        if hasattr(self, 'download_history_table'):
            self._load_recent_history(self.download_history_table, "download")

    def _load_search_history(self):
        """加载搜索历史记录"""
        try:
            from core.infrastructure.path_resolver import get_search_history_file
            history_file = get_search_history_file()
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    all_history = json.load(f)
                # 过滤非字典类型的异常数据
                valid_history = [item for item in all_history if isinstance(item, dict)]
                if len(valid_history) != len(all_history):
                    log("WARNING", f"搜索历史中存在 {len(all_history) - len(valid_history)} 条格式异常的数据")
                # 只显示最近10条
                recent = valid_history[-10:] if len(valid_history) > 10 else valid_history
                return recent
        except Exception as e:
            log("ERROR", f"加载搜索历史失败: {e}")
        return []
    
    def _save_search_record(self, keyword, result_count):
        """保存搜索记录"""
        try:
            from datetime import datetime
            from core.infrastructure.path_resolver import get_search_history_file
            
            history_file = get_search_history_file()
            all_history = []
            
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    all_history = json.load(f)
            
            # 添加新记录
            new_record = {
                "keyword": keyword,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "results": result_count
            }
            all_history.append(new_record)
            
            # 只保留最近100条记录
            if len(all_history) > 100:
                all_history = all_history[-100:]
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(all_history, f, indent=4, ensure_ascii=False)
        except Exception as e:
            log("ERROR", f"保存搜索记录失败: {e}")

    def _init_ui(self):
        """初始化UI"""
        # 使用滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.viewport().setStyleSheet("background: transparent;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(10)
        container.setLayout(main_layout)

        self._create_header(main_layout)
        
        # 创建历史记录组件
        self._create_history_section(main_layout)
        
        self._create_tools_section(main_layout)
        self._create_donation_section(main_layout)
        
        scroll.setWidget(container)
        
        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        self.setLayout(page_layout)

    def _create_header(self, parent_layout):
        """创建头部区域"""
        header_widget = QWidget()
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 5)
        header_layout.setSpacing(2)
        header_widget.setLayout(header_layout)

        title_row_layout = QHBoxLayout()
        title_row_layout.setSpacing(8)
        title_row_layout.setContentsMargins(0, 0, 0, 0)

        icon_pixmap = self.icon_manager.load_title_svg("title_more.svg", self._accent_color, size=(28, 28))
        self.header_icon_label = None
        if icon_pixmap:
            self.header_icon_label = QLabel()
            self.header_icon_label.setPixmap(icon_pixmap)
            self.header_icon_label.setFixedSize(28, 28)
            title_row_layout.addWidget(self.header_icon_label)

        self.header_title_label = QLabel(_("more.title"))
        self.header_title_label.setFont(title_font())
        self.header_title_label.setStyleSheet(f"color: {self._accent_color};")
        title_row_layout.addWidget(self.header_title_label)
        title_row_layout.addStretch()

        header_layout.addLayout(title_row_layout)

        subtitle = QLabel(_("more.subtitle"))
        subtitle.setFont(body_font())
        subtitle.setStyleSheet("color: #666;")

        header_layout.addWidget(subtitle)
        parent_layout.addWidget(header_widget)

    def _create_group(self, title):
        """创建分组框"""
        frame = QFrame()
        frame.setObjectName("groupFrame")
        frame.setStyleSheet("""
            #groupFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #E0E8F0;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        frame.setLayout(layout)
        
        # 添加标题
        title_label = QLabel(title)
        title_label.setFont(bold_font())
        title_label.setStyleSheet(f"color: {self._accent_color};")
        layout.addWidget(title_label)

        if not hasattr(self, '_group_title_labels'):
            self._group_title_labels = []
        self._group_title_labels.append(title_label)

        return frame

    def _create_history_section(self, parent_layout):
        """创建历史记录组件"""
        group = self._create_group(_("more.history_group"))
        layout = group.layout()

        # 创建标签页组件
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(body_font())
        self.tab_widget.setStyleSheet(self._get_history_tab_style())

        # 下载记录标签页
        download_tab = self._create_history_tab("download")
        self.tab_widget.addTab(download_tab, _("more.download_record_tab"))

        # 链接处理记录标签页
        link_tab = self._create_history_tab("link")
        self.tab_widget.addTab(link_tab, _("more.link_process_tab"))

        # 资源库搜索记录标签页
        search_tab = self._create_history_tab("search")
        self.tab_widget.addTab(search_tab, _("more.search_record_tab"))

        layout.addWidget(self.tab_widget)
        parent_layout.addWidget(group)

    def _get_history_tab_style(self):
        """获取历史记录标签页样式表"""
        return f"""
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
        """

    def _create_history_tab(self, tab_type):
        """创建历史记录标签页"""
        tab_widget = QWidget()
        tab_widget.setProperty("tab_type", tab_type)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        tab_widget.setLayout(layout)

        # 创建表格
        table = QTableWidget()
        
        # 保存为实例变量以便事件过滤器引用
        if tab_type == "download":
            self.download_history_table = table
        elif tab_type == "link":
            self.link_history_table = table
        elif tab_type == "search":
            self.search_history_table = table
        
        table.setObjectName(f"{tab_type}_history_table")
        table.setFont(small_font())
        table.horizontalHeader().setFont(bold_font())
        table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid #E0E8F0;
                border-radius: 6px;
                background: white;
                gridline-color: #E0E8F0;
            }}
            QTableWidget::item {{
                padding: 5px 10px;
            }}
            QTableWidget::item:selected {{
                background: {self._accent_color};
                color: white;
            }}
            QHeaderView::section {{
                background: #F0F4F8;
                color: #333;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #E0E8F0;
                font-family: "{get_harmonyos_family()}";
                font-weight: bold;
            }}
        """)

        # 设置表格属性
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.horizontalHeader().setStretchLastSection(True)
        table.verticalHeader().setVisible(False)
        table.setMinimumHeight(350)  # 设置最小高度
        
        # 安装滚动隔离
        from core.ui.scroll_isolation import install_scroll_isolation
        install_scroll_isolation(table)

        # 设置表头
        if tab_type == "download":
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels([
                _("more.history.header_filename"),
                _("more.history.header_download_time"),
                _("more.history.header_status"),
                _("more.history.header_action"),
            ])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        elif tab_type == "link":
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels([
                _("more.history.header_original_link"),
                _("more.history.header_process_time"),
                _("more.history.header_status"),
            ])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        elif tab_type == "search":
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels([
                _("more.history.header_search_keyword"),
                _("more.history.header_search_time"),
                _("more.history.header_result_count"),
            ])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)

        # 加载最近10条历史
        self._load_recent_history(table, tab_type)

        layout.addWidget(table)
        return tab_widget

    def _load_recent_history(self, table, tab_type):
        """加载最近历史记录"""
        if tab_type == "download":
            # 从下载器获取下载历史
            try:
                if not self.downloader:
                    # 下载器尚未注入，显示空表格（静默处理）
                    table.setRowCount(0)
                    return
                all_tasks = self.downloader.get_all_tasks()
                # 过滤非字典类型的异常数据
                valid_tasks = [t for t in all_tasks if isinstance(t, dict)]
                if len(valid_tasks) != len(all_tasks):
                    log("WARNING", f"下载历史中存在 {len(all_tasks) - len(valid_tasks)} 条格式异常的数据")
                # 只显示最近10条
                recent_tasks = valid_tasks[-10:] if len(valid_tasks) > 10 else valid_tasks
                recent_tasks.reverse()  # 最新的在上面
                
                table.setRowCount(len(recent_tasks))
                for row_idx, task in enumerate(recent_tasks):
                    # 文件名
                    filename = task.get("save_path", "")
                    if filename:
                        filename = os.path.basename(filename)
                    filename = filename[:30] + "..." if filename and len(filename) > 30 else (filename or _("common.unnamed"))
                    table.setItem(row_idx, 0, QTableWidgetItem(filename))
                    
                    # 下载时间（使用任务添加时间，如果没有则用当前时间）
                    # 暂时用任务ID的时间戳部分
                    task_id = task.get("task_id", "")
                    timestamp = ""
                    if task_id.startswith("task_"):
                        try:
                            ts = float(task_id.split("_")[1])
                            from datetime import datetime
                            timestamp = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
                        except Exception:
                            pass
                    table.setItem(row_idx, 1, QTableWidgetItem(timestamp))
                    
                    # 状态
                    status = task.get("status", "")
                    table.setItem(row_idx, 2, QTableWidgetItem(status))
                    
            except Exception as e:
                log("ERROR", f"加载下载历史失败: {str(e)}")
                # 如果失败，显示空表格
                table.setRowCount(0)
                
        elif tab_type == "link":
            # 从URL修改器获取链接处理历史
            self.url_modifier._reload_history()
            history = self.url_modifier.get_history()
            # 过滤非字典类型的异常数据
            valid_history = [item for item in history if isinstance(item, dict)]
            if len(valid_history) != len(history):
                log("WARNING", f"链接处理历史中存在 {len(history) - len(valid_history)} 条格式异常的数据")
            # 只显示最近10条
            recent_history = valid_history[:10]
            
            table.setRowCount(len(recent_history))
            for row_idx, item in enumerate(recent_history):
                # 原始链接
                url = item.get("url", "")
                url_short = url[:50] + "..." if len(url) > 50 else url
                table.setItem(row_idx, 0, QTableWidgetItem(url_short))
                
                # 处理时间
                timestamp = item.get("timestamp", "")
                table.setItem(row_idx, 1, QTableWidgetItem(timestamp))
                
                # 状态
                table.setItem(row_idx, 2, QTableWidgetItem(_("common.success")))
                
        elif tab_type == "search":
            # 资源库搜索记录（从历史记录文件加载）
            search_history = self._load_search_history()
            
            # 填充表格
            table.setRowCount(len(search_history))
            for row_idx, item in enumerate(search_history):
                table.setItem(row_idx, 0, QTableWidgetItem(item.get("keyword", "")))
                table.setItem(row_idx, 1, QTableWidgetItem(item.get("time", "")))
                table.setItem(row_idx, 2, QTableWidgetItem(str(item.get("results", ""))))

    def _create_tools_section(self, parent_layout):
        """创建工具区域"""
        group = self._create_group(_("more.tools_group"))
        layout = group.layout()

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.clear_history_btn = self._create_button(_("more.clear_history"), "#FFC107", self._clear_history)
        self.open_log_btn = self._create_button(_("more.view_log"), self._accent_color, self._open_log)
        self.tutorial_btn = self._create_button(
            _("welcome_onboarding.more_page.button_text"), self._accent_color, self._open_welcome_wizard
        )

        button_layout.addWidget(self.clear_history_btn)
        button_layout.addWidget(self.open_log_btn)
        button_layout.addWidget(self.tutorial_btn)
        button_layout.addStretch()

        layout.addLayout(button_layout)
        parent_layout.addWidget(group)

    def _create_donation_section(self, parent_layout):
        """创建捐赠区域"""
        group = self._create_group(_("more.support_author_group"))
        layout = group.layout()

        info_label = QLabel(_("more.support_author_message"))
        info_label.setFont(body_font())
        info_label.setStyleSheet("color: #666;")

        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)

        self.donation_btn = self._create_button(_("more.donate_button"), "#E2A82E", self._show_donation_dialog)
        self.bilibili_btn = self._create_button(_("more.bilibili_button"), "#FF6B9D",
            lambda: webbrowser.open("https://space.bilibili.com/3537111380658360"))
        self.afdian_btn = self._create_button(_("more.afdian_button"), "#FF7A45",
            lambda: webbrowser.open(AFDIAN_URL))
        afdian_icon = load_svg_library_icon(
            "07_nature_food/爱发电_svg.svg",
            size=(18, 18),
            color_map={"#FF7A45": "#FFFFFF", "#FF955C": "#FFFFFF", "#FFFFFF": "#FF7A45"},
        )
        if afdian_icon:
            self.afdian_btn.setIcon(afdian_icon)
            self.afdian_btn.setIconSize(QSize(18, 18))

        button_layout.addWidget(self.donation_btn)
        button_layout.addWidget(self.bilibili_btn)
        button_layout.addWidget(self.afdian_btn)
        button_layout.addStretch()

        afdian_desc = QLabel(_("more.afdian_desc"))
        afdian_desc.setFont(small_font())
        afdian_desc.setStyleSheet("color: #888888;")

        layout.addWidget(info_label)
        layout.addLayout(button_layout)
        layout.addWidget(afdian_desc)

        parent_layout.addWidget(group)

    def _show_donation_dialog(self):
        """显示赞赏码对话框"""
        from gui.widgets.donation_dialog import show_donation_dialog
        show_donation_dialog(self)

    def _open_welcome_wizard(self):
        """重新打开新手引导向导（非首次运行模式）。"""
        wizard = WelcomeWizard(parent=self, is_first_run=False)
        wizard.exec()

    def _create_button(self, text, color, callback):
        """创建自定义按钮 - 统一样式"""
        btn = create_styled_button(text, color, callback,
            style_kwargs={"hover_percent": 10, "pressed_percent": 20, "padding": "6px 16px"})
        # 根据文本宽度计算最小宽度，避免 emoji + 中文显示不全
        fm = QFontMetrics(btn.font())
        min_width = fm.horizontalAdvance(text) + 32
        btn.setMinimumWidth(max(min_width, 110))
        return btn

    def _clear_history(self):
        """清空历史记录"""
        reply = QMessageBox.question(
            self, _("common.confirm"), _("more.confirm_clear_history"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # 清空URL修改器历史
                self.url_modifier.clear_history()

                # 清空下载任务列表
                if self.downloader:
                    self.downloader.clear_all_tasks()

                QMessageBox.information(self, _("common.success"), _("more.history_cleared"))

                # 刷新所有历史记录表格
                self._refresh_history_tables()
            except Exception as e:
                QMessageBox.critical(self, _("common.error"), _("more.clear_history_failed_template", error=str(e)))

    def _refresh_history_tables(self):
        """刷新所有历史记录表格"""
        # 找到历史记录标签页组件
        tab_widget = None
        for child in self.findChildren(QTabWidget):
            if tab_widget is None:
                tab_widget = child
                break
        if not tab_widget:
            return
            
        # 刷新每个标签页的表格
        for tab_idx in range(tab_widget.count()):
            tab = tab_widget.widget(tab_idx)
            if not tab:
                continue
                
            # 找到表格
            table = None
            for child in tab.findChildren(QTableWidget):
                table = child
                break
            if not table:
                continue
                
            # 重新加载历史记录
            tab_type = tab.property("tab_type")
            if tab_type in ("download", "link", "search"):
                self._load_recent_history(table, tab_type)
                
    def _open_log(self):
        """打开日志文件（跨平台）"""
        log_file = "url_modifier.log"
        if os.path.exists(log_file):
            if not open_file(log_file):
                QMessageBox.information(self, _("common.tip"), _("more.log_file_not_exist"))
        else:
            QMessageBox.information(self, _("common.tip"), _("more.log_file_not_exist"))

    def showEvent(self, event):
        """页面显示时刷新历史记录表格"""
        super().showEvent(event)
        self._refresh_history_tables()

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新更多页面所有视觉元素。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        self._accent_color = primary

        # 刷新标题栏图标与标题颜色
        if self.header_icon_label is not None:
            icon_pixmap = self.icon_manager.load_title_svg(
                "title_more.svg", primary, size=(28, 28)
            )
            if icon_pixmap:
                self.header_icon_label.setPixmap(icon_pixmap)
        if self.header_title_label is not None:
            self.header_title_label.setStyleSheet(f"color: {primary};")

        # 刷新分组标题颜色
        if hasattr(self, '_group_title_labels'):
            for title_label in self._group_title_labels:
                title_label.setStyleSheet(f"color: {primary};")

        # 刷新标签页样式
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setStyleSheet(self._get_history_tab_style())
            self.tab_widget.style().unpolish(self.tab_widget)
            self.tab_widget.style().polish(self.tab_widget)
            self.tab_widget.update()

        # 刷新历史记录表格样式
        for table in (self.download_history_table, self.link_history_table, self.search_history_table):
            table.setStyleSheet(f"""
                QTableWidget {{
                    border: 1px solid #E0E8F0;
                    border-radius: 6px;
                    background: white;
                    gridline-color: #E0E8F0;
                }}
                QTableWidget::item {{
                    padding: 5px 10px;
                }}
                QTableWidget::item:selected {{
                    background: {primary};
                    color: white;
                }}
                QHeaderView::section {{
                    background: #F0F4F8;
                    color: #333;
                    padding: 8px;
                    border: none;
                    border-bottom: 2px solid #E0E8F0;
                    font-family: "{get_harmonyos_family()}";
                    font-weight: bold;
                }}
            """)

        # 刷新使用主题色的按钮
        if hasattr(self, 'open_log_btn'):
            self.open_log_btn.setAccentColor(primary)
        if hasattr(self, 'tutorial_btn'):
            self.tutorial_btn.setAccentColor(primary)
