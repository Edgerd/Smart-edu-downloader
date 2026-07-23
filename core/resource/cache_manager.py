# -*- coding: utf-8 -*-
"""
资源缓存管理模块

提供缓存策略接口和资源缓存管理器，负责资源列表的缓存加载、保存、过期检查等。
通过策略模式支持不同的缓存后端（文件缓存、内存缓存等）。
"""

import os
import json
import datetime
from abc import ABC, abstractmethod
from typing import Optional, Any

from core.infrastructure.logger import log
from core.infrastructure.path_resolver import (
    get_cache_dir, get_resource_list_file, get_cache_meta_file
)


# 缓存配置（系统临时目录/cache 下）
CACHE_DIR = get_cache_dir()
CACHE_FILE = get_resource_list_file()
CACHE_META_FILE = get_cache_meta_file()
CACHE_EXPIRE_DAYS = 7  # 缓存有效期为7天


class ICacheStrategy(ABC):
    """缓存策略接口

    定义缓存操作的统一接口，支持不同的缓存后端实现。
    """

    @abstractmethod
    def load(self) -> Optional[Any]:
        """加载缓存数据"""
        pass

    @abstractmethod
    def save(self, data: Any) -> bool:
        """保存缓存数据"""
        pass

    @abstractmethod
    def clear(self) -> bool:
        "清除缓存"
        pass


class FileCacheStrategy(ICacheStrategy):
    """文件缓存策略

    将缓存数据保存到JSON文件，并使用独立的元数据文件记录更新时间。
    保持与原有缓存文件结构的兼容性。
    """

    def __init__(self, cache_file: str, meta_file: str, cache_dir: str):
        self.cache_file = cache_file
        self.meta_file = meta_file
        self.cache_dir = cache_dir
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            log("DEBUG", f"创建缓存目录: {self.cache_dir}")

    def load(self) -> Optional[Any]:
        """从缓存文件加载数据"""
        if not os.path.exists(self.cache_file):
            log("DEBUG", "缓存文件不存在")
            return None

        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            log("DEBUG", f"从缓存加载资源列表，大小: {len(json.dumps(data))} 字节")
            return data
        except Exception as e:
            log("WARNING", f"加载缓存失败: {e}")
            return None

    def save(self, data: Any) -> bool:
        """保存数据到缓存文件"""
        self._ensure_cache_dir()
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._save_cache_meta()
            log("DEBUG", f"资源列表已保存到缓存: {self.cache_file}")
            return True
        except Exception as e:
            log("WARNING", f"保存缓存失败: {e}")
            return False

    def clear(self) -> bool:
        """清除缓存文件和元数据文件"""
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                log("DEBUG", "已删除缓存文件")

            if os.path.exists(self.meta_file):
                os.remove(self.meta_file)
                log("DEBUG", "已删除缓存元数据文件")

            return True
        except Exception as e:
            log("WARNING", f"清除缓存失败: {e}")
            return False

    def _load_cache_meta(self) -> dict:
        """加载缓存元数据"""
        if os.path.exists(self.meta_file):
            try:
                with open(self.meta_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                log("WARNING", f"加载缓存元数据失败: {e}")
        return {'last_update_time': 0}

    def _save_cache_meta(self):
        """保存缓存元数据"""
        self._ensure_cache_dir()
        meta = {'last_update_time': int(datetime.datetime.now().timestamp())}
        try:
            with open(self.meta_file, 'w', encoding='utf-8') as f:
                json.dump(meta, f)
            log("DEBUG", f"保存缓存元数据到: {self.meta_file}")
        except Exception as e:
            log("WARNING", f"保存缓存元数据失败: {e}")

    def is_expired(self, ttl_days: int) -> bool:
        """检查缓存是否过期"""
        meta = self._load_cache_meta()
        if not meta or 'last_update_time' not in meta:
            return True

        last_update = datetime.datetime.fromtimestamp(meta['last_update_time'])
        now = datetime.datetime.now()
        delta = now - last_update

        if delta.days >= ttl_days:
            log("INFO", f"缓存已过期，上次更新时间: {last_update}, 已过 {delta.days} 天")
            return True
        return False

    def get_meta_info(self) -> dict:
        """获取缓存元数据信息"""
        return self._load_cache_meta()


class ResourceCacheManager:
    """资源缓存管理器

    负责资源列表的缓存管理，包括内存缓存和磁盘缓存。
    支持缓存过期检查和强制刷新。
    """

    def __init__(self, cache_strategy: ICacheStrategy, ttl_days: int = CACHE_EXPIRE_DAYS):
        self.cache_strategy = cache_strategy
        self.ttl_days = ttl_days
        self._memory_cache: Optional[dict] = None

    def get_resource_list(self, force_refresh: bool = False) -> Optional[dict]:
        """获取缓存的资源列表

        Args:
            force_refresh: 是否强制刷新（跳过缓存）

        Returns:
            缓存的资源列表，无缓存时返回 None
        """
        # 检查内存缓存
        if not force_refresh and self._memory_cache is not None:
            log("DEBUG", "返回内存中的资源列表")
            # 如果磁盘缓存文件不存在，补存一次
            if not isinstance(self.cache_strategy, FileCacheStrategy) or not os.path.exists(self.cache_strategy.cache_file):
                log("WARNING", "磁盘缓存文件缺失，正在补存...")
                self.save_resource_list(self._memory_cache)
            return self._memory_cache

        # 检查磁盘缓存
        if not force_refresh and not self.cache_strategy.is_expired(self.ttl_days):
            cached_data = self.cache_strategy.load()
            if cached_data:
                log("INFO", "使用缓存的资源列表")
                self._memory_cache = cached_data
                return self._memory_cache

        return None

    def save_resource_list(self, resource_list: dict) -> bool:
        """保存资源列表到缓存

        Args:
            resource_list: 资源列表数据

        Returns:
            是否保存成功
        """
        self._memory_cache = resource_list
        return self.cache_strategy.save(resource_list)

    def clear_cache(self) -> bool:
        """清除所有缓存（内存+磁盘）"""
        self._memory_cache = None
        result = self.cache_strategy.clear()

        # 重置缓存元数据
        if isinstance(self.cache_strategy, FileCacheStrategy):
            self.cache_strategy._save_cache_meta()

        log("SUCCESS", "缓存已清除")
        return result

    def get_cache_info(self) -> dict:
        """获取缓存信息"""
        info = {
            'expired': self.cache_strategy.is_expired(self.ttl_days),
            'cache_exists': os.path.exists(self.cache_strategy.cache_file) if isinstance(self.cache_strategy, FileCacheStrategy) else self._memory_cache is not None,
            'last_update': None,
            'days_since_update': None
        }

        if isinstance(self.cache_strategy, FileCacheStrategy):
            meta = self.cache_strategy.get_meta_info()
            if meta and 'last_update_time' in meta:
                last_update = datetime.datetime.fromtimestamp(meta['last_update_time'])
                info['last_update'] = last_update.strftime('%Y-%m-%d %H:%M:%S')
                info['days_since_update'] = (datetime.datetime.now() - last_update).days

        return info

    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        return self.cache_strategy.is_expired(self.ttl_days)
