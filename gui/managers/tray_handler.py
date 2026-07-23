# -*- coding: utf-8 -*-
"""托盘处理器 - 系统托盘初始化、事件处理、进度更新"""

from core.infrastructure.logger import log
from core.i18n import _


class TrayHandler:
    """托盘处理器"""
    
    def __init__(self, main_window):
        """初始化"""
        self.main_window = main_window
    
    def init_system_tray(self):
        """初始化系统托盘"""
        try:
            from gui.widgets.system_tray import SystemTrayManager
            
            self.main_window.tray_manager = SystemTrayManager(self.main_window)
            tray_success = self.main_window.tray_manager.init_tray()
            
            if tray_success:
                self.main_window.tray_manager.show_window_requested.connect(self.on_show_from_tray)
                self.main_window.tray_manager.quit_requested.connect(self.on_quit_from_tray)
                
                log("INFO", "系统托盘初始化成功")
            else:
                self.main_window.tray_manager = None
                log("WARNING", "系统托盘不可用")
                
        except Exception as e:
            log("ERROR", f"初始化系统托盘失败: {e}")
            self.main_window.tray_manager = None
    
    def connect_downloader_signals(self):
        """连接下载器信号到托盘"""
        if self.main_window.tray_manager and self.main_window.downloader:
            # 先断开旧连接再重连，避免重复初始化托盘时回调被翻倍连接
            try:
                self.main_window.downloader.progress_updated.disconnect(self.on_download_progress_for_tray)
            except Exception:
                pass
            self.main_window.downloader.progress_updated.connect(self.on_download_progress_for_tray)
            log("INFO", "已连接下载器进度信号到托盘")
    
    def on_show_from_tray(self):
        """从托盘显示窗口"""
        self.main_window.showNormal()
        self.main_window.raise_()
        self.main_window.activateWindow()
        self.main_window._minimized_to_tray = False
        log("INFO", "已从托盘恢复窗口")
    
    def on_quit_from_tray(self):
        """从托盘退出"""
        log("INFO", "用户从托盘退出")
        self.main_window._cleanup_and_quit()
    
    def on_download_progress_for_tray(self, progress, text):
        """下载进度更新通知托盘"""
        if self.main_window.tray_manager:
            try:
                self.main_window.tray_manager.update_progress(progress, text)
                if int(progress) % 25 == 0:
                    self.main_window.tray_manager.update_icon_with_progress(progress)
            except Exception as e:
                log("ERROR", f"更新托盘进度失败: {e}")
    
    def handle_close_event(self, event):
        """处理窗口关闭事件"""
        try:
            from gui.pages.setting_page import SettingPage
            settings = SettingPage.load_settings()
            minimize_to_tray = settings.get('minimize_to_tray', True)
            
            if minimize_to_tray and self.main_window.tray_manager:
                self.main_window.hide()
                self.main_window._minimized_to_tray = True
                
                # 显示托盘通知
                if settings.get('tray_notifications', True):
                    self.main_window.tray_manager.show_message(
                        "Smart Edu Downloader",
                        _('widgets.system_tray.minimized_to_tray_message')
                    )
                
                event.ignore()
                return True  # 表示已处理
        except Exception as e:
            log("ERROR", f"处理关闭事件失败: {e}")
        
        return False  # 表示未处理，交给主窗口真正关闭
    
    def cleanup(self):
        """清理托盘资源"""
        try:
            if hasattr(self.main_window, 'tray_manager') and self.main_window.tray_manager:
                self.main_window.tray_manager.cleanup()
        except Exception as e:
            log("ERROR", f"清理托盘资源失败: {e}")
