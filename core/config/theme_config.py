# -*- coding: utf-8 -*-
"""主题配置模块。

提供内置主题预设、主题配置读取与派生、自定义主题 HSL 调节以及旧设置迁移功能。
"""

import colorsys
from typing import Any, Dict, List, Optional, Tuple

from core.i18n import _


def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """将十六进制颜色字符串转换为 RGB 元组。"""
    color = hex_color.strip().lstrip("#")
    if len(color) == 3:
        r, g, b = [int(c * 2, 16) for c in color]
    elif len(color) == 6:
        r = int(color[0:2], 16)
        g = int(color[2:4], 16)
        b = int(color[4:6], 16)
    else:
        raise ValueError(f"Unsupported color format: {hex_color}")
    return r, g, b


def _rgb_to_hex(r: int, g: int, b: int) -> str:
    """将 RGB 值转换为十六进制颜色字符串。"""
    return f"#{max(0, min(255, r)):02x}{max(0, min(255, g)):02x}{max(0, min(255, b)):02x}"


# 图标着色时需要替换的基准颜色集合（白色 + 历史主题色）
ICON_BASE_COLORS = {"white", "#ffffff", "#fff", "#1A82E2", "#2078DA", "#007AFF", "#1277DD"}


# 自定义主题标识
CUSTOM_PRESET_KEY = "custom"

# 系统主题色（自动跟随操作系统强调色）标识
SYSTEM_PRESET_KEY = "system_theme"


# 内置主题预设列表
BUILT_IN_PRESETS: List[Dict[str, Any]] = [
    {
        "name": "theme.preset.jingdianlan",
        "key": "jingdianlan",
        "primary": "#1277DD",
        "background": "#E8F4FD",
        "opacity": 255,
        "use_gradient": False,
        "gradient": None,
    },
    {
        "name": "theme.preset.xuansuhei",
        "key": "xuansuhei",
        "primary": "#282A30",
        "background": "#E6E7EA",
        "opacity": 255,
        "use_gradient": False,
        "gradient": None,
    },
    {
        "name": "theme.preset.tieganfen",
        "key": "tieganfen",
        "primary": "#E9849D",
        "background": "#F5DDE2",
        "opacity": 255,
        "use_gradient": False,
        "gradient": None,
    },
    {
        "name": "theme.preset.shenmizi",
        "key": "shenmizi",
        "primary": "#8B37A6",
        "background": "#EDDDF1",
        "opacity": 255,
        "use_gradient": False,
        "gradient": None,
    },
    {
        "name": "theme.preset.ouhuangcai",
        "key": "ouhuangcai",
        "primary": "#8F36A1",
        "background": "#EDDDF0",
        "opacity": 255,
        "use_gradient": True,
        "gradient": {
            "direction": "horizontal",
            "start": "#7349C2",
            "end": "#BB3E68",
        },
    },
    {
        "name": "theme.preset.qiuyijin",
        "key": "qiuyijin",
        "primary": "#B49C26",
        "background": "#F0ECD1",
        "opacity": 255,
        "use_gradient": False,
        "gradient": None,
    },
    {
        "name": "theme.preset.huoyuecheng",
        "key": "huoyuecheng",
        "primary": "#D46A1E",
        "background": "#F5E6D8",
        "opacity": 255,
        "use_gradient": False,
        "gradient": None,
    },
    {
        "name": "theme.preset.tiaopiaohong",
        "key": "tiaopiaohong",
        "primary": "#C12F22",
        "background": "#F6E0DE",
        "opacity": 255,
        "use_gradient": False,
        "gradient": None,
    },
    {
        "name": "theme.preset.jikelan",
        "key": "jikelan",
        "primary": "#2E45B7",
        "background": "#E0E3F4",
        "opacity": 255,
        "use_gradient": False,
        "gradient": None,
    },
    {
        "name": "theme.preset.xingkonglan",
        "key": "xingkonglan",
        "primary": "#2B4BAD",
        "background": "#DEE4F4",
        "opacity": 255,
        "use_gradient": False,
        "gradient": None,
    },
]

# 默认主题：经典蓝
DEFAULT_PRESET_KEY = "jingdianlan"


def _preset_by_key(key: str) -> Optional[Dict[str, Any]]:
    """根据 key 查找内置预设。"""
    for preset in BUILT_IN_PRESETS:
        if preset["key"] == key:
            return preset.copy()
    return None


# 旧版中文预设名称到 i18n 键的兼容映射
_LEGACY_PRESET_NAMES = {
    "经典蓝": "theme.preset.jingdianlan",
    "玄素黑": "theme.preset.xuansuhei",
    "铁杆粉": "theme.preset.tieganfen",
    "神秘紫": "theme.preset.shenmizi",
    "欧皇彩": "theme.preset.ouhuangcai",
    "秋议金": "theme.preset.qiuyijin",
    "活跃橙": "theme.preset.huoyuecheng",
    "跳票红": "theme.preset.tiaopiaohong",
    "极客蓝": "theme.preset.jikelan",
    "星空蓝": "theme.preset.xingkonglan",
}


def _resolve_preset_name(name: str) -> str:
    """将可能的旧版中文名称解析为当前 i18n 键。"""
    if name in _LEGACY_PRESET_NAMES:
        return _LEGACY_PRESET_NAMES[name]
    return name


def _preset_by_name(name: str) -> Optional[Dict[str, Any]]:
    """根据显示名称查找内置预设（兼容旧版中文名）。"""
    resolved = _resolve_preset_name(name)
    for preset in BUILT_IN_PRESETS:
        if preset["name"] == resolved:
            return preset.copy()
    return None


def _default_config() -> Dict[str, Any]:
    """返回默认主题配置。"""
    preset = _preset_by_key(DEFAULT_PRESET_KEY)
    if preset is None:
        preset = BUILT_IN_PRESETS[0].copy()
    return {
        "key": preset["key"],
        "preset": _(preset["name"]),
        "primary": preset["primary"],
        "background": preset["background"],
        "opacity": 255,
        "use_gradient": bool(preset.get("use_gradient")),
        "gradient": preset.get("gradient"),
        "custom": None,
    }


def _derive_background(primary: str) -> str:
    """根据主色自动派生内容区背景色。

    基于现有主题预设的统计规律，在 HSL 空间中对主色进行变换：
    色相保持不变，亮度固定到约 91%，饱和度按主色饱和度的 0.78 倍缩放，
    使派生背景色与内置预设风格保持一致。
    """
    try:
        h, s, _ = hex_to_hsl(primary)
        new_l = 91
        new_s = max(6, min(95, round(s * 0.78)))
        return hsl_to_hex(h, new_s, new_l)
    except Exception:
        return "#E8F4FD"


def hex_to_hsl(hex_color: str) -> Tuple[int, int, int]:
    """将十六进制颜色转换为 HSL 三元组（0-360, 0-100, 0-100）。"""
    try:
        r, g, b = _hex_to_rgb(hex_color)
        h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
        return (
            int(round(h * 360)),
            int(round(s * 100)),
            int(round(l * 100)),
        )
    except Exception:
        return (210, 75, 55)


def hsl_to_hex(h: int, s: int, l: int) -> str:
    """将 HSL 三元组转换为十六进制颜色。"""
    try:
        h = max(0, min(360, h)) / 360.0
        s = max(0, min(100, s)) / 100.0
        l = max(0, min(100, l)) / 100.0
        r, g, b = colorsys.hls_to_rgb(h, l, s)
        return _rgb_to_hex(
            int(round(r * 255)),
            int(round(g * 255)),
            int(round(b * 255)),
        )
    except Exception:
        return "#2078DA"


def apply_hsl(base: str, h: Optional[int], s: Optional[int], l: Optional[int]) -> str:
    """基于基础色应用 HSL 调节，None 表示保持原值。"""
    try:
        base_h, base_s, base_l = hex_to_hsl(base)
        new_h = h if h is not None else base_h
        new_s = s if s is not None else base_s
        new_l = l if l is not None else base_l
        return hsl_to_hex(new_h, new_s, new_l)
    except Exception:
        return base


def build_custom_config(
    base: str,
    h: int,
    s: int,
    l: int,
    opacity: int,
    use_gradient: bool,
) -> Dict[str, Any]:
    """根据用户自定义 HSL 滑块生成自定义主题配置。"""
    primary = apply_hsl(base, h, s, l)
    return {
        "key": CUSTOM_PRESET_KEY,
        "preset": _("theme.preset.custom"),
        "primary": primary,
        "background": _derive_background(primary),
        "opacity": max(0, min(255, opacity)),
        "use_gradient": bool(use_gradient),
        "gradient": None,
        "custom": {
            "base": base,
            "h": h,
            "s": s,
            "l": l,
            "opacity": max(0, min(255, opacity)),
            "use_gradient": bool(use_gradient),
        },
    }


def get_theme_config(settings: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """从设置字典读取主题配置，缺失或旧格式时返回默认配置。

    若当前为系统主题色模式，则重新读取操作系统强调色以保证每次启动
    都能同步最新颜色。
    """
    if not settings:
        return _default_config()

    config = settings.get("theme_color")
    if not isinstance(config, dict) or "primary" not in config:
        return _default_config()

    if config.get("key") == SYSTEM_PRESET_KEY:
        # 延迟导入避免循环依赖
        try:
            from core.ui.system_theme_reader import get_system_theme_config
            system_config = get_system_theme_config()
            if system_config:
                return system_config
        except Exception:
            pass

    return config


def primary_color(config: Dict[str, Any]) -> str:
    """返回主题主色（控件强调色来源）。"""
    return config.get("primary", _default_config()["primary"])


def background_color(config: Dict[str, Any]) -> str:
    """返回内容区背景色。"""
    bg = config.get("background")
    if bg:
        return bg
    return _derive_background(primary_color(config))


def title_bar_gradient(config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """返回标题栏/导航栏渐变配置，无渐变时返回 None。"""
    if not config.get("use_gradient"):
        return None
    gradient = config.get("gradient")
    if gradient and gradient.get("start") and gradient.get("end"):
        return gradient
    return None


def opacity(config: Dict[str, Any]) -> int:
    """返回标题栏/导航栏不透明度（0-255）。"""
    return max(0, min(255, config.get("opacity", 255)))


def preset_name(config: Dict[str, Any]) -> str:
    """返回当前主题预设名称。"""
    return config.get("preset", _("theme.preset.custom"))


def built_in_preset_names() -> List[str]:
    """返回所有内置预设 i18n 键。"""
    return [preset["name"] for preset in BUILT_IN_PRESETS]


def built_in_presets() -> List[Dict[str, Any]]:
    """返回所有内置预设的副本。"""
    return [preset.copy() for preset in BUILT_IN_PRESETS]


def config_from_preset_name(name: str) -> Dict[str, Any]:
    """根据预设名称生成完整配置，未找到时返回默认配置。

    兼容旧版中文预设名。
    """
    if name == _("theme.preset.custom") or name == "自定义":
        return config_from_preset_key(CUSTOM_PRESET_KEY)

    preset = _preset_by_name(name)
    if preset is None:
        return _default_config()

    return config_from_preset_key(preset["key"])


def config_from_preset_key(key: str) -> Dict[str, Any]:
    """根据预设 key 生成完整配置，未找到时返回默认配置。"""
    if key == CUSTOM_PRESET_KEY:
        base_config = _default_config()
        base_config["key"] = CUSTOM_PRESET_KEY
        base_config["preset"] = _("theme.preset.custom")
        base_config["custom"] = {
            "base": base_config["primary"],
            "h": 222,
            "s": 73,
            "l": 49,
            "opacity": 255,
            "use_gradient": False,
        }
        return base_config

    if key == SYSTEM_PRESET_KEY:
        # 延迟导入避免循环依赖
        try:
            from core.ui.system_theme_reader import get_system_theme_config
            system_config = get_system_theme_config()
            if system_config:
                return system_config
        except Exception:
            pass
        # 读取失败时回退到默认配置，但保留系统主题标识
        fallback = _default_config()
        fallback["key"] = SYSTEM_PRESET_KEY
        fallback["preset"] = _("theme.preset.system_theme")
        return fallback

    preset = _preset_by_key(key)
    if preset is None:
        return _default_config()

    return {
        "key": preset["key"],
        "preset": _(preset["name"]),
        "primary": preset["primary"],
        "background": preset["background"],
        "opacity": preset.get("opacity", 255),
        "use_gradient": bool(preset.get("use_gradient", False)),
        "gradient": preset.get("gradient"),
        "custom": None,
    }


def migrate_old_theme_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """把旧版 theme_color/accent_color 字符串迁移为新的主题配置字典。

    直接修改传入字典并返回。
    """
    if not isinstance(settings, dict):
        return settings

    # 删除旧的 accent_color
    if "accent_color" in settings:
        del settings["accent_color"]

    old_theme = settings.get("theme_color")
    if isinstance(old_theme, dict) and "primary" in old_theme:
        # 已经是新格式，仅确保 custom 字段存在
        return settings

    # 旧版字符串映射
    if isinstance(old_theme, str):
        old_lower = old_theme.lower()
        if old_lower in {"#2078da", "#1277dd", "#1a82e2"}:
            settings["theme_color"] = config_from_preset_name("极客蓝")
        elif old_lower == "#2ecc71":
            settings["theme_color"] = config_from_preset_name("活跃橙")
        else:
            custom = build_custom_config(
                base=old_theme,
                h=hex_to_hsl(old_theme)[0],
                s=hex_to_hsl(old_theme)[1],
                l=hex_to_hsl(old_theme)[2],
                opacity=255,
                use_gradient=False,
            )
            settings["theme_color"] = custom
    else:
        settings["theme_color"] = _default_config()

    return settings
