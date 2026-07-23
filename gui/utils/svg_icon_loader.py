# -*- coding: utf-8 -*-
"""SVG 图标加载工具。

提供从项目 resources/svg_library 目录加载 SVG 并渲染为 QIcon 的通用方法，
支持按颜色映射表替换 SVG 中的填充色。
"""

import os

from PyQt5.QtCore import Qt, QByteArray
from PyQt5.QtGui import QIcon, QPixmap, QPainter
from PyQt5.QtSvg import QSvgRenderer


def load_svg_library_icon(icon_subpath, size=(24, 24), color_map=None):
    """从 svg_library 加载 SVG 并渲染为 QIcon。

    Args:
        icon_subpath: 图标在 svg_library 下的相对路径，例如
            "07_nature_food/爱发电_svg.svg"。
        size: 渲染后的图标尺寸，格式为 (宽, 高)。
        color_map: 可选的颜色映射字典。为避免替换顺序导致颜色互相覆盖，
            内部会先统一替换为临时占位符再写入目标颜色。

    Returns:
        QIcon or None: 加载成功返回图标，失败返回 None。
    """
    project_root = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    svg_path = os.path.join(project_root, "resources", "svg_library", icon_subpath)
    if not os.path.exists(svg_path):
        return None

    try:
        with open(svg_path, "r", encoding="utf-8") as f:
            svg_data = f.read()
    except Exception:
        return None

    if color_map:
        placeholders = {}
        for index, old_color in enumerate(color_map.keys()):
            placeholder = f"__COLOR_{index}__"
            placeholders[placeholder] = color_map[old_color]
            svg_data = svg_data.replace(old_color, placeholder)
        for placeholder, new_color in placeholders.items():
            svg_data = svg_data.replace(placeholder, new_color)

    renderer = QSvgRenderer(QByteArray(svg_data.encode("utf-8")))
    if not renderer.isValid():
        return None

    pixmap = QPixmap(size[0], size[1])
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    try:
        renderer.render(painter)
    finally:
        if painter.isActive():
            painter.end()

    return QIcon(pixmap)
