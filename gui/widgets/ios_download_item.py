# -*- coding: utf-8 -*-
"""iOS风格下载项组件"""

from PyQt5.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QFrame, QSizePolicy)
from PyQt5.QtCore import pyqtSignal

from gui.fonts import body_font, small_font
from gui.styles import load_primary_color
from gui.widgets.ios_progress_bar import iOSProgressBar
from gui.widgets.download_status_indicator import DownloadStatusIndicator
from gui.widgets.material_button import MaterialIconButton
from core.i18n import _


class iOSDownloadItem(QFrame):
    """iOS风格下载项组件
    
    特性:
    - 整合进度条和状态指示器
    - 支持操作按钮（暂停/继续、重试、删除等）
    - 平滑的状态切换动画
    - iOS风格的卡片设计
    """
    
    # 信号
    pause_clicked = pyqtSignal(str)      # task_id
    resume_clicked = pyqtSignal(str)     # task_id
    retry_clicked = pyqtSignal(str)      # task_id
    delete_clicked = pyqtSignal(str)     # task_id
    open_file_clicked = pyqtSignal(str)  # save_path
    
    def __init__(self, parent=None, task_id="", filename="", save_path="",
                 total_size=0, downloaded_size=0, status="waiting", speed=0):
        super().__init__(parent)
        
        self._task_id = task_id
        self._filename = filename
        self._save_path = save_path
        self._total_size = total_size
        self._downloaded_size = downloaded_size
        self._status = status
        self._speed = speed
        
        # 样式配置
        self._accent_color = load_primary_color()

        self._setup_ui()
        self._update_display()

    def _update_frame_style(self):
        """更新卡片边框样式，跟随主题色。"""
        self.setStyleSheet(f"""
            QFrame {{
                background: #FFFFFF;
                border: 1px solid #E5E5EA;
                border-radius: 10px;
                padding: 10px;
            }}
            QFrame:hover {{
                border-color: {self._accent_color};
                background: #F8FAFC;
            }}
        """)

    def _setup_ui(self):
        """设置UI"""
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Plain)
        self._update_frame_style()
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(8)
        
        # 设置最小高度
        self.setMinimumHeight(70)
        
        # 顶部行：文件名 + 操作按钮
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)
        
        # 文件名
        self.filename_label = QLabel(self._filename)
        self.filename_label.setFont(body_font())
        self.filename_label.setStyleSheet("color: #1C1C1E;")
        self.filename_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        top_layout.addWidget(self.filename_label)
        
        # 操作按钮容器
        self.action_buttons_layout = QHBoxLayout()
        self.action_buttons_layout.setSpacing(4)
        top_layout.addLayout(self.action_buttons_layout)
        
        self._create_action_buttons()
        
        main_layout.addLayout(top_layout)
        
        # 进度条区域
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(4)
        
        # 进度条
        self.progress_bar = iOSProgressBar()
        self.progress_bar.setBarHeight(8)
        self.progress_bar.setCornerRadius(4)
        self.progress_bar.setFixedHeight(24)
        self.progress_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        progress_layout.addWidget(self.progress_bar)
        
        # 底部信息行：状态指示器 + 大小/速度信息
        info_layout = QHBoxLayout()
        info_layout.setSpacing(8)
        
        # 状态指示器
        self.status_indicator = DownloadStatusIndicator()
        info_layout.addWidget(self.status_indicator)
        
        # 大小/速度信息
        self.info_label = QLabel()
        self.info_label.setFont(small_font())
        self.info_label.setStyleSheet("color: #8E8E93;")
        self.info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        info_layout.addWidget(self.info_label)
        
        progress_layout.addLayout(info_layout)
        
        main_layout.addLayout(progress_layout)
    
    def _create_action_buttons(self):
        """创建操作按钮"""
        # 清除现有按钮
        while self.action_buttons_layout.count():
            item = self.action_buttons_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if self._status == "downloading":
            self._add_button("", self._on_pause, _("widgets.download_item.pause"))
        elif self._status == "paused":
            self._add_button("▶", self._on_resume, _("widgets.download_item.resume"))
        elif self._status == "failed":
            self._add_button("🔄", self._on_retry, _("widgets.download_item.retry"))

        # 所有状态都显示删除按钮
        self._add_button("🗑", self._on_delete, _("common.delete"))

        # 已完成状态显示打开文件按钮
        if self._status == "completed":
            self._add_button("📂", self._on_open_file, _("widgets.download_item.open_file"))
    
    def _add_button(self, icon, callback, tooltip):
        """添加 MD3 图标按钮"""
        btn = MaterialIconButton(icon)
        btn.setFixedSize(28, 28)
        btn._base_button.setCornerRadius(14)
        btn._base_button.setElevation(0, 0)
        btn.setAccentColor(self._accent_color)
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        self.action_buttons_layout.addWidget(btn)
    
    def _update_display(self):
        """更新显示"""
        if self._total_size > 0:
            progress = int((self._downloaded_size / self._total_size) * 100)
            self.progress_bar.setValue(progress)
        else:
            self.progress_bar.setValue(0)
        
        self.status_indicator.setState(self._status)
        
        status_text = self._get_status_text()
        self.status_indicator.setText(status_text)
        
        if self._status == "downloading":
            self.progress_bar.setState(iOSProgressBar.STATE_DOWNLOADING)
        elif self._status == "paused":
            self.progress_bar.setState(iOSProgressBar.STATE_PAUSED)
        elif self._status == "completed":
            self.progress_bar.setState(iOSProgressBar.STATE_COMPLETED)
            self.progress_bar.setValue(100)
        elif self._status == "failed":
            self.progress_bar.setState(iOSProgressBar.STATE_FAILED)
        else:
            self.progress_bar.setState(iOSProgressBar.STATE_WAITING)
        
        self._update_info_label()
        
        self._create_action_buttons()
    
    def _get_status_text(self):
        """获取状态文字"""
        if self._status == "waiting":
            return _("widgets.status_indicator.waiting")
        elif self._status == "downloading":
            return _("widgets.status_indicator.downloading")
        elif self._status == "paused":
            return _("widgets.status_indicator.paused")
        elif self._status == "completed":
            return _("common.status_done")
        elif self._status == "failed":
            return _("widgets.status_indicator.failed")
        return _("common.unknown")
    
    def _update_info_label(self):
        """更新信息标签"""
        downloaded = self._format_size(self._downloaded_size)
        total = self._format_size(self._total_size)
        
        if self._status == "completed":
            self.info_label.setText(f"{total}")
        elif self._status == "downloading" and self._speed > 0:
            speed = self._format_size(self._speed)
            self.info_label.setText(f"{downloaded} / {total}  ·  {speed}/s")
        elif self._status == "failed":
            self.info_label.setText(f"{downloaded} / {total}")
        else:
            self.info_label.setText(f"{downloaded} / {total}")
    
    def _format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    # 事件处理
    def _on_pause(self):
        self.pause_clicked.emit(self._task_id)
    
    def _on_resume(self):
        self.resume_clicked.emit(self._task_id)
    
    def _on_retry(self):
        self.retry_clicked.emit(self._task_id)
    
    def _on_delete(self):
        self.delete_clicked.emit(self._task_id)
    
    def _on_open_file(self):
        self.open_file_clicked.emit(self._save_path)
    
    # 公共方法
    def update_task(self, task):
        """更新任务数据"""
        self._task_id = task.get("task_id", self._task_id)
        self._filename = task.get("title", self._filename)
        self._save_path = task.get("save_path", self._save_path)
        self._total_size = task.get("total_size", self._total_size)
        self._downloaded_size = task.get("downloaded_size", self._downloaded_size)
        self._status = task.get("status", self._status)
        self._speed = task.get("speed", self._speed)
        
        display_name = self._filename
        if display_name and len(display_name) > 30:
            display_name = display_name[:30] + "..."
        self.filename_label.setText(display_name or _("common.unnamed"))
        
        self._update_display()
    
    def set_accent_color(self, color):
        """设置强调色"""
        self._accent_color = color
        self.progress_bar.setGradientColors(color, self._adjust_color(color, 30))
        self._update_frame_style()
        self._create_action_buttons()
        self.update()

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新下载项视觉元素。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        self.set_accent_color(primary)

    def _adjust_color(self, color_str, adjustment):
        """调整颜色亮度"""
        from PyQt5.QtGui import QColor
        color = QColor(color_str)
        r = max(0, min(255, color.red() + adjustment))
        g = max(0, min(255, color.green() + adjustment))
        b = max(0, min(255, color.blue() + adjustment))
        return QColor(r, g, b)
    
    def task_id(self):
        """获取任务ID"""
        return self._task_id
    
    def save_path(self):
        """获取保存路径"""
        return self._save_path
