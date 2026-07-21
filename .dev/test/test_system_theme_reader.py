# -*- coding: utf-8 -*-
"""系统主题色读取模块测试。"""
import sys
import os

# 将项目根目录加入路径（脚本位于 .dev/test/，需向上三级）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.chdir(project_root)

from core.ui.system_theme_reader import (
    _color_to_hsl,
    get_system_theme_config,
    get_system_accent_color,
)


def test_color_to_hsl():
    """颜色转 HSL 应返回合法三元组。"""
    h, s, l = _color_to_hsl("#2078DA")
    assert 0 <= h <= 360, f"色相越界: {h}"
    assert 0 <= s <= 100, f"饱和度越界: {s}"
    assert 0 <= l <= 100, f"亮度越界: {l}"
    print(f"_color_to_hsl('#2078DA') = ({h}, {s}, {l})")


def test_get_system_theme_config_on_windows():
    """在 Windows 上应能读取到合法的主题配置。"""
    config = get_system_theme_config()
    if config is None:
        print("当前未读取到系统主题色（可能平台不支持或读取失败）")
        return

    primary = config.get("primary")
    assert primary and primary.startswith("#") and len(primary) == 7, (
        f"主色格式异常: {primary!r}"
    )
    background = config.get("background")
    assert background and background.startswith("#") and len(background) == 7, (
        f"背景色格式异常: {background!r}"
    )
    assert config.get("key") == "custom"
    assert config.get("use_gradient") is False
    print(f"系统主题配置: primary={primary}, background={background}")


def test_get_system_accent_color_format():
    """读取到的系统强调色应为 #RRGGBB 格式或 None。"""
    color = get_system_accent_color()
    if color is None:
        print("未读取到系统强调色")
        return
    assert isinstance(color, str) and color.startswith("#") and len(color) == 7, (
        f"颜色格式异常: {color!r}"
    )
    print(f"系统强调色: {color}")


def main():
    """运行所有测试。"""
    test_color_to_hsl()
    test_get_system_accent_color_format()
    test_get_system_theme_config_on_windows()
    print("系统主题色读取测试通过")


if __name__ == "__main__":
    main()
