# -*- coding: utf-8 -*-
"""
页面管理器
职责：页面加载、预加载、实例更新
"""

import traceback
from PyQt5.QtCore import QTimer

from core.infrastructure.logger import log


class PageManager:
    """页面管理器 - 管理页面生命周期
    
    属性:
        main_window: 主窗口引用
        pages: 页面实例列表
        page_loaded: 页面加载状态列表
        preload_pending: 预加载等待状态字典
    """
    
    PAGE_COUNT = 5
    
    def __init__(self, main_window):
        """初始化页面管理器
        
        Args:
            main_window: 主窗口实例引用
        """
        self.main_window = main_window
        self.pages = [None] * self.PAGE_COUNT
        self.page_loaded = [False] * self.PAGE_COUNT
        self.preload_pending = {}
    
    def load_page(self, index):
        """加载指定页面 - 延迟加载
        
        Args:
            index: 页面索引 (0-4)
        """
        if not (0 <= index < self.PAGE_COUNT):
            log("ERROR", f"页面索引越界: {index}")
            return
        if self.page_loaded[index]:
            return
        
        page = self._create_page_instance(index)
        if page is None:
            log("ERROR", f"创建页面 {index} 实例失败，返回 None")
            return
        
        self.pages[index] = page
        self.main_window.stacked_widget.addWidget(page)
        self.page_loaded[index] = True
        log("INFO", f"页面 {index} 已加载")
        
        # 同步页面的共享实例（确保 downloader/resource_lib 是最新的）
        self.update_page_instances(index)
        
        # 如果加载的是设置页面，连接设置保存信号
        if index == 3 and hasattr(page, 'settings_saved'):
            page.settings_saved.connect(self.main_window._on_settings_saved)
    
    def preload_page(self, index):
        """预加载页面 - 鼠标悬停时触发
        
        Args:
            index: 页面索引 (0-4)
        """
        if not (0 <= index < self.PAGE_COUNT):
            return
        # 防止重复触发预加载
        if self.preload_pending.get(index, False):
            return
        if not self.page_loaded[index]:
            self.preload_pending[index] = True
            # 安全模式：使用默认参数绑定值，避免 lambda 闭包隐患
            QTimer.singleShot(100, lambda idx=index: self._do_preload_page_safe(idx))
    
    def do_preload_page(self, index):
        """执行实际的预加载
        
        Args:
            index: 页面索引 (0-4)
        """
        self.preload_pending[index] = False
        self.load_page(index)
    
    def _do_preload_page_safe(self, index):
        """安全执行预加载（带异常保护）
        
        Args:
            index: 页面索引 (0-4)
        """
        try:
            self.do_preload_page(index)
        except Exception as e:
            from core.infrastructure.logger import log
            log("ERROR", f"预加载页面 {index} 失败: {e}\n{traceback.format_exc()}")
    
    def update_page_instances(self, index):
        """更新页面的共享实例
        
        Args:
            index: 页面索引 (0-4)
        """
        if not (0 <= index < self.PAGE_COUNT):
            return
        page = self.pages[index]
        if page is None:
            return
        
        # 始终同步页面的 downloader 引用（即使为 None 也同步，保持状态一致）
        if hasattr(page, 'downloader'):
            page.downloader = self.main_window.downloader
        if hasattr(page, 'set_downloader'):
            page.set_downloader(self.main_window.downloader)
        if hasattr(page, 'resource_lib'):
            page.resource_lib = self.main_window.resource_lib
            # 如果页面是资源页面且还没加载过资源列表，触发延迟加载
            if self.main_window.resource_lib and hasattr(page, '_load_resource_list_async') and hasattr(page, '_resource_list_loaded') and not page._resource_list_loaded:
                log("DEBUG", f"页面 {index} resource_lib 已注入，触发延迟加载")
                page._load_resource_list_async()
                page._resource_list_loaded = True
        if hasattr(page, 'main_window'):
            page.main_window = self.main_window
    
    def _create_page_instance(self, index):
        """创建页面实例
        
        Args:
            index: 页面索引 (0-4)
            
        Returns:
            QWidget or None: 页面实例
        """
        from gui.pages import HomePage, DownloadPage, SettingPage, MorePage, ResourcePage
        
        if index == 0:
            return HomePage(
                main_window=self.main_window,
                downloader=self.main_window.downloader,
                resource_lib=self.main_window.resource_lib
            )
        elif index == 1:
            return ResourcePage(
                downloader=self.main_window.downloader,
                resource_lib=self.main_window.resource_lib
            )
        elif index == 2:
            return DownloadPage(downloader=self.main_window.downloader)
        elif index == 3:
            return SettingPage(downloader=self.main_window.downloader)
        elif index == 4:
            page = MorePage()
            if self.main_window.downloader:
                page.set_downloader(self.main_window.downloader)
            return page
        
        return None
    
    def is_page_loaded(self, index):
        """检查页面是否已加载
        
        Args:
            index: 页面索引
            
        Returns:
            bool: 页面是否已加载
        """
        if not (0 <= index < self.PAGE_COUNT):
            return False
        return self.page_loaded[index]
    
    def get_page(self, index):
        """获取页面实例
        
        Args:
            index: 页面索引
            
        Returns:
            QWidget or None: 页面实例
        """
        if not (0 <= index < self.PAGE_COUNT):
            return None
        return self.pages[index]
