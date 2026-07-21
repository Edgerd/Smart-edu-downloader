# -*- coding: utf-8 -*-
"""修改 SED settings.json 的配置项。"""

import json
import os
import sys

SETTINGS_PATH = r'C:\Users\Administrator\AppData\Local\Temp\Smart-edu-downloader\settings\settings.json'


def load_settings(path: str) -> dict:
    """加载 settings.json。"""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_settings(path: str, settings: dict) -> None:
    """保存 settings.json。"""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(settings, f, ensure_ascii=False, indent=2)


def set_title_bar_style(settings: dict, style: str) -> dict:
    """设置标题栏样式。"""
    settings['title_bar_style'] = style
    return settings


def set_gradient(settings: dict, enabled: bool) -> dict:
    """设置标题栏渐变开关。"""
    if 'theme_color' not in settings or not isinstance(settings['theme_color'], dict):
        settings['theme_color'] = {}
    settings['theme_color']['use_gradient'] = enabled
    return settings


def main():
    """根据命令行参数修改设置。"""
    if len(sys.argv) < 2:
        print('用法: python modify_settings.py <title_bar_style> [gradient_on|gradient_off]')
        sys.exit(1)

    style = sys.argv[1]
    gradient_arg = sys.argv[2] if len(sys.argv) > 2 else None

    settings = load_settings(SETTINGS_PATH)
    settings = set_title_bar_style(settings, style)

    if gradient_arg == 'gradient_on':
        settings = set_gradient(settings, True)
    elif gradient_arg == 'gradient_off':
        settings = set_gradient(settings, False)

    save_settings(SETTINGS_PATH, settings)
    print(f'已更新: title_bar_style={style}, use_gradient={settings.get("theme_color", {}).get("use_gradient")}')


if __name__ == '__main__':
    main()
