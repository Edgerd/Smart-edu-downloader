"""
资源库模块

提供资源库的门面接口，保持向后兼容性。
内部职责已拆分到独立的组件模块：
- cache_manager.py: 缓存管理（ResourceCacheManager, FileCacheStrategy）
- resource_fetcher.py: 网络请求（ResourceFetcher）
- resource_parser.py: 资源解析（ResourceParser）
- resource_processor.py: 数据处理（ResourceProcessor）
- search_service.py: 搜索服务（SearchService）
"""
import re
import threading
from typing import Optional, List, Dict, Tuple
from urllib.parse import urlparse, parse_qs, urlunparse
from core.infrastructure.logger import log
from core.infrastructure.path_resolver import get_cache_dir, get_resource_list_file, get_cache_meta_file
from core.network.http_client import get_http_client
from core.resource.search_engine import SearchEngine
from core.resource.cache_manager import ResourceCacheManager, FileCacheStrategy, CACHE_DIR, CACHE_FILE, CACHE_META_FILE, CACHE_EXPIRE_DAYS
from core.resource.resource_fetcher import ResourceFetcher
from core.resource.resource_parser import ResourceParser
from core.resource.resource_processor import ResourceProcessor
from core.resource.search_service import SearchService
DEFAULT_TIMEOUT = (30, 60)

class URLFixer:
    SUPPORTED_DOMAINS = ['basic.smartedu.cn', 'www.smartedu.cn', 'smartedu.cn', 's-file-1.ykt.cbern.com.cn', 'r1-ndr-private.ykt.cbern.com.cn', 'c1.ykt.cbern.com.cn']
    URL_PATTERNS = {'contentId': ['contentId=([a-f0-9\\-]{36})', 'contentId=([a-zA-Z0-9\\-]+)', '/([a-f0-9\\-]{36})', 'id=([a-f0-9\\-]{36})', 'resourceId=([a-f0-9\\-]{36})'], 'contentType': ['contentType=([a-zA-Z_]+)', 'type=([a-zA-Z_]+)']}

    @classmethod
    def fix_url(cls, url: str) -> str:
        """修复URL - 主入口"""
        if not url:
            return url
        original_url = url
        url = cls._basic_clean(url)
        url = cls._fix_protocol(url)
        url = cls._fix_domain(url)
        url = cls._fix_path(url)
        url = cls._fix_params(url)
        url = cls._handle_special_formats(url)
        if url != original_url:
            log('DEBUG', f'URL已修复: {original_url[:50]}... -> {url[:50]}...')
        return url

    @classmethod
    def _basic_clean(cls, url: str) -> str:
        """基础清理"""
        url = url.strip()
        url = re.sub('(?<!:)//+', '/', url)
        url = url.replace(' ', '')
        url = url.replace('\n', '').replace('\r', '').replace('\t', '')
        return url

    @classmethod
    def _fix_protocol(cls, url: str) -> str:
        """修复协议"""
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        if url.startswith('http://'):
            url = 'https://' + url[7:]
        return url

    @classmethod
    def _fix_domain(cls, url: str) -> str:
        """修复域名"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if domain.startswith('www.'):
                domain = domain[4:]
            domain_mapping = {'smart-edu.cn': 'smartedu.cn', 'edu.cn': 'basic.smartedu.cn'}
            for old, new in domain_mapping.items():
                if domain.endswith(old) and (not domain.endswith(new)):
                    domain = domain.replace(old, new)
                    break
            if not any((d in domain for d in cls.SUPPORTED_DOMAINS)):
                if 'ykt.cbern' in domain:
                    pass
                else:
                    log('WARNING', f'未知域名: {domain}，尝试继续处理')
            parsed = parsed._replace(netloc=domain)
            url = urlunparse(parsed)
        except Exception as e:
            log('WARNING', f'域名修复失败: {e}')
        return url

    @classmethod
    def _fix_path(cls, url: str) -> str:
        """修复路径"""
        try:
            parsed = urlparse(url)
            path = parsed.path
            if path and (not path.startswith('/')):
                path = '/' + path
            path = path.replace('//', '/')
            parsed = parsed._replace(path=path)
            url = urlunparse(parsed)
        except Exception as e:
            log('WARNING', f'路径修复失败: {e}')
        return url

    @classmethod
    def _fix_params(cls, url: str) -> str:
        """修复URL参数"""
        try:
            parsed = urlparse(url)
            query = parsed.query
            if not query:
                return url
            params = parse_qs(query)
            param_mapping = {'contentid': 'contentId', 'content_id': 'contentId', 'contenttype': 'contentType', 'content_type': 'contentType', 'catalogtype': 'catalogType', 'catalog_type': 'catalogType', 'subcatalog': 'subCatalog'}
            new_params = {}
            for key, value in params.items():
                fixed_key = param_mapping.get(key.lower(), key)
                if fixed_key in new_params:
                    if isinstance(new_params[fixed_key], list):
                        new_params[fixed_key].extend(value)
                    else:
                        new_params[fixed_key] = [new_params[fixed_key]] + value
                else:
                    new_params[fixed_key] = value
            query_parts = []
            for key, value in new_params.items():
                if isinstance(value, list):
                    for v in value:
                        query_parts.append(f'{key}={v}')
                else:
                    query_parts.append(f'{key}={value}')
            new_query = '&'.join(query_parts)
            parsed = parsed._replace(query=new_query)
            url = urlunparse(parsed)
        except Exception as e:
            log('WARNING', f'参数修复失败: {e}')
        return url

    @classmethod
    def _handle_special_formats(cls, url: str) -> str:
        """处理特殊URL格式"""
        if 's-file-1.ykt.cbern.com.cn' in url and '/edu_product/' in url:
            return url
        if 'contentId' not in url and 'tchMaterial/detail' in url:
            match = re.search('/([a-f0-9\\-]{36})(?:[/?]|$)', url)
            if match:
                content_id = match.group(1)
                if '?' in url:
                    url = url.split('?')[0] + f'?contentId={content_id}&' + url.split('?')[1]
                else:
                    url += f'?contentId={content_id}'
                log('DEBUG', f'从路径提取contentId: {content_id}')
        if '/zxx/ndrv2/resources/tch_material/details/' in url:
            match = re.search('/details/([a-f0-9\\-]{36})', url)
            if match:
                content_id = match.group(1)
                url = f'https://basic.smartedu.cn/tchMaterial/detail?contentId={content_id}&catalogType=tchMaterial&subCatalog=tchMaterial'
                log('DEBUG', f'API链接转换为页面URL: {url}')
        if 'thematic_course' in url or 'contentType=thematic_course' in url:
            if 'contentType' not in url:
                if '?' in url:
                    url += '&contentType=thematic_course'
                else:
                    url += '?contentType=thematic_course'
        if 'syncClassroom/basicWork' in url:
            if 'contentType' not in url:
                if '?' in url:
                    url += '&contentType=basic_work'
                else:
                    url += '?contentType=basic_work'
        if 'tchMaterial/detail' in url:
            if 'catalogType' not in url:
                url += '&catalogType=tchMaterial' if '?' in url else '?catalogType=tchMaterial'
            if 'subCatalog' not in url:
                url += '&subCatalog=tchMaterial'
        return url

    @classmethod
    def extract_content_id(cls, url: str) -> Optional[str]:
        """从URL中提取contentId"""
        for pattern in cls.URL_PATTERNS['contentId']:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    @classmethod
    def extract_content_type(cls, url: str) -> str:
        """从URL中提取contentType"""
        for pattern in cls.URL_PATTERNS['contentType']:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1)
        if 'thematic_course' in url:
            return 'thematic_course'
        if 'syncClassroom/basicWork' in url:
            return 'basic_work'
        return 'assets_document'

    @classmethod
    def is_valid_smartedu_url(cls, url: str) -> bool:
        """检查是否是有效的智慧教育平台URL"""
        if not url:
            return False
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            if not any((d in domain for d in cls.SUPPORTED_DOMAINS)):
                return False
            return True
        except Exception:
            return False

class ResourceLibrary:
    """资源库门面类 - 单例模式

    保持原有接口兼容性，内部职责已委托给独立的组件模块：
    - ResourceCacheManager: 缓存管理
    - ResourceFetcher: 网络请求
    - ResourceParser: 资源解析
    - ResourceProcessor: 数据处理
    - SearchService: 搜索服务
    """
    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._http = get_http_client()
        self._cache_manager = ResourceCacheManager(FileCacheStrategy(CACHE_FILE, CACHE_META_FILE, CACHE_DIR), CACHE_EXPIRE_DAYS)
        self._resource_fetcher = ResourceFetcher(self._http)
        self._resource_parser = ResourceParser(URLFixer, self._resource_fetcher)
        self._resource_processor = ResourceProcessor()
        self._search_service = SearchService(SearchEngine(), self._resource_processor)
        self.access_token = self._http.get_access_token()
        self.headers = self._http.get_headers()
        self.session = self._http.get_session()
        self._resource_list = None

    def parse(self, url: str, bookmarks: bool) -> Tuple[Optional[str], Optional[str], List[Dict], Optional[str]]:
        """解析资源，获取资源下载链接

        Returns:
            (resource_url, title, chapters, cover_url)
        """
        return self._resource_parser.parse(url, bookmarks)

    def parse_url(self, url: str, get_bookmarks: bool=True) -> Tuple[Optional[str], Optional[str], List[Dict], Optional[str]]:
        """兼容方法

        Returns:
            (resource_url, title, chapters, cover_url)
        """
        return self.parse(url, get_bookmarks)

    def fetch_book_list(self) -> dict:
        """获取课本列表"""
        return self._resource_fetcher.fetch_book_list()

    def fetch_resource_list(self, force_refresh: bool=False) -> dict:
        """获取资源列表 - 支持缓存机制（7天自动更新 + 手动刷新）

        Args:
            force_refresh: 是否强制刷新（跳过缓存），默认False

        Returns:
            资源列表字典
        """
        cached_data = self._cache_manager.get_resource_list(force_refresh)
        if cached_data:
            self._resource_list = cached_data
            self._resource_processor.set_resource_list(self._resource_list)
            return self._resource_list
        log('STEP', '开始获取资源列表（缓存过期或强制刷新）')
        self._resource_list = self.fetch_book_list()
        self._resource_processor.set_resource_list(self._resource_list)
        self._cache_manager.save_resource_list(self._resource_list)
        log('SUCCESS', '资源列表获取完成并已缓存')
        return self._resource_list

    def parse_hierarchy(self, hierarchy, _depth=0) -> dict:
        """解析层级数据"""
        return self._resource_fetcher.parse_hierarchy(hierarchy, _depth)

    def get_resource_url(self, content_id: str, resource_type: str='assets_document') -> str:
        """根据资源ID构建资源URL"""
        return self._resource_processor.get_resource_url(content_id, resource_type)

    def clear_cache(self):
        """清除所有缓存（内存+文件）"""
        self._resource_list = None
        self._resource_processor.clear_cache()
        self._cache_manager.clear_cache()

    def get_cache_info(self) -> dict:
        """获取缓存信息"""
        return self._cache_manager.get_cache_info()

    def set_access_token(self, token: str):
        """设置 Access Token - 委托给统一 HTTP 客户端"""
        self._http.set_access_token(token)
        self.access_token = self._http.get_access_token()
        self.headers = self._http.get_headers()
        self._resource_fetcher.update_access_token()

    def search_resources(self, keyword: str):
        """搜索资源 - 委托给搜索服务

        Args:
            keyword: 搜索关键词

        Returns:
            搜索结果列表（兼容旧接口）
        """
        if not self._resource_list:
            self._resource_list = self.fetch_resource_list()
        return self._search_service.search(keyword, with_stats=False)

    def search_resources_with_stats(self, keyword: str):
        """搜索资源并返回统计信息

        Args:
            keyword: 搜索关键词

        Returns:
            (搜索结果列表, 统计信息字典)
        """
        if not self._resource_list:
            self._resource_list = self.fetch_resource_list()
        return self._search_service.search(keyword, with_stats=True)

    def get_search_suggestions(self, partial_keyword: str, limit: int=10) -> list:
        """获取搜索建议

        Args:
            partial_keyword: 部分关键词
            limit: 返回数量限制

        Returns:
            搜索建议列表
        """
        if not self._resource_list:
            self._resource_list = self.fetch_resource_list()
        return self._search_service.get_suggestions(partial_keyword, limit)

    def get_hot_keywords(self, limit: int=10) -> list:
        """获取热门关键词

        Args:
            limit: 返回数量限制

        Returns:
            热门关键词列表
        """
        return self._search_service.get_hot_keywords(limit)

    def get_search_history(self, limit: int=20) -> list:
        """获取搜索历史

        Args:
            limit: 返回数量限制

        Returns:
            搜索历史列表
        """
        return self._search_service.get_search_history(limit)

    def clear_search_history(self):
        """清空搜索历史"""
        self._search_service.clear_search_history()

    def remove_search_history(self, keyword: str):
        """删除指定搜索历史

        Args:
            keyword: 要删除的关键词
        """
        self._search_service.remove_search_history(keyword)

    def get_search_engine(self):
        """获取搜索引擎实例"""
        return self._search_service.search_engine