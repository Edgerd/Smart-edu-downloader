# -*- coding: utf-8 -*-
"""
滚动隔离工具模块

防止表格/树形控件内的滚轮事件穿透到外层 QScrollArea。
当鼠标悬停在表格内时，滚轮只滚动表格内容，不滚动外层页面。
"""

from PyQt5.QtCore import QEvent, QObject
from PyQt5.QtWidgets import QTableWidget, QTreeWidget, QAbstractScrollArea


class _WheelEventFilter(QObject):
    """滚轮事件拦截过滤器"""

    def __init__(self, widget: QAbstractScrollArea, parent=None):
        super().__init__(parent)
        self._widget = widget

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and obj is self._widget:
            scrollbar = self._widget.verticalScrollBar()
            if scrollbar and scrollbar.maximum() > scrollbar.minimum():
                event.accept()
                return True
        return super().eventFilter(obj, event)


def install_scroll_isolation(table: QTableWidget):
    """为表格控件安装滚动隔离

    Args:
        table: 要安装滚动隔离的表格控件
    """
    filt = _WheelEventFilter(table, table)
    table.installEventFilter(filt)
    table._scroll_filter = filt


def install_tree_scroll_isolation(tree: QTreeWidget):
    """为树形控件安装滚动隔离

    Args:
        tree: 要安装滚动隔离的树形控件
    """
    filt = _WheelEventFilter(tree, tree)
    tree.installEventFilter(filt)
    tree._scroll_filter = filt
