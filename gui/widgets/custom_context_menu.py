# -*- coding: utf-8 -*-
"""Material Design 风格的自定义右键菜单控件。"""
from core.i18n import _

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from gui.widgets.material_menu import MaterialMenu

try:
    from gui.fonts import body_font as _body_font
except ImportError:
    _body_font = None


try:
    from gui.styles import load_primary_color
except ImportError:
    def load_primary_color():
        """加载主题主色，失败时返回项目默认蓝色。"""
        return "#1277DD"


class CustomContextMenu:
    """Material Design 风格的自定义右键菜单管理器。"""

    @staticmethod
    def _default_font():
        """返回默认菜单字体，优先使用项目正文字体。"""
        if _body_font is not None:
            try:
                return _body_font()
            except Exception:
                pass
        return QFont("Microsoft YaHei UI", 10)

    @staticmethod
    def _create_menu(parent, font=None):
        """创建并应用 Material 风格的菜单。"""
        accent = load_primary_color()
        menu = MaterialMenu(parent, accent_color=accent)
        return menu

    @staticmethod
    def setup_for_text_edit(text_edit, font=None):
        """为 QTextEdit 设置自定义右键菜单。"""
        text_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        text_edit.customContextMenuRequested.connect(
            lambda pos: CustomContextMenu._show_text_edit_menu(text_edit, pos, font)
        )

    @staticmethod
    def _show_text_edit_menu(text_edit, pos, font=None):
        """显示 QTextEdit 的右键菜单。"""
        menu = CustomContextMenu._create_menu(text_edit, font)

        if text_edit.isReadOnly():
            menu.addAction(_("widgets.controls.select_all"), text_edit.selectAll, "Ctrl+A")

            if text_edit.toPlainText():
                menu.addAction(_("widgets.controls.copy"), text_edit.copy, "Ctrl+C")

            menu.exec(text_edit.mapToGlobal(pos))
            return

        has_selection = text_edit.textCursor().hasSelection()
        clipboard = QApplication.clipboard()
        has_clipboard = False
        if clipboard:
            try:
                has_clipboard = bool(clipboard.text())
            except Exception:
                has_clipboard = False

        menu.addAction(
            _("widgets.controls.undo"), text_edit.undo, "Ctrl+Z",
            enabled=text_edit.document().isUndoAvailable()
        )
        menu.addAction(
            _("widgets.controls.redo"), text_edit.redo, "Ctrl+Y",
            enabled=text_edit.document().isRedoAvailable()
        )
        menu.addSeparator()
        menu.addAction(_("widgets.controls.cut"), text_edit.cut, "Ctrl+X", enabled=has_selection)
        menu.addAction(_("widgets.controls.copy"), text_edit.copy, "Ctrl+C", enabled=has_selection)
        menu.addAction(_("widgets.controls.paste"), text_edit.paste, "Ctrl+V", enabled=has_clipboard)
        menu.addAction(
            _("common.delete"),
            lambda: text_edit.textCursor().removeSelectedText(),
            enabled=has_selection
        )
        menu.addSeparator()
        menu.addAction(_("widgets.controls.select_all"), text_edit.selectAll, "Ctrl+A")

        menu.exec(text_edit.mapToGlobal(pos))

    @staticmethod
    def setup_for_line_edit(line_edit, font=None):
        """为 QLineEdit 设置自定义右键菜单。"""
        line_edit.setContextMenuPolicy(Qt.CustomContextMenu)
        line_edit.customContextMenuRequested.connect(
            lambda pos: CustomContextMenu._show_line_edit_menu(line_edit, pos, font)
        )

    @staticmethod
    def _show_line_edit_menu(line_edit, pos, font=None):
        """显示 QLineEdit 的右键菜单。"""
        menu = CustomContextMenu._create_menu(line_edit, font)

        has_selection = line_edit.hasSelectedText()
        clipboard = QApplication.clipboard()
        has_clipboard = False
        if clipboard:
            try:
                has_clipboard = bool(clipboard.text())
            except Exception:
                has_clipboard = False

        menu.addAction(_("widgets.controls.undo"), line_edit.undo, "Ctrl+Z", enabled=False)
        menu.addAction(_("widgets.controls.redo"), line_edit.redo, "Ctrl+Y", enabled=False)
        menu.addSeparator()
        menu.addAction(_("widgets.controls.cut"), line_edit.cut, "Ctrl+X", enabled=has_selection)
        menu.addAction(_("widgets.controls.copy"), line_edit.copy, "Ctrl+C", enabled=has_selection)
        menu.addAction(_("widgets.controls.paste"), line_edit.paste, "Ctrl+V", enabled=has_clipboard)
        menu.addAction(_("common.delete"), line_edit.del_, enabled=has_selection)
        menu.addSeparator()
        menu.addAction(_("widgets.controls.select_all"), line_edit.selectAll, "Ctrl+A")

        menu.exec(line_edit.mapToGlobal(pos))

    @staticmethod
    def show_context_menu(parent, pos, status_bar=None, font=None):
        """弹出包含复制/粘贴/剪切/全选和更多操作的示例上下文菜单。

        Args:
            parent: 触发菜单的父控件。
            pos: 父控件坐标系下的右键位置。
            status_bar: 用于显示操作提示的状态栏或标签，可选。
            font: 菜单字体，可选（当前版本保留参数以保持兼容性）。
        """
        menu = CustomContextMenu._create_menu(parent, font)

        def _notify(text: str):
            if status_bar is not None:
                try:
                    status_bar.showMessage(_("widgets.context_menu.execute_template", text=text))
                except Exception:
                    pass

        menu.addAction(_("widgets.controls.copy"), lambda: _notify(_("widgets.controls.copy")))
        menu.addAction(_("widgets.controls.paste"), lambda: _notify(_("widgets.controls.paste")))
        menu.addAction(_("widgets.controls.cut"), lambda: _notify(_("widgets.controls.cut")))
        menu.addAction(_("widgets.controls.select_all"), lambda: _notify(_("widgets.controls.select_all")))
        menu.addSeparator()

        more_menu = menu.addMenu(_("widgets.context_menu.more_operations"))
        more_menu.addAction(
            _("widgets.context_menu.sub_item_one"),
            lambda: _notify(_("widgets.context_menu.sub_item_one_notify"))
        )
        more_menu.addAction(
            _("widgets.context_menu.sub_item_two"),
            lambda: _notify(_("widgets.context_menu.sub_item_two_notify"))
        )

        menu.exec(parent.mapToGlobal(pos))


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QLabel, QTextEdit, QStatusBar, QApplication

    class DemoWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(_("widgets.context_menu.demo_title"))
            self.resize(600, 400)

            central = QWidget()
            self.setCentralWidget(central)
            central.setStyleSheet("background: #F5F5F5;")
            central.setContextMenuPolicy(Qt.CustomContextMenu)
            central.customContextMenuRequested.connect(self._on_context_menu)

            layout = QVBoxLayout(central)
            layout.setContentsMargins(40, 40, 40, 40)

            hint = QLabel(_("widgets.context_menu.hint"))
            hint.setAlignment(Qt.AlignCenter)
            hint.setStyleSheet("font-size: 16px; color: #666;")
            layout.addWidget(hint)

            text_edit = QTextEdit()
            text_edit.setPlaceholderText(_("widgets.context_menu.demo_placeholder"))
            text_edit.setStyleSheet("background: white; border-radius: 6px; padding: 8px;")
            CustomContextMenu.setup_for_text_edit(text_edit)
            layout.addWidget(text_edit)

            self._status = QStatusBar()
            self.setStatusBar(self._status)
            self._status.showMessage(_("widgets.context_menu.demo_status_message"))

        def _on_context_menu(self, pos):
            CustomContextMenu.show_context_menu(self.centralWidget(), pos, self._status)

    app = QApplication(sys.argv)
    window = DemoWindow()
    window.show()
    sys.exit(app.exec())
