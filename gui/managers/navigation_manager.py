# -*- coding: utf-8 -*-
"""导航管理器 - 导航路由、页面切换、按钮状态"""

import traceback
from PyQt5.QtCore import QTimer

from core.infrastructure.logger import log


class NavigationManager:
    """导航管理器 - 管理页面切换和导航按钮状态"""
    
    def __init__(self, main_window):
        """初始化"""
        self.main_window = main_window
        self.current_page_index = 0
    
    def switch_page(self, index):
        """切换页面"""
        if index == self.current_page_index:
            return

        old_index = self.current_page_index
        self.current_page_index = index

        # 立即切换页面显示
        if self.main_window.page_manager.is_page_loaded(index):
            self.main_window.stacked_widget.setCurrentWidget(
                self.main_window.page_manager.get_page(index)
            )
            self.main_window.page_manager.update_page_instances(index)
        else:
            QTimer.singleShot(0, lambda idx=index: self._load_and_switch_page_safe(idx))

        try:
            self.main_window.animation_manager.animate_tab_switch(old_index, index)
        except Exception:
            pass
    
    def _load_and_switch_page_safe(self, index):
        """安全加载页面并切换"""
        try:
            self._load_and_switch_page(index)
        except Exception as e:
            from core.infrastructure.logger import log
            log("ERROR", f"延迟加载页面 {index} 失败: {e}\n{traceback.format_exc()}")
    
    def _load_and_switch_page(self, index):
        """加载页面并切换"""
        if self.main_window.page_manager.is_page_loaded(index):
            return
            
        self.main_window.page_manager.load_page(index)
        self.main_window.stacked_widget.setCurrentWidget(
            self.main_window.page_manager.get_page(index)
        )
        self.main_window.page_manager.update_page_instances(index)
    
    def update_button_styles(self, selected_index):
        """更新按钮样式"""
        if hasattr(self.main_window, 'nav_bar') and hasattr(self.main_window.nav_bar, 'set_active_button'):
            self.main_window.nav_bar.set_active_button(selected_index)
    
    def navigate_to_setting_and_highlight_token(self):
        """跳转到设置页面并高亮Token输入框"""
        try:
            if self.current_page_index != 3:
                self.switch_page(3)
                log("INFO", "已自动切换到设置页面")
            
            def do_highlight():
                setting_page = self.main_window.page_manager.get_page(3)
                if setting_page and hasattr(setting_page, 'highlight_token_input'):
                    setting_page.highlight_token_input()
                    log("SUCCESS", "已触发 Access Token 输入框高亮")
                else:
                    log("WARNING", "设置页面未加载或不支持高亮功能")
            
            # 延迟 300ms 执行，确保页面已切换
            QTimer.singleShot(300, do_highlight)
            
        except Exception as e:
            log("ERROR", f"跳转到设置页面失败: {e}")
    
    def get_current_index(self):
        """获取当前页面索引"""
        return self.current_page_index
    
    def set_current_index(self, index):
        """设置当前页面索引"""
        self.current_page_index = index
