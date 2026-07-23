# -*- coding: utf-8 -*-
"""鼠标悬停提示混入类"""

from PyQt5.QtCore import QEvent
from PyQt5.QtWidgets import QWidget


class HoverTooltipMixin:
    """鼠标悬停提示混入类"""

    def setup_hover_tooltips(self):
        """初始化鼠标悬停事件处理 - 安装事件过滤器"""
        if not hasattr(self, '_hover_initialized'):
            self.installEventFilter(self)
            self._hover_initialized = True

    def _init_mouse_hover_events(self):
        """初始化鼠标悬停事件处理 - setup_hover_tooltips 的兼容别名

        保留旧名称以便现有页面（home_page/download_page/resource_page/more_page）
        继续使用一致的调用入口。
        """
        self.setup_hover_tooltips()

    def _get_status_manager(self):
        """获取状态栏管理器 - 子类可重写"""
        return getattr(self, 'status_manager', None)

    def _get_hover_tooltips(self):
        """获取悬停提示映射 - 子类可重写"""
        return getattr(self, '_hover_tooltips', {})

    def eventFilter(self, obj, event):
        """事件过滤器 - 处理鼠标悬停事件"""
        status_manager = self._get_status_manager()
        if status_manager is not None:
            if event.type() == QEvent.Enter:
                tooltips = self._get_hover_tooltips()
                for attr_name, tooltip_key in tooltips.items():
                    if hasattr(self, attr_name) and getattr(self, attr_name) is obj:
                        tooltip = status_manager.get_tooltip(tooltip_key)
                        if tooltip:
                            status_manager.set_status(tooltip)
                        break
            elif event.type() == QEvent.Leave:
                status_manager.set_ready_status()

        return QWidget.eventFilter(self, obj, event)
