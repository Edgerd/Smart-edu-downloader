# -*- coding: utf-8 -*-
"""
崩溃测试工具组件

在调试面板提供一键模拟未处理异常的功能，用于验证全局崩溃捕获、
崩溃日志输出以及错误提示窗口能否正常触发与显示。
"""

import threading

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel

from core.i18n import _
from gui.fonts import body_font
from gui.widgets.material_button import MaterialButton

try:
    from qfluentwidgets import MessageBox as FluentMessageBox
except Exception:
    FluentMessageBox = None


class CrashTesterWidget(QWidget):
    """崩溃测试工具组件。

    提供一个按钮，点击后在独立线程中抛出一个未处理异常，
    从而触发已安装的 global crash handler 并弹出错误提示窗口。
    """

    def __init__(self, parent: QWidget = None, show_title: bool = True):
        """初始化崩溃测试工具组件。

        Args:
            parent: 父级控件。
            show_title: 是否显示组件标题。
        """
        super().__init__(parent)
        self._show_title = show_title
        self._init_ui()

    def _init_ui(self):
        """初始化界面。"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        if self._show_title:
            title = QLabel(_("debug.tools.crash_tester_title"))
            title.setFont(body_font())
            title.setStyleSheet("font-weight: bold; color: #333;")
            layout.addWidget(title)

        self.crash_btn = MaterialButton(
            _("debug.tools.trigger_crash"),
            variant=MaterialButton.VARIANT_OUTLINED,
        )
        self.crash_btn.setAccentColor("#DC3545")
        self.crash_btn.setFixedHeight(40)
        self.crash_btn.clicked.connect(self._on_trigger_crash)
        layout.addWidget(self.crash_btn)

        hint_label = QLabel(_("debug.tools.crash_tester_hint"))
        hint_label.setFont(body_font())
        hint_label.setStyleSheet("color: #888;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)

        layout.addStretch()

    def _on_trigger_crash(self):
        """点击后确认并触发一次模拟崩溃。"""
        if not self._confirm_crash():
            return

        def _raise_crash():
            """在后台线程抛出异常，触发全局崩溃处理器。"""
            raise RuntimeError(_("debug.tools.test_crash_message"))

        threading.Thread(target=_raise_crash, daemon=True).start()

    def _confirm_crash(self) -> bool:
        """弹出确认框询问是否模拟崩溃。

        使用顶层主窗口作为父级，使弹窗在主窗口居中显示，
        避免以内嵌小组件为父级时位置偏移或显示不完整。

        Returns:
            用户确认返回 True，否则返回 False。
        """
        title = _("debug.tools.confirm_crash_title")
        message = _("debug.tools.confirm_crash_message")
        parent = self.window() if self.window() is not None else self
        if FluentMessageBox is not None:
            box = FluentMessageBox(title, message, parent)
            box.yesButton.setText(_("common.ok"))
            box.cancelButton.setText(_("common.cancel"))
            return bool(box.exec())
        from PyQt5.QtWidgets import QMessageBox
        box = QMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(message)
        box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        box.setDefaultButton(QMessageBox.No)
        box.setStyleSheet(
            "QMessageBox { background-color: #FFFFFF; }"
            "QLabel { color: #333333; }"
            "QPushButton {"
            "  background-color: #2078DA; color: #FFFFFF;"
            "  border: none; border-radius: 6px; padding: 4px 12px;"
            "  min-width: 60px;"
            "}"
            "QPushButton:hover { background-color: #1A6BC0; }"
        )
        return box.exec() == QMessageBox.Yes

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化刷新按钮颜色。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        if hasattr(self, "crash_btn") and self.crash_btn is not None:
            self.crash_btn.setAccentColor("#DC3545")
