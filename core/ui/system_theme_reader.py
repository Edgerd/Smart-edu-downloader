# -*- coding: utf-8 -*-
"""系统主题色读取模块。

提供跨平台接口获取操作系统当前强调色（主题色），
主要用于实验性功能将系统主题色同步为程序主题色。
"""

import subprocess
from typing import Any, Dict, Optional, Tuple

from core.config.theme_config import (
    SYSTEM_PRESET_KEY,
    _derive_background,
    hex_to_hsl,
)
from core.i18n import _
from core.infrastructure.logger import log
from core.infrastructure.platform_utils import get_platform


def get_system_accent_color() -> Optional[str]:
    """获取操作系统当前强调色。

    Returns:
        str: 十六进制颜色字符串（如 #2078DA），获取失败或平台不支持时返回 None。
    """
    system = get_platform()
    if system == "windows":
        return _get_windows_accent_color()
    if system == "darwin":
        return _get_macos_accent_color()
    return _get_linux_accent_color()


def _get_windows_accent_color() -> Optional[str]:
    """从 Windows 注册表读取强调色。

    优先读取 ``HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\
    Explorer\\Accent`` 下的 ``AccentPalette`` 调色板，取第 4 个颜色（BGRA）
    作为用户当前强调色；调色板不可用时回退到 ``DWM\\AccentColor``。

    Returns:
        str: RGB 十六进制颜色字符串；读取失败返回 None。
    """
    import winreg

    # 首选：AccentPalette 调色板，第 4 项（偏移 12）为用户主题强调色
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"
        )
        value, _ = winreg.QueryValueEx(key, "AccentPalette")
        winreg.CloseKey(key)

        if isinstance(value, bytes) and len(value) >= 16:
            # 调色板每项 4 字节，按小端序存储的 BGRA DWORD，取第 4 项（索引 3）
            offset = 12
            dword = int.from_bytes(value[offset:offset + 4], "little")
            b = (dword >> 16) & 0xFF
            g = (dword >> 8) & 0xFF
            r = dword & 0xFF
            return f"#{r:02X}{g:02X}{b:02X}"
    except Exception as e:
        log("DEBUG", f"读取 Windows AccentPalette 失败: {e}")

    # 回退：DWM AccentColor（DWORD，BGRA 格式）
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\DWM"
        )
        value, _ = winreg.QueryValueEx(key, "AccentColor")
        winreg.CloseKey(key)

        if isinstance(value, int):
            bgra = value & 0xFFFFFFFF
            a = (bgra >> 24) & 0xFF
            b = (bgra >> 16) & 0xFF
            g = (bgra >> 8) & 0xFF
            r = bgra & 0xFF
            # 忽略纯透明结果
            if a == 0:
                return None
            return f"#{r:02X}{g:02X}{b:02X}"
    except Exception as e:
        log("DEBUG", f"读取 Windows DWM AccentColor 失败: {e}")

    return None


def _get_macos_accent_color() -> Optional[str]:
    """从 macOS 系统偏好设置读取强调色。

    通过 ``defaults read -g AppleAccentColor`` 获取索引，
    映射到对应颜色值。

    Returns:
        str: RGB 十六进制颜色字符串；读取失败返回 None。
    """
    accent_map = {
        "-1": "#697986",  # 石墨色
        "0": "#E95464",   # 红色
        "1": "#ED7F31",   # 橙色
        "2": "#F5C518",   # 黄色
        "3": "#68D44F",   # 绿色
        "4": "#3F8DED",   # 蓝色
        "5": "#9B59B6",   # 紫色
        "6": "#EC6197",   # 粉色
    }
    try:
        result = subprocess.run(
            ["defaults", "read", "-g", "AppleAccentColor"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        index = result.stdout.strip()
        if index in accent_map:
            return accent_map[index]
    except Exception as e:
        log("DEBUG", f"读取 macOS 强调色失败: {e}")
    return None


def _get_linux_accent_color() -> Optional[str]:
    """从 Linux 桌面环境读取强调色。

    目前支持 GNOME 的 ``gsettings`` 读取 ``accent-color`` 或
    ``theme-gtk-name`` 中常见的主题色。

    Returns:
        str: RGB 十六进制颜色字符串；读取失败返回 None。
    """
    try:
        result = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "accent-color"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
        )
        value = result.stdout.strip().strip("'\"")
        color_map = {
            "blue": "#3F8DED",
            "teal": "#26A69A",
            "green": "#68D44F",
            "yellow": "#F5C518",
            "orange": "#ED7F31",
            "red": "#E95464",
            "pink": "#EC6197",
            "purple": "#9B59B6",
            "slate": "#697986",
        }
        if value in color_map:
            return color_map[value]
    except Exception as e:
        log("DEBUG", f"读取 Linux 强调色失败: {e}")
    return None


def _color_to_hsl(color: str) -> Tuple[int, int, int]:
    """将颜色转换为 HSL 三元组，失败时返回默认值。

    Args:
        color: 十六进制颜色字符串。

    Returns:
        Tuple[int, int, int]: HSL 值。
    """
    try:
        return hex_to_hsl(color)
    except Exception:
        return (210, 75, 55)


def get_system_theme_config() -> Optional[Dict[str, Any]]:
    """基于系统强调色生成程序主题配置字典。

    Returns:
        Dict[str, Any]: 可用于 ``theme_color`` 设置项的配置字典；
        不支持或读取失败时返回 None。
    """
    color = get_system_accent_color()
    if not color:
        return None

    # 简单校验颜色格式
    try:
        stripped = color.lstrip("#")
        if len(stripped) != 6 or not all(c in "0123456789ABCDEFabcdef" for c in stripped):
            log("WARNING", f"读取到非法的系统主题色格式: {color}")
            return None
    except Exception:
        return None

    h, s, l = _color_to_hsl(color)
    return {
        "key": SYSTEM_PRESET_KEY,
        "preset": _("theme.preset.system_theme"),
        "primary": color,
        "background": _derive_background(color),
        "opacity": 255,
        "use_gradient": False,
        "gradient": None,
        "custom": {
            "base": color,
            "h": h,
            "s": s,
            "l": l,
            "opacity": 255,
            "use_gradient": False,
        },
    }
