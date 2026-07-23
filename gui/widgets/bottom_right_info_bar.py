# -*- coding: utf-8 -*-
"""程序窗口右下角信息提示组件。

封装 qfluentwidgets InfoBar，提供固定在父窗口右下角弹出的非阻塞提示，
支持成功、警告、错误、信息四种类型，可自动消失或手动关闭。
"""

import sys
import io

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget

# 静默导入 qfluentwidgets，避免其 Pro 提示输出到控制台
_old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    from qfluentwidgets import InfoBar, InfoBarPosition
finally:
    sys.stdout = _old_stdout


class BottomRightInfoBar:
    """右下角信息提示管理器。

    所有提示均显示在传入的父窗口右下角，多个提示会自动堆叠。
    """

    DEFAULT_DURATION = 2500

    @classmethod
    def success(cls, title: str, content: str = "", parent: QWidget = None,
                duration: int = DEFAULT_DURATION):
        """显示成功提示。"""
        cls._show("success", title, content, parent, duration)

    @classmethod
    def warning(cls, title: str, content: str = "", parent: QWidget = None,
                duration: int = DEFAULT_DURATION):
        """显示警告提示。"""
        cls._show("warning", title, content, parent, duration)

    @classmethod
    def error(cls, title: str, content: str = "", parent: QWidget = None,
              duration: int = DEFAULT_DURATION):
        """显示错误提示。"""
        cls._show("error", title, content, parent, duration)

    @classmethod
    def info(cls, title: str, content: str = "", parent: QWidget = None,
             duration: int = DEFAULT_DURATION):
        """显示普通信息提示。"""
        cls._show("info", title, content, parent, duration)

    @classmethod
    def _show(cls, kind: str, title: str, content: str,
              parent: QWidget, duration: int):
        """创建并显示 InfoBar。

        Args:
            kind: 提示类型， success / warning / error / info。
            title: 提示标题。
            content: 提示内容。
            parent: 父窗口，提示将停靠在其右下角。
            duration: 显示时长（毫秒），0 表示不自动关闭。
        """
        if parent is None:
            from gui.main_window import get_main_window
            parent = get_main_window()

        kwargs = {
            "title": title,
            "content": content,
            "orient": Qt.Horizontal,
            "isClosable": True,
            "position": InfoBarPosition.BOTTOM_RIGHT,
            "duration": duration,
            "parent": parent,
        }

        if kind == "success":
            InfoBar.success(**kwargs).show()
        elif kind == "warning":
            InfoBar.warning(**kwargs).show()
        elif kind == "error":
            InfoBar.error(**kwargs).show()
        else:
            InfoBar.info(**kwargs).show()


def show_bottom_right_info(title: str, content: str = "", kind: str = "info",
                           parent: QWidget = None, duration: int = 2500):
    """便捷函数：在程序窗口右下角显示信息提示。

    Args:
        title: 提示标题。
        content: 提示内容。
        kind: 提示类型， success / warning / error / info。
        parent: 父窗口，默认使用主窗口。
        duration: 显示时长（毫秒）。
    """
    BottomRightInfoBar._show(kind, title, content, parent, duration)
