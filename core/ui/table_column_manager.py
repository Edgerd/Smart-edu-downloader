# -*- coding: utf-8 -*-
"""表格列宽管理模块"""

from PyQt5.QtWidgets import QTableWidget, QTreeWidget

from core.infrastructure.logger import log


def save_table_widths(table: QTableWidget) -> dict:
    """保存表格列宽配置"""
    widths = {}
    header = table.horizontalHeader()
    for col in range(table.columnCount()):
        widths[f"col_{col}"] = header.sectionSize(col)
    return widths


def restore_table_widths(table: QTableWidget, widths: dict) -> None:
    """恢复表格列宽配置"""
    if not widths:
        return
    header = table.horizontalHeader()
    for col in range(table.columnCount()):
        key = f"col_{col}"
        if key in widths and widths[key] > 0:
            header.resizeSection(col, widths[key])


def save_tree_widths(tree: QTreeWidget) -> dict:
    """保存树控件列宽配置"""
    widths = {}
    header = tree.header()
    for col in range(tree.columnCount()):
        widths[f"col_{col}"] = header.sectionSize(col)
    return widths


def restore_tree_widths(tree: QTreeWidget, widths: dict) -> None:
    """恢复树控件列宽配置"""
    if not widths:
        return
    header = tree.header()
    for col in range(tree.columnCount()):
        key = f"col_{col}"
        if key in widths and widths[key] > 0:
            header.resizeSection(col, widths[key])


def restore_table_widths_from_settings(table: QTableWidget, setting_key: str) -> None:
    """从设置中恢复表格列宽"""
    try:
        from core.config.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        saved_widths = settings_mgr.get(setting_key, {})
        if saved_widths:
            restore_table_widths(table, saved_widths)
    except Exception as e:
        log("WARNING", f"恢复表格列宽失败 ({setting_key}): {e}")


def restore_tree_widths_from_settings(tree: QTreeWidget, setting_key: str) -> None:
    """从设置中恢复树控件列宽"""
    try:
        from core.config.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        saved_widths = settings_mgr.get(setting_key, {})
        if saved_widths:
            restore_tree_widths(tree, saved_widths)
    except Exception as e:
        log("WARNING", f"恢复树控件列宽失败 ({setting_key}): {e}")


def save_table_widths_to_settings(table: QTableWidget, setting_key: str) -> None:
    """保存表格列宽到设置"""
    try:
        from core.config.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        widths = save_table_widths(table)
        settings_mgr.set(setting_key, widths, auto_save=False)
    except Exception as e:
        log("ERROR", f"保存表格列宽失败 ({setting_key}): {e}")


def save_tree_widths_to_settings(tree: QTreeWidget, setting_key: str) -> None:
    """保存树控件列宽到设置"""
    try:
        from core.config.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        widths = save_tree_widths(tree)
        settings_mgr.set(setting_key, widths, auto_save=False)
    except Exception as e:
        log("ERROR", f"保存树控件列宽失败 ({setting_key}): {e}")
