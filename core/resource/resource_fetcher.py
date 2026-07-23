"""
资源获取器模块

负责从网络获取资源数据，包括资源详情、课本列表、书签信息等。
将网络请求逻辑从资源解析中分离，便于独立测试和替换网络层。
"""
import re
from typing import Optional, Dict, List, Tuple
from core.infrastructure.logger import log
from core.network.http_client import get_http_client
_MAX_HIERARCHY_DEPTH = 50

class ResourceFetcher:
    """资源获取器

    封装所有与智慧教育平台API的网络请求，包括：
    - 获取资源详情数据
    - 获取课本列表
    - 获取书签/章节信息
    - 获取专题课程资源列表
    """

    def __init__(self, http_client=None):
        self._http = http_client or get_http_client()
        self.access_token = self._http.get_access_token()

    def update_access_token(self):
        """更新访问令牌（在令牌变更后调用）"""
        self.access_token = self._http.get_access_token()

    def fetch_resource_data(self, content_id: str, content_type: str, url: str='') -> Optional[dict]:
        """获取资源详情数据

        优先请求资源详情 JSON API；若返回 403/404 等错误，则回退到
        课本列表 API 中查找对应 content_id 的资源数据。

        Args:
            content_id: 内容ID
            content_type: 内容类型
            url: 原始URL（用于判断特殊类型，如基础性作业）

        Returns:
            资源详情JSON数据，失败时返回 None
        """
        if re.search('^https?://([^/]+)/syncClassroom/basicWork/detail', url):
            api_url = f'https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/special_edu/resources/details/{content_id}.json'
            log('DEBUG', '检测为基础性作业')
        elif content_type == 'thematic_course':
            api_url = f'https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/special_edu/resources/details/{content_id}.json'
            log('DEBUG', '检测为专题课程')
        else:
            api_url = f'https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/resources/tch_material/details/{content_id}.json'
            log('DEBUG', '检测为普通电子课本')
        log('STEP', f'请求API: {api_url}')
        with self._http.get(api_url) as response:
            log('DEBUG', f'API响应状态码: {response.status_code}')
            if response.status_code == 200:
                return response.json()
            log('WARNING', f'详情API请求失败，状态码: {response.status_code}，尝试从资源列表获取')
        # 详情 API 失败时回退到资源列表查找
        return self.fetch_resource_data_from_list(content_id)

    def fetch_resource_data_from_list(self, content_id: str) -> Optional[dict]:
        """从课本列表 API 中查找指定 content_id 的资源数据。

        Args:
            content_id: 内容ID

        Returns:
            资源详情JSON数据，失败时返回 None
        """
        log('STEP', f'从资源列表查找: {content_id}')
        try:
            with self._http.get('https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/resources/tch_material/version/data_version.json') as version_resp:
                version_resp.raise_for_status()
                list_urls = version_resp.json().get('urls', '').split(',')
            for list_url in list_urls:
                if not list_url:
                    continue
                try:
                    with self._http.get(list_url) as book_resp:
                        book_resp.raise_for_status()
                        books = book_resp.json()
                    for book in books:
                        if book.get('id') == content_id:
                            log('SUCCESS', '从资源列表找到资源数据')
                            return book
                except Exception as e:
                    log('WARNING', f'获取资源列表失败 ({list_url}): {e}')
                    continue
        except Exception as e:
            log('WARNING', f'从资源列表查找资源失败: {e}')
        return None

    def fetch_thematic_course_resources(self, content_id: str) -> Optional[List[dict]]:
        """获取专题课程资源列表

        Args:
            content_id: 专题课程内容ID

        Returns:
            资源列表，失败时返回 None
        """
        log('DEBUG', '获取专题课程资源列表...')
        with self._http.get(f'https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/special_edu/thematic_course/{content_id}/resources/list.json') as resources_resp:
            if resources_resp.status_code != 200:
                log('ERROR', f'获取专题课程资源列表失败，状态码: {resources_resp.status_code}')
                return None
            return resources_resp.json()

    def fetch_mapping_data(self, mapping_url: str) -> Optional[dict]:
        """获取书签映射数据

        Args:
            mapping_url: 映射文件URL

        Returns:
            映射数据JSON，失败时返回 None
        """
        log('DEBUG', f'获取mapping文件: {mapping_url}')
        with self._http.get(mapping_url) as map_resp:
            if map_resp.status_code != 200:
                log('WARNING', f'获取mapping文件失败，状态码: {map_resp.status_code}')
                return None
            return map_resp.json()

    def fetch_tree_data(self, ebook_id: str) -> Optional[dict]:
        """获取目录树数据

        Args:
            ebook_id: 电子书ID

        Returns:
            目录树JSON数据，失败时返回 None
        """
        log('STEP', '获取目录树...')
        with self._http.get(f'https://s-file-1.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/trees/{ebook_id}.json') as tree_resp:
            if tree_resp.status_code != 200:
                log('WARNING', f'获取目录树失败，状态码: {tree_resp.status_code}')
                return None
            return tree_resp.json()

    def fetch_book_list(self) -> dict:
        """获取课本列表

        从智慧教育平台获取完整的课本列表，包括标签层级和书籍数据。

        Returns:
            解析后的层级资源字典
        """
        with self._http.get('https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/tags/tch_material_tag.json') as tags_resp:
            tags_data = tags_resp.json()
        parsed_hier = self.parse_hierarchy(tags_data['hierarchies'])
        with self._http.get('https://s-file-1.ykt.cbern.com.cn/zxx/ndrs/resources/tch_material/version/data_version.json') as list_resp:
            list_data = list_resp.json()['urls'].split(',')
        for url in list_data:
            try:
                with self._http.get(url) as book_resp:
                    book_data = book_resp.json()
                for book in book_data:
                    if book.get('tag_paths'):
                        path_parts = book['tag_paths'][0].split('/')
                        if len(path_parts) < 2:
                            continue
                        tag_paths = path_parts[2:]
                        if not tag_paths:
                            continue
                        try:
                            temp_hier = parsed_hier[path_parts[1]]
                        except KeyError:
                            continue
                        if tag_paths[0] not in temp_hier.get('children', {}):
                            continue
                        for p in tag_paths:
                            if temp_hier.get('children') and temp_hier['children'].get(p):
                                temp_hier = temp_hier['children'].get(p)
                        if not temp_hier.get('children'):
                            temp_hier['children'] = {}
                        book['display_name'] = book.get('title') or book.get('name') or f"(未知电子课本 {book['id']})"
                        book['resource_type_code'] = book.get('resource_type_code') or 'assets_document'
                        temp_hier['children'][book['id']] = book
            except Exception as e:
                log('ERROR', f'获取书籍数据失败: {e}')
                continue
        return parsed_hier

    def parse_hierarchy(self, hierarchy, _depth=0) -> dict:
        """解析层级数据

        Args:
            hierarchy: 层级数据
            _depth: 当前递归深度（内部使用，防止栈溢出）

        Returns:
            解析后的层级字典
        """
        if not hierarchy:
            return {}
        if _depth >= _MAX_HIERARCHY_DEPTH:
            log('WARNING', f'parse_hierarchy 递归深度超过限制 ({_MAX_HIERARCHY_DEPTH})，已截断')
            return {}
        parsed = {}
        for h in hierarchy:
            for ch in h['children']:
                parsed[ch['tag_id']] = {'display_name': ch['tag_name'], 'children': self.parse_hierarchy(ch.get('hierarchies', []), _depth + 1)}
        return parsed