# -*- coding: utf-8 -*-
"""
状态栏管理模块
"""
from core.i18n import _
from PyQt5.QtCore import pyqtSignal, QObject


class StatusBarManager(QObject):
    """状态栏管理器"""
    
    # 定义信号
    status_updated = pyqtSignal(str)
    
    def __init__(self, main_window=None):
        """初始化状态栏管理器"""
        super().__init__()
        self.main_window = main_window
        self.status_label = None
        self._init_status_bar()
        self._button_tooltips = self._load_button_tooltips()
    
    def _init_status_bar(self):
        """初始化状态栏"""
        if self.main_window and hasattr(self.main_window, 'status_label'):
            self.status_label = self.main_window.status_label
    
    def _load_button_tooltips(self):
        """加载按钮提示信息
        
        包含所有按钮的详细注释
        """
        return {
            # 标题栏按钮
            'minimize': _("core.status_bar.minimize_tooltip"),
            'maximize': _("core.status_bar.maximize_tooltip"),
            'close': _("core.status_bar.close_tooltip"),

            # 导航栏按钮
            'nav_home': _("core.tooltips.nav_home"),
            'nav_resource': _("core.tooltips.nav_resource"),
            'nav_download': _("core.tooltips.nav_download"),
            'nav_setting': _("core.tooltips.nav_settings"),
            'nav_more': _("core.tooltips.nav_more"),

            # 主页按钮
            'smart_btn': _("main_window.smart_search_tooltip"),
            'open_in_browser': _("core.tooltips.open_in_browser"),
            'clear_all': _("core.tooltips.clear_all"),

            # URL输入框
            'url_input': _("main_window.url_input_tooltip"),

            # 结果区域
            'result_text': _("core.tooltips.result_text"),
            'progress_bar': _("core.tooltips.progress_bar"),
            'loading_label': _("core.tooltips.loading_label"),

            # 历史记录区域
            'history_table': _("core.tooltips.history_table"),
            'clear_history': _("core.tooltips.clear_history"),

            # 资源库按钮
            'refresh_list': _("core.tooltips.refresh_list"),
            'add_to_download': _("core.tooltips.add_to_download"),
            'search_resource': _("core.tooltips.search_resource"),
            'start_search': _("core.tooltips.start_search"),
            'clear_search': _("core.tooltips.clear_search"),
            'input_resource_url': _("core.tooltips.input_resource_url"),
            'parse_resource_url': _("core.tooltips.parse_resource_url"),
            'chapter_tree': _("core.tooltips.chapter_tree"),
            'search_result_table': _("core.tooltips.search_result_table"),
            'prev_page': _("core.tooltips.prev_page"),
            'next_page': _("core.tooltips.next_page"),

            # 下载界面按钮
            'start_all': _("core.tooltips.start_all"),
            'pause_all': _("core.tooltips.pause_all"),
            'resume_all': _("core.tooltips.resume_all"),
            'cancel_all': _("core.tooltips.cancel_all"),
            'clear_completed': _("core.tooltips.clear_completed"),
            'clear_failed': _("core.tooltips.clear_failed"),
            'clear_cancelled': _("core.tooltips.clear_cancelled"),
            'open_folder': _("core.tooltips.open_folder"),
            're_download': _("core.tooltips.re_download"),
            'download_table': _("core.tooltips.download_table"),

            # 更多功能界面按钮
            'clear_history_more': _("core.tooltips.clear_history_more"),
            'view_log': _("core.tooltips.view_log"),
            'donation': _("core.tooltips.donation"),
            'bilibili': _("core.tooltips.bilibili"),
            'download_history_table': _("core.tooltips.download_history_table"),
            'link_history_table': _("core.tooltips.link_history_table"),
            'search_history_table': _("core.tooltips.search_history_table"),
        }
    
    def set_status(self, text):
        """设置状态栏文本
        
        Args:
            text: 要显示的状态栏文本
        """
        if self.status_label:
            self.status_label.setText(text)
        self.status_updated.emit(text)
    
    def set_process_status(self, step, total):
        """设置处理状态
        
        Args:
            step: 当前步骤
            total: 总步骤
        """
        status_text = _('core.status_bar.processing_template', arg1={step}, arg2={total})
        self.set_status(status_text)
    
    def set_download_status(self, progress, filename):
        """设置下载状态
        
        Args:
            progress: 下载进度（0-100）
            filename: 文件名
        """
        status_text = _('core.status_bar.downloading_template', arg1={filename}, arg2={progress})
        self.set_status(status_text)
    
    def set_ready_status(self):
        """设置就绪状态"""
        self.set_status(_("common.status_ready"))
    
    def set_error_status(self, error_msg):
        """设置错误状态
        
        Args:
            error_msg: 错误信息
        """
        status_text = _('core.status_bar.error_template', arg1={error_msg})
        self.set_status(status_text)
    
    def set_info_status(self, info_msg):
        """设置信息状态
        
        Args:
            info_msg: 信息内容
        """
        status_text = _('core.status_bar.info_template', arg1={info_msg})
        self.set_status(status_text)
    
    def add_button_tooltip(self, button, tooltip_key):
        """为按钮添加悬停提示
        
        Args:
            button: 按钮对象
            tooltip_key: 提示信息的键
        """
        if button and tooltip_key in self._button_tooltips:
            tooltip = self._button_tooltips[tooltip_key]
            button.setToolTip(tooltip)
            button.setMouseTracking(True)
    
    def add_widget_tooltip(self, widget, tooltip_text):
        """为任意控件添加悬停提示
        
        Args:
            widget: 控件对象
            tooltip_text: 提示文本
        """
        if widget:
            widget.setToolTip(tooltip_text)
            widget.setMouseTracking(True)
    
    def update_all_tooltips(self, main_window):
        """更新所有按钮的提示信息
        
        Args:
            main_window: 主窗口对象
        """
        # 直接为标题栏按钮添加提示信息
        if hasattr(main_window, 'min_btn'):
            main_window.min_btn.setToolTip(_("core.status_bar.minimize_tooltip"))
            main_window.min_btn.setMouseTracking(True)
        
        if hasattr(main_window, 'max_btn'):
            main_window.max_btn.setToolTip(_("core.status_bar.maximize_tooltip"))
            main_window.max_btn.setMouseTracking(True)
        
        if hasattr(main_window, 'close_btn'):
            main_window.close_btn.setToolTip(_("core.status_bar.close_tooltip"))
            main_window.close_btn.setMouseTracking(True)
        
        # 为导航栏按钮添加提示信息
        if hasattr(main_window, 'nav_buttons'):
            nav_tooltips = [
                _("core.tooltips.nav_home"),
                _("core.tooltips.nav_resource"),
                _("core.tooltips.nav_download"),
                _("core.tooltips.nav_settings"),
                _("core.tooltips.nav_more"),
            ]
            for i, btn in enumerate(main_window.nav_buttons):
                if i < len(nav_tooltips):
                    btn.setToolTip(nav_tooltips[i])
                    btn.setMouseTracking(True)
        
        # 为主页按钮添加提示信息（如果主页已加载）
        if hasattr(main_window, 'pages') and main_window.pages[0]:
            home_page = main_window.pages[0]
            if hasattr(home_page, 'smart_btn'):
                home_page.smart_btn.setToolTip(_("main_window.smart_search_tooltip"))
                home_page.smart_btn.setMouseTracking(True)
            if hasattr(home_page, 'url_input'):
                home_page.url_input.setToolTip(_("main_window.url_input_tooltip"))
                home_page.url_input.setMouseTracking(True)
    
    def get_tooltip(self, tooltip_key):
        """获取指定键的提示信息
        
        Args:
            tooltip_key: 提示信息的键
            
        Returns:
            str: 提示信息文本
        """
        return self._button_tooltips.get(tooltip_key, '')


# 全局状态栏管理器实例
_global_status_manager = None


def get_status_manager(main_window=None):
    """获取全局状态栏管理器实例
    
    Args:
        main_window: 主窗口对象
        
    Returns:
        StatusBarManager: 状态栏管理器实例
    """
    global _global_status_manager
    if _global_status_manager is None:
        _global_status_manager = StatusBarManager(main_window)
    elif main_window:
        # 总是使用最新的main_window来更新状态栏
        _global_status_manager.main_window = main_window
        _global_status_manager._init_status_bar()
        # 重新更新所有按钮的提示信息
        _global_status_manager.update_all_tooltips(main_window)
    return _global_status_manager


def set_status(text):
    """设置状态栏文本（便捷函数）
    
    Args:
        text: 要显示的状态栏文本
    """
    manager = get_status_manager()
    manager.set_status(text)


def set_process_status(step, total):
    """设置处理状态（便捷函数）
    
    Args:
        step: 当前步骤
        total: 总步骤
    """
    manager = get_status_manager()
    manager.set_process_status(step, total)


def set_download_status(progress, filename):
    """设置下载状态（便捷函数）
    
    Args:
        progress: 下载进度（0-100）
        filename: 文件名
    """
    manager = get_status_manager()
    manager.set_download_status(progress, filename)


def set_ready_status():
    """设置就绪状态（便捷函数）"""
    manager = get_status_manager()
    manager.set_ready_status()


def set_error_status(error_msg):
    """设置错误状态（便捷函数）
    
    Args:
        error_msg: 错误信息
    """
    manager = get_status_manager()
    manager.set_error_status(error_msg)


def set_info_status(info_msg):
    """设置信息状态（便捷函数）
    
    Args:
        info_msg: 信息内容
    """
    manager = get_status_manager()
    manager.set_info_status(info_msg)
