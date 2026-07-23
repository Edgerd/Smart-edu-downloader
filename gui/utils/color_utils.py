# -*- coding: utf-8 -*-
"""颜色计算工具模块。

提供统一的颜色转换、变亮/变暗、混合以及 Material Design 水波纹色调计算函数。
"""

from typing import Tuple


class ColorError(ValueError):
    """颜色解析错误"""
    pass


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """将十六进制颜色字符串转换为 RGB 元组。

    Args:
        hex_color: 十六进制颜色，支持 #RGB、#RRGGBB、#ARGB、#AARRGGBB。

    Returns:
        (R, G, B) 元组，范围 0-255。

    Raises:
        ColorError: 颜色格式无法解析。
    """
    color = hex_color.strip().lstrip("#")
    if not color:
        raise ColorError("Empty color string")

    if len(color) == 3:
        r, g, b = [int(c * 2, 16) for c in color]
    elif len(color) == 6:
        r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
    elif len(color) == 4:
        # ARGB，忽略 alpha
        _, r, g, b = [int(c * 2, 16) for c in color]
    elif len(color) == 8:
        # AARRGGBB，忽略 alpha
        r, g, b = int(color[2:4], 16), int(color[4:6], 16), int(color[6:8], 16)
    else:
        raise ColorError(f"Unsupported color format: {hex_color}")

    return r, g, b


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """将 RGB 值转换为十六进制颜色字符串。

    Args:
        r: 红色通道，0-255。
        g: 绿色通道，0-255。
        b: 蓝色通道，0-255。

    Returns:
        #RRGGBB 格式字符串。
    """
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


def _brightness(r: int, g: int, b: int) -> float:
    """计算人眼感知亮度。"""
    return (r * 299 + g * 587 + b * 114) / 1000


def lighten(hex_color: str, percent: int) -> str:
    """按比例向白色混合，使颜色变亮。

    Args:
        hex_color: 基础颜色。
        percent: 向白色混合的百分比，0-100。

    Returns:
        变亮后的 #RRGGBB 颜色。
    """
    try:
        r, g, b = hex_to_rgb(hex_color)
        p = max(0, min(100, percent)) / 100
        r = int(r + (255 - r) * p)
        g = int(g + (255 - g) * p)
        b = int(b + (255 - b) * p)
        return rgb_to_hex(r, g, b)
    except ColorError:
        return hex_color


def darken(hex_color: str, percent: int) -> str:
    """按比例向黑色混合，使颜色变暗。

    Args:
        hex_color: 基础颜色。
        percent: 向黑色混合的百分比，0-100。

    Returns:
        变暗后的 #RRGGBB 颜色。
    """
    try:
        r, g, b = hex_to_rgb(hex_color)
        p = max(0, min(100, percent)) / 100
        r = int(r * (1 - p))
        g = int(g * (1 - p))
        b = int(b * (1 - p))
        return rgb_to_hex(r, g, b)
    except ColorError:
        return hex_color


def mix(color1: str, color2: str, weight: float) -> str:
    """将两种颜色按权重线性混合。

    Args:
        color1: 第一种颜色。
        color2: 第二种颜色。
        weight: color2 的权重，0.0-1.0。

    Returns:
        混合后的 #RRGGBB 颜色。
    """
    try:
        r1, g1, b1 = hex_to_rgb(color1)
        r2, g2, b2 = hex_to_rgb(color2)
        w = max(0.0, min(1.0, weight))
        r = int(r1 * (1 - w) + r2 * w)
        g = int(g1 * (1 - w) + g2 * w)
        b = int(b1 * (1 - w) + b2 * w)
        return rgb_to_hex(r, g, b)
    except ColorError:
        return color1


def adjust_brightness(hex_color: str, delta: int) -> str:
    """通过增减RGB值调整颜色亮度。

    Args:
        hex_color: 基础颜色。
        delta: RGB增减量，正数变亮，负数变暗。

    Returns:
        调整后的 #RRGGBB 颜色。
    """
    try:
        r, g, b = hex_to_rgb(hex_color)
        r = max(0, min(255, r + delta))
        g = max(0, min(255, g + delta))
        b = max(0, min(255, b + delta))
        return rgb_to_hex(r, g, b)
    except ColorError:
        return hex_color


def ripple_tint(
    base_color: str,
    lighten_percent: int = 18,
    darken_percent: int = 12,
    threshold: int = 128,
) -> str:
    """根据基础色亮度返回淡化后的水波纹颜色。

    规则：
    - 深色背景（亮度 <= threshold）=> 使用 lighten 变淡。
    - 浅色背景（亮度 > threshold）=> 使用 darken 变暗。

    示例：
        ripple_tint("#2078DA")  # 深色 -> 淡蓝色
        ripple_tint("#E8F0FE")  # 浅色 -> 略深的蓝色

    Args:
        base_color: 基础背景色。
        lighten_percent: 深色背景时的变亮百分比。
        darken_percent: 浅色背景时的变暗百分比。
        threshold: 深浅色亮度阈值。

    Returns:
        淡化后的 #RRGGBB 颜色。
    """
    try:
        r, g, b = hex_to_rgb(base_color)
        brightness = _brightness(r, g, b)
        if brightness <= threshold:
            return lighten(base_color, lighten_percent)
        return darken(base_color, darken_percent)
    except ColorError:
        return base_color
