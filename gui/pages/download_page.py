# -*- coding: utf-8 -*-
"""下载管理页面"""
from core.i18n import _

import os
import re
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QFrame,
                             QMessageBox, QScrollArea, QGridLayout,
                             QAction, QApplication)
from PyQt5.QtCore import Qt, QTimer, QMimeData, QUrl, QByteArray
from PyQt5.QtGui import QDrag, QPixmap, QPainter, QColor
from PyQt5.QtSvg import QSvgRenderer
from enum import Enum

from gui.fonts import title_font, body_font, bold_font, large_font
from gui.widgets.hover_tooltip_mixin import HoverTooltipMixin
from core.ui.icon_manager import IconManager
from core.ui.table_column_manager import restore_table_widths_from_settings

from core.infrastructure.logger import log
from core.infrastructure.platform_utils import open_file, open_directory

from gui.widgets.ios_progress_bar import iOSProgressBar
from gui.styles import get_button_style, load_primary_color, get_fluent_table_style, get_fluent_menu_style, wrap_in_rounded_container, apply_menu_style
from core.config.theme_config import ICON_BASE_COLORS
from gui.widgets.material_button import MaterialButton
from gui.widgets.rounded_menu import RoundedMenu


class TaskAction(str, Enum):
    """任务控制动作枚举"""
    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"
    RETRY = "retry"


# 动作处理器配置：(downloader方法名, 允许执行的当前状态集合)
_ACTION_HANDLERS = {
    TaskAction.PAUSE: ("pause_task", {"pending", "downloading"}),
    TaskAction.RESUME: ("retry_task", {"paused", "failed", "cancelled"}),
    TaskAction.CANCEL: ("cancel_task", {"pending", "downloading", "paused"}),
    TaskAction.RETRY: ("retry_task", {"failed", "paused"}),
}


class DragDropTableWidget(QTableWidget):
    """支持拖出文件的自定义表格控件"""

    def __init__(self, downloader, parent=None):
        super().__init__(parent)
        self.downloader = downloader
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setAcceptDrops(True)

    def startDrag(self, supportedActions):
        selected_rows = self.selectionModel().selectedRows()
        if not selected_rows:
            return

        urls = []
        for index in selected_rows:
            row = index.row()
            filename_item = self.item(row, 0)
            if filename_item:
                task_id = filename_item.data(Qt.UserRole)
                if task_id:
                    task = self.downloader.get_task(task_id)
                    if task:
                        save_path = task.get('save_path', '')
                        if save_path and os.path.exists(save_path):
                            urls.append(QUrl.fromLocalFile(save_path))

        if urls:
            mime_data = QMimeData()
            mime_data.setUrls(urls)
            drag = QDrag(self)
            drag.setMimeData(mime_data)
            drag.exec(Qt.CopyAction | Qt.MoveAction)


class DownloadPage(QWidget, HoverTooltipMixin):
    """下载管理页面类"""

    def __init__(self, parent=None, downloader=None):
        super().__init__(parent)
        self.downloader = downloader
        self._accent_color = load_primary_color()

        self._task_state_cache = {}
        self._last_stats_hash = None

        self.icon_manager = IconManager()

        from core.ui.status_bar import get_status_manager
        self.status_manager = get_status_manager()

        self._init_ui()
        self._init_mouse_hover_events()

    def _init_ui(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        scroll.viewport().setStyleSheet("background: transparent;")

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 10, 15, 10)
        main_layout.setSpacing(10)
        container.setLayout(main_layout)

        self._create_header(main_layout)
        self._create_stats_area(main_layout)
        self._create_progress_area(main_layout)
        self._create_download_list(main_layout)
        self._create_action_buttons(main_layout)

        scroll.setWidget(container)

        page_layout = QVBoxLayout()
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)
        self.setLayout(page_layout)

        self._start_update_timer()
        self._connect_downloader_signals()

    def _create_header(self, parent_layout):
        from gui.widgets.page_header import PageHeader
        self.header_widget = PageHeader.create_header(
            parent_layout=parent_layout,
            icon_manager=self.icon_manager,
            accent_color=self._accent_color,
            icon_name="title_download.svg",
            title_text=_("download.page_title"),
            subtitle_text=_("download.page_subtitle")
        )

    def _create_stats_area(self, parent_layout):
        stats_frame = QFrame()
        stats_frame.setObjectName("statsFrame")
        stats_frame.setStyleSheet("""
            #statsFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #E0E8F0;
                padding: 10px;
            }
        """)

        stats_layout = QGridLayout()
        stats_layout.setSpacing(10)
        stats_layout.setContentsMargins(0, 0, 0, 0)
        stats_frame.setLayout(stats_layout)

        self.stats_labels = {}
        self.stats_icon_labels = {}
        stats_config = [
            {"name": "waiting", "label": _("widgets.status_indicator.waiting"), "icon": "01_user_interface/加载_svg.svg", "color": "#FFC107"},
            {"name": "downloading", "label": _("widgets.status_indicator.downloading"), "icon": "02_media_tech/下载_svg.svg", "color": self._accent_color},
            {"name": "paused", "label": _("widgets.status_indicator.paused"), "icon": "02_media_tech/暂停_svg.svg", "color": "#6C757D"},
            {"name": "completed", "label": _("widgets.status_indicator.completed"), "icon": "01_user_interface/对勾_svg.svg", "color": "#28A745"},
            {"name": "failed", "label": _("widgets.status_indicator.failed"), "icon": "01_user_interface/叉号_svg.svg", "color": "#DC3545"}
        ]

        for i, config in enumerate(stats_config):
            stat_widget = QWidget()
            stat_layout = QVBoxLayout()
            stat_layout.setSpacing(2)
            stat_layout.setContentsMargins(0, 0, 0, 0)
            stat_widget.setLayout(stat_layout)

            stat_value = QLabel("0")
            stat_value.setFont(large_font())
            stat_value.setStyleSheet(f"color: {config['color']};")
            stat_value.setAlignment(Qt.AlignCenter)

            label_layout = QHBoxLayout()
            label_layout.setSpacing(4)
            label_layout.setAlignment(Qt.AlignCenter)
            label_layout.setContentsMargins(0, 0, 0, 0)

            icon_label = QLabel()
            icon_label.setFixedSize(16, 16)
            icon_pixmap = self._load_status_icon(config['icon'], config['color'], (16, 16))
            if icon_pixmap:
                icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(Qt.AlignCenter)

            text_label = QLabel(config['label'])
            text_label.setFont(body_font())
            text_label.setStyleSheet("color: #666;")
            text_label.setAlignment(Qt.AlignCenter)

            label_layout.addWidget(icon_label)
            label_layout.addWidget(text_label)

            stat_layout.addWidget(stat_value)
            stat_layout.addLayout(label_layout)

            self.stats_labels[config['name']] = stat_value
            self.stats_icon_labels[config['name']] = icon_label
            stats_layout.addWidget(stat_widget, i // 3, i % 3)

        parent_layout.addWidget(stats_frame)

    def _create_progress_area(self, parent_layout):
        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        progress_frame.setStyleSheet("""
            #progressFrame {
                background: white;
                border-radius: 12px;
                border: 1px solid #E5E5EA;
                padding: 12px;
            }
        """)

        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(10)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_frame.setLayout(progress_layout)

        progress_label = QLabel(_("download.total_progress_label"))
        progress_label.setFont(bold_font())
        progress_label.setStyleSheet("color: #1C1C1E;")

        self.total_progress_bar = iOSProgressBar()
        self.total_progress_bar.setBarHeight(10)
        self.total_progress_bar.setCornerRadius(5)
        self.total_progress_bar.setFixedHeight(28)
        self.total_progress_bar.setMinimumHeight(28)
        self.total_progress_bar.setMinimumWidth(100)
        self.total_progress_bar.setMaximum(1000)

        self.total_progress_bar.setGradientColors(self._accent_color, self._adjust_color(self._accent_color, 30))

        self.total_size_label = QLabel(_("download.total_size_initial"))
        self.total_size_label.setFont(body_font())
        self.total_size_label.setStyleSheet("color: #8E8E93;")

        progress_layout.addWidget(progress_label)
        progress_layout.addWidget(self.total_progress_bar)
        progress_layout.addWidget(self.total_size_label)

        parent_layout.addWidget(progress_frame)

    def _create_download_list(self, parent_layout):
        list_frame = QFrame()
        list_frame.setObjectName("listFrame")
        list_frame.setStyleSheet("""
            #listFrame {
                background: white;
                border-radius: 8px;
                border: 1px solid #E0E8F0;
                padding: 10px;
            }
        """)

        list_layout = QVBoxLayout()
        list_layout.setSpacing(8)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_frame.setLayout(list_layout)

        list_label = QLabel(_("download.task_list_label"))
        list_label.setFont(bold_font())
        list_label.setStyleSheet("color: #333;")

        self.download_table = DragDropTableWidget(self.downloader)
        self.download_table.setColumnCount(4)
        self.download_table.setHorizontalHeaderLabels([
            _("download.header_filename"),
            _("download.header_status"),
            _("download.header_progress"),
            _("download.header_size"),
        ])
        self.download_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.download_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.download_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Interactive)
        self.download_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Interactive)
        self.download_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.download_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.download_table.verticalHeader().setVisible(False)
        self.download_table.setAlternatingRowColors(True)
        self.download_table.setStyleSheet(get_fluent_table_style(self._accent_color))
        self.download_table.setMinimumHeight(200)
        
        # 安装滚动隔离
        from core.ui.scroll_isolation import install_scroll_isolation
        install_scroll_isolation(self.download_table)

        # 延迟恢复列宽（等待表格初始化完成）
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(100, lambda: restore_table_widths_from_settings(
            self.download_table, "table_width_download_page"))

        self.download_table.cellDoubleClicked.connect(self._on_double_click)
        self.download_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.download_table.customContextMenuRequested.connect(self._show_context_menu)

        # 用圆角容器包裹表格
        table_container = wrap_in_rounded_container(self.download_table)

        list_layout.addWidget(list_label)
        list_layout.addWidget(table_container)
        parent_layout.addWidget(list_frame, 1)

    def _create_action_buttons(self, parent_layout):
        button_frame = QWidget()
        button_layout = QGridLayout()
        button_layout.setSpacing(12)
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_frame.setLayout(button_layout)

        accent = self._accent_color

        self.pause_all_btn = self._create_md3_button(_("download.pause_all"), accent, self._pause_all)
        self.resume_all_btn = self._create_md3_button(_("download.resume_all"), accent, self._resume_all)
        self.cancel_all_btn = self._create_md3_button(_("download.cancel_all"), accent, self._cancel_all)
        self.open_folder_btn = self._create_md3_button(_("download.open_folder"), accent, self._open_folder)
        self.refresh_btn = self._create_md3_button(_("common.refresh"), accent, self._refresh_list)
        self.clear_history_btn = self._create_md3_button(_("more.clear_history"), accent, self._clear_history)

        button_layout.addWidget(self.pause_all_btn, 0, 0)
        button_layout.addWidget(self.resume_all_btn, 0, 1)
        button_layout.addWidget(self.cancel_all_btn, 0, 2)
        button_layout.addWidget(self.open_folder_btn, 1, 0)
        button_layout.addWidget(self.refresh_btn, 1, 1)
        button_layout.addWidget(self.clear_history_btn, 1, 2)

        parent_layout.addWidget(button_frame)

    def _create_md3_button(self, text, color, callback):
        """创建 MD3 风格按钮"""
        btn = MaterialButton(text)
        btn.setAccentColor(color)
        btn.setFixedHeight(40)
        btn.clicked.connect(callback)
        return btn

    @staticmethod
    def _adjust_color(color: str, delta: int) -> str:
        """调整颜色亮度

        Args:
            color: 十六进制颜色
            delta: RGB 增减量

        Returns:
            调整后的十六进制颜色
        """
        try:
            r = max(0, min(255, int(color[1:3], 16) + delta))
            g = max(0, min(255, int(color[3:5], 16) + delta))
            b = max(0, min(255, int(color[5:7], 16) + delta))
            return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:
            return color

    def _load_status_icon(self, icon_path, color, size=(16, 16)):
        """加载 svg_library 中的状态图标并着色

        Args:
            icon_path: 图标相对路径，如 "01_user_interface/加载_svg.svg"
            color: 目标颜色
            size: 图标尺寸

        Returns:
            QPixmap or None: 着色后的图标，加载失败返回 None
        """
        cache_key = f"{icon_path}/{color}/{size}"
        if hasattr(self, '_status_icon_cache') and cache_key in self._status_icon_cache:
            return self._status_icon_cache[cache_key]

        if not hasattr(self, '_status_icon_cache'):
            self._status_icon_cache = {}

        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        full_path = os.path.join(base_dir, "resources", "svg_library", icon_path)
        if not os.path.exists(full_path):
            return None

        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
        except Exception:
            return None

        color_pattern = "|".join(re.escape(c) for c in ICON_BASE_COLORS)
        svg_content = re.sub(
            rf'fill="({color_pattern})"',
            f'fill="{color}"',
            svg_content,
            flags=re.IGNORECASE,
        )

        renderer = QSvgRenderer(QByteArray(svg_content.encode('utf-8')))
        if not renderer.isValid():
            return None

        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            renderer.render(painter)
        finally:
            if painter.isActive():
                painter.end()

        self._status_icon_cache[cache_key] = pixmap
        return pixmap

    def _connect_downloader_signals(self):
        """连接下载器信号，实现事件驱动的列表更新"""
        if not self.downloader:
            return

        signals = [
            (self.downloader.task_updated, self._on_task_updated),
            (self.downloader.task_completed, self._on_task_completed),
            (self.downloader.task_failed, self._on_task_failed),
            (self.downloader.task_added, self._on_task_added),
        ]
        for signal, slot in signals:
            try:
                signal.disconnect(slot)
            except (TypeError, RuntimeError):
                pass
            signal.connect(slot)

    def _disconnect_downloader_signals(self):
        """断开当前下载器的所有信号连接"""
        if not self.downloader:
            return

        signals = [
            self.downloader.task_updated,
            self.downloader.task_completed,
            self.downloader.task_failed,
            self.downloader.task_added,
        ]
        for signal in signals:
            try:
                signal.disconnect()
            except (TypeError, RuntimeError):
                pass

    def set_downloader(self, downloader):
        """设置下载器实例，先断开旧信号再连接新信号"""
        if self.downloader and self.downloader is not downloader:
            self._disconnect_downloader_signals()
        self.downloader = downloader
        if downloader:
            self._connect_downloader_signals()

    def _on_task_completed(self, task_id):
        task = self.downloader.get_task(task_id)
        if task:
            save_path = task.get("save_path", "")
            filename = os.path.basename(save_path)
            try:
                from gui.widgets.notification_widget import show_notification
                show_notification(_("download.completed_notification_title"), _("download.completed_notification_message_template", filename=filename))
            except Exception:
                pass

    def _on_task_failed(self, task_id, error):
        task = self.downloader.get_task(task_id)
        if task:
            filename = os.path.basename(task.get("save_path", _("common.unnamed")))
            if _("download.error_page_not_found") in error or _("download.error_link_not_found") in error:
                QMessageBox.warning(
                    self, _("download.download_failed_title"),
                    _("download.error_not_found_template", filename=filename)
                )
            elif "Access Token" in error:
                QMessageBox.warning(
                    self, _("download.download_failed_title"),
                    _("download.error_token_template", filename=filename, error=error)
                )
            elif "HTTP" in error or _("download.error_status_code") in error:
                QMessageBox.warning(
                    self, _("download.download_failed_title"),
                    _("download.error_generic_template", filename=filename, error=error)
                )
            else:
                QMessageBox.warning(
                    self, _("download.download_failed_title"),
                    _("download.error_generic_template", filename=filename, error=error)
                )

    def _on_task_updated(self, task_id):
        """任务进度更新时刷新列表"""
        self._refresh_list()

    def _on_task_added(self, task_id):
        """新任务添加时刷新列表"""
        self._refresh_list()

    def _start_update_timer(self):
        """启动下载列表更新定时器（优化：降低频率，添加窗口可见性检查）"""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._refresh_list)
        self.update_timer.start(1000)  # 从500ms降低到1000ms

    STATUS_MAP = {
        "pending": _("widgets.status_indicator.waiting"),
        "downloading": _("widgets.status_indicator.downloading"),
        "paused": _("widgets.status_indicator.paused"),
        "completed": _("widgets.status_indicator.completed"),
        "failed": _("widgets.status_indicator.failed"),
        "cancelled": _("download.cancel_action"),
    }

    def _translate_status(self, status):
        return self.STATUS_MAP.get(status, status)

    def _refresh_list(self):
        """增量更新下载列表，状态未变化时跳过UI刷新"""
        if not self.downloader:
            return

        active_tasks = self.downloader.get_active_tasks()
        completed_tasks = self.downloader.get_completed_tasks()
        all_tasks = active_tasks + completed_tasks

        current_state = {}
        stats = {k: 0 for k in ["waiting", "downloading", "paused", "completed", "failed"]}
        total_downloaded = 0
        total_size = 0

        for task in all_tasks:
            tid = task.get("task_id", "")
            if tid:
                current_state[tid] = (
                    task.get("status", ""),
                    task.get("downloaded_size", 0),
                    task.get("total_size", 0),
                    task.get("speed", 0)
                )
                stats[task.get("status", "")] = stats.get(task.get("status", ""), 0) + 1
                total_downloaded += task.get("downloaded_size", 0)
                total_size += task.get("total_size", 0)

        if current_state == self._task_state_cache and len(all_tasks) == len(self._task_state_cache):
            return

        self._task_state_cache = current_state
        self._update_ui_from_tasks(all_tasks, stats, total_downloaded, total_size)

    def _update_ui_from_tasks(self, all_tasks, stats, total_downloaded, total_size):
        task_ids_in_list = set()
        task_map = {}
        for task in all_tasks:
            tid = task.get("task_id", "")
            if tid:
                task_ids_in_list.add(tid)
                task_map[tid] = task

        existing_rows = {}
        for row in range(self.download_table.rowCount()):
            item = self.download_table.item(row, 0)
            if item:
                tid = item.data(Qt.UserRole)
                if tid:
                    existing_rows[tid] = row

        ids_to_remove = set(existing_rows.keys()) - task_ids_in_list
        ids_to_add = task_ids_in_list - set(existing_rows.keys())

        self.download_table.setUpdatesEnabled(False)

        try:
            if ids_to_remove:
                rows_to_remove = sorted([existing_rows[tid] for tid in ids_to_remove], reverse=True)
                for row in rows_to_remove:
                    self.download_table.removeRow(row)
                existing_rows = {}
                for row in range(self.download_table.rowCount()):
                    item = self.download_table.item(row, 0)
                    if item:
                        tid = item.data(Qt.UserRole)
                        if tid:
                            existing_rows[tid] = row

            for task_id in ids_to_add:
                task = task_map[task_id]
                row = self.download_table.rowCount()
                self.download_table.insertRow(row)
                existing_rows[task_id] = row

                filename = task.get("save_path", "")
                if filename:
                    filename = os.path.basename(filename)
                filename = filename[:30] + "..." if filename and len(filename) > 30 else (filename or _("common.unnamed"))

                filename_item = QTableWidgetItem(filename)
                filename_item.setData(Qt.UserRole, task_id)
                self.download_table.setItem(row, 0, filename_item)
                for col in range(1, 4):
                    self.download_table.setItem(row, col, QTableWidgetItem(""))

            for task_id, task in task_map.items():
                if task_id not in existing_rows:
                    continue
                row = existing_rows[task_id]

                raw_status = task.get("status", "")
                task_total = task.get("total_size", 0)
                downloaded = task.get("downloaded_size", 0)

                status_text = self._translate_status(raw_status)
                if raw_status == "downloading" and task.get("speed", 0) > 0:
                    speed_str = self._format_speed(task.get("speed", 0))
                    status_text = _("download.downloading_template", speed=speed_str)
                elif raw_status == "failed":
                    error_msg = task.get("error", "")
                    if error_msg:
                        error_short = error_msg[:30] + "..." if len(error_msg) > 30 else error_msg
                        status_text = _("download.failed_template", error=error_short)

                status_item = self.download_table.item(row, 1)
                if status_item is None or status_item.text() != status_text:
                    if status_item is None:
                        status_item = QTableWidgetItem(status_text)
                        self.download_table.setItem(row, 1, status_item)
                    else:
                        status_item.setText(status_text)

                progress_text = f"{int((downloaded / task_total) * 100)}%" if task_total > 0 else "0%"
                progress_item = self.download_table.item(row, 2)
                if progress_item is None or progress_item.text() != progress_text:
                    if progress_item is None:
                        progress_item = QTableWidgetItem(progress_text)
                        self.download_table.setItem(row, 2, progress_item)
                    else:
                        progress_item.setText(progress_text)

                size_text = self._format_size(downloaded)
                size_item = self.download_table.item(row, 3)
                if size_item is None or size_item.text() != size_text:
                    if size_item is None:
                        size_item = QTableWidgetItem(size_text)
                        self.download_table.setItem(row, 3, size_item)
                    else:
                        size_item.setText(size_text)

            expected_rows = len(task_map)
            while self.download_table.rowCount() > expected_rows:
                self.download_table.removeRow(self.download_table.rowCount() - 1)

        finally:
            self.download_table.setUpdatesEnabled(True)

        for key, label in self.stats_labels.items():
            label.setText(str(stats.get(key, 0)))

        total_progress = int((total_downloaded / total_size) * 1000) if total_size > 0 else 0
        self.total_progress_bar.setValue(total_progress)

        # 根据任务状态设置进度条状态
        if stats["completed"] > 0 and stats["completed"] == len(all_tasks):
            # 所有任务完成
            self.total_progress_bar.setState(iOSProgressBar.STATE_COMPLETED)
        elif stats["downloading"] > 0:
            # 有任务在下载
            self.total_progress_bar.setState(iOSProgressBar.STATE_DOWNLOADING)
        elif stats["paused"] > 0:
            # 有任务暂停
            self.total_progress_bar.setState(iOSProgressBar.STATE_PAUSED)
        elif stats["failed"] > 0:
            # 有任务失败
            self.total_progress_bar.setState(iOSProgressBar.STATE_FAILED)
        else:
            # 等待中
            self.total_progress_bar.setState(iOSProgressBar.STATE_WAITING)

        total_size_mb = total_size / (1024 * 1024)
        self.total_size_label.setText(_("download.total_size_template", size=f"{total_size_mb:.2f}"))

    def _on_double_click(self, row, column):
        task = self._get_task_from_row(row)
        if task:
            self._open_file(task)

    def _get_task_from_row(self, row):
        filename_item = self.download_table.item(row, 0)
        if filename_item:
            task_id = filename_item.data(Qt.UserRole)
            if task_id:
                return self.downloader.get_task(task_id)
        return None

    def _show_context_menu(self, pos):
        """显示右键菜单"""
        item = self.download_table.itemAt(pos)
        if not item:
            return
        row = self.download_table.row(item)
        task = self._get_task_from_row(row)
        if not task:
            return

        menu = RoundedMenu(self)
        menu.setFont(body_font())
        apply_menu_style(menu, accent_color=self._accent_color)  # 修复：解决黑色背景

        open_file_action = QAction(_("download.open_file_action"), self)
        open_file_action.setFont(body_font())
        open_file_action.triggered.connect(lambda: self._open_file(task))
        menu.addAction(open_file_action)

        open_folder_action = QAction(_("download.open_folder_action"), self)
        open_folder_action.setFont(body_font())
        open_folder_action.triggered.connect(lambda: self._open_file_folder(task))
        menu.addAction(open_folder_action)

        menu.addSeparator()

        if self._can_execute(task, TaskAction.PAUSE):
            pause_action = QAction(_("download.pause_action"), self)
            pause_action.setFont(body_font())
            pause_action.triggered.connect(lambda: self._execute_task_and_refresh(task, TaskAction.PAUSE))
            menu.addAction(pause_action)
        
        if self._can_execute(task, TaskAction.RESUME):
            resume_action = QAction(_("download.resume_action"), self)
            resume_action.setFont(body_font())
            resume_action.triggered.connect(lambda: self._execute_task_and_refresh(task, TaskAction.RESUME))
            menu.addAction(resume_action)

        if self._can_execute(task, TaskAction.CANCEL):
            cancel_action = QAction(_("download.cancel_action"), self)
            cancel_action.setFont(body_font())
            cancel_action.triggered.connect(lambda: self._execute_task_and_refresh(task, TaskAction.CANCEL))
            menu.addAction(cancel_action)

        if self._can_execute(task, TaskAction.RETRY):
            retry_action = QAction(_("download.retry_action"), self)
            retry_action.setFont(body_font())
            retry_action.triggered.connect(lambda: self._execute_task_and_refresh(task, TaskAction.RETRY))
            menu.addAction(retry_action)

        if task.get("status") in ["completed", "failed", "cancelled"]:
            redownload_action = QAction(_("download.redownload_action"), self)
            redownload_action.setFont(body_font())
            redownload_action.triggered.connect(lambda: self._redownload_task(task))
            menu.addAction(redownload_action)

        menu.addSeparator()

        copy_path_action = QAction(_("download.copy_path_action"), self)
        copy_path_action.setFont(body_font())
        copy_path_action.triggered.connect(lambda: self._copy_path(task))
        menu.addAction(copy_path_action)

        delete_action = QAction(_("download.delete_task_action"), self)
        delete_action.setFont(body_font())
        delete_action.triggered.connect(lambda: self._delete_task(task))
        menu.addAction(delete_action)

        menu.exec(self.download_table.mapToGlobal(pos))

    def _open_file(self, task):
        save_path = task.get("save_path", "")
        if save_path and os.path.exists(save_path):
            if not open_file(save_path):
                QMessageBox.warning(self, _("common.tip"), _("download.file_not_ready"))
        else:
            QMessageBox.warning(self, _("common.tip"), _("download.file_not_ready"))

    def _format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"

    def _format_speed(self, speed_bytes):
        return f"{self._format_size(speed_bytes)}/s"

    def _open_file_folder(self, task):
        save_path = task.get("save_path", "")
        if save_path:
            folder_path = os.path.dirname(save_path)
            if os.path.exists(folder_path):
                open_directory(folder_path, select_file=save_path)

    def _can_execute(self, task, action: TaskAction):
        """检查任务是否可以执行指定动作"""
        if not task:
            return False
        _unused_action, allowed_status = _ACTION_HANDLERS[action]
        return task.get("status") in allowed_status

    def _execute_task_action(self, task_id, action: TaskAction):
        """执行单任务动作"""
        if not task_id:
            return False
        
        task = self.downloader.get_task(task_id)
        if not self._can_execute(task, action):
            return False
            
        method_name, _unused_status = _ACTION_HANDLERS[action]
        getattr(self.downloader, method_name)(task_id)
        return True

    def _execute_task_and_refresh(self, task, action: TaskAction):
        """执行单任务动作并刷新列表"""
        task_id = task.get("task_id")
        if self._execute_task_action(task_id, action):
            self._refresh_list()

    def _execute_batch_action(self, action: TaskAction, tasks=None):
        """执行批量任务动作"""
        candidates = tasks or self.downloader.get_active_tasks()
        changed = False
        for task in candidates:
            task_id = task.get("task_id")
            if self._execute_task_action(task_id, action):
                changed = True
        
        if changed:
            self._refresh_list()

    def _pause_task(self, task):
        self._execute_task_and_refresh(task, TaskAction.PAUSE)

    def _resume_task(self, task):
        self._execute_task_and_refresh(task, TaskAction.RESUME)

    def _cancel_task(self, task):
        self._execute_task_and_refresh(task, TaskAction.CANCEL)

    def _retry_task(self, task):
        self._execute_task_and_refresh(task, TaskAction.RETRY)

    def _redownload_task(self, task):
        url = task.get("url")
        title = task.get("title")
        chapters = task.get("chapters")
        if url:
            self.downloader.add_download_task(url, title=title, chapters=chapters)
            self._refresh_list()
            log("SUCCESS", f"已添加重新下载任务: {title}")

    def _copy_path(self, task):
        save_path = task.get("save_path", "")
        if save_path:
            QApplication.clipboard().setText(save_path)

    def _delete_task(self, task):
        reply = QMessageBox.question(
            self, _("common.confirm"), _("download.confirm_delete_task"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            task_id = task.get("task_id")
            if task_id:
                self.downloader.remove_task(task_id)
            self._refresh_list()

    def _pause_all(self):
        self._execute_batch_action(TaskAction.PAUSE)

    def _resume_all(self):
        self._execute_batch_action(TaskAction.RESUME)

    def _cancel_all(self):
        reply = QMessageBox.question(
            self, _("common.confirm"), _("download.confirm_cancel_all"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._execute_batch_action(TaskAction.CANCEL)

    def _open_folder(self):
        folder_path = self.downloader.get_download_dir()
        if os.path.exists(folder_path):
            if not open_directory(folder_path):
                QMessageBox.warning(self, _("common.error"), _("download.download_folder_missing"))
        else:
            QMessageBox.warning(self, _("common.error"), _("download.download_folder_missing"))

    def _clear_history(self):
        reply = QMessageBox.question(
            self, _("common.confirm"), _("download.confirm_clear_finished"),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.downloader.clear_all_tasks()
            self._refresh_list()

    def get_downloader(self):
        return self.downloader

    def add_url_from_resource(self, url, title=None, chapters=None):
        if url:
            task_id = self.downloader.add_download_task(url, title=title, chapters=chapters)
            if task_id is None:
                return False
            self._refresh_list()
            log("SUCCESS", f"已添加下载任务: {task_id}")
            return True
        return False

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        for url in urls:
            local_path = url.toLocalFile()
            if local_path and os.path.exists(local_path):
                log("INFO", f"拖入文件: {local_path}")

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新下载页面所有视觉元素

        Args:
            primary: 主题主色
            background: 主题背景色
        """
        self._accent_color = primary

        # 刷新页面头部（大标题 + 图标）
        if hasattr(self, 'header_widget'):
            from gui.widgets.page_header import PageHeader
            PageHeader.update_header(
                self.header_widget,
                self.icon_manager,
                primary,
                "title_download.svg",
            )

        # 刷新下载表格样式
        self.download_table.setStyleSheet(get_fluent_table_style(primary))

        # 刷新统计标签颜色
        if hasattr(self, 'stats_labels'):
            colors = {
                'waiting': '#FFC107',
                'downloading': primary,
                'paused': '#6C757D',
                'completed': '#28A745',
                'failed': '#DC3545'
            }
            for key, label in self.stats_labels.items():
                label.setStyleSheet(f"color: {colors.get(key, primary)};")

        # 刷新统计图标颜色（下载中图标跟随主题色）
        if hasattr(self, 'stats_icon_labels'):
            downloading_icon = self.stats_icon_labels.get('downloading')
            if downloading_icon:
                icon_pixmap = self._load_status_icon(
                    "02_media_tech/下载_svg.svg", primary, (16, 16)
                )
                if icon_pixmap:
                    downloading_icon.setPixmap(icon_pixmap)

        # 刷新进度条渐变颜色
        self.total_progress_bar.setGradientColors(primary, self._adjust_color(primary, 30))

        # 刷新操作按钮颜色
        self.pause_all_btn.setAccentColor(primary)
        self.resume_all_btn.setAccentColor(primary)
        self.cancel_all_btn.setAccentColor(primary)
        self.open_folder_btn.setAccentColor(primary)
        self.refresh_btn.setAccentColor(primary)
        self.clear_history_btn.setAccentColor(primary)
