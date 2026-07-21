# -*- coding: utf-8 -*-
"""测试主题选择器系统主题色选项加载。"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.chdir(project_root)

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from gui.components.theme_selector import ThemeSelector
from core.config.theme_config import SYSTEM_PRESET_KEY, config_from_preset_key

# 测试系统主题配置生成
config = config_from_preset_key(SYSTEM_PRESET_KEY)
print(f"系统主题配置 key={config.get('key')}, preset={config.get('preset')}, primary={config.get('primary')}")

# 测试选择器创建
selector = ThemeSelector(initial_config=config)
print(f"选择器 radio 数量: {len(selector._radio_buttons)}")
print(f"系统主题 radio 存在: {SYSTEM_PRESET_KEY in selector._radio_buttons}")
print(f"系统主题 radio 文本: {selector._radio_buttons[SYSTEM_PRESET_KEY].text()}")

# 测试自动更新定时器
print(f"定时器间隔: {selector._system_theme_timer.interval()} ms")
