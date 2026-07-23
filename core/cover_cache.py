# -*- coding: utf-8 -*-
"""封面缓存模块。

提供封面图片的下载、缓存和自动清理功能。
过期天数通过设置项 cache_cleanup_period 动态读取，
与通用缓存清理保持一致的过期策略。
"""

import os
import time
import threading
from typing import Optional

from requests.exceptions import RequestException

from core.i18n import _
from core.infrastructure.logger import log
from core.infrastructure.path_resolver import get_temp_dir


# 缓存目录
COVER_CACHE_DIR = os.path.join(get_temp_dir(), 'covers')
# 默认过期天数（设置不可用时兜底）
DEFAULT_EXPIRE_DAYS = 7
# 周期文本到天数的映射
_PERIOD_TO_DAYS = {
    "每天": 1, "每日": 1, "every_day": 1,
    "每周": 7, "每週": 7, "every_week": 7,
    "每月": 30, "every_month": 30,
}


def _get_expire_days_from_settings() -> Optional[int]:
    """从设置管理器读取封面缓存过期天数。

    读取 cache_cleanup_period 设置项，映射为天数。
    返回 None 表示"从不"清理。

    Returns:
        过期天数，None 表示跳过清理，兜底返回 DEFAULT_EXPIRE_DAYS。
    """
    try:
        from core.config.settings_manager import get_setting
        period = get_setting("cache_cleanup_period", "每周")
        if period in ("从不", "never"):
            return None
        return _PERIOD_TO_DAYS.get(period, DEFAULT_EXPIRE_DAYS)
    except Exception:
        return DEFAULT_EXPIRE_DAYS


class CoverCache:
    """封面缓存管理器（单例模式）。

    负责封面图片的下载、本地缓存和过期清理。
    过期策略与设置中的 cache_cleanup_period 联动。
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self._download_lock = threading.Lock()
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """确保封面缓存目录存在。"""
        try:
            os.makedirs(COVER_CACHE_DIR, exist_ok=True)
        except OSError as e:
            log("WARNING", f"创建封面缓存目录失败: {e}")

    def get_cover_path(self, content_id: str) -> Optional[str]:
        """获取已缓存的封面文件路径。

        自动检查缓存是否过期，过期文件会被删除。

        Args:
            content_id: 内容唯一标识。

        Returns:
            有效缓存文件路径，不存在或已过期时返回 None。
        """
        if not content_id:
            return None

        expire_days = _get_expire_days_from_settings()

        for ext in ('.jpg', '.png', '.webp'):
            filepath = os.path.join(COVER_CACHE_DIR, f"{content_id}{ext}")
            if os.path.exists(filepath):
                if expire_days is None:
                    return filepath
                file_age = time.time() - os.path.getmtime(filepath)
                if file_age < expire_days * 86400:
                    return filepath
                else:
                    try:
                        os.remove(filepath)
                        log("DEBUG", "已删除过期封面")
                    except OSError:
                        pass
        return None

    def download_cover(self, cover_url: str, content_id: str) -> Optional[str]:
        """下载封面并保存到本地缓存。

        Args:
            cover_url: 封面图片 URL。
            content_id: 内容唯一标识。

        Returns:
            本地缓存文件路径，下载失败时返回 None。
        """
        if not cover_url or not content_id:
            return None

        cached_path = self.get_cover_path(content_id)
        if cached_path:
            return cached_path

        with self._download_lock:
            cached_path = self.get_cover_path(content_id)
            if cached_path:
                return cached_path

            try:
                from core.network.http_client import get_http_client

                http_client = get_http_client()

                with http_client.get_stream(cover_url, timeout=30) as response:
                    if response.status_code != 200:
                        log("WARNING", f"下载封面失败: {cover_url[:80]}... 状态码: {response.status_code}")
                        return None

                    content_type = response.headers.get('Content-Type', '')
                    if 'png' in content_type:
                        ext = '.png'
                    elif 'webp' in content_type:
                        ext = '.webp'
                    else:
                        ext = '.jpg'

                    filepath = os.path.join(COVER_CACHE_DIR, f"{content_id}{ext}")

                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)

                log("DEBUG", "封面下载成功")
                return filepath

            except RequestException as e:
                log("WARNING", f"下载封面网络异常: {e}")
                return None
            except OSError as e:
                log("WARNING", f"保存封面缓存失败: {e}")
                return None

    def clear_expired_covers(self, days: Optional[int] = None) -> int:
        """清理过期的封面缓存文件。

        Args:
            days: 过期天数，传入 None 时从设置读取 cache_cleanup_period。
                  设置"从不"时跳过清理返回 0。

        Returns:
            清理的文件数量。
        """
        if days is None:
            days = _get_expire_days_from_settings()
        if days is None:
            log("DEBUG", '封面缓存清理已跳过（设置项为"从不"）')
            return 0

        count = 0
        now = time.time()
        threshold = now - (days * 86400)

        try:
            if not os.path.exists(COVER_CACHE_DIR):
                return 0

            for filename in os.listdir(COVER_CACHE_DIR):
                filepath = os.path.join(COVER_CACHE_DIR, filename)
                if not os.path.isfile(filepath):
                    continue
                if os.path.getmtime(filepath) < threshold:
                    try:
                        os.remove(filepath)
                        count += 1
                    except OSError as e:
                        log("WARNING", f"清理过期封面失败: {filepath} - {e}")
        except OSError as e:
            log("WARNING", f"扫描封面缓存目录失败: {e}")

        if count > 0:
            log("INFO", f"清理了 {count} 个过期封面缓存")
        return count


def get_cover_cache() -> CoverCache:
    """获取封面缓存管理器单例。"""
    return CoverCache()