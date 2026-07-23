# -*- coding: utf-8 -*-
"""设置页 qfluentwidgets SettingCard 配置项工厂。

集中管理设置页使用的 OptionsConfigItem / RangeConfigItem，
避免各标签页重复创建，便于统一分组和默认值维护。
"""

from typing import Any, Iterable, Optional

import sys
import io

# 静默导入，避免 Pro 提示输出到控制台
_old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    from qfluentwidgets import OptionsConfigItem, OptionsValidator, RangeConfigItem, RangeValidator
finally:
    sys.stdout = _old_stdout


class SettingConfigItems:
    """设置页配置项缓存。

    同一配置项在不同卡片间共享，确保 valueChanged 信号统一。
    """

    _cache = {}

    @classmethod
    def get_option(cls, key: str, default: Any, options: Iterable[Any]) -> OptionsConfigItem:
        """获取或创建 OptionsConfigItem。

        Args:
            key: 设置键名。
            default: 默认值。
            options: 可选值列表。

        Returns:
            OptionsConfigItem 实例。
        """
        if key not in cls._cache:
            cls._cache[key] = OptionsConfigItem(
                "Settings", key, default, OptionsValidator(list(options))
            )
        return cls._cache[key]

    @classmethod
    def get_range(cls, key: str, default: int, min_value: int, max_value: int) -> RangeConfigItem:
        """获取或创建 RangeConfigItem。

        Args:
            key: 设置键名。
            default: 默认值。
            min_value: 最小值。
            max_value: 最大值。

        Returns:
            RangeConfigItem 实例。
        """
        if key not in cls._cache:
            cls._cache[key] = RangeConfigItem(
                "Settings", key, default, RangeValidator(min_value, max_value)
            )
        return cls._cache[key]

    @classmethod
    def clear(cls):
        """清空缓存（主要用于测试）。"""
        cls._cache.clear()


def setting_option_item(key: str, default: Any, options: Iterable[Any]) -> OptionsConfigItem:
    """便捷函数：获取设置选项配置项。"""
    return SettingConfigItems.get_option(key, default, options)


def setting_range_item(key: str, default: int, min_value: int, max_value: int) -> RangeConfigItem:
    """便捷函数：获取设置范围配置项。"""
    return SettingConfigItems.get_range(key, default, min_value, max_value)
