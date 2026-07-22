"""主页模块"""
from core.i18n import _
import re
import json
import os
import threading
from urllib.parse import urlparse, unquote
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QFrame, QProgressBar, QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QGridLayout, QTabWidget
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon
from gui.fonts import title_font, subtitle_font, body_font, bold_font, get_harmonyos_family
from gui.widgets import CustomContextMenu, CoverWidget
from gui.widgets.material_button import MaterialButton, MaterialIconButton
from gui.widgets.hover_tooltip_mixin import HoverTooltipMixin
from gui.widgets.animated_gradient_edit import AnimatedGradientBorderEdit
from core.ui.icon_manager import IconManager
from core.infrastructure.thread_pool import submit_task
from core.infrastructure.logger import log
from core.url.url_modifier import URLModifier
from core.resource.resource_library import ResourceLibrary, URLFixer
try:
    from gui.styles import load_primary_color, create_styled_button, get_fluent_table_style, wrap_in_rounded_container
except ImportError:
    from gui.styles import load_primary_color, create_styled_button, get_fluent_table_style

    def wrap_in_rounded_container(widget, accent_color: str = None):
        """将控件包装在圆角容器中"""
        if accent_color is None:
            accent_color = load_primary_color()
        container = QWidget()
        container.setStyleSheet('''
            QWidget {
                background: #FFFFFF;
                border: 1px solid #E5E5E5;
                border-radius: 8px;
            }
        ''')
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(widget)
        return container
from core.ui.table_column_manager import restore_table_widths_from_settings

class HomePage(QWidget, HoverTooltipMixin):
    """主页类"""
    SUBJECT_ALIASES = {'政治': '道德与法治', '道德与法治': '政治', '信息': '信息科技', '信息科技': '信息', '科技': '信息科技', '生物': '生物学', '生物学': '生物', '外语': '英语', '英语': '外语'}
    url_parsed = pyqtSignal(str, str, list, str)
    download_added = pyqtSignal(str)
    result_updated = pyqtSignal(str, str)
    task_success = pyqtSignal(str)
    task_error = pyqtSignal(str)
    load_cover_signal = pyqtSignal(str, str)
    cover_load_failed = pyqtSignal(str)

    def __init__(self, parent=None, main_window=None, downloader=None, resource_lib=None):
        super().__init__(parent)
        self.main_window = main_window
        self.url_modifier = URLModifier()
        self.downloader = downloader
        self.resource_lib = resource_lib or ResourceLibrary()
        self.current_task_id = None
        self.current_resource_url = None
        self.current_title = None
        self.current_chapters = None
        self._accent_color = load_primary_color()
        self._download_info_lock = threading.Lock()
        self._search_results = []
        self._current_search_index = 0
        self._nav_buttons_visible = False
        self._cover_url_cache = {}
        self._pending_cover_content_id = None
        self.icon_manager = IconManager()
        from core.ui.status_bar import get_status_manager
        self.status_manager = get_status_manager(main_window)
        self._init_mouse_hover_events()
        self._init_ui()

    def _init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        scroll.viewport().setStyleSheet('background: transparent;')
        container = QWidget()
        container.setStyleSheet('background: transparent;')
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(10)
        container.setLayout(main_layout)
        self._create_content_area(main_layout)
        self._create_button_area(main_layout)
        self._create_result_area(main_layout)
        self._create_history_area(main_layout)
        scroll.setWidget(container)
        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        self.setLayout(page_layout)
        self._start_update_timer()
        self._connect_signals()

    def _create_content_area(self, parent_layout):
        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        content_widget.setLayout(content_layout)
        left_column = QVBoxLayout()
        left_column.setSpacing(8)
        left_column.setContentsMargins(0, 0, 0, 0)
        self._create_header_row(left_column)
        self._create_url_input_area(left_column)
        content_layout.addLayout(left_column)
        self.cover_widget = CoverWidget()
        content_layout.addWidget(self.cover_widget)
        parent_layout.addWidget(content_widget)

    def _create_header_row(self, parent_layout):
        header_container = QWidget()
        header_layout = QVBoxLayout(header_container)
        header_layout.setSpacing(0)
        header_layout.setContentsMargins(0, 0, 0, 0)
        title_row_layout = QHBoxLayout()
        title_row_layout.setSpacing(8)
        title_row_layout.setContentsMargins(0, 0, 0, 0)
        icon_pixmap = self.icon_manager.load_title_svg('title_home.svg', self._accent_color, size=(28, 28))
        if icon_pixmap:
            self.header_icon_label = QLabel()
            self.header_icon_label.setPixmap(icon_pixmap)
            self.header_icon_label.setFixedSize(28, 28)
            title_row_layout.addWidget(self.header_icon_label)
        else:
            self.header_icon_label = None
        self.header_title_label = QLabel(_('home.title'))
        self.header_title_label.setFont(title_font())
        self.header_title_label.setStyleSheet(f'color: {self._accent_color};')
        title_row_layout.addWidget(self.header_title_label)
        title_row_layout.addStretch()
        header_layout.addLayout(title_row_layout)
        self.header_subtitle_label = QLabel(_('home.app_name_short'))
        self.header_subtitle_label.setFont(body_font())
        self.header_subtitle_label.setStyleSheet('color: #666;')
        header_layout.addWidget(self.header_subtitle_label)
        parent_layout.addWidget(header_container)

    def _create_url_input_area(self, parent_layout):
        input_frame = QFrame()
        input_frame.setObjectName('inputFrame')
        input_frame.setStyleSheet('''
            #inputFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #E0E8F0;
                padding: 10px;
            }
        ''')
        input_layout = QVBoxLayout()
        input_layout.setSpacing(8)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_frame.setLayout(input_layout)
        url_label = QLabel(_('home.search_placeholder_short'))
        url_label.setFont(bold_font())
        url_label.setStyleSheet('color: #333;')
        self.url_input = AnimatedGradientBorderEdit()
        self.url_input.setPlaceholderText(_('home.search_placeholder'))
        self.url_input.setFont(body_font())
        self.url_input.setMaximumHeight(120)
        self.url_input.textChanged.connect(self._on_url_input_changed)
        if self.main_window:
            self.main_window._add_hover_tooltip(self.url_input, _('home.search_placeholder_short'))
        input_layout.addWidget(url_label)
        input_layout.addWidget(self.url_input)
        parent_layout.addWidget(input_frame)

    def _create_button_area(self, parent_layout):
        """创建按钮区域，包含智能检索按钮和导航按钮组"""
        button_frame = QWidget()
        button_layout = QGridLayout()
        button_layout.setSpacing(8)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_frame.setLayout(button_layout)
        self.smart_btn = self._create_button(_('home.smart_search_button'), self._accent_color, self._smart_search_and_download)
        self.smart_btn.setEnabled(True)
        if self.main_window:
            self.main_window._add_hover_tooltip(self.smart_btn, _('main_window.smart_search_tooltip'))
        button_layout.addWidget(self.smart_btn, 0, 0)
        self._create_navigation_buttons(button_layout)
        parent_layout.addWidget(button_frame)

    def _create_navigation_buttons(self, button_layout):
        """创建搜索结果导航按钮组（默认隐藏）"""
        accent = self._accent_color
        self.confirm_btn = MaterialButton(_('home.this_one_button'))
        self.confirm_btn.setAccentColor(accent)
        self.confirm_btn.setFixedHeight(40)
        self.confirm_btn.clicked.connect(self._confirm_search_download)
        self.confirm_btn.hide()
        button_layout.addWidget(self.confirm_btn, 0, 0)
        self.prev_btn = MaterialIconButton()
        self.prev_btn.setToolTip(_('home.previous_button'))
        self.prev_btn.setAccentColor(accent)
        self._set_nav_icon(self.prev_btn, '上一个_svg.svg')
        self.prev_btn.clicked.connect(self._navigate_prev)
        self.prev_btn.hide()
        button_layout.addWidget(self.prev_btn, 0, 1)
        self.next_btn = MaterialIconButton()
        self.next_btn.setToolTip(_('home.next_button'))
        self.next_btn.setAccentColor(accent)
        self._set_nav_icon(self.next_btn, '下一个_svg.svg')
        self.next_btn.clicked.connect(self._navigate_next)
        self.next_btn.hide()
        button_layout.addWidget(self.next_btn, 0, 2)

    def _set_nav_icon(self, button, icon_name):
        """为导航按钮设置白色 SVG 图标，不跟随主题色。

        Args:
            button: MaterialIconButton 实例。
            icon_name: SVG 图标文件名。
        """
        # 翻页按钮图标固定为白色，避免与主题色按钮背景融为一体
        pixmap = self.icon_manager.load_title_svg(icon_name, "#FFFFFF", size=(20, 20))
        if pixmap and not pixmap.isNull():
            button.setIcon(QIcon(pixmap))
            button.setIconSize(pixmap.rect().size())
        else:
            button.setText('↑' if '上' in icon_name else '↓')

    def _create_button(self, text, color, callback):
        return create_styled_button(text, color, callback, fixed_height=32)

    def _create_result_area(self, parent_layout):
        result_frame = QFrame()
        result_frame.setObjectName('resultFrame')
        result_frame.setStyleSheet('''
            #resultFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #E0E8F0;
                padding: 10px;
            }
        ''')
        result_layout = QVBoxLayout()
        result_layout.setSpacing(8)
        result_layout.setContentsMargins(0, 0, 0, 0)
        result_frame.setLayout(result_layout)
        result_label = QLabel(_('home.result_label'))
        result_label.setFont(bold_font())
        result_label.setStyleSheet('color: #333;')
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(body_font())
        self.result_text.setStyleSheet('''
            QTextEdit {
                border: 1px solid #E0E8F0;
                border-radius: 6px;
                background: white;
                color: #333;
                padding: 8px;
            }
        ''')
        self.result_text.setMaximumHeight(100)
        CustomContextMenu.setup_for_text_edit(self.result_text, body_font())
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet(f'''
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background: #E0E8F0;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self._accent_color}, stop:1 #28A745);
                border-radius: 4px;
            }}
        ''')
        self.progress_bar.hide()
        self.loading_label = QLabel(_('home.loading'))
        self.loading_label.setFont(subtitle_font())
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.hide()
        result_layout.addWidget(result_label)
        result_layout.addWidget(self.result_text)
        result_layout.addWidget(self.loading_label)
        result_layout.addWidget(self.progress_bar)
        parent_layout.addWidget(result_frame)

    def _create_history_area(self, parent_layout):
        history_frame = QFrame()
        history_frame.setObjectName('historyFrame')
        history_frame.setStyleSheet('''
            #historyFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #E0E8F0;
                padding: 10px;
            }
        ''')
        history_layout = QVBoxLayout()
        history_layout.setSpacing(8)
        history_layout.setContentsMargins(0, 0, 0, 0)
        history_frame.setLayout(history_layout)
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(body_font())
        self.tab_widget.setStyleSheet(self._get_history_tab_style())
        download_tab, self.download_history_table = self._create_history_tab('download')
        self.tab_widget.addTab(download_tab, _('more.download_record_tab'))
        link_tab, self.link_history_table = self._create_history_tab('link')
        self.tab_widget.addTab(link_tab, _('more.link_process_tab'))
        search_tab, self.search_history_table = self._create_history_tab('search')
        self.tab_widget.addTab(search_tab, _('more.search_record_tab'))
        history_layout.addWidget(self.tab_widget)
        parent_layout.addWidget(history_frame)
        self._refresh_history_tables()

    def _get_history_tab_style(self):
        """获取历史记录标签页样式表"""
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
        tab_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        tab_widget.setLayout(layout)
        table = QTableWidget()
        table.setFont(body_font())
        table.horizontalHeader().setFont(bold_font())
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setMinimumHeight(180)
        table.setStyleSheet(get_fluent_table_style(self._accent_color))
        from core.ui.scroll_isolation import install_scroll_isolation
        install_scroll_isolation(table)
        if tab_type == 'download':
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels([_('home.history.header_filename'), _('home.history.header_download_time'), _('home.history.header_status')])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
            table_key = 'table_width_home_download_history'
        elif tab_type == 'link':
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels([_('home.history.header_original_link'), _('home.history.header_process_time'), _('home.history.header_status')])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
            table_key = 'table_width_home_link_history'
            table.doubleClicked.connect(self._load_from_link_history)
        elif tab_type == 'search':
            table.setColumnCount(3)
            table.setHorizontalHeaderLabels([_('home.history.header_search_keyword'), _('home.history.header_search_time'), _('home.history.header_result_count')])
            table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
            table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
            table_key = 'table_width_home_search_history'
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, lambda t=table, k=table_key: restore_table_widths_from_settings(t, k))
        container = wrap_in_rounded_container(table)
        layout.addWidget(container)
        return (tab_widget, table)

    def _start_update_timer(self):
        """启动下载进度更新定时器（优化：降低频率，添加窗口可见性检查）"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._update_download_progress)
        self.update_timer.start(1000)  # 从500ms降低到1000ms
        
        # 连接downloader信号实现事件驱动更新
        if self.downloader:
            self.downloader.task_updated.connect(self._on_task_updated)
            self.downloader.task_completed.connect(self._on_task_completed)

    def _connect_signals(self):
        self.url_parsed.connect(self._on_url_parsed)
        self.download_added.connect(self._on_download_added)
        self.result_updated.connect(self._on_result_updated)
        self.task_success.connect(self._on_task_success)
        self.task_error.connect(self._on_task_error)
        self.load_cover_signal.connect(self._on_cover_url_ready)
        self.cover_load_failed.connect(self._on_cover_load_failed)
        self.url_input.returnPressed.connect(self._on_input_return)

    @pyqtSlot(str, str)
    def _on_cover_url_ready(self, cover_url: str, content_id: str):
        """封面 URL 获取完成，检查是否仍对应当前选中的结果后加载。

        Args:
            cover_url: 封面图片 URL。
            content_id: 对应教材的 content_id。
        """
        if content_id != self._pending_cover_content_id:
            return
        if cover_url and content_id:
            self.cover_widget.load_cover_from_url(cover_url, content_id)
        else:
            self.cover_widget.clear()

    @pyqtSlot(str)
    def _on_cover_load_failed(self, content_id: str):
        """封面加载失败，仅当仍对应当前选中结果时恢复占位符。

        Args:
            content_id: 对应教材的 content_id。
        """
        if content_id == self._pending_cover_content_id:
            self.cover_widget.clear()

    def _on_input_return(self):
        """输入框回车键处理：导航按钮可见时触发'就是这个'，否则触发'智能检索'"""
        if self._nav_buttons_visible and self._search_results:
            self._confirm_search_download()
        else:
            self._smart_search_and_download()

    def _on_result_updated(self, text, color):
        font_family = get_harmonyos_family()
        self.result_text.setHtml(f'<pre style="color: {color}; font-family: {font_family}; white-space: pre-wrap; font-size: 9pt; margin: 0;">{text}</pre>')

    def _on_url_parsed(self, resource_url, title, chapters, cover_url):
        self.current_resource_url = resource_url
        self.current_title = title
        self.current_chapters = chapters
        if resource_url:
            self._show_result(_('home.parse_success_template', title=title, url=resource_url), '#28A745')
            self.smart_btn.setEnabled(True)
            self._refresh_history_tables()
            self.status_manager.set_ready_status()
            if cover_url:
                content_id = URLFixer.extract_content_id(resource_url) or ''
                self.cover_widget.load_cover_from_url(cover_url, content_id)
            else:
                self.cover_widget.clear()
        else:
            self._show_result(_('resource.parse_failed_no_link'), '#DC3545')
            self.smart_btn.setEnabled(True)
            self.status_manager.set_error_status(_('resource.unable_to_get_download_link'))
        self.smart_btn.setEnabled(True)

    def _smart_search_and_download(self):
        """智能检索并下载：自动检测输入类型，URL 下载或关键词搜索"""
        url_text = self.url_input.toPlainText().strip()
        if not url_text:
            self._show_result(_('home.please_enter_content'), '#FFC107')
            return
        self.status_manager.set_status(_('home.intelligent_searching'))
        urls = [line.strip() for line in url_text.splitlines() if line.strip()]
        if not urls:
            self._show_result(_('home.please_enter_content'), '#FFC107')
            return
        self.smart_btn.setEnabled(False)
        self.result_text.clear()
        first_line = urls[0].lower()
        is_url = first_line.startswith('http://') or first_line.startswith('https://') or first_line.startswith('www.')
        if is_url:
            self._do_url_download(urls)
        else:
            self._do_keyword_search(url_text)

    def _expand_keyword_with_aliases(self, keyword: str) -> list:
        """根据学科别名表扩展关键词，返回多个搜索关键词"""
        variants = [keyword]
        for alias_from, alias_to in self.SUBJECT_ALIASES.items():
            if alias_from in keyword and alias_to not in keyword:
                variant = keyword.replace(alias_from, alias_to)
                if variant not in variants:
                    variants.append(variant)
        return variants

    def _do_keyword_search(self, keyword):
        """执行关键词搜索流程"""
        self._show_result(_('resource.searching'), self._accent_color)

        def search_and_display():
            try:
                keyword_variants = self._expand_keyword_with_aliases(keyword)
                all_results = []
                seen_ids = set()
                for variant in keyword_variants:
                    results = self.resource_lib.search_resources(variant)
                    for r in results:
                        rid = r.get('content_id') or r.get('id') or r.get('uuid') or r.get('title')
                        if rid and rid not in seen_ids:
                            seen_ids.add(rid)
                            all_results.append(r)
                if not all_results:
                    self.result_updated.emit(_('home.no_textbook_found'), '#FFC107')
                    from PyQt5.QtCore import QMetaObject, Qt
                    QMetaObject.invokeMethod(self, '_on_search_no_results', Qt.QueuedConnection)
                    return
                self._search_results = all_results
                self._current_search_index = 0
                from PyQt5.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(self, '_on_search_results_ready', Qt.QueuedConnection)
            except Exception as e:
                self.result_updated.emit(_('home.search_error_template', error=str(e)), '#DC3545')
                from PyQt5.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(self, '_on_search_error', Qt.QueuedConnection)
        submit_task(search_and_display)

    @pyqtSlot()
    def _on_search_results_ready(self):
        """搜索完成，显示导航按钮和第一个结果"""
        self._show_navigation_buttons()
        self._update_search_display()
        self.status_manager.set_ready_status()

    @pyqtSlot()
    def _on_search_no_results(self):
        """搜索无结果"""
        self.smart_btn.setEnabled(True)
        self.status_manager.set_ready_status()

    @pyqtSlot()
    def _on_search_error(self):
        """搜索出错"""
        self.smart_btn.setEnabled(True)
        self.status_manager.set_ready_status()

    @pyqtSlot()
    def _on_search_download_parse_error(self):
        """搜索结果下载解析失败，恢复按钮"""
        self.confirm_btn.setEnabled(True)
        self.prev_btn.setEnabled(True)
        self.next_btn.setEnabled(True)
        self.status_manager.set_ready_status()

    def _do_url_download(self, urls):
        """URL 下载流程（原逻辑）"""
        from PyQt5.QtWidgets import QFileDialog
        smarted_urls = []
        direct_urls = []
        for url in urls:
            if URLFixer.is_valid_smartedu_url(url):
                smarted_urls.append(url)
            else:
                direct_urls.append(url)
        if len(smarted_urls) > 1 or len(direct_urls) > 1:
            self._show_result(_('home.multiple_links_selected'), self._accent_color)
            dir_path = QFileDialog.getExistingDirectory(self, _('home.choose_download_folder'))
            if not dir_path:
                self.smart_btn.setEnabled(True)
                self.status_manager.set_ready_status()
                return
            dir_path = os.path.normpath(dir_path)
        else:
            dir_path = None

        def do_download():
            try:
                for url in smarted_urls:
                    resource_url, title, chapters, _unused = self.resource_lib.parse(url, bookmarks=True)
                    if not resource_url:
                        self.result_updated.emit(_('home.parse_failed_icon_template', url=url), '#FFC107')
                        continue
                    default_filename = title or 'download'
                    if dir_path:
                        safe_title = default_filename.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                        save_path = os.path.join(dir_path, f'{safe_title}.pdf')
                        task_id = self.downloader.add_download_task(resource_url, title=title, chapters=chapters, save_path=save_path)
                        self.current_task_id = task_id
                        self.download_added.emit(task_id)
                        from PyQt5.QtCore import QMetaObject, Qt
                        QMetaObject.invokeMethod(self, '_reset_status', Qt.QueuedConnection)
                    else:
                        with self._download_info_lock:
                            self._single_download_info = {'resource_url': resource_url, 'title': title, 'chapters': chapters}
                        from PyQt5.QtCore import QMetaObject, Qt
                        QMetaObject.invokeMethod(self, '_handle_single_download', Qt.QueuedConnection)
                        return
                for url in direct_urls:
                    parsed = urlparse(url)
                    filename = os.path.basename(parsed.path) or 'download'
                    filename = unquote(filename)
                    filename = re.sub('[<>:"/\\\\|?*]', '_', filename).strip()
                    if not filename:
                        filename = 'download'
                    if dir_path:
                        save_path = os.path.join(dir_path, filename)
                        task_id = self.downloader.add_download_task(url, title=filename, chapters=[], save_path=save_path)
                        if task_id:
                            self.current_task_id = task_id
                            self.download_added.emit(task_id)
                            from PyQt5.QtCore import QMetaObject, Qt
                            QMetaObject.invokeMethod(self, '_reset_status', Qt.QueuedConnection)
                    else:
                        with self._download_info_lock:
                            self._direct_link_info = {'url': url, 'filename': filename}
                        from PyQt5.QtCore import QMetaObject, Qt
                        QMetaObject.invokeMethod(self, '_handle_direct_link_download', Qt.QueuedConnection)
                        return
            except Exception as e:
                self.result_updated.emit(_('home.download_error_template', error=str(e)), '#DC3545')
                error_msg = str(e)
                QTimer.singleShot(0, lambda: self._set_error_status(error_msg))
        has_smarted = bool(smarted_urls)
        has_direct = bool(direct_urls)
        if dir_path:
            submit_task(do_download)
        elif has_smarted and (not has_direct):

            def prepare_single():
                try:
                    url = smarted_urls[0]
                    resource_url, title, chapters, _unused = self.resource_lib.parse(url, bookmarks=True)
                    if not resource_url:
                        self.result_updated.emit(_('home.parse_failed_icon_template', url=url), '#FFC107')
                        self.smart_btn.setEnabled(True)
                        return
                    with self._download_info_lock:
                        self._single_download_info = {'resource_url': resource_url, 'title': title, 'chapters': chapters}
                    from PyQt5.QtCore import QMetaObject, Qt
                    QMetaObject.invokeMethod(self, '_handle_single_download', Qt.QueuedConnection)
                except Exception as e:
                    self.result_updated.emit(_('home.parse_error_template', error=str(e)), '#DC3545')
                    self.smart_btn.setEnabled(True)
            submit_task(prepare_single)
        elif has_direct and (not has_smarted):
            url = direct_urls[0]
            parsed = urlparse(url)
            filename = os.path.basename(parsed.path) or 'download'
            filename = unquote(filename)
            filename = re.sub('[<>:"/\\\\|?*]', '_', filename).strip()
            if not filename:
                filename = 'download'
            with self._download_info_lock:
                self._direct_link_info = {'url': url, 'filename': filename}
            from PyQt5.QtCore import QMetaObject, Qt
            QMetaObject.invokeMethod(self, '_handle_direct_link_download', Qt.QueuedConnection)
        else:
            submit_task(do_download)

    @pyqtSlot()
    def _handle_direct_link_download(self):
        if not hasattr(self, '_direct_link_info'):
            return
        with self._download_info_lock:
            if not self._direct_link_info:
                return
            info = self._direct_link_info
            self._direct_link_info = None
        from PyQt5.QtWidgets import QFileDialog
        save_path, _unused = QFileDialog.getSaveFileName(self, _('home.save_file_dialog'), info['filename'], _('common.all_files_filter'))
        if not save_path:
            self.smart_btn.setEnabled(True)
            self.status_manager.set_ready_status()
            return
        save_path = os.path.normpath(save_path)
        task_id = self.downloader.add_download_task(info['url'], title=info['filename'], chapters=[], save_path=save_path)
        self.current_task_id = task_id
        if task_id:
            self.download_added.emit(task_id)
        self.status_manager.set_ready_status()

    def _on_download_added(self, task_id):
        self._show_result(f"{_('gui.pages.home_page.fstr_003')}{task_id}{_('gui.pages.home_page.fstr_001')}", '#28A745')
        QTimer.singleShot(1000, self._switch_to_download_page)

    @pyqtSlot()
    def _switch_to_download_page(self):
        if self.main_window and hasattr(self.main_window, '_switch_page'):
            self.main_window._switch_page(2)

    def _update_download_progress(self):
        """更新下载进度（定时器调用，带窗口可见性检查）"""
        # 窗口最小化时跳过更新
        if self.windowState() & Qt.WindowMinimized:
            return
            
        if self.current_task_id:
            task = self.downloader.get_task(self.current_task_id)
            if task and task.get('status') == 'downloading':
                total_size = task.get('total_size', 0)
                downloaded_size = task.get('downloaded_size', 0)
                if total_size > 0:
                    progress = int(downloaded_size / total_size * 100)
                    self.progress_bar.setValue(progress)
    
    def _on_task_updated(self, task_id):
        """事件驱动的下载进度更新"""
        if task_id == self.current_task_id:
            self._update_download_progress()
    
    def _on_task_completed(self, task_id):
        """下载完成事件处理"""
        if task_id == self.current_task_id:
            self.progress_bar.setValue(100)

    @pyqtSlot()
    def _handle_single_download(self):
        if not hasattr(self, '_single_download_info'):
            return
        with self._download_info_lock:
            if not self._single_download_info:
                return
            info = self._single_download_info
            self._single_download_info = None
        from PyQt5.QtWidgets import QFileDialog
        save_path, _unused = QFileDialog.getSaveFileName(self, _('home.save_file_dialog'), info['title'] or 'download', _('home.pdf_filter'))
        if not save_path:
            if self._nav_buttons_visible:
                self.confirm_btn.setEnabled(True)
                self.prev_btn.setEnabled(True)
                self.next_btn.setEnabled(True)
            else:
                self.smart_btn.setEnabled(True)
            self.status_manager.set_ready_status()
            return
        save_path = os.path.normpath(save_path)
        task_id = self.downloader.add_download_task(info['resource_url'], title=info['title'], chapters=info['chapters'], save_path=save_path)
        self.current_task_id = task_id
        self.download_added.emit(task_id)
        self.status_manager.set_ready_status()
        if self._nav_buttons_visible:
            self._reset_search_buttons()

    def _show_result(self, text, color):
        font_family = get_harmonyos_family()
        self.result_text.setHtml(f'<pre style="color: {color}; font-family: {font_family}; white-space: pre-wrap; font-size: 9pt; margin: 0;">{text}</pre>')

    def _show_loading(self):
        self.loading_label.show()

    def _refresh_history_tables(self):
        self._refresh_download_history()
        self._refresh_link_history()
        self._refresh_search_history()

    def _refresh_download_history(self):
        try:
            if not self.downloader:
                self.download_history_table.setRowCount(0)
                return
            all_tasks = self.downloader.get_all_tasks()
            valid_tasks = [t for t in all_tasks if isinstance(t, dict)]
            recent_tasks = valid_tasks[-10:] if len(valid_tasks) > 10 else valid_tasks
            recent_tasks.reverse()
            self.download_history_table.setRowCount(len(recent_tasks))
            for row_idx, task in enumerate(recent_tasks):
                filename = task.get('save_path', '')
                if filename:
                    filename = os.path.basename(filename)
                filename = filename[:30] + '...' if filename and len(filename) > 30 else filename or _('common.unnamed')
                self.download_history_table.setItem(row_idx, 0, QTableWidgetItem(filename))
                task_id = task.get('task_id', '')
                timestamp = ''
                if task_id.startswith('task_'):
                    try:
                        ts = float(task_id.split('_')[1])
                        from datetime import datetime
                        timestamp = datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
                    except Exception:
                        pass
                self.download_history_table.setItem(row_idx, 1, QTableWidgetItem(timestamp))
                self.download_history_table.setItem(row_idx, 2, QTableWidgetItem(task.get('status', '')))
        except Exception as e:
            log('ERROR', f'加载下载历史失败: {str(e)}')
            self.download_history_table.setRowCount(0)

    def _refresh_link_history(self):
        self.url_modifier._reload_history()
        history = self.url_modifier.get_history()
        valid_history = [item for item in history if isinstance(item, dict)]
        recent_history = valid_history[:10]
        self.link_history_table.setRowCount(len(recent_history))
        for i, item in enumerate(recent_history):
            timestamp = item.get('timestamp', '')
            self.link_history_table.setItem(i, 0, QTableWidgetItem(timestamp[:16]))
            url = item.get('url', '')
            url_display = url[:40] + '...' if len(url) > 40 else url
            self.link_history_table.setItem(i, 1, QTableWidgetItem(url_display))
            self.link_history_table.setItem(i, 2, QTableWidgetItem(_('common.success')))

    def _refresh_search_history(self):
        try:
            from core.infrastructure.path_resolver import get_search_history_file
            history_file = get_search_history_file()
            all_history = []
            if os.path.exists(history_file):
                with open(history_file, 'r', encoding='utf-8') as f:
                    all_history = json.load(f)
            valid_history = [item for item in all_history if isinstance(item, dict)]
            recent = valid_history[-10:] if len(valid_history) > 10 else valid_history
            recent.reverse()
            self.search_history_table.setRowCount(len(recent))
            for row_idx, item in enumerate(recent):
                self.search_history_table.setItem(row_idx, 0, QTableWidgetItem(item.get('keyword', '')))
                self.search_history_table.setItem(row_idx, 1, QTableWidgetItem(item.get('time', '')))
                self.search_history_table.setItem(row_idx, 2, QTableWidgetItem(str(item.get('results', ''))))
        except Exception as e:
            log('ERROR', f'加载搜索历史失败: {e}')
            self.search_history_table.setRowCount(0)

    def _load_from_link_history(self, index):
        row = index.row()
        url_item = self.link_history_table.item(row, 1)
        if url_item:
            history = self.url_modifier.get_history()
            if row < len(history):
                self.url_input.setText(history[row]['url'])

    @pyqtSlot()
    def _hide_loading(self):
        self.loading_label.hide()

    @pyqtSlot()
    def _reset_status(self):
        self.status_manager.set_ready_status()

    @pyqtSlot(str)
    def _set_error_status(self, error_msg):
        self.status_manager.set_error_status(error_msg)

    @pyqtSlot(str)
    def _on_task_success(self, message=None):
        if self._nav_buttons_visible:
            self.confirm_btn.setEnabled(True)
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
        else:
            self.smart_btn.setEnabled(True)
        self._hide_loading()
        self._reset_status()
        msg = message if message is not None else _('home.operation_success')
        if msg:
            self._show_result(msg, '#28A745')

    @pyqtSlot(str)
    def _on_task_error(self, error_msg):
        if self._nav_buttons_visible:
            self.confirm_btn.setEnabled(True)
            self.prev_btn.setEnabled(True)
            self.next_btn.setEnabled(True)
        else:
            self.smart_btn.setEnabled(True)
        self._hide_loading()
        self._set_error_status(error_msg)
        self._show_result(error_msg, '#DC3545')

    def _on_url_input_changed(self):
        """输入框内容变化时，重置导航按钮为智能检索按钮"""
        if self._nav_buttons_visible:
            self._reset_search_buttons()
        url_text = self.url_input.toPlainText().strip()
        if not url_text:
            return
        urls = [line.strip() for line in url_text.splitlines() if line.strip()]
        if len(urls) == 1:
            self._check_and_handle_single_url(urls[0])

    def _check_and_handle_single_url(self, url: str):
        if self._is_direct_download_url(url):
            self._auto_handle_direct_url(url)

    def _is_direct_download_url(self, url: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path.lower()
        file_extensions = ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.zip', '.rar', '.7z', '.tar', '.gz', '.mp3', '.mp4', '.avi', '.mov', '.wmv', '.jpg', '.png', '.gif', '.webp', '.txt', '.csv', '.xlsx']
        for ext in file_extensions:
            if path.endswith(ext):
                return True
        if re.match('https?://.*ykt\\.cbern\\.com\\.cn/.*', url, re.IGNORECASE):
            return True
        return False

    def _auto_handle_direct_url(self, url: str):
        from PyQt5.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, _('home.direct_link_detected'), _('home.direct_link_prompt_template', url=url[:80]), QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
        if reply == QMessageBox.Yes:
            self._start_direct_download(url)

    def _start_direct_download(self, url: str):
        self.smart_btn.setEnabled(False)
        self._show_result(_('home.preparing_download'), self._accent_color)

        def do_download():
            try:
                filename = self._extract_filename_from_url(url)
                from PyQt5.QtCore import QMetaObject, Qt
                with self._download_info_lock:
                    self._direct_download_info = {'url': url, 'filename': filename}
                QMetaObject.invokeMethod(self, '_handle_direct_download', Qt.QueuedConnection)
            except Exception as e:
                self.result_updated.emit(_('home.download_error_template', error=str(e)), '#DC3545')
        submit_task(do_download)

    def _extract_filename_from_url(self, url: str) -> str:
        parsed = urlparse(url)
        path = unquote(parsed.path)
        filename = os.path.basename(path)
        if not filename or '.' not in filename:
            filename = 'download.pdf'
        return filename

    @pyqtSlot()
    def _handle_direct_download(self):
        if not hasattr(self, '_direct_download_info'):
            return
        with self._download_info_lock:
            if not self._direct_download_info:
                return
            info = self._direct_download_info
            self._direct_download_info = None
        from PyQt5.QtWidgets import QFileDialog
        save_path, _unused = QFileDialog.getSaveFileName(self, _('home.save_file_dialog'), info['filename'], _('home.all_document_filter'))
        if not save_path:
            self.smart_btn.setEnabled(True)
            return
        save_path = os.path.normpath(save_path)
        task_id = self.downloader.add_download_task(info['url'], title=os.path.basename(save_path), chapters=[], save_path=save_path)
        self.current_task_id = task_id
        self.download_added.emit(task_id)

    def showEvent(self, event):
        super().showEvent(event)
        self.smart_btn.setEnabled(True)
        self._refresh_history_tables()

    def _show_navigation_buttons(self):
        """显示导航按钮组，隐藏智能检索按钮"""
        self._nav_buttons_visible = True
        self.smart_btn.hide()
        self.confirm_btn.show()
        self.prev_btn.show()
        self.next_btn.show()

    def _reset_search_buttons(self):
        """恢复智能检索按钮，隐藏导航按钮组"""
        self._nav_buttons_visible = False
        self.confirm_btn.hide()
        self.prev_btn.hide()
        self.next_btn.hide()
        self.smart_btn.show()
        self.smart_btn.setEnabled(True)
        self._search_results = []

    def _update_search_display(self):
        """更新封面预览和处理结果，显示当前选中搜索结果"""
        if not self._search_results:
            return
        idx = self._current_search_index
        result = self._search_results[idx]
        title = result.get('title', '') or result.get('name', '') or result.get('book_name', '') or _('home.unknown_textbook')
        subject = result.get('subject', '')
        grade = result.get('grade', '')
        publisher = result.get('publisher', '')
        info_parts = [p for p in [subject, grade, publisher] if p]
        info_line = ' · '.join(info_parts) if info_parts else ''
        lines = [title]
        if info_line:
            lines.append(info_line)
        lines.append(f'({idx + 1}/{len(self._search_results)})')
        self._show_result('\n'.join(lines), self._accent_color)
        self._load_cover_for_search_result(result)

    def _load_cover_for_search_result(self, item):
        """加载搜索结果中资源的封面。

        优先使用搜索结果自带的 cover_url；若不存在则回退到教材信息
        提取器从详情页获取。通过信号回到主线程更新封面，避免跨线程
        操作 UI。

        Args:
            item: 搜索结果字典，包含 url、cover_url 等信息。
        """
        if not item:
            self.cover_widget.clear()
            return
        url = item.get('url', '')
        content_id = item.get('content_id') or item.get('id') or ''
        if not url or not content_id:
            self.cover_widget.clear()
            return

        # 优先使用搜索结果自带的封面 URL
        cover_url = item.get('cover_url', '')
        if cover_url:
            self._cover_url_cache[content_id] = cover_url
            self._pending_cover_content_id = content_id
            self.load_cover_signal.emit(cover_url, content_id)
            return

        # 命中缓存时直接加载，避免重复请求 API
        cached_cover_url = self._cover_url_cache.get(content_id)
        if cached_cover_url:
            self._pending_cover_content_id = content_id
            self.load_cover_signal.emit(cached_cover_url, content_id)
            return

        # 主线程显示加载状态，并记录当前待加载的 content_id
        self._pending_cover_content_id = content_id
        self.cover_widget._show_loading()

        def _fetch_cover():
            try:
                from core.resource.textbook_info import TextbookInfoExtractor
                extractor = TextbookInfoExtractor()
                info = extractor.get_textbook_info(url)
                cover_url = info.get('cover_url', '')
                if cover_url:
                    self._cover_url_cache[content_id] = cover_url
                    self.load_cover_signal.emit(cover_url, content_id)
                else:
                    self.cover_load_failed.emit(content_id)
            except Exception as e:
                log('WARNING', f'主页搜索结果封面加载失败: {e}')
                self.cover_load_failed.emit(content_id)
        submit_task(_fetch_cover)

    def _navigate_next(self):
        """切换到下一个搜索结果"""
        if not self._search_results:
            return
        self._current_search_index += 1
        if self._current_search_index >= len(self._search_results):
            self._current_search_index = 0
        self._update_search_display()

    def _navigate_prev(self):
        """切换到上一个搜索结果"""
        if not self._search_results:
            return
        self._current_search_index -= 1
        if self._current_search_index < 0:
            self._current_search_index = len(self._search_results) - 1
        self._update_search_display()

    def _confirm_search_download(self):
        """确认下载当前选中的搜索结果"""
        if not self._search_results:
            self._show_result(_('home.please_select_textbook'), '#FFC107')
            return
        idx = self._current_search_index
        result = self._search_results[idx]
        resource_url = result.get('url', '') or result.get('resource_url', '') or result.get('book_url', '')
        title = result.get('title', '') or result.get('name', '') or result.get('book_name', '') or _('home.unknown_textbook')
        if not resource_url:
            content_id = result.get('content_id', '') or result.get('id', '') or result.get('uuid', '')
            if content_id:
                resource_url = f'https://ykt.cbern.com.cn/course/course-info?contentId={content_id}'
            else:
                self._show_result(_('home.cannot_get_download_link'), '#FFC107')
                return
        self.status_manager.set_status(f"{_('gui.pages.home_page.fstr_004')}{title}")
        self.confirm_btn.setEnabled(False)
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self._show_result(f"{_('gui.pages.home_page.fstr_002')}{title}...", self._accent_color)

        def do_download():
            try:
                resource_url_parsed, parsed_title, chapters, _unused = self.resource_lib.parse(resource_url, bookmarks=True)
                if not resource_url_parsed:
                    self.result_updated.emit(_('home.parse_failed_icon_template', url=resource_url), '#FFC107')
                    from PyQt5.QtCore import QMetaObject, Qt
                    QMetaObject.invokeMethod(self, '_on_search_download_parse_error', Qt.QueuedConnection)
                    return
                from core.config.settings_manager import get_default_download_dir
                download_dir = get_default_download_dir()
                if not os.path.exists(download_dir):
                    os.makedirs(download_dir, exist_ok=True)
                safe_title = (parsed_title or title).replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
                save_path = os.path.join(download_dir, f'{safe_title}.pdf')
                task_id = self.downloader.add_download_task(resource_url_parsed, title=parsed_title or title, chapters=chapters, save_path=save_path)
                if task_id:
                    self.current_task_id = task_id
                    self.download_added.emit(task_id)
                    self.result_updated.emit(_('home.added_to_queue_template', title=safe_title, path=download_dir), '#28A745')
                    from PyQt5.QtCore import QMetaObject, Qt
                    QMetaObject.invokeMethod(self, '_switch_to_download_page', Qt.QueuedConnection)
                else:
                    self.result_updated.emit(_('home.add_task_failed'), '#DC3545')
                    from PyQt5.QtCore import QMetaObject, Qt
                    QMetaObject.invokeMethod(self, '_on_search_download_parse_error', Qt.QueuedConnection)
            except Exception as e:
                self.result_updated.emit(_('home.download_error_plain_template', error=str(e)), '#DC3545')
                from PyQt5.QtCore import QMetaObject, Qt
                QMetaObject.invokeMethod(self, '_on_search_download_parse_error', Qt.QueuedConnection)
        submit_task(do_download)

    def keyPressEvent(self, event):
        """键盘事件处理，支持上/下键切换搜索结果"""
        if self._nav_buttons_visible and self._search_results:
            if event.key() == Qt.Key_Up:
                self._navigate_prev()
                return
            elif event.key() == Qt.Key_Down:
                self._navigate_next()
                return
        super().keyPressEvent(event)

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新主页所有视觉元素。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        self._accent_color = primary

        # 清除图标缓存，确保 SVG 按新主题色重新着色
        self.icon_manager.clear_pixmap_cache()

        # 刷新标题栏图标与标题颜色
        if self.header_icon_label is not None:
            icon_pixmap = self.icon_manager.load_title_svg(
                'title_home.svg', primary, size=(28, 28)
            )
            if icon_pixmap:
                self.header_icon_label.setPixmap(icon_pixmap)
        if self.header_title_label is not None:
            self.header_title_label.setStyleSheet(f'color: {primary};')

        # 刷新按钮颜色
        self.smart_btn.setAccentColor(primary)
        self.confirm_btn.setAccentColor(primary)
        self.prev_btn.setAccentColor(primary)
        self.next_btn.setAccentColor(primary)

        # 刷新导航按钮图标颜色
        self._set_nav_icon(self.prev_btn, '上一个_svg.svg')
        self._set_nav_icon(self.next_btn, '下一个_svg.svg')

        # 刷新进度条颜色
        self.progress_bar.setStyleSheet(f'''
            QProgressBar {{
                border: none;
                border-radius: 4px;
                background: #E0E8F0;
                height: 8px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {primary}, stop:1 #28A745);
                border-radius: 4px;
            }}
        ''')

        # 刷新历史记录表格样式
        if hasattr(self, 'download_history_table'):
            self.download_history_table.setStyleSheet(get_fluent_table_style(primary))
        if hasattr(self, 'link_history_table'):
            self.link_history_table.setStyleSheet(get_fluent_table_style(primary))
        if hasattr(self, 'search_history_table'):
            self.search_history_table.setStyleSheet(get_fluent_table_style(primary))

        # 刷新历史记录标签页样式
        if hasattr(self, 'tab_widget'):
            self.tab_widget.setStyleSheet(self._get_history_tab_style())
            self.tab_widget.style().unpolish(self.tab_widget)
            self.tab_widget.style().polish(self.tab_widget)
            self.tab_widget.update()

        # 刷新封面控件
        if hasattr(self, 'cover_widget') and hasattr(self.cover_widget, 'update_theme_colors'):
            self.cover_widget.update_theme_colors(primary, background)
            self.cover_widget.update()
