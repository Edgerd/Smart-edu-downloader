"""
资源库页面模块
"""
from core.i18n import _
import webbrowser
import traceback
from functools import partial
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
                             QTableWidgetItem, QHeaderView, QAbstractItemView, QFrame,
                             QTextEdit, QScrollArea, QGridLayout, QTreeWidget, QTreeWidgetItem,
                             QMessageBox, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from qfluentwidgets import setCustomStyleSheet
from gui.fonts import title_font, body_font, small_font, bold_font, get_harmonyos_family
from gui.widgets import HoverTooltipMixin, CoverWidget, CustomContextMenu
from core.ui.icon_manager import IconManager
from core.infrastructure.thread_pool import submit_task
from core.resource.resource_library import ResourceLibrary, URLFixer
from gui.widgets import WheelComboBox
from ..widgets.custom_controls import ChineseLineEdit
from core.infrastructure.logger import log
from gui.styles import load_primary_color
from gui.widgets.material_button import MaterialButton

class ResourcePage(QWidget, HoverTooltipMixin):
    """资源库页面类 - 完全按照原版 selection_handler() 逻辑实现"""
    parse_finished = pyqtSignal(object, object, object, object)
    parse_error = pyqtSignal(str)
    search_finished = pyqtSignal(object)
    search_error = pyqtSignal(str)
    resource_loaded = pyqtSignal(object)
    url_generated = pyqtSignal(str)
    select_result = pyqtSignal(object)
    add_download_ready = pyqtSignal(str, str, object)
    update_parse_result = pyqtSignal(str)
    load_cover_signal = pyqtSignal(str, str)

    def __init__(self, parent=None, main_window=None, downloader=None, resource_lib=None):
        super().__init__(parent)
        self.resource_lib = resource_lib or ResourceLibrary()
        self.downloader = downloader
        self.current_resource = None
        self.resource_list = {}
        self.loading = False
        self.event_flag = False
        self.search_results = []
        self.current_page = 1
        self.items_per_page = 20
        self.current_search_keyword = ''
        self._resource_list_loaded = False
        self._parse_from_search = False
        self._accent_color = load_primary_color()
        self._filtered_results = []
        self._filter_subjects = []
        self._filter_grades = []
        self._filter_publishers = []
        self.icon_manager = IconManager()
        from core.ui.status_bar import get_status_manager
        self.status_manager = get_status_manager()
        self._init_signals()
        self._init_ui()
        self._init_mouse_hover_events()

    def _init_signals(self):
        """初始化信号连接"""
        self.parse_finished.connect(self._on_parse_complete)
        self.parse_error.connect(self._on_parse_error)
        self.search_finished.connect(self._on_search_complete)
        self.search_error.connect(self._on_search_error)
        self.resource_loaded.connect(self._on_resource_loaded)
        self.url_generated.connect(self._on_url_generated)
        self.select_result.connect(self._on_select_result)
        self.add_download_ready.connect(self._do_add_download)
        self.update_parse_result.connect(self._safe_set_parse_result)

    def _init_ui(self):
        """初始化UI"""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet('QScrollArea { border: none; background: transparent; }')
        container = QWidget()
        container.setStyleSheet('background: transparent;')
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(10)
        container.setLayout(main_layout)
        self._create_content_area(main_layout)
        self._create_chapter_tree(main_layout)
        self._create_url_parse_area(main_layout)
        self._create_search_area(main_layout)
        scroll.setWidget(container)
        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        self.setLayout(page_layout)

    def _create_content_area(self, parent_layout):
        """创建内容区域（标题+下拉选框+封面）"""
        content_widget = QWidget()
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(12)
        content_widget.setLayout(content_layout)
        left_column = QVBoxLayout()
        left_column.setSpacing(0)
        left_column.setContentsMargins(0, 0, 0, 0)
        self._create_header_row(left_column)
        left_column.addSpacing(8)
        self._create_browser_area(left_column)
        content_layout.addLayout(left_column)
        self.cover_widget = CoverWidget()
        self.load_cover_signal.connect(self.cover_widget.load_cover_from_url)
        content_layout.addWidget(self.cover_widget)
        parent_layout.addWidget(content_widget)

    def _create_header_row(self, parent_layout):
        """创建标题行"""
        title_row_layout = QHBoxLayout()
        title_row_layout.setSpacing(8)
        title_row_layout.setContentsMargins(0, 0, 0, 0)
        self.header_icon_label = None
        icon_pixmap = self.icon_manager.load_title_svg('title_resource.svg', self._accent_color, size=(28, 28))
        if icon_pixmap:
            self.header_icon_label = QLabel()
            self.header_icon_label.setPixmap(icon_pixmap)
            self.header_icon_label.setFixedSize(28, 28)
            title_row_layout.addWidget(self.header_icon_label)
        self.header_title_label = QLabel(_('resource.title'))
        self.header_title_label.setFont(title_font())
        self.header_title_label.setStyleSheet(f'color: {self._accent_color};')
        title_row_layout.addWidget(self.header_title_label)
        title_row_layout.addStretch()
        parent_layout.addLayout(title_row_layout)
        self.header_subtitle_label = QLabel(_('resource.subtitle'))
        self.header_subtitle_label.setFont(body_font())
        self.header_subtitle_label.setStyleSheet('color: #666;')
        parent_layout.addWidget(self.header_subtitle_label)

    def _create_browser_area(self, parent_layout):
        """创建资源浏览区域 - 完全按照原版级联下拉菜单实现"""
        browser_frame = QFrame()
        browser_frame.setObjectName('browserFrame')
        browser_frame.setStyleSheet('\n            #browserFrame {\n                background: white;\n                border-radius: 8px;\n                border: 1px solid #E0E8F0;\n                padding: 10px;\n            }\n        ')
        browser_layout = QVBoxLayout()
        browser_layout.setSpacing(8)
        browser_layout.setContentsMargins(0, 0, 0, 0)
        browser_frame.setLayout(browser_layout)
        browser_label = QLabel(_('resource.browse_label'))
        browser_label.setFont(bold_font())
        browser_label.setStyleSheet('color: #333;')
        self.loading_label = QLabel(_('resource.loading_resources'))
        self.loading_label.setFont(body_font())
        self.loading_label.setStyleSheet('color: #666;')
        self.loading_label.setVisible(False)
        dropdown_frame = QWidget()
        self.dropdown_layout = QGridLayout()
        self.dropdown_layout.setSpacing(8)
        self.dropdown_layout.setContentsMargins(0, 0, 0, 0)
        dropdown_frame.setLayout(self.dropdown_layout)
        self.combo_boxes = []
        self.combo_count = 8
        for i in range(self.combo_count):
            combo = WheelComboBox()
            combo.setFont(body_font())
            combo.setFixedHeight(32)
            combo.setMinimumWidth(100)
            combo.setMaximumWidth(240)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            setCustomStyleSheet(combo, "QPushButton { text-align: left; }", "QPushButton { text-align: left; }")
            combo.currentTextChanged.connect(lambda text, c=combo: c.setToolTip(text))
            combo.setVisible(False)
            combo.setEnabled(False)
            self.combo_boxes.append(combo)
            row = i // 4
            col = i % 4
            self.dropdown_layout.addWidget(combo, row, col)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        self.refresh_btn = MaterialButton(_('resource.refresh_list'))
        self.refresh_btn.setFont(body_font())
        self.refresh_btn.setFixedHeight(28)
        self.refresh_btn.clicked.connect(self._refresh_resource_list)
        self.refresh_btn.setAccentColor(self._accent_color)
        self.download_btn = MaterialButton(_('resource.add_to_download'))
        self.download_btn.setFont(body_font())
        self.download_btn.setFixedHeight(28)
        self.download_btn.setEnabled(False)
        self.download_btn.clicked.connect(self._add_to_download)
        self.download_btn.setAccentColor(self._accent_color)
        button_layout.addWidget(self.refresh_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.download_btn)
        browser_layout.addWidget(browser_label)
        browser_layout.addWidget(self.loading_label)
        browser_layout.addWidget(dropdown_frame)
        browser_layout.addLayout(button_layout)
        parent_layout.addWidget(browser_frame)

    def showEvent(self, event):
        """页面显示时加载资源列表（延迟加载）"""
        super().showEvent(event)
        if not self._resource_list_loaded:
            if self.resource_lib:
                self._load_resource_list_async()
                self._resource_list_loaded = True

    def _create_search_area(self, parent_layout):
        """创建搜索区域"""
        search_frame = QFrame()
        search_frame.setObjectName('searchFrame')
        search_frame.setStyleSheet('\n            #searchFrame {\n                background: white;\n                border-radius: 8px;\n                border: 1px solid #E0E8F0;\n                padding: 15px;\n            }\n        ')
        search_layout = QVBoxLayout()
        search_layout.setSpacing(12)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_frame.setLayout(search_layout)
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        search_title = QLabel(_('resource.search_label'))
        search_title.setFont(bold_font())
        search_title.setStyleSheet('color: #333;')
        title_row.addWidget(search_title)
        title_row.addStretch()
        search_layout.addLayout(title_row)
        search_input_layout = QHBoxLayout()
        search_input_layout.setSpacing(10)
        self.search_input = ChineseLineEdit()
        self.search_input.setPlaceholderText(_('resource.search_placeholder'))
        self.search_input.setFont(body_font())
        self.search_input.setStyleSheet(f'\n            QLineEdit {{\n                border: 2px solid #E0E8F0;\n                border-radius: 6px;\n                padding: 8px 12px;\n                background: white;\n                color: #333;\n            }}\n            QLineEdit:focus {{\n                border-color: {self._accent_color};\n                background: white;\n            }}\n            QLineEdit:hover {{\n                border-color: #B0C8E8;\n            }}\n        ')
        self.search_input.setFixedHeight(36)
        self.search_input.returnPressed.connect(self._search_resources)
        self.search_btn = MaterialButton(_('resource.search_button'))
        self.search_btn.setFont(bold_font())
        self.search_btn.setFixedHeight(36)
        self.search_btn.setMinimumWidth(100)
        self.search_btn.clicked.connect(self._search_resources)
        self.search_btn.setAccentColor(self._accent_color)
        search_input_layout.addWidget(self.search_input)
        search_input_layout.addWidget(self.search_btn)
        search_layout.addLayout(search_input_layout)
        filter_layout = QHBoxLayout()
        filter_layout.setSpacing(12)
        subject_label = QLabel(_('resource.subject_label'))
        subject_label.setFont(body_font())
        subject_label.setStyleSheet('color: #666;')
        filter_layout.addWidget(subject_label)
        self.filter_subject_combo = WheelComboBox()
        self.filter_subject_combo.setFont(body_font())
        self.filter_subject_combo.setFixedHeight(32)
        self.filter_subject_combo.setMinimumWidth(120)
        self.filter_subject_combo.setMaximumWidth(220)
        self.filter_subject_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        setCustomStyleSheet(self.filter_subject_combo, "QPushButton { text-align: left; }", "QPushButton { text-align: left; }")
        self.filter_subject_combo.currentTextChanged.connect(lambda text, c=self.filter_subject_combo: c.setToolTip(text))
        self.filter_subject_combo.addItem(_('resource.all_subjects'), None)
        self.filter_subject_combo.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.filter_subject_combo)
        grade_label = QLabel(_('resource.grade_label'))
        grade_label.setFont(body_font())
        grade_label.setStyleSheet('color: #666;')
        filter_layout.addWidget(grade_label)
        self.filter_grade_combo = WheelComboBox()
        self.filter_grade_combo.setFont(body_font())
        self.filter_grade_combo.setFixedHeight(32)
        self.filter_grade_combo.setMinimumWidth(120)
        self.filter_grade_combo.setMaximumWidth(220)
        self.filter_grade_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        setCustomStyleSheet(self.filter_grade_combo, "QPushButton { text-align: left; }", "QPushButton { text-align: left; }")
        self.filter_grade_combo.currentTextChanged.connect(lambda text, c=self.filter_grade_combo: c.setToolTip(text))
        self.filter_grade_combo.addItem(_('resource.all_grades'), None)
        self.filter_grade_combo.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.filter_grade_combo)
        publisher_label = QLabel(_('resource.version_label'))
        publisher_label.setFont(body_font())
        publisher_label.setStyleSheet('color: #666;')
        filter_layout.addWidget(publisher_label)
        self.filter_publisher_combo = WheelComboBox()
        self.filter_publisher_combo.setFont(body_font())
        self.filter_publisher_combo.setFixedHeight(32)
        self.filter_publisher_combo.setMinimumWidth(140)
        self.filter_publisher_combo.setMaximumWidth(240)
        self.filter_publisher_combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        setCustomStyleSheet(self.filter_publisher_combo, "QPushButton { text-align: left; }", "QPushButton { text-align: left; }")
        self.filter_publisher_combo.currentTextChanged.connect(lambda text, c=self.filter_publisher_combo: c.setToolTip(text))
        self.filter_publisher_combo.addItem(_('resource.all_versions'), None)
        self.filter_publisher_combo.currentIndexChanged.connect(self._apply_filters)
        filter_layout.addWidget(self.filter_publisher_combo)
        filter_layout.addStretch()
        self.reset_filter_btn = MaterialButton(_('resource.reset_filter'), variant=MaterialButton.VARIANT_OUTLINED)
        self.reset_filter_btn.setFont(body_font())
        self.reset_filter_btn.setFixedHeight(32)
        self.reset_filter_btn.clicked.connect(self._reset_filters)
        self.reset_filter_btn.setAccentColor(self._accent_color)
        filter_layout.addWidget(self.reset_filter_btn)
        search_layout.addLayout(filter_layout)
        self.search_result_table = QTableWidget()
        self.search_result_table.setColumnCount(5)
        self.search_result_table.setHorizontalHeaderLabels([_('resource.header_title'), _('resource.header_version'), _('resource.header_subject'), _('resource.header_grade'), _('resource.header_action')])
        self.search_result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.search_result_table.setColumnWidth(1, 120)
        self.search_result_table.setColumnWidth(2, 100)
        self.search_result_table.setColumnWidth(3, 100)
        self.search_result_table.setColumnWidth(4, 80)
        self.search_result_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.search_result_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.search_result_table.setAlternatingRowColors(True)
        self.search_result_table.verticalHeader().setVisible(False)
        from core.ui.scroll_isolation import install_scroll_isolation
        install_scroll_isolation(self.search_result_table)
        self.search_result_table.setStyleSheet(self._get_search_result_table_style())
        self.search_result_table.setMinimumHeight(400)
        self.search_result_table.setMaximumHeight(600)
        self.search_result_table.cellDoubleClicked.connect(self._on_search_result_double_clicked)
        self.search_result_table.itemSelectionChanged.connect(self._on_search_selection_changed)
        search_layout.addWidget(self.search_result_table)
        self.empty_state_label = QLabel(_('resource.no_search_results'))
        self.empty_state_label.setFont(body_font())
        self.empty_state_label.setAlignment(Qt.AlignCenter)
        self.empty_state_label.setStyleSheet('color: #999; padding: 40px;')
        self.empty_state_label.setVisible(False)
        search_layout.addWidget(self.empty_state_label)
        self.search_loading_label = QLabel(_('resource.searching'))
        self.search_loading_label.setFont(body_font())
        self.search_loading_label.setAlignment(Qt.AlignCenter)
        self.search_loading_label.setStyleSheet(f'\n            background: rgba(255, 255, 255, 0.9);\n            color: {self._accent_color};\n            padding: 20px;\n            border-radius: 8px;\n        ')
        self.search_loading_label.setVisible(False)
        search_layout.addWidget(self.search_loading_label)
        pagination_layout = QHBoxLayout()
        pagination_layout.setSpacing(8)
        self.page_info_label = QLabel(_('resource.page_info_empty'))
        self.page_info_label.setFont(body_font())
        self.page_info_label.setStyleSheet('color: #666;')
        pagination_layout.addWidget(self.page_info_label)
        pagination_layout.addStretch()
        self.prev_page_btn = MaterialButton(_('resource.previous_page'), variant=MaterialButton.VARIANT_OUTLINED)
        self.prev_page_btn.setFont(body_font())
        self.prev_page_btn.setFixedHeight(32)
        self.prev_page_btn.setMinimumWidth(80)
        self.prev_page_btn.clicked.connect(self._prev_page)
        self.prev_page_btn.setEnabled(False)
        self.prev_page_btn.setAccentColor(self._accent_color)
        pagination_layout.addWidget(self.prev_page_btn)
        self.page_buttons_layout = QHBoxLayout()
        self.page_buttons_layout.setSpacing(4)
        pagination_layout.addLayout(self.page_buttons_layout)
        self.next_page_btn = MaterialButton(_('resource.next_page'), variant=MaterialButton.VARIANT_OUTLINED)
        self.next_page_btn.setFont(body_font())
        self.next_page_btn.setFixedHeight(32)
        self.next_page_btn.setMinimumWidth(80)
        self.next_page_btn.clicked.connect(self._next_page)
        self.next_page_btn.setEnabled(False)
        self.next_page_btn.setAccentColor(self._accent_color)
        pagination_layout.addWidget(self.next_page_btn)
        search_layout.addLayout(pagination_layout)
        parent_layout.addWidget(search_frame)

    def _get_search_result_table_style(self):
        """获取搜索结果表格样式表"""
        return f'''
            QTableWidget {{
                border: 1px solid #E0E8F0;
                border-radius: 6px;
                background: white;
                gridline-color: #F0F0F0;
            }}
            QTableWidget::item {{
                padding: 8px;
                font-size: 9pt;
                color: #333;
            }}
            QTableWidget::item:selected {{
                background: {self._accent_color}20;
                color: #333;
            }}
            QTableWidget::item:hover {{
                background: #F8F9FA;
            }}
            QHeaderView::section {{
                background: #F8F9FA;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #E0E8F0;
                font-family: "{get_harmonyos_family()}";
                font-weight: bold;
                font-size: 9pt;
                color: #333;
            }}
        '''

    def _create_url_parse_area(self, parent_layout):
        """创建URL解析区域"""
        parse_frame = QFrame()
        parse_frame.setObjectName('parseFrame')
        parse_frame.setStyleSheet('\n            #parseFrame {\n                background: white;\n                border-radius: 8px;\n                border: 1px solid #E0E8F0;\n                padding: 10px;\n            }\n        ')
        parse_layout = QVBoxLayout()
        parse_layout.setSpacing(8)
        parse_layout.setContentsMargins(0, 0, 0, 0)
        parse_frame.setLayout(parse_layout)
        parse_label = QLabel(_('resource.url_parse_tab'))
        parse_label.setFont(bold_font())
        parse_label.setStyleSheet('color: #333;')
        url_input_layout = QHBoxLayout()
        url_input_layout.setSpacing(8)
        self.url_input = ChineseLineEdit()
        self.url_input.setPlaceholderText(_('resource.url_placeholder'))
        self.url_input.setFont(body_font())
        self.url_input.setStyleSheet(f'\n            QLineEdit {{\n                border: 2px solid #E0E8F0;\n                border-radius: 6px;\n                padding: 6px 10px;\n                background: white;\n            }}\n            QLineEdit:focus {{\n                border-color: {self._accent_color};\n                background: white;\n            }}\n        ')
        self.url_input.setFixedHeight(32)
        self.parse_btn = MaterialButton(_('resource.parse_button'))
        self.parse_btn.setFont(body_font())
        self.parse_btn.setFixedHeight(32)
        self.parse_btn.setFixedWidth(70)
        self.parse_btn.clicked.connect(self._parse_url)
        self.parse_btn.setAccentColor(self._accent_color)
        self.open_btn = MaterialButton(_('resource.open_in_browser'))
        self.open_btn.setFont(body_font())
        self.open_btn.setFixedHeight(32)
        self.open_btn.setFixedWidth(70)
        self.open_btn.clicked.connect(self._open_in_browser)
        self.open_btn.setAccentColor(self._accent_color)
        self.add_download_btn = MaterialButton(_('resource.add_download'))
        self.add_download_btn.setFont(body_font())
        self.add_download_btn.setFixedHeight(32)
        self.add_download_btn.setFixedWidth(90)
        self.add_download_btn.clicked.connect(self._add_to_download)
        self.add_download_btn.setAccentColor(self._accent_color)
        url_input_layout.addWidget(self.url_input)
        url_input_layout.addWidget(self.parse_btn)
        url_input_layout.addWidget(self.open_btn)
        url_input_layout.addWidget(self.add_download_btn)
        self.parse_result = QTextEdit()
        self.parse_result.setReadOnly(True)
        self.parse_result.setFont(body_font())
        self.parse_result.setStyleSheet('\n            QTextEdit {\n                border: 1px solid #E0E8F0;\n                border-radius: 6px;\n                background: white;\n                color: #333;\n                padding: 8px;\n            }\n        ')
        self.parse_result.setMaximumHeight(80)
        parse_layout.addWidget(parse_label)
        parse_layout.addLayout(url_input_layout)
        parse_layout.addWidget(self.parse_result)
        parent_layout.addWidget(parse_frame)

    def _create_chapter_tree(self, parent_layout):
        """创建章节目录树"""
        chapter_frame = QFrame()
        chapter_frame.setObjectName('chapterFrame')
        chapter_frame.setStyleSheet('\n            #chapterFrame {\n                background: white;\n                border-radius: 8px;\n                border: 1px solid #E0E8F0;\n                padding: 10px;\n            }\n        ')
        chapter_layout = QVBoxLayout()
        chapter_layout.setSpacing(8)
        chapter_layout.setContentsMargins(0, 0, 0, 0)
        chapter_frame.setLayout(chapter_layout)
        chapter_label = QLabel(_('resource.chapter_catalog_tab'))
        chapter_label.setFont(bold_font())
        chapter_label.setStyleSheet('color: #333;')
        self.chapter_tree = QTreeWidget()
        self.chapter_tree.setHeaderLabels([_('resource.chapter_label'), _('resource.page_number_label')])
        self.chapter_tree.setStyleSheet('\n            QTreeWidget {\n                border: 1px solid #E0E8F0;\n                border-radius: 6px;\n                background: white;\n            }\n            QTreeWidget::item {\n                padding: 4px;\n                font-size: 9pt;\n            }\n            QTreeWidget::item:selected {\n                background: #E8F4FC;\n            }\n            QHeaderView::section {\n                background: #F0F4F8;\n                padding: 6px;\n                border: none;\n                font-weight: bold;\n                font-size: 9pt;\n            }\n        ')
        self.chapter_tree.setMinimumHeight(600)
        self.chapter_tree.setMaximumHeight(2000)
        chapter_layout.addWidget(chapter_label)
        chapter_layout.addWidget(self.chapter_tree)
        parent_layout.addWidget(chapter_frame, 1)

    def _load_resource_list_async(self, force_refresh: bool=False):
        """异步加载资源列表
        
        Args:
            force_refresh: 是否强制刷新（跳过缓存），默认False
        """
        if not self.resource_lib:
            log('DEBUG', 'resource_lib 未初始化，延迟加载资源列表')
            self.loading = False
            return
        self.loading = True
        self.loading_label.setVisible(True)

        def load():
            try:
                resource_list = self.resource_lib.fetch_resource_list(force_refresh=force_refresh)
                self.resource_loaded.emit(resource_list)
            except Exception as e:
                log('ERROR', f'加载资源列表失败: {e}')
                self.parse_error.emit(str(e))
            finally:
                self.loading = False
        submit_task(load)

    @pyqtSlot(object)
    def _on_resource_loaded(self, resource_list):
        """资源加载完成的回调"""
        log('DEBUG', f'_on_resource_loaded: resource_list={resource_list is not None}, 类型数={(len(resource_list) if resource_list else 0)}')
        self.resource_list = resource_list
        self.loading_label.setVisible(False)
        self._init_dropdowns()

    def _init_dropdowns(self):
        """初始化下拉菜单 - 预加载所有下拉框"""
        if not self.resource_list:
            return
        for i, combo in enumerate(self.combo_boxes):
            combo.blockSignals(True)
            combo.clear()
            combo.setVisible(True)
            combo.setEnabled(i == 0)
            combo.blockSignals(False)
        first_combo = self.combo_boxes[0]
        first_combo.blockSignals(True)
        first_combo.addItem(_('resource.resource_type_label'), None)
        for key, value in self.resource_list.items():
            display_name = value.get('display_name', '')
            if display_name:
                first_combo.addItem(display_name, key)
        first_combo.blockSignals(False)
        for i, combo in enumerate(self.combo_boxes):
            combo.currentIndexChanged.connect(partial(self._on_combo_changed, i))

    def _on_combo_changed(self, index):
        """下拉菜单选择改变 - 完全按照原版 selection_handler() 逻辑"""
        if self.event_flag or self.loading:
            return
        self.event_flag = True
        self.cover_widget.clear()
        try:
            current_hier = self.resource_list
            end_flag = False
            for i in range(index + 1):
                try:
                    current_text = self.combo_boxes[i].currentText()
                    current_id = next((k for k, v in current_hier.items() if v.get('display_name') == current_text), None)
                    if current_id is None:
                        end_flag = True
                        break
                    current_hier = current_hier[current_id].get('children', {})
                except (StopIteration, KeyError):
                    end_flag = True
                    break
            if index < self.combo_count - 1 and (not end_flag):
                next_combo = self.combo_boxes[index + 1]
                next_combo.blockSignals(True)
                next_combo.clear()
                next_combo.addItem(_('resource.category_template', index=index + 1), None)
                for key, value in current_hier.items():
                    display_name = value.get('display_name', '')
                    if display_name:
                        next_combo.addItem(display_name, key)
                next_combo.blockSignals(False)
                next_combo.setEnabled(True)
                for i in range(index + 2, self.combo_count):
                    self.combo_boxes[i].setEnabled(False)
                    self.combo_boxes[i].blockSignals(True)
                    self.combo_boxes[i].clear()
                    self.combo_boxes[i].blockSignals(False)
            if end_flag or not current_hier:
                self._generate_url_from_selection(index)
                for i in range(index + 1, self.combo_count):
                    self.combo_boxes[i].setEnabled(False)
                    self.combo_boxes[i].blockSignals(True)
                    self.combo_boxes[i].clear()
                    self.combo_boxes[i].blockSignals(False)
        finally:
            self.event_flag = False

    def _generate_url_from_selection(self, index):
        """根据选择生成URL - 完全按照原版逻辑"""
        current_hier = self.resource_list
        for i in range(index + 1):
            try:
                current_text = self.combo_boxes[i].currentText()
                current_id = next((k for k, v in current_hier.items() if v.get('display_name') == current_text), None)
                if current_id is None:
                    return
                if i == index:
                    resource_type = current_hier[current_id].get('resource_type_code') or 'assets_document'
                    url = f'https://basic.smartedu.cn/tchMaterial/detail?contentType={resource_type}&contentId={current_id}&catalogType=tchMaterial&subCatalog=tchMaterial'
                    self.url_generated.emit(url)
                    return
                current_hier = current_hier[current_id].get('children', {})
            except (StopIteration, KeyError):
                return

    @pyqtSlot(str)
    def _on_url_generated(self, url):
        """URL生成后的回调"""
        self.url_input.setText(url)
        self.download_btn.setEnabled(True)
        try:
            if not self.isVisible():
                return
        except RuntimeError:
            return
        self._parse_url()

    def _refresh_resource_list(self):
        """刷新资源列表（强制重新获取）"""
        if not self.resource_lib:
            log('WARNING', 'resource_lib 未初始化，无法刷新资源列表')
            return
        self.resource_lib.clear_cache()
        self._reset_all_dropdowns()
        self._load_resource_list_async(force_refresh=True)

    def _reset_all_dropdowns(self):
        """重置所有下拉菜单"""
        for combo in self.combo_boxes:
            combo.blockSignals(True)
            combo.clear()
            combo.setVisible(False)
            combo.setEnabled(False)
            combo.blockSignals(False)

    def _add_to_download(self):
        """添加到下载队列"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, _('common.tip'), _('resource.no_resource_link'))
            return
        self._add_to_download_auto(url)

    def _add_to_download_auto(self, url):
        """全自动模式添加到下载（原有逻辑）"""
        if self.current_resource and self.current_resource.get('url'):
            self.add_download_ready.emit(self.current_resource['url'], self.current_resource.get('title', ''), self.current_resource.get('chapters', []))
            return
        self.download_btn.setEnabled(False)
        self.update_parse_result.emit(_('resource.parsing_resource_wait'))

        def parse_and_add():
            try:
                parse_result = self.resource_lib.parse(url, bookmarks=True)
                if not parse_result or len(parse_result) != 4:
                    self.parse_error.emit(_('resource.unable_to_get_download_link'))
                    return
                resource_url, title, chapters, _unused = parse_result
                if resource_url:
                    self.current_resource = {'url': resource_url, 'title': title, 'chapters': chapters}
                    self.add_download_ready.emit(resource_url, title, chapters)
                else:
                    self.parse_error.emit(_('resource.unable_to_get_download_link'))
            except Exception as e:
                try:
                    self.parse_error.emit(str(e))
                except Exception:
                    pass
        submit_task(parse_and_add)

    @pyqtSlot(str, str, object)
    def _do_add_download(self, resource_url, title, chapters):
        """执行添加到下载队列"""
        if not resource_url:
            log('ERROR', '添加到下载失败：资源URL为空')
            self.download_btn.setEnabled(True)
            return
        try:
            if not self.isVisible():
                return
        except RuntimeError:
            return
        self._perform_add_download(resource_url, title, chapters)

    def _perform_add_download(self, resource_url, title, chapters):
        """执行实际的添加下载逻辑"""
        try:
            log('DEBUG', '[step 1] 开始添加下载')
            try:
                main_window = self.window()
                log('DEBUG', f'[step 2] 获取主窗口: {main_window}')
            except RuntimeError:
                log('ERROR', '资源页面已被销毁，无法添加下载')
                return
            if not main_window:
                log('ERROR', '未找到主窗口')
                self.download_btn.setEnabled(True)
                return
            if not hasattr(main_window, 'page_manager'):
                log('ERROR', '主窗口页面管理器未初始化')
                self.download_btn.setEnabled(True)
                return
            download_page_index = 2
            log('DEBUG', f'[step 3] 检查下载页面是否已加载: {download_page_index}')
            try:
                if not main_window.page_manager.is_page_loaded(download_page_index):
                    log('DEBUG', '[step 3.1] 加载下载页面...')
                    main_window.page_manager.load_page(download_page_index)
                    log('DEBUG', '[step 3.1] 加载完成')
            except Exception as e:
                log('ERROR', f'加载下载页面失败: {e}')
                self.download_btn.setEnabled(True)
                return
            download_page = main_window.page_manager.get_page(download_page_index)
            log('DEBUG', f'[step 4] 获取下载页面: {download_page}')
            if not download_page:
                log('ERROR', '无法获取下载页面对象')
                self.download_btn.setEnabled(True)
                return
            if not hasattr(download_page, 'add_url_from_resource'):
                log('ERROR', '下载页面不支持添加资源')
                self.download_btn.setEnabled(True)
                return
            if not hasattr(download_page, 'downloader') or not download_page.downloader:
                log('ERROR', '下载器未初始化')
                self.download_btn.setEnabled(True)
                return
            log('DEBUG', f'[step 5] 调用 add_url_from_resource: url={resource_url[:50]}...')
            try:
                success = download_page.add_url_from_resource(resource_url, title, chapters)
                log('DEBUG', f"[step 5] 添加结果: {('成功' if success else '取消')}")
                if not success:
                    self.download_btn.setEnabled(True)
                    return
            except Exception as e:
                log('ERROR', f'添加到下载队列失败: {e}')
                self.download_btn.setEnabled(True)
                QMessageBox.warning(main_window, _('resource.add_to_download_failed_title'), _('resource.add_to_download_failed_template', error=str(e)))
                return
            self.download_btn.setEnabled(True)
            log('DEBUG', '[step 6] 弹出成功对话框')
            QMessageBox.information(main_window, _('common.tip'), _('resource.added_to_queue_template', title=title))
            log('DEBUG', '[step 6] 对话框已关闭')
            log('DEBUG', '[step 7] 切换到下载页面')
            try:
                if hasattr(main_window, 'navigation_manager'):
                    main_window.navigation_manager.switch_page(download_page_index)
                    log('DEBUG', '[step 7] 切换完成')
            except Exception as e:
                log('WARNING', f'页面切换失败: {e}')
            log('DEBUG', '[step 8] 全部完成')
        except Exception as e:
            log('ERROR', f'添加到下载失败: {e}')
            log('ERROR', f'调用栈: {traceback.format_exc()}')
            self.download_btn.setEnabled(True)
            try:
                parent_win = self.window()
            except RuntimeError:
                parent_win = None
            QMessageBox.warning(parent_win or self, _('common.error'), _('resource.add_to_download_failed_template', error=str(e)))

    def _find_main_window(self):
        """查找主窗口（保留兼容性，推荐使用 self.window()）"""
        try:
            return self.window()
        except RuntimeError:
            pass
        from gui import MainWindow
        parent = self.parent()
        while parent:
            if isinstance(parent, MainWindow):
                return parent
            parent = parent.parent()
        return None

    def _apply_filters(self):
        """应用筛选条件"""
        if not self.search_results:
            return
        subject = self.filter_subject_combo.currentText()
        grade = self.filter_grade_combo.currentText()
        publisher = self.filter_publisher_combo.currentText()
        self._filtered_results = []
        for item in self.search_results:
            if subject != _('resource.all_subjects') and item.get('subject', '') != subject:
                continue
            if grade != _('resource.all_grades') and item.get('grade', '') != grade:
                continue
            if publisher != _('resource.all_versions') and item.get('publisher', '') != publisher:
                continue
            self._filtered_results.append(item)
        self.current_page = 1
        self._display_current_page()
        self._update_pagination_controls()

    def _reset_filters(self):
        """重置所有筛选条件"""
        self.filter_subject_combo.blockSignals(True)
        self.filter_grade_combo.blockSignals(True)
        self.filter_publisher_combo.blockSignals(True)
        self.filter_subject_combo.setCurrentIndex(0)
        self.filter_grade_combo.setCurrentIndex(0)
        self.filter_publisher_combo.setCurrentIndex(0)
        self.filter_subject_combo.blockSignals(False)
        self.filter_grade_combo.blockSignals(False)
        self.filter_publisher_combo.blockSignals(False)
        self._apply_filters()

    def _populate_filter_options(self):
        """从搜索结果中提取筛选选项并填充下拉框"""
        subjects = set()
        grades = set()
        publishers = set()
        for item in self.search_results:
            if item.get('subject'):
                subjects.add(item['subject'])
            if item.get('grade'):
                grades.add(item['grade'])
            if item.get('publisher'):
                publishers.add(item['publisher'])
        current_subject = self.filter_subject_combo.currentText()
        current_grade = self.filter_grade_combo.currentText()
        current_publisher = self.filter_publisher_combo.currentText()
        self.filter_subject_combo.blockSignals(True)
        self.filter_grade_combo.blockSignals(True)
        self.filter_publisher_combo.blockSignals(True)
        self.filter_subject_combo.clear()
        self.filter_subject_combo.addItem(_('resource.all_subjects'), None)
        for subject in sorted(subjects):
            self.filter_subject_combo.addItem(subject, subject)
        self.filter_grade_combo.clear()
        self.filter_grade_combo.addItem(_('resource.all_grades'), None)
        for grade in sorted(grades):
            self.filter_grade_combo.addItem(grade, grade)
        self.filter_publisher_combo.clear()
        self.filter_publisher_combo.addItem(_('resource.all_versions'), None)
        for publisher in sorted(publishers):
            self.filter_publisher_combo.addItem(publisher, publisher)
        idx = self.filter_subject_combo.findText(current_subject)
        if idx >= 0:
            self.filter_subject_combo.setCurrentIndex(idx)
        idx = self.filter_grade_combo.findText(current_grade)
        if idx >= 0:
            self.filter_grade_combo.setCurrentIndex(idx)
        idx = self.filter_publisher_combo.findText(current_publisher)
        if idx >= 0:
            self.filter_publisher_combo.setCurrentIndex(idx)
        self.filter_subject_combo.blockSignals(False)
        self.filter_grade_combo.blockSignals(False)
        self.filter_publisher_combo.blockSignals(False)

    def _show_loading(self, show=True):
        """显示/隐藏加载状态"""
        self.search_loading_label.setVisible(show)
        self.search_result_table.setVisible(not show)
        self.empty_state_label.setVisible(False)

    def _show_empty_state(self, show=True):
        """显示/隐藏空状态"""
        self.empty_state_label.setVisible(show)
        self.search_result_table.setVisible(not show)
        self.search_loading_label.setVisible(False)

    def _search_resources(self):
        """搜索资源"""
        keyword = self.search_input.text().strip()
        if not keyword:
            QMessageBox.warning(self, _('common.tip'), _('resource.search_placeholder'))
            return
        self.search_result_table.setRowCount(0)
        self.current_search_keyword = keyword
        self._show_loading(True)
        self._show_empty_state(False)

        def search():
            try:
                results = self.resource_lib.search_resources(keyword)
                self.search_finished.emit(results)
            except Exception as e:
                self.search_error.emit(str(e))
        submit_task(search)

    @pyqtSlot(object)
    def _on_search_complete(self, results):
        """搜索完成回调 - 使用智能匹配结果，隐藏重复名称项目"""
        self._show_loading(False)
        seen_titles = set()
        unique_results = []
        for item in results:
            title = item.get('title', '')
            if title not in seen_titles:
                seen_titles.add(title)
                unique_results.append(item)
        self.search_results = unique_results
        self._filtered_results = unique_results
        self.current_page = 1
        if not unique_results:
            self._show_empty_state(True)
            self._update_pagination_controls()
            self.cover_widget.clear()
            return
        self._populate_filter_options()
        self._display_current_page()
        self._update_pagination_controls()

    def _display_current_page(self):
        """显示当前页的搜索结果"""
        self.search_result_table.setRowCount(0)
        results_to_display = self._filtered_results if self._filtered_results else self.search_results
        start_index = (self.current_page - 1) * self.items_per_page
        end_index = start_index + self.items_per_page
        current_page_results = results_to_display[start_index:end_index]
        for i, item in enumerate(current_page_results):
            self.search_result_table.insertRow(i)
            title_text = item.get('title', '')[:50]
            self.search_result_table.setItem(i, 0, QTableWidgetItem(title_text))
            self.search_result_table.setItem(i, 1, QTableWidgetItem(item.get('publisher', '')))
            self.search_result_table.setItem(i, 2, QTableWidgetItem(item.get('subject', '')))
            self.search_result_table.setItem(i, 3, QTableWidgetItem(item.get('grade', '')))
            self.search_result_table.item(i, 0).setData(Qt.UserRole, item)
            select_btn = MaterialButton(_('resource.select_button'))
            select_btn.setFont(small_font())
            select_btn.setFixedHeight(26)
            select_btn.setFixedWidth(60)
            select_btn.clicked.connect(lambda checked, item=item: self._select_search_result(item))
            select_btn.setAccentColor(self._accent_color)
            self.search_result_table.setCellWidget(i, 4, select_btn)

        if current_page_results:
            self.search_result_table.blockSignals(True)
            self.search_result_table.selectRow(0)
            self.search_result_table.blockSignals(False)
            self._load_cover_for_search_result(current_page_results[0])

    def _update_pagination_controls(self):
        """更新分页控件状态"""
        results_to_display = self._filtered_results if self._filtered_results else self.search_results
        total_pages = (len(results_to_display) + self.items_per_page - 1) // self.items_per_page
        self.page_info_label.setText(_('resource.page_info_template', current=self.current_page, total=total_pages, count=len(results_to_display)))
        self.prev_page_btn.setEnabled(self.current_page > 1)
        self.next_page_btn.setEnabled(self.current_page < total_pages)
        self._update_page_buttons(total_pages)

    def _update_page_buttons(self, total_pages):
        """更新页码按钮"""
        while self.page_buttons_layout.count():
            child = self.page_buttons_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        if total_pages <= 1:
            return
        max_visible = 5
        start_page = max(1, self.current_page - max_visible // 2)
        end_page = min(total_pages, start_page + max_visible - 1)
        if end_page - start_page < max_visible - 1:
            start_page = max(1, end_page - max_visible + 1)
        if start_page > 1:
            btn = self._create_page_button('1', 1)
            self.page_buttons_layout.addWidget(btn)
            if start_page > 2:
                label = QLabel('...')
                label.setStyleSheet('color: #666; padding: 0 4px;')
                self.page_buttons_layout.addWidget(label)
        for page in range(start_page, end_page + 1):
            btn = self._create_page_button(str(page), page, is_current=page == self.current_page)
            self.page_buttons_layout.addWidget(btn)
        if end_page < total_pages:
            if end_page < total_pages - 1:
                label = QLabel('...')
                label.setStyleSheet('color: #666; padding: 0 4px;')
                self.page_buttons_layout.addWidget(label)
            btn = self._create_page_button(str(total_pages), total_pages)
            self.page_buttons_layout.addWidget(btn)

    def _create_page_button(self, text, page, is_current=False):
        """创建页码按钮"""
        variant = MaterialButton.VARIANT_FILLED if is_current else MaterialButton.VARIANT_OUTLINED
        btn = MaterialButton(text, variant=variant)
        btn.setFont(body_font())
        btn.setFixedWidth(32)
        btn.setFixedHeight(32)
        btn.clicked.connect(lambda checked, p=page: self._go_to_page(p))
        if is_current:
            btn.setAccentColor(self._accent_color)
        else:
            btn.setAccentColor('#666')
        return btn

    def _go_to_page(self, page):
        """跳转到指定页"""
        self.current_page = page
        self._display_current_page()
        self._update_pagination_controls()

    def _prev_page(self):
        """上一页"""
        if self.current_page > 1:
            self.current_page -= 1
            self._display_current_page()
            self._update_pagination_controls()

    def _next_page(self):
        """下一页"""
        total_pages = (len(self.search_results) + self.items_per_page - 1) // self.items_per_page
        if self.current_page < total_pages:
            self.current_page += 1
            self._display_current_page()
            self._update_pagination_controls()

    @pyqtSlot(str)
    def _on_search_error(self, error_msg):
        """搜索出错回调"""
        QMessageBox.warning(self, _('common.error'), _('resource.search_failed_template', error=error_msg))

    def _on_search_result_double_clicked(self, row, column):
        """搜索结果双击事件 - 双击表格触发下载"""
        title_item = self.search_result_table.item(row, 0)
        if title_item:
            item = title_item.data(Qt.UserRole)
            if item:
                self._select_search_result(item)

    def _on_search_selection_changed(self):
        """搜索结果表格选择变化时更新封面预览"""
        selected_items = self.search_result_table.selectedItems()
        if not selected_items:
            return
        row = selected_items[0].row()
        title_item = self.search_result_table.item(row, 0)
        if not title_item:
            return
        item = title_item.data(Qt.UserRole)
        if item:
            self._load_cover_for_search_result(item)

    def _select_search_result(self, item):
        """选择搜索结果中的资源 - 通过信号处理"""
        self.select_result.emit(item)

    @pyqtSlot(str)
    def _safe_set_parse_result(self, text):
        """安全设置 parse_result 文本"""
        try:
            self.parse_result.setText(text)
        except Exception as e:
            log('ERROR', f'设置 parse_result 出错: {e}')

    @pyqtSlot(object)
    def _on_select_result(self, item):
        """选择搜索结果中的资源 - 通过信号处理"""
        url = item.get('url')
        title = item.get('title', '')
        if url:
            self.url_input.setText(url)
            self.download_btn.setEnabled(True)
            self._parse_from_search = True
            self.update_parse_result.emit(_('resource.selected_parsing_template', title=title))
            self._parse_url()

    def _load_cover_for_search_result(self, item):
        """加载搜索结果中资源的封面

        Args:
            item: 搜索结果字典，包含 title, url 等信息
        """
        if not item:
            self.cover_widget.clear()
            return
        url = item.get('url', '')
        if not url:
            self.cover_widget.clear()
            return
        content_id = URLFixer.extract_content_id(url) or ''
        self.cover_widget.clear()

        def _fetch_cover():
            try:
                from core.resource.textbook_info import TextbookInfoExtractor
                extractor = TextbookInfoExtractor()
                info = extractor.get_textbook_info(url)
                cover_url = info.get('cover_url', '')
                if cover_url and content_id:
                    self.load_cover_signal.emit(cover_url, content_id)
                else:
                    self.cover_widget.clear()
            except Exception as e:
                log('WARNING', f'搜索结果封面加载失败: {e}')
                self.cover_widget.clear()
        submit_task(_fetch_cover)

    def _parse_url(self):
        """解析URL"""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, _('common.tip'), _('resource.url_placeholder'))
            return
        self.update_parse_result.emit(_('resource.parsing'))

        def parse():
            try:
                parse_result = self.resource_lib.parse(url, bookmarks=True)
                if not parse_result or len(parse_result) != 4:
                    self.parse_error.emit(_('resource.unable_to_get_download_link'))
                    return
                resource_url, title, chapters, cover_url = parse_result
                self.parse_finished.emit(resource_url, title, chapters, cover_url)
            except Exception as e:
                self.parse_error.emit(str(e))
        submit_task(parse)

    @pyqtSlot(object, object, object, object)
    def _on_parse_complete(self, resource_url, title, chapters, cover_url):
        """解析完成的回调"""
        try:
            if resource_url:
                result_text = f"{_('gui.pages.resource_page.fstr_002')}{title}{_('gui.pages.resource_page.fstr_001')}{resource_url}"
                self.update_parse_result.emit(result_text)
                self._update_chapter_tree(chapters)
                self.current_resource = {'url': resource_url, 'title': title, 'chapters': chapters}
                if cover_url:
                    content_id = URLFixer.extract_content_id(resource_url) or ''
                    self.cover_widget.load_cover_from_url(cover_url, content_id)
                else:
                    self.cover_widget.clear()
                if self._parse_from_search:
                    self._parse_from_search = False
                    self.add_download_ready.emit(resource_url, title, chapters)
            else:
                self.update_parse_result.emit(_('resource.parse_failed_no_link'))
                self.chapter_tree.clear()
                self._parse_from_search = False
                self.cover_widget.clear()
        except Exception as e:
            log('ERROR', f'解析完成回调出错: {e}')
            QMessageBox.warning(self, _('common.error'), _('resource.parse_result_error_template', error=str(e)))
            self._parse_from_search = False

    @pyqtSlot(str)
    def _on_parse_error(self, error_msg):
        """解析出错的回调"""
        self.update_parse_result.emit(_('resource.parse_error_template', error=error_msg))

    @pyqtSlot(object)
    def _update_chapter_tree(self, chapters):
        """更新章节目录树"""
        try:
            self.chapter_tree.clear()
            if not chapters:
                return

            def add_chapters(parent, chapter_list):
                for chapter in chapter_list:
                    title = chapter.get('title', '')
                    page = chapter.get('page_index')
                    page_str = f'P{page}' if page else ''
                    item = QTreeWidgetItem(parent)
                    item.setText(0, title)
                    item.setText(1, page_str)
                    children = chapter.get('children', [])
                    if children:
                        add_chapters(item, children)
            add_chapters(self.chapter_tree, chapters)
            self.chapter_tree.expandAll()
        except Exception as e:
            log('ERROR', f'更新章节目录树出错: {e}')

    def _open_in_browser(self):
        """在浏览器中打开"""
        url = self.url_input.text().strip()
        if url:
            webbrowser.open(url)

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新资源页面所有视觉元素

        Args:
            primary: 主题主色
            background: 主题背景色
        """
        self._accent_color = primary

        # 清除图标缓存，确保 SVG 按新主题色重新着色
        self.icon_manager.clear_pixmap_cache()

        # 刷新标题栏图标与标题颜色
        if self.header_icon_label is not None:
            icon_pixmap = self.icon_manager.load_title_svg(
                'title_resource.svg', primary, size=(28, 28)
            )
            if icon_pixmap:
                self.header_icon_label.setPixmap(icon_pixmap)
        if self.header_title_label is not None:
            self.header_title_label.setStyleSheet(f'color: {primary};')

        # 刷新按钮颜色
        self.refresh_btn.setAccentColor(primary)
        self.download_btn.setAccentColor(primary)
        self.search_btn.setAccentColor(primary)
        self.parse_btn.setAccentColor(primary)
        self.open_btn.setAccentColor(primary)
        self.add_download_btn.setAccentColor(primary)
        self.reset_filter_btn.setAccentColor(primary)
        self.prev_page_btn.setAccentColor(primary)
        self.next_page_btn.setAccentColor(primary)

        # 刷新搜索输入框样式
        self.search_input.setStyleSheet(f'''
            QLineEdit {{
                border: 2px solid #E0E8F0;
                border-radius: 6px;
                padding: 8px 12px;
                background: white;
                color: #333;
            }}
            QLineEdit:focus {{
                border-color: {primary};
                background: white;
            }}
            QLineEdit:hover {{
                border-color: #B0C8E8;
            }}
        ''')

        # 刷新URL输入框样式
        self.url_input.setStyleSheet(f'''
            QLineEdit {{
                border: 2px solid #E0E8F0;
                border-radius: 6px;
                padding: 6px 10px;
                background: white;
            }}
            QLineEdit:focus {{
                border-color: {primary};
                background: white;
            }}
        ''')

        # 刷新筛选下拉框样式
        for combo in (
            self.filter_subject_combo,
            self.filter_grade_combo,
            self.filter_publisher_combo,
        ):
            if combo is not None:
                combo.update_theme_colors(primary, background)

        # 刷新资源浏览级联下拉框样式
        for combo in self.combo_boxes:
            if combo is not None:
                combo.update_theme_colors(primary, background)

        # 刷新搜索结果表格样式
        self.search_result_table.setStyleSheet(self._get_search_result_table_style())

        # 刷新搜索加载标签样式
        self.search_loading_label.setStyleSheet(f'''
            background: rgba(255, 255, 255, 0.9);
            color: {primary};
            padding: 20px;
            border-radius: 8px;
        ''')

        # 刷新章节目录树样式
        self.chapter_tree.setStyleSheet(f'''
            QTreeWidget {{
                border: 1px solid #E0E8F0;
                border-radius: 6px;
                background: white;
            }}
            QTreeWidget::item {{
                padding: 4px;
                font-size: 9pt;
            }}
            QTreeWidget::item:selected {{
                background: {primary}20;
            }}
            QHeaderView::section {{
                background: #F0F4F8;
                padding: 6px;
                border: none;
                font-family: "{get_harmonyos_family()}";
                font-weight: bold;
                font-size: 9pt;
            }}
        ''')

        # 刷新分页按钮（会重新生成页码按钮）
        self._update_pagination_controls()

        # 刷新当前页表格中的选择按钮
        self._display_current_page()

        # 刷新封面控件
        if hasattr(self, 'cover_widget') and hasattr(self.cover_widget, 'update_theme_colors'):
            self.cover_widget.update_theme_colors(primary, background)
            self.cover_widget.update()
