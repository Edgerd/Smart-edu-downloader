# -*- coding: utf-8 -*-
"""
调试面板模块

提供调试面板窗口和全局日志接口。
"""

import sys
import os
from datetime import datetime
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QStackedWidget, QShortcut, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QKeySequence

from .fonts import title_font, body_font, get_harmonyos_family
from .styles import (
    get_global_scrollbar_style,
    load_primary_color, load_background_color,
)
from .widgets.material_button import MaterialButton
from .widgets.vertical_tab_widget import VerticalTabWidget
from core.ui.icon_manager import IconManager
from core.i18n import _
from .components.debug.log_tab import LogTab
from .components.debug.console_tab import ConsoleTab
from .components.debug.info_tab import InfoTab
from .components.debug.debug_tools_tab import DebugToolsTab
from .components.debug.lab_tab import LabTab


class LogEmitter(QObject):
    """日志发射器"""
    log_signal = pyqtSignal(str, str)

    def __init__(self):
        super().__init__()


class DebugPanel(QWidget):
    """调试面板窗口"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, parent=None):
        if hasattr(DebugPanel, '_initialized') and DebugPanel._initialized:
            return
        DebugPanel._initialized = True

        super().__init__(parent)
        self.setObjectName("debugPanel")
        self.setWindowTitle(_("debug.panel.title"))
        self.setWindowFlags(Qt.Window)
        self._accent_color = load_primary_color()
        self._background_color = load_background_color()
        self.resize(1000, 700)
        self.setMinimumSize(800, 500)
        self.setStyleSheet(self._get_panel_style())

        try:
            self._init_ui()
            self._create_shortcuts()
            self.log("调试面板已初始化", "INFO")
        except Exception as e:
            from core.infrastructure.logger import log
            log("ERROR", f"DebugPanel 初始化失败: {e}")

    def _get_panel_style(self) -> str:
        """获取调试面板全局样式"""
        return f"""
            #debugPanel {{
                background-color: {self._background_color};
            }}
            #debugPanel QGroupBox {{
                background-color: {self._background_color};
                border: 1px solid {self._accent_color};
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }}
            #debugPanel QGroupBox::title {{
                color: {self._accent_color};
                font-family: "{get_harmonyos_family()}";
                font-weight: bold;
                subcontrol-origin: margin;
                padding: 0 5px;
            }}
            {get_global_scrollbar_style(self._accent_color)}
        """

    def _init_ui(self):
        """初始化UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏（参照下载界面 PageHeader 风格）
        header_container = QWidget()
        header_container.setStyleSheet("background-color: transparent;")
        header_layout = QHBoxLayout(header_container)
        header_layout.setContentsMargins(15, 10, 15, 10)
        header_layout.setSpacing(15)

        # 左侧标题区域：图标 + 标题 + 副标题
        title_area = QWidget()
        title_area.setStyleSheet("background-color: transparent;")
        title_area_layout = QVBoxLayout(title_area)
        title_area_layout.setContentsMargins(0, 0, 0, 0)
        title_area_layout.setSpacing(2)

        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(0, 0, 0, 0)

        self.icon_manager = IconManager()
        icon_pixmap = self.icon_manager.load_title_svg(
            "title_debug.svg", self._accent_color, size=(28, 28)
        )
        self.header_icon_label = None
        if icon_pixmap:
            self.header_icon_label = QLabel()
            self.header_icon_label.setPixmap(icon_pixmap)
            self.header_icon_label.setFixedSize(28, 28)
            self.header_icon_label.setStyleSheet("background-color: transparent;")
            title_row.addWidget(self.header_icon_label)

        self.header_title_label = QLabel(_("debug.panel.title"))
        self.header_title_label.setFont(title_font())
        self.header_title_label.setStyleSheet(f"color: {self._accent_color}; background-color: transparent;")
        title_row.addWidget(self.header_title_label)
        title_row.addStretch()
        title_area_layout.addLayout(title_row)

        subtitle_label = QLabel(_("debug.panel.subtitle"))
        subtitle_label.setFont(body_font())
        subtitle_label.setStyleSheet("color: #666; background-color: transparent;")
        title_area_layout.addWidget(subtitle_label)

        header_layout.addWidget(title_area)
        header_layout.addStretch()

        # 最小化按钮
        self.minimize_btn = MaterialButton(_("debug.panel.minimize_button"), variant=MaterialButton.VARIANT_OUTLINED)
        self.minimize_btn.setAccentColor("#6C757D")
        self.minimize_btn.setFixedWidth(80)
        self.minimize_btn.setFixedHeight(32)
        self.minimize_btn.clicked.connect(self.hide)
        header_layout.addWidget(self.minimize_btn)

        main_layout.addWidget(header_container)

        # 内容区域：左侧垂直导航 + 右侧内容
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # 左侧垂直导航栏（设置同款）
        self.nav_bar = VerticalTabWidget()
        self.nav_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.nav_bar.tab_bar.setFixedWidth(140)
        self.nav_bar.stacked_widget.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        self.nav_bar.stacked_widget.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {self._background_color};
                border: none;
                border-radius: 0px;
            }}
        """)

        # 创建各标签页
        self.log_tab = LogTab()
        self.console_tab = ConsoleTab()
        self.info_tab = InfoTab()
        self.debug_tools_tab = DebugToolsTab()
        self.lab_tab = LabTab()

        # 添加标签页：标题 + 图标路径
        icon_base = os.path.join("resources", "images", "dev")
        self.nav_bar.addTab(self.log_tab, _("debug.panel.log_tab"), os.path.join(icon_base, "芯片.svg"))
        self.nav_bar.addTab(self.console_tab, _("debug.panel.console_tab"), os.path.join(icon_base, "代码.svg"))
        self.nav_bar.addTab(self.info_tab, _("debug.panel.info_tab"), os.path.join(icon_base, "文档.svg"))
        self.nav_bar.addTab(self.debug_tools_tab, _("debug.panel.tools_tab"), os.path.join(icon_base, "链接.svg"))
        self.nav_bar.addTab(self.lab_tab, _("debug.lab.title"), os.path.join(icon_base, "灯光.svg"))

        content_layout.addWidget(self.nav_bar)

        # 右侧内容区域
        self.stack = self.nav_bar.stacked_widget

        main_layout.addLayout(content_layout)

        # 调试面板UI初始化完成

    def _create_shortcuts(self):
        """创建快捷键"""
        self.f12_shortcut = QShortcut(QKeySequence("F12"), self)
        self.f12_shortcut.activated.connect(self.hide)

    def log(self, message: str, level: str = "INFO"):
        """添加日志"""
        self.log_tab.log(message, level)

    def console_log(self, message: str):
        """控制台输出"""
        self.console_tab.console_log(message)

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新面板所有视觉元素。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        self._accent_color = primary
        self._background_color = background
        self.setStyleSheet(self._get_panel_style())
        self.nav_bar.setBackgroundColor(background)
        self.nav_bar.setAccentColor(primary)

        # 同步右侧内容区背景色，避免残留旧背景或变白
        self.nav_bar.stacked_widget.setStyleSheet(f"""
            QStackedWidget {{
                background-color: {background};
                border: none;
                border-radius: 0px;
            }}
        """)

        # 清除图标缓存并刷新标题栏图标与标题颜色
        self.icon_manager.clear_pixmap_cache()
        if self.header_icon_label is not None:
            icon_pixmap = self.icon_manager.load_title_svg(
                "title_debug.svg", primary, size=(28, 28)
            )
            if icon_pixmap:
                self.header_icon_label.setPixmap(icon_pixmap)
        if self.header_title_label is not None:
            self.header_title_label.setStyleSheet(
                f"color: {primary}; background-color: transparent;"
            )

        # 递归刷新所有子标签页
        for tab in (
            self.log_tab,
            self.console_tab,
            self.info_tab,
            self.debug_tools_tab,
            self.lab_tab,
        ):
            if hasattr(tab, "update_theme_colors"):
                try:
                    tab.update_theme_colors(primary, background)
                except Exception as e:
                    from core.infrastructure.logger import log
                    log(
                        "WARNING",
                        f"调试子标签页 {type(tab).__name__} 主题色更新失败: {e}",
                    )


class DebugWindowManager:
    """调试窗口管理器"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.panel = DebugPanel()
        self.log_emitter = LogEmitter()
        self.log_emitter.log_signal.connect(self._handle_log)
    
    def _handle_log_safe(self, message: str, level: str):
        """安全处理日志信号（通过 QTimer 确保在主线程执行）"""
        from PyQt5.QtCore import QTimer
        panel_ref = getattr(self, 'panel', None)
        if panel_ref is not None:
            QTimer.singleShot(0, lambda: panel_ref.log(message, level))

    def _handle_log(self, message: str, level: str):
        """处理日志信号"""
        self._handle_log_safe(message, level)

    def log(self, message: str, level: str = "INFO"):
        """添加日志（线程安全）"""
        self.log_emitter.log_signal.emit(message, level)

    def show_panel(self):
        """显示面板"""
        self.panel.show()
        self.panel.raise_()
        self.panel.activateWindow()

    def toggle_panel(self):
        """切换面板显示"""
        if self.panel.isVisible():
            self.panel.hide()
        else:
            self.show_panel()


_global_debug_manager = None

def get_debug_manager() -> DebugWindowManager:
    """获取全局调试管理器"""
    global _global_debug_manager
    if _global_debug_manager is None:
        _global_debug_manager = DebugWindowManager()
    return _global_debug_manager


def log(message: str, level: str = "INFO"):
    """快捷日志函数"""
    dm = get_debug_manager()
    dm.log(message, level)
