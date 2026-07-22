# -*- coding: utf-8 -*-
"""GUI 公共样式工具"""

from typing import Any, Dict

from core.config.theme_config import (
    background_color as _background_color,
    get_theme_config as _get_theme_config,
    primary_color as _primary_color,
)
from core.infrastructure.logger import log
from gui.utils.color_utils import darken
from gui.fonts import get_harmonyos_family


def get_button_style(color: str, hover_percent: int = 15, pressed_percent: int = 30, padding: str = "5px 10px") -> str:
    """生成按钮样式表"""
    return f"""
        QPushButton {{
            background: {color};
            color: white;
            border: none;
            border-radius: 6px;
            padding: {padding};
            font-family: "{get_harmonyos_family()}";
            font-weight: bold;
        }}
        QPushButton:hover {{
            background: {darken(color, hover_percent)};
        }}
        QPushButton:pressed {{
            background: {darken(color, pressed_percent)};
        }}
        QPushButton:disabled {{
            background: #CCC;
            color: #888;
        }}
    """


def load_theme_color() -> Dict[str, Any]:
    """加载完整主题配置字典。"""
    try:
        from core.config.settings_manager import get_settings_manager
        settings = get_settings_manager().get_all()
        return _get_theme_config(settings)
    except Exception:
        pass
    return _get_theme_config(None)


def load_primary_color() -> str:
    """加载主题主色（控件强调色来源）。"""
    return _primary_color(load_theme_color())


def load_background_color() -> str:
    """加载内容区背景色。"""
    return _background_color(load_theme_color())


def load_accent_color() -> str:
    """兼容旧接口：加载主题主色。

    主题色与强调色已合并，此方法保留以避免外部调用方一次性崩溃，
    实际返回主题主色。
    """
    return load_primary_color()


def create_styled_button(text: str, color: str, callback, font_fn=None, 
                         fixed_height: int = None, style_kwargs: dict = None):
    """创建 MD3 风格的统一样式按钮"""
    from PyQt5.QtCore import Qt
    from gui.widgets.material_button import MaterialButton
    
    if font_fn is None:
        from gui.fonts import body_font
        font_fn = body_font
    
    btn = MaterialButton(text)
    btn.setAccentColor(color)
    btn.setFont(font_fn())
    btn.setCursor(Qt.PointingHandCursor)
    if fixed_height is not None:
        btn.setFixedHeight(fixed_height)
    else:
        btn.setFixedHeight(40)
    btn.clicked.connect(callback)
    return btn


def get_fluent_table_style(accent_color: str = None) -> str:
    """获取Fluent风格表格样式"""
    if accent_color is None:
        accent_color = load_primary_color()
    return f"""
        QTableWidget {{
            border: 1px solid #E5E5E5;
            border-radius: 8px;
            background: #FFFFFF;
            gridline-color: #F0F0F0;
            selection-background-color: {accent_color};
            selection-color: #FFFFFF;
        }}
        QTableWidget::item {{
            padding: 6px 10px;
            font-size: 9pt;
            color: #333333;
            border: none;
        }}
        QTableWidget::item:hover {{
            background: #F5F9FC;
        }}
        QTableWidget::item:selected {{
            background: {accent_color};
            color: #FFFFFF;
        }}
        QHeaderView::section {{
            background: #FFFFFF;
            color: #333333;
            padding: 8px 12px;
            border: none;
            border-bottom: 2px solid #E8E8E8;
            font-family: "{get_harmonyos_family()}";
            font-weight: bold;
            font-size: 9pt;
        }}
        QHeaderView::section:hover {{
            background: #F8F8F8;
        }}
        QTableWidget QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0;
            border-radius: 4px;
        }}
        QTableWidget QScrollBar::handle:vertical {{
            background: #D0D0D0;
            min-height: 30px;
            border-radius: 4px;
        }}
        QTableWidget QScrollBar::handle:vertical:hover {{
            background: #B0B0B0;
        }}
        QTableWidget QScrollBar::add-line:vertical,
        QTableWidget QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QTableWidget QScrollBar::add-page:vertical,
        QTableWidget QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
    """


def get_fluent_tree_style(accent_color: str = None) -> str:
    """获取Fluent风格树控件样式"""
    if accent_color is None:
        accent_color = load_primary_color()
    return f"""
        QTreeWidget {{
            border: 1px solid #E5E5E5;
            border-radius: 8px;
            background: #FFFFFF;
            color: #333333;
            selection-background-color: {accent_color};
            selection-color: #FFFFFF;
        }}
        QTreeWidget::item {{
            padding: 4px 8px;
            font-size: 9pt;
            border: none;
        }}
        QTreeWidget::item:hover {{
            background: #F5F9FC;
        }}
        QTreeWidget::item:selected {{
            background: {accent_color};
            color: #FFFFFF;
        }}
        QHeaderView::section {{
            background: #FFFFFF;
            color: #333333;
            padding: 8px 12px;
            border: none;
            border-bottom: 2px solid #E8E8E8;
            font-family: "{get_harmonyos_family()}";
            font-weight: bold;
            font-size: 9pt;
        }}
        QTableWidget QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            border-radius: 4px;
        }}
        QTreeWidget QScrollBar::handle:vertical {{
            background: #D0D0D0;
            min-height: 30px;
            border-radius: 4px;
        }}
        QTreeWidget QScrollBar::handle:vertical:hover {{
            background: #B0B0B0;
        }}
        QTreeWidget QScrollBar::add-line:vertical,
        QTreeWidget QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QTreeWidget QScrollBar::add-page:vertical,
        QTreeWidget QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
    """


def get_fluent_menu_style(accent_color: str = None) -> str:
    """获取Fluent风格菜单样式"""
    if accent_color is None:
        accent_color = load_primary_color()
    return f"""
        QMenu {{
            background: #FFFFFF;
            border: 1px solid #E0E0E0;
            border-radius: 8px;
            padding: 6px 0px;
            color: #333333;
        }}
        QMenu::item {{
            padding: 6px 18px;
            font-size: 9pt;
            color: #333333;
            background: transparent;
        }}
        QMenu::item:selected {{
            background: {accent_color};
            color: #FFFFFF;
        }}
        QMenu::item:disabled {{
            color: #BBBBBB;
            background: transparent;
        }}
        QMenu::separator {{
            height: 1px;
            background: #E8E8E8;
            margin: 2px 12px;
        }}
    """


def get_fluent_rounded_menu_style(accent_color: str = None) -> str:
    """获取用于圆角绘制菜单的 Fluent 菜单项样式。"""
    if accent_color is None:
        accent_color = load_primary_color()
    return f"""
        QMenu {{
            background: transparent;
            border: none;
            padding: 6px 0px;
            color: #333333;
        }}
        QMenu::item {{
            padding: 6px 18px;
            font-size: 9pt;
            color: #333333;
            background: transparent;
        }}
        QMenu::item:selected {{
            background: {accent_color};
            color: #FFFFFF;
        }}
        QMenu::item:disabled {{
            color: #BBBBBB;
            background: transparent;
        }}
        QMenu::separator {{
            height: 1px;
            background: #E8E8E8;
            margin: 2px 12px;
        }}
    """


def get_global_scrollbar_style(accent_color: str = None) -> str:
    """获取全局 Fluent 风格滚动条样式（适用于 QTextEdit/QScrollArea 等）

    Args:
        accent_color: 主题强调色；为 None 时自动读取当前主题色。

    Returns:
        滚动条样式表字符串；根据 ``scrollbar_follow_theme`` 设置决定是否使用主题色。
    """
    try:
        from core.config.settings_manager import get_settings_manager
        follow_theme = get_settings_manager().get("scrollbar_follow_theme", False)
    except Exception:
        follow_theme = False

    if follow_theme and accent_color:
        handle_color = accent_color
        hover_color = darken(accent_color, 15)
    else:
        handle_color = "#D0D0D0"
        hover_color = "#B0B0B0"

    return f"""
        QScrollBar:vertical {{
            background: transparent;
            width: 8px;
            margin: 0;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical {{
            background: {handle_color};
            min-height: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:vertical:hover {{
            background: {hover_color};
        }}
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {{
            background: transparent;
        }}
        QScrollBar:horizontal {{
            background: transparent;
            height: 8px;
            margin: 0;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal {{
            background: {handle_color};
            min-width: 30px;
            border-radius: 4px;
        }}
        QScrollBar::handle:horizontal:hover {{
            background: {hover_color};
        }}
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {{
            width: 0px;
        }}
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {{
            background: transparent;
        }}
    """


def get_message_box_style(accent_color: str = None) -> str:
    """获取 QMessageBox 全局样式，避免原生弹窗在暗色系统主题下显示黑底。

    Args:
        accent_color: 主题强调色；为 None 时自动读取当前主题色。

    Returns:
        用于 QApplication.setStyleSheet 的样式字符串。
    """
    if accent_color is None:
        accent_color = load_primary_color()
    hover_color = darken(accent_color, 10)
    pressed_color = darken(accent_color, 20)
    return f"""
        QMessageBox {{
            background-color: #FFFFFF;
            border-radius: 8px;
        }}
        QMessageBox QLabel {{
            color: #333333;
            font-size: 13px;
        }}
        QMessageBox QPushButton {{
            background-color: {accent_color};
            color: #FFFFFF;
            border: none;
            border-radius: 6px;
            padding: 5px 14px;
            min-width: 70px;
            font-size: 13px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {hover_color};
        }}
        QMessageBox QPushButton:pressed {{
            background-color: {pressed_color};
        }}
        QMessageBox QPushButton:default {{
            background-color: {accent_color};
        }}
    """


def apply_global_message_box_style(app, accent_color: str = None) -> None:
    """为整个应用设置 QMessageBox 全局样式。

    Args:
        app: QApplication 实例。
        accent_color: 主题强调色；为 None 时自动读取当前主题色。
    """
    try:
        app.setStyleSheet(get_message_box_style(accent_color))
    except Exception as e:
        log("WARNING", f"应用 QMessageBox 全局样式失败: {e}")


def apply_menu_style(menu, accent_color: str = None) -> None:
    """为 QMenu 应用 Fluent 风格样式（解决部分平台下系统默认样式导致的黑色背景问题）

    Args:
        menu: QMenu 实例
        accent_color: 强调色（用于选中项背景），为 None 时自动从设置读取
    """
    try:
        if accent_color is None:
            accent_color = load_accent_color()
        try:
            from gui.widgets.rounded_menu import RoundedMenu
        except ImportError:
            RoundedMenu = None
        if RoundedMenu is not None and isinstance(menu, RoundedMenu):
            menu.setStyleSheet(get_fluent_rounded_menu_style(accent_color))
        else:
            menu.setStyleSheet(get_fluent_menu_style(accent_color))
    except Exception as e:
        log("WARNING", f"应用菜单样式失败: {e}")
        # 兜底：退回到最小可用样式，避免菜单不可读
        menu.setStyleSheet(
            "QMenu { background: #FFFFFF; color: #333333; border: 1px solid #E0E0E0; }"
        )


def wrap_in_rounded_container(widget, accent_color: str = None):
    """将控件包装在圆角容器中"""
    from PyQt5.QtWidgets import QWidget, QVBoxLayout
    container = QWidget()
    container.setStyleSheet("""
        QWidget {{
            background: #FFFFFF;
            border: 1px solid #E5E5E5;
            border-radius: 8px;
        }}
    """)
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(widget)
    return container
