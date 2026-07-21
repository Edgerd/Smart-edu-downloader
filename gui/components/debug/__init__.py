# -*- coding: utf-8 -*-
"""
调试面板组件模块

提供重构后的调试面板各个独立组件。
"""

from .navigation_bar import NavigationBar
from .log_tab import LogTab
from .console_tab import ConsoleTab
from .info_tab import InfoTab
from .debug_tools_tab import DebugToolsTab
from .lab_tab import LabTab

__all__ = [
    "NavigationBar",
    "LogTab",
    "ConsoleTab",
    "InfoTab",
    "DebugToolsTab",
    "LabTab",
]
