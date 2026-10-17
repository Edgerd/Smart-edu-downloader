# -*- coding: utf-8 -*-
"""字体管理"""

import os
from PyQt5.QtGui import QFont, QFontDatabase

from core.infrastructure.platform_utils import (
    get_default_ui_font_family,
    get_default_monospace_font_family,
    UI_FONT_FALLBACKS,
    get_platform,
)


def get_platform_ui_font_fallbacks() -> list:
    """获取当前平台的 UI 字体回退族列表。"""
    return list(UI_FONT_FALLBACKS.get(get_platform(), UI_FONT_FALLBACKS["linux"]))

# 字体路径
# gui/fonts.py -> 上1级=项目根目录 -> 但实际字体在 resources/fonts/ 所以需要上2级
# 等等，gui/fonts.py 在 gui/ 下，上1级 = 项目根目录
FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources', 'fonts')

# 字体文件名
HARMONYOS_BLACK = 'HarmonyOS_Black.ttf'
HARMONYOS_BOLD = 'HarmonyOS_Bold.ttf'
HARMONYOS_MEDIUM = 'HarmonyOS_Medium.ttf'
HARMONYOS_REGULAR = 'HarmonyOS_Regular.ttf'
HARMONYOS_LIGHT = 'HarmonyOS_Light.ttf'
HARMONYOS_THIN = 'HarmonyOS_Thin.ttf'
PIXEL_FONT = 'Pixel.ttf'

# 字体大小配置
FONT_SIZE_TITLE = 15      # 标题字体大小（放大一号）
FONT_SIZE_NAV = 11        # 导航栏字体大小（比正文字体大一号）
FONT_SIZE_SUBTITLE = 12   # 副标题字体大小
FONT_SIZE_BODY = 10       # 正文字体大小
FONT_SIZE_SMALL = 8       # 小字体大小
FONT_SIZE_MONOSPACE = 10  # 等宽字体大小（用于日志/控制台）
FONT_SIZE_LARGE = 18      # 大字体大小（用于统计数字等）

# 已注册的字体族名称
_harmonyos_family = None
_pixel_family = None

def _load_fonts():
    """加载字体文件"""
    global _harmonyos_family, _pixel_family
    
    # 加载 HarmonyOS 字体（使用 Regular 作为基础）
    harmonyos_path = os.path.join(FONT_DIR, HARMONYOS_REGULAR)
    if os.path.exists(harmonyos_path):
        font_id = QFontDatabase.addApplicationFont(harmonyos_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                _harmonyos_family = families[0]
    
    # 加载 Pixel 字体
    pixel_path = os.path.join(FONT_DIR, PIXEL_FONT)
    if os.path.exists(pixel_path):
        font_id = QFontDatabase.addApplicationFont(pixel_path)
        if font_id != -1:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                _pixel_family = families[0]
    
    # 加载其他字重的 HarmonyOS 字体
    for font_file in [HARMONYOS_BOLD, HARMONYOS_MEDIUM, HARMONYOS_LIGHT, HARMONYOS_BLACK, HARMONYOS_THIN]:
        font_path = os.path.join(FONT_DIR, font_file)
        if os.path.exists(font_path):
            QFontDatabase.addApplicationFont(font_path)

def _ui_fallback_families():
    """构建 UI 字体回退族列表（鸿蒙优先，其次微软雅黑等）。"""
    families = []
    if _harmonyos_family:
        families.append(_harmonyos_family)
    for family in get_platform_ui_font_fallbacks():
        if family not in families:
            families.append(family)
    return families or ["Microsoft YaHei", "HarmonyOS Sans SC"]

def _apply_font_families(font: QFont) -> QFont:
    """为字体设置回退族（Qt >= 5.13 支持 setFamilies）。"""
    try:
        font.setFamilies(_ui_fallback_families())
    except AttributeError:
        pass
    return font

def get_harmonyos_family():
    """获取 HarmonyOS 字体族名称"""
    if _harmonyos_family is None:
        _load_fonts()
    return _harmonyos_family or get_default_ui_font_family()

def get_pixel_family():
    """获取 Pixel 字体族名称"""
    if _pixel_family is None:
        _load_fonts()
    return _pixel_family or get_default_monospace_font_family()

def title_font():
    """获取标题字体"""
    return _apply_font_families(QFont(get_harmonyos_family(), FONT_SIZE_TITLE, QFont.Bold))

def nav_font():
    """获取导航栏字体"""
    return _apply_font_families(QFont(get_harmonyos_family(), FONT_SIZE_NAV, QFont.Medium))

def subtitle_font():
    """获取副标题字体"""
    return _apply_font_families(QFont(get_harmonyos_family(), FONT_SIZE_SUBTITLE, QFont.Medium))

def body_font():
    """获取正文字体"""
    return _apply_font_families(QFont(get_harmonyos_family(), FONT_SIZE_BODY))

def small_font():
    """获取小字体"""
    return _apply_font_families(QFont(get_harmonyos_family(), FONT_SIZE_SMALL))

def bold_font():
    """获取粗体字"""
    return _apply_font_families(QFont(get_harmonyos_family(), FONT_SIZE_BODY, QFont.Bold))

def monospace_font():
    """获取等宽字体（用于日志/控制台）"""
    return _apply_font_families(QFont(get_pixel_family(), FONT_SIZE_MONOSPACE))

def large_font():
    """获取大字体（用于统计数字等）"""
    return _apply_font_families(QFont(get_harmonyos_family(), FONT_SIZE_LARGE, QFont.Bold))

# 延迟初始化 - 由调用方在 Qt 应用程序初始化后调用
def init_fonts():
    """初始化加载字体（应在 Qt 应用程序初始化后调用）"""
    global _harmonyos_family
    _load_fonts()
    # 设置全局默认字体，覆盖未显式指定字体的界面
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app is not None:
            default_font = _apply_font_families(
                QFont(get_harmonyos_family(), FONT_SIZE_BODY)
            )
            app.setFont(default_font)
    except Exception:
        pass
