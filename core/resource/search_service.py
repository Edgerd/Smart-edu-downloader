# -*- coding: utf-8 -*-
"""
搜索服务模块

封装搜索引擎的调用，提供统一的搜索接口，包括资源搜索、搜索建议、
热门关键词和搜索历史管理等功能。
"""
from typing import List, Dict, Tuple, Union

from core.infrastructure.logger import log
from core.resource.search_engine import SearchEngine, SEARCH_MODE_APPROXIMATE
from core.resource.resource_processor import ResourceProcessor


class SearchService:
    """搜索服务

    封装搜索引擎的调用逻辑，提供以下功能：
    - 资源搜索（支持统计信息）
    - 搜索建议
    - 热门关键词
    - 搜索历史管理

    依赖ResourceProcessor提供扁平化资源数据，依赖SearchEngine执行实际搜索。
    """

    def __init__(self, search_engine: SearchEngine, resource_processor: ResourceProcessor):
        self.search_engine = search_engine
        self.resource_processor = resource_processor

    def search(self, keyword: str, with_stats: bool = False) -> Union[List[Dict], Tuple[List[Dict], Dict]]:
        """搜索资源

        Args:
            keyword: 搜索关键词
            with_stats: 是否返回统计信息

        Returns:
            with_stats=False: 搜索结果列表
            with_stats=True: (搜索结果列表, 统计信息字典)
        """
        # 获取扁平化的资源列表
        flat_resources = self.resource_processor.get_flat_resources()
        self.search_engine.set_flat_resources(flat_resources)

        # 配置搜索参数
        self._configure_search_engine()

        # 执行搜索
        if with_stats:
            return self.search_engine.search(keyword)
        else:
            results, _unused_stats = self.search_engine.search(keyword)
            return results

    def _configure_search_engine(self):
        """从设置管理器读取搜索配置并应用到搜索引擎"""
        try:
            from core.config.settings_manager import get_settings_manager
            settings_mgr = get_settings_manager()
            self.search_engine.set_search_config(
                mode=settings_mgr.get("search_mode", SEARCH_MODE_APPROXIMATE),
                suggestions_enabled=settings_mgr.get("search_suggestions_enabled", True),
                max_results=settings_mgr.get("search_max_results", 100),
                smart_repair=settings_mgr.get("search_smart_repair", True)
            )
        except Exception as e:
            log("WARNING", f"读取搜索设置失败: {e}")

    def get_suggestions(self, partial_keyword: str, limit: int = 10) -> list:
        """获取搜索建议

        Args:
            partial_keyword: 部分关键词
            limit: 返回数量限制

        Returns:
            搜索建议列表
        """
        flat_resources = self.resource_processor.get_flat_resources()
        self.search_engine.set_flat_resources(flat_resources)

        return self.search_engine.get_suggestions(partial_keyword, limit)

    def get_hot_keywords(self, limit: int = 10) -> list:
        """获取热门关键词

        Args:
            limit: 返回数量限制

        Returns:
            热门关键词列表
        """
        return self.search_engine.suggester.get_hot_keywords(limit)

    def get_search_history(self, limit: int = 20) -> list:
        """获取搜索历史

        Args:
            limit: 返回数量限制

        Returns:
            搜索历史列表
        """
        return self.search_engine.history.get_history(limit)

    def clear_search_history(self):
        """清空搜索历史"""
        self.search_engine.history.clear_history()

    def remove_search_history(self, keyword: str):
        """删除指定搜索历史

        Args:
            keyword: 要删除的关键词
        """
        self.search_engine.history.delete_history(keyword)
