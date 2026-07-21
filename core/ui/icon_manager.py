# -*- coding: utf-8 -*-
"""图标资源管理模块"""
from core.i18n import _

import os
import re
from PyQt5.QtGui import QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt, QByteArray
from PyQt5.QtSvg import QSvgRenderer

# P2-4优化：预编译SVG颜色替换正则表达式
# 将除透明外的所有 fill 颜色统一替换为目标主题色，避免 SVG 源文件使用
# 非预期基准色时图标无法随主题变化。
_FILL_REGEX = re.compile(
    r'fill="(?!none|transparent)([^"]*)"',
    re.IGNORECASE
)


class IconManager:
    """图标资源管理器（单例）。

    全局共享 SVG 文本缓存与 pixmap 缓存，确保主题色切换时只需清空一次缓存，
    所有引用处都能重新按新颜色渲染图标。
    """

    _instance = None

    def __new__(cls, base_dir=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, base_dir=None):
        """初始化图标管理器"""
        if self._initialized:
            return
        self._initialized = True

        if base_dir is None:
            # core/ui/icon_manager.py -> 上2级=项目根目录
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

        self.nav_icon_dir = os.path.join(base_dir, "resources", "images", "nav")
        self.title_icon_dir = os.path.join(base_dir, "resources", "images", "titles")
        self._svg_cache = {}
        self._pixmap_cache = {}
    
    def get_svg_path(self, icon_name):
        """获取导航 SVG 图标文件路径"""
        return os.path.join(self.nav_icon_dir, icon_name)
    
    def get_title_svg_path(self, icon_name):
        """获取标题 SVG 图标文件路径"""
        return os.path.join(self.title_icon_dir, icon_name)
    
    def _read_svg_content(self, icon_name):
        """读取 SVG 文件内容并缓存"""
        if icon_name in self._svg_cache:
            return self._svg_cache[icon_name]
        
        path = self.get_svg_path(icon_name)
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self._svg_cache[icon_name] = content
            return content
        except Exception:
            return None
    
    def _read_title_svg_content(self, icon_name):
        """读取标题 SVG 文件内容并缓存"""
        cache_key = f"title:{icon_name}"
        if cache_key in self._svg_cache:
            return self._svg_cache[cache_key]
        
        path = self.get_title_svg_path(icon_name)
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            self._svg_cache[cache_key] = content
            return content
        except Exception:
            return None
    
    def load_colored_pixmap(self, icon_name, color, size=(24, 24)):
        """加载导航 SVG 并着色为指定颜色
        
        原理：
        1. 读取 SVG 源文本
        2. 将 fill 颜色替换为目标颜色
        3. 渲染为 QPixmap
        
        Args:
            icon_name: 图标文件名,如"nav_home.svg"
            color: 目标颜色 (QColor 或 颜色字符串如 "#1A82E2")
            size: 图标尺寸(宽,高)
        
        Returns:
            QPixmap or None: 着色后的图标
        """
        if isinstance(color, QColor):
            color_str = color.name()
        else:
            color_str = color
        
        cache_key = f"{icon_name}/{color_str}/{size}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]
        
        svg_content = self._read_svg_content(icon_name)
        if svg_content is None:
            return None
        
        # P2-4优化：使用预编译正则表达式替换 SVG 中的 fill 颜色（单次遍历替代多次replace）
        svg_content = _FILL_REGEX.sub(f'fill="{color_str}"', svg_content)
        
        # 渲染 SVG
        renderer = QSvgRenderer(QByteArray(svg_content.encode('utf-8')))
        if not renderer.isValid():
            return None
        
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
        painter.end()
        
        self._pixmap_cache[cache_key] = pixmap
        return pixmap
    
    def load_svg_raw(self, icon_name, size=(24, 24)):
        """加载标题 SVG 保持原始颜色（不进行着色处理）
        
        Args:
            icon_name: 图标文件名,如"title_home.svg"
            size: 图标尺寸
        
        Returns:
            QPixmap or None: 原始颜色的图标
        """
        cache_key = f"raw:{icon_name}/{size}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]
        
        svg_content = self._read_title_svg_content(icon_name)
        if svg_content is None:
            return None
        
        # 渲染 SVG（不修改颜色）
        renderer = QSvgRenderer(QByteArray(svg_content.encode('utf-8')))
        if not renderer.isValid():
            return None
        
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
        painter.end()
        
        self._pixmap_cache[cache_key] = pixmap
        return pixmap
    
    def load_title_svg(self, icon_name, color, size=(24, 24)):
        """加载标题 SVG 并着色为指定颜色
        
        Args:
            icon_name: 图标文件名,如"title_home.svg"
            color: 目标颜色
            size: 图标尺寸
        
        Returns:
            QPixmap or None: 着色后的图标
        """
        if isinstance(color, QColor):
            color_str = color.name()
        else:
            color_str = color
        
        cache_key = f"title:{icon_name}/{color_str}/{size}"
        if cache_key in self._pixmap_cache:
            return self._pixmap_cache[cache_key]
        
        svg_content = self._read_title_svg_content(icon_name)
        if svg_content is None:
            return None
        
        # P2-4优化：使用预编译正则表达式替换 SVG 中的 fill 颜色
        svg_content = _FILL_REGEX.sub(f'fill="{color_str}"', svg_content)
        
        # 渲染 SVG
        renderer = QSvgRenderer(QByteArray(svg_content.encode('utf-8')))
        if not renderer.isValid():
            return None
        
        pixmap = QPixmap(size[0], size[1])
        pixmap.fill(Qt.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        renderer.render(painter)
        painter.end()
        
        self._pixmap_cache[cache_key] = pixmap
        return pixmap
    
    def clear_cache(self):
        """清空所有缓存"""
        self._svg_cache.clear()
        self._pixmap_cache.clear()

    def clear_pixmap_cache(self):
        """清空 pixmap 缓存，保留 SVG 文本缓存。

        主题色切换时调用，确保已着色的图标按新颜色重新渲染。
        """
        self._pixmap_cache.clear()


# 导航栏图标配置（SVG 版本）
NAV_ICONS = [
    {
        "name": _("nav.home.name"),
        "icon_file": "nav_home.svg",
        "tip": _("nav.home.tip")
    },
    {
        "name": _("nav.resource.name"),
        "icon_file": "nav_resource.svg",
        "tip": _("nav.resource.tip")
    },
    {
        "name": _("settings.tabs.download"),
        "icon_file": "nav_download.svg",
        "tip": _("nav.download.tip")
    },
    {
        "name": _("settings.title"),
        "icon_file": "nav_settings.svg",
        "tip": _("nav.settings.tip")
    },
    {
        "name": _("nav.more.name"),
        "icon_file": "nav_more.svg",
        "tip": _("nav.more.tip")
    }
]
