# -*- coding: utf-8 -*-
"""多语言支持模块。

提供全局可访问的翻译函数以及语言切换辅助接口。
"""

from core.i18n.translator import Translator

_translator = Translator()


def _(key: str, **kwargs) -> str:
    """获取当前语言下指定键的翻译文本。

    支持以点号分隔的嵌套键；若传入 kwargs，将对结果调用 str.format。
    当键缺失或格式化失败时，返回原键。

    Args:
        key: 翻译键，如 "app.name" 或 "common.ok"。
        **kwargs: 用于格式化翻译文本的占位符参数。

    Returns:
        str: 翻译后的文本；若缺失则返回原键。
    """
    text = _translator.translate(key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, ValueError, IndexError):
            pass
        if "{...}" in text:
            result = text
            try:
                for value in kwargs.values():
                    result = result.replace("{...}", str(value), 1)
                return result
            except Exception:
                pass
    return text


def tr(key: str, **kwargs) -> str:
    """_ 的别名，便于不同习惯调用。"""
    return _(key, **kwargs)


def gettext(key: str, **kwargs) -> str:
    """gettext 风格别名。"""
    return _(key, **kwargs)


def set_language(locale: str) -> bool:
    """设置当前语言。

    Args:
        locale: 目标语言代码。

    Returns:
        bool: 是否设置成功。
    """
    return _translator.set_language(locale)


def get_available_languages() -> list:
    """返回已加载的语言列表。"""
    return _translator.get_available_languages()


def get_current_locale() -> str:
    """返回当前语言代码。"""
    return _translator.get_current_locale()


__all__ = [
    "_",
    "tr",
    "gettext",
    "set_language",
    "get_available_languages",
    "get_current_locale",
]
