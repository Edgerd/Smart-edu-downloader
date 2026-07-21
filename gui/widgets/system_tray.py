# -*- coding: utf-8 -*-
"""系统托盘模块"""
from core.i18n import _

import os
from PyQt5.QtWidgets import QSystemTrayIcon, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from core.infrastructure.logger import log
from gui.widgets.rounded_menu import RoundedMenu
from gui.styles import load_primary_color


class SystemTrayManager(QObject):
    """系统托盘管理器"""
    
    show_window_requested = pyqtSignal()
    quit_requested = pyqtSignal()
    
    def __init__(self, main_window=None):
        """初始化托盘管理器"""
        super().__init__(main_window)
        self.main_window = main_window
        self.tray_icon = None
        self.tray_menu = None
        self._progress_value = 0
        self._progress_text = ""
        self._original_icon = None
        self._is_showing_progress = False
        
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_dir = os.path.join(base_dir, "resources", "logo")
        resources_dir = os.path.join(base_dir, "resources", "images")
        self._icon_paths = [
            os.path.join(logo_dir, "logo_48x48.png"),
            os.path.join(logo_dir, "logo_48x48.ico"),
            os.path.join(resources_dir, "icon.png"),
            os.path.join(resources_dir, "app_icon.ico"),
            os.path.join(resources_dir, "favicon.ico"),
        ]
    
    def init_tray(self):
        """初始化系统托盘"""
        try:
            if not QSystemTrayIcon.isSystemTrayAvailable():
                log("WARNING", "系统不支持托盘图标")
                return False
            
            self.tray_icon = QSystemTrayIcon(self.main_window)
            self._original_icon = self._create_icon()
            self.tray_icon.setIcon(self._original_icon)
            self.tray_icon.setToolTip("Smart Edu Downloader")
            self._create_tray_menu()
            self.tray_icon.activated.connect(self._on_activated)
            self.tray_icon.show()
            
            log("SUCCESS", "系统托盘已初始化")
            return True
            
        except Exception as e:
            log("ERROR", f"初始化系统托盘失败: {e}")
            return False
    
    def _get_icon_path(self):
        """获取图标路径"""
        for path in self._icon_paths:
            if os.path.exists(path):
                return path
        return ""
    
    def _create_icon(self):
        """创建托盘图标"""
        icon_path = self._get_icon_path()
        if icon_path:
            log("INFO", f"加载托盘图标: {icon_path}")
            return QIcon(icon_path)
        
        log("WARNING", "未找到托盘图标文件，使用默认图标")
        return self._draw_default_icon()
    
    def _draw_default_icon(self, size=32, show_progress=False, progress=0):
        """绘制默认托盘图标"""
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        try:
            accent_color = load_primary_color()
            if show_progress and progress > 0:
                self._draw_progress_icon(painter, size, progress, accent_color)
            else:
                self._draw_normal_icon(painter, size, accent_color)
        finally:
            if painter.isActive():
                painter.end()

        return QIcon(pixmap)

    def _draw_normal_icon(self, painter, size, accent_color):
        """绘制普通托盘图标"""
        painter.setBrush(QColor(accent_color))
        painter.setPen(Qt.NoPen)
        margin = size * 2 // 32
        painter.drawEllipse(
            margin, margin,
            size - margin * 2, size - margin * 2
        )

        painter.setPen(QColor("white"))
        font = QFont("Arial", size // 2, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 0, size, size, Qt.AlignCenter, "S")

    def _draw_progress_icon(self, painter, size, progress, accent_color):
        """绘制带进度的托盘图标"""
        margin = size * 2 // 32
        rect_margin = margin
        rect_size = size - margin * 2

        painter.setBrush(QColor("#E0E0E0"))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(
            rect_margin, rect_margin,
            rect_size, rect_size
        )

        if progress > 0:
            painter.setBrush(QColor(accent_color))
            start_angle = 90 * 16
            span_angle = -int(progress * 360 * 16 / 100)
            painter.drawPie(
                rect_margin, rect_margin,
                rect_size, rect_size,
                start_angle, span_angle
            )
        
        painter.setPen(QColor("white"))
        font = QFont("Arial", size // 3, QFont.Bold)
        painter.setFont(font)
        painter.drawText(0, 0, size, size, Qt.AlignCenter, f"{int(progress)}%")
    
    def _create_tray_menu(self):
        """创建托盘菜单"""
        self.tray_menu = RoundedMenu()
        from gui.styles import apply_menu_style
        apply_menu_style(self.tray_menu)  # 修复：解决托盘菜单黑色背景

        show_action = QAction(_("widgets.system_tray.show_main_window"), self.main_window)
        show_action.triggered.connect(lambda: self.show_window_requested.emit())
        self.tray_menu.addAction(show_action)
        
        self.tray_menu.addSeparator()
        
        self.progress_action = QAction(_("widgets.system_tray.progress_not_started"), self.main_window)
        self.progress_action.setEnabled(False)
        self.tray_menu.addAction(self.progress_action)
        
        self.tray_menu.addSeparator()
        
        quit_action = QAction(_("widgets.system_tray.quit_app"), self.main_window)
        quit_action.triggered.connect(lambda: self.quit_requested.emit())
        self.tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
    
    def _on_activated(self, reason):
        """处理托盘图标激活事件"""
        if reason in (QSystemTrayIcon.DoubleClick, QSystemTrayIcon.Trigger):
            self.show_window_requested.emit()
    
    def show_message(self, title, message, icon=QSystemTrayIcon.Information, duration=3000):
        """显示托盘通知消息"""
        if self.tray_icon and self.tray_icon.isVisible():
            try:
                self.tray_icon.showMessage(title, message, icon, duration)
                log("DEBUG", f"托盘通知: {title} - {message}")
            except Exception as e:
                log("ERROR", f"显示托盘通知失败: {e}")
    
    def update_progress(self, progress, text):
        """更新托盘进度显示"""
        self._progress_value = progress
        self._progress_text = text
        
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.setToolTip(f"Smart Edu Downloader\n{text}")
        
        if hasattr(self, 'progress_action'):
            self.progress_action.setText(_("widgets.system_tray.progress_template", text=text))
    
    def update_icon_with_progress(self, progress):
        """更新托盘图标显示进度"""
        if not self.tray_icon or not self.tray_icon.isVisible():
            return
        
        try:
            progress_icon = self._draw_default_icon(size=32, show_progress=True, progress=progress)
            self.tray_icon.setIcon(progress_icon)
            self._is_showing_progress = True
            
        except Exception as e:
            log("ERROR", f"更新托盘图标失败: {e}")
    
    def reset_icon(self):
        """重置托盘图标"""
        if self.tray_icon and self._original_icon and self._is_showing_progress:
            try:
                self.tray_icon.setIcon(self._original_icon)
                self._is_showing_progress = False
                log("DEBUG", "托盘图标已重置")
            except Exception as e:
                log("ERROR", f"重置托盘图标失败: {e}")
    
    def hide_tray(self):
        """隐藏托盘图标"""
        if self.tray_icon and self.tray_icon.isVisible():
            self.tray_icon.hide()
            log("INFO", "托盘图标已隐藏")
    
    def show_tray(self):
        """显示托盘图标"""
        if self.tray_icon and not self.tray_icon.isVisible():
            self.tray_icon.show()
            log("INFO", "托盘图标已显示")
    
    def is_visible(self):
        """检查托盘图标是否可见"""
        return self.tray_icon is not None and self.tray_icon.isVisible()
    
    def cleanup(self):
        """清理托盘资源"""
        if self.tray_icon:
            try:
                self.tray_icon.hide()
                self.tray_icon.deleteLater()
                self.tray_icon = None
                log("INFO", "托盘资源已清理")
            except Exception as e:
                log("ERROR", f"清理托盘资源失败: {e}")
