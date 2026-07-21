# -*- coding: utf-8 -*-
"""多语言翻译模块。

提供语言文件扫描、加载、翻译查询以及当前语言切换等功能。
"""

import json
import os
import threading
from typing import Any, Dict, List

from core.infrastructure.path_resolver import get_project_root


class Translator:
    """翻译器，负责加载多语言文件并提供翻译查询。

    以单例模式运行，应用生命周期内只维护一份语言数据。
    """

    _instance = None
    _lock = threading.Lock()

    DEFAULT_LANGUAGE = "zh_CN"

    def __new__(cls):
        """创建或返回单例实例。"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """初始化翻译器，加载所有可用语言文件。"""
        if self._initialized:
            return

        self._translations: Dict[str, Dict[str, Any]] = {}
        self._current_locale = self.DEFAULT_LANGUAGE
        self._load_languages()
        self._initialized = True

    def _get_i18n_dir(self) -> str:
        """获取语言文件根目录。"""
        return os.path.join(get_project_root(), "resources", "i18n")

    def _load_languages(self) -> None:
        """扫描并加载 i18n 目录下所有语言文件。"""
        i18n_dir = self._get_i18n_dir()
        if not os.path.isdir(i18n_dir):
            return

        for filename in os.listdir(i18n_dir):
            if not filename.endswith(".json"):
                continue
            locale = filename[:-5]
            file_path = os.path.join(i18n_dir, filename)
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    self._translations[locale] = data
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                continue

    def set_language(self, locale: str) -> bool:
        """设置当前语言。

        Args:
            locale: 语言代码，如 "zh_CN"。

        Returns:
            bool: 设置成功返回 True；若指定语言未加载则回退到默认语言并返回 False。
        """
        if locale in self._translations:
            self._current_locale = locale
            return True
        self._current_locale = self.DEFAULT_LANGUAGE
        return False

    def get_text(self, key: str) -> str:
        """根据键获取当前语言的翻译文本。

        支持以点号分隔的嵌套键。若键缺失，返回键本身。

        Args:
            key: 翻译键，如 "app.name" 或 "common.ok"。

        Returns:
            str: 翻译后的文本；若找不到对应翻译则返回原键。
        """
        return self.translate(key)

    def translate(self, key: str) -> str:
        """根据键获取当前语言的翻译文本。

        当前语言缺失指定键时，自动回退到默认中文语言包查找。

        Args:
            key: 翻译键。

        Returns:
            str: 翻译后的文本；找不到时返回原键。
        """
        data = self._translations.get(self._current_locale)
        fallback_data = self._translations.get(self.DEFAULT_LANGUAGE, {})
        if data is None:
            data = fallback_data

        parts = key.split(".")

        def _lookup(source: Dict[str, Any]) -> Any:
            value = source
            for part in parts:
                if isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return None
            return value if isinstance(value, str) else None

        value = _lookup(data)
        if value is None and data is not fallback_data:
            value = _lookup(fallback_data)
        return value if value is not None else key

    def get_available_languages(self) -> List[Dict[str, str]]:
        """返回已加载的语言列表。

        Returns:
            List[Dict[str, str]]: 每个元素包含 "code" 和 "name"。
        """
        languages = []
        for code in sorted(self._translations.keys()):
            info = self._translations[code]
            name = info.get("language", {}).get("name", code)
            languages.append({"code": code, "name": name})
        return languages

    def get_current_locale(self) -> str:
        """获取当前语言代码。"""
        return self._current_locale
