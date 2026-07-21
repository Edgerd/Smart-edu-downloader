# -*- coding: utf-8 -*-
"""
自定义右键控件
"""
from core.i18n import _

from PyQt5.QtWidgets import QSpinBox, QLineEdit, QApplication
from PyQt5.QtGui import QWheelEvent
from qfluentwidgets import ComboBox as FluentComboBox
from gui.styles import load_primary_color
from gui.fonts import get_harmonyos_family, body_font
from gui.utils.color_utils import lighten


class NoWheelSpinBox(QSpinBox):
    """禁用滚轮的SpinBox，增强样式表支持"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        from gui.fonts import body_font
        self.setFont(body_font())
        self._setup_style()
    
    def _setup_style(self):
        """设置默认样式，避免样式表解析问题"""
        accent_color = load_primary_color()
        font_family = get_harmonyos_family()
        hover_bg = lighten(accent_color, 92)
        self.setStyleSheet(f"""
            QSpinBox {{
                border: 2px solid #E0E8F0;
                border-radius: 6px;
                padding: 6px 8px;
                background: #F8FAFC;
                min-height: 24px;
                font-family: "{font_family}";
            }}
            QSpinBox:hover {{
                border-color: {accent_color};
                background: {hover_bg};
            }}
            QSpinBox:focus {{
                border-color: {accent_color};
                background: white;
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                border: none;
                width: 20px;
                background: transparent;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background: #F0F0F0;
            }}
        """)
    
    def wheelEvent(self, event: QWheelEvent):
        event.ignore()


class NoWheelComboBox(FluentComboBox):
    """禁用滚轮的 Fluent 下拉框"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFont(body_font())

    def wheelEvent(self, event: QWheelEvent):
        """忽略滚轮事件"""
        event.ignore()


class WheelComboBox(FluentComboBox):
    """支持滚轮切换选项的 Fluent 下拉框"""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setFont(body_font())

    def wheelEvent(self, event: QWheelEvent):
        """处理滚轮事件切换选项

        Args:
            event: 滚轮事件
        """
        if self.isEnabled():
            delta = event.angleDelta().y()
            current_index = self.currentIndex()

            if delta > 0:
                new_index = max(0, current_index - 1)
            else:
                new_index = min(self.count() - 1, current_index + 1)

            if new_index != current_index:
                self.setCurrentIndex(new_index)

            event.accept()
        else:
            event.ignore()


class ChineseLineEdit(QLineEdit):
    """带中文右键菜单的输入框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
    
    def contextMenuEvent(self, event):
        """创建中文右键菜单"""
        from gui.widgets.rounded_menu import RoundedMenu
        menu = RoundedMenu(self)
        from gui.fonts import body_font
        menu.setFont(body_font())
        from gui.styles import apply_menu_style
        apply_menu_style(menu)  # 修复：解决黑色背景

        undo_action = menu.addAction(_("widgets.controls.undo"))
        undo_action.setFont(body_font())
        undo_action.setEnabled(self.isUndoAvailable())
        undo_action.triggered.connect(self.undo)
        
        redo_action = menu.addAction(_("widgets.controls.redo"))
        redo_action.setFont(body_font())
        redo_action.setEnabled(self.isRedoAvailable())
        redo_action.triggered.connect(self.redo)
        
        menu.addSeparator()
        
        cut_action = menu.addAction(_("widgets.controls.cut"))
        cut_action.setFont(body_font())
        cut_action.setEnabled(self.hasSelectedText())
        cut_action.triggered.connect(self.cut)
        
        copy_action = menu.addAction(_("widgets.controls.copy"))
        copy_action.setFont(body_font())
        copy_action.setEnabled(self.hasSelectedText())
        copy_action.triggered.connect(self.copy)
        
        # 粘贴
        paste_action = menu.addAction(_("widgets.controls.paste"))
        paste_action.setFont(body_font())
        clipboard = QApplication.clipboard()
        has_clipboard_text = False
        if clipboard:
            try:
                has_clipboard_text = len(clipboard.text()) > 0
            except Exception:
                has_clipboard_text = False
        paste_action.setEnabled(has_clipboard_text)
        paste_action.triggered.connect(self.paste)
        
        # 删除
        delete_action = menu.addAction(_("common.delete"))
        delete_action.setFont(body_font())
        delete_action.setEnabled(self.hasSelectedText())
        delete_action.triggered.connect(self._delete_selected)
        
        menu.addSeparator()
        
        # 全选
        select_all_action = menu.addAction(_("widgets.controls.select_all"))
        select_all_action.setFont(body_font())
        select_all_action.setEnabled(len(self.text()) > 0)
        select_all_action.triggered.connect(self.selectAll)
        
        menu.exec(event.globalPos())
    
    def _delete_selected(self):
        """删除选中的文本"""
        if self.hasSelectedText():
            self.del_()
