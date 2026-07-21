"""
资源解析器模块

负责解析资源URL，提取资源下载链接、标题、封面URL和章节信息。
将解析逻辑与网络请求分离，便于独立测试解析逻辑。
"""
import re
from typing import Optional, List, Dict, Tuple
from core.infrastructure.logger import log
from core.resource.resource_fetcher import ResourceFetcher

class ResourceParser:
    """资源解析器

    负责解析资源URL，提取以下信息：
    - 资源下载链接（resource_url）
    - 资源标题（title）
    - 章节信息（chapters）
    - 封面URL（cover_url）

    依赖URLFixer进行URL修复和参数提取，依赖ResourceFetcher进行网络请求。
    """

    def __init__(self, url_fixer, resource_fetcher: ResourceFetcher):
        self.url_fixer = url_fixer
        self.resource_fetcher = resource_fetcher

    def parse(self, url: str, bookmarks: bool) -> Tuple[Optional[str], Optional[str], List[Dict], Optional[str]]:
        """解析资源，获取资源下载链接

        Args:
            url: 资源URL
            bookmarks: 是否获取书签信息

        Returns:
            (resource_url, title, chapters, cover_url)
        """
        log('STEP', f'开始解析URL: {url[:80]}...')
        url = self.url_fixer.fix_url(url)
        log('DEBUG', f'修复后URL: {url[:80]}...')
        try:
            content_id = None
            content_type = None
            resource_url = None
            chapters = []
            content_id = self.url_fixer.extract_content_id(url)
            if not content_id:
                query_start = url.find('?')
                if query_start != -1:
                    query_string = url[query_start + 1:]
                    for q in query_string.split('&'):
                        if not q or '=' not in q:
                            continue
                        if q.split('=')[0] == 'contentId':
                            content_id = q.split('=')[1]
                            break
            if not content_id:
                log('ERROR', '未找到 contentId 参数')
                return (None, None, None, None)
            log('DEBUG', f'提取到 contentId: {content_id}')
            content_type = self.url_fixer.extract_content_type(url)
            if not content_type:
                query_start = url.find('?')
                if query_start != -1:
                    query_string = url[query_start + 1:]
                    for q in query_string.split('&'):
                        if not q or '=' not in q:
                            continue
                        if q.split('=')[0] == 'contentType':
                            content_type = q.split('=')[1]
                            break
            if not content_type:
                content_type = 'assets_document'
            log('DEBUG', f'内容类型: {content_type}')
            data = self.resource_fetcher.fetch_resource_data(content_id, content_type, url)
            if not data:
                return (None, None, None, None)
            title = data.get('title')
            log('SUCCESS', f'获取到资源标题: {title}')
            cover_url = self._extract_cover_url(data, content_id)
            log('STEP', '解析资源下载链接...')
            ti_items = data.get('ti_items') or []
            resource_url = self._extract_resource_url(ti_items)
            if not resource_url:
                log('WARNING', '未找到直接下载链接，尝试获取专题课程资源列表...')
                if content_type == 'thematic_course':
                    resources_data = self.resource_fetcher.fetch_thematic_course_resources(content_id)
                    if resources_data is None:
                        return (None, None, None, None)
                    for resource in resources_data:
                        if resource['resource_type_code'] == 'assets_document':
                            resource_url = self._extract_resource_url(resource.get('ti_items') or [])
                            if resource_url:
                                break
                    if not resource_url:
                        log('ERROR', '专题课程资源列表中未找到下载链接')
                        return (None, None, None, None)
                else:
                    log('ERROR', '未找到资源下载链接')
                    return (None, None, None, None)
            log('SUCCESS', f'获取到下载链接: {resource_url[:80]}...')
            log('DEBUG', f"封面 URL: {(cover_url[:80] if cover_url else 'None')}")
            if bookmarks:
                chapters = self._extract_chapters(data)
            log('SUCCESS', f'解析完成: {title}')
            return (resource_url, title, chapters, cover_url)
        except Exception as e:
            log('ERROR', f'解析URL失败: {e}')
            return (None, None, None, None)

    def parse_url(self, url: str, get_bookmarks: bool=True) -> Tuple[Optional[str], Optional[str], List[Dict], Optional[str]]:
        """兼容方法

        Returns:
            (resource_url, title, chapters, cover_url)
        """
        return self.parse(url, get_bookmarks)

    def _extract_resource_url(self, ti_items: list) -> Optional[str]:
        """从 ti_items 列表中提取资源下载链接

        根据是否有 access_token 选择不同的CDN域名：
        - 有token：使用 r1-ndr-private.ykt.cbern.com.cn
        - 无token：使用 c1.ykt.cbern.com.cn

        Args:
            ti_items: ti_items 列表

        Returns:
            资源下载链接，未找到时返回 None
        """
        access_token = self.resource_fetcher.access_token
        for item in ti_items:
            if item.get('ti_is_source_file'):
                resource_url = item.get('ti_storage')
                if resource_url:
                    resource_url = resource_url.replace('cs_path:${ref-path}', 'https://r1-ndr-private.ykt.cbern.com.cn' if access_token else 'https://c1.ykt.cbern.com.cn')
                    log('DEBUG', '从 ti_storage 获取链接')
                else:
                    resource_url = next((u for u in item.get('ti_storages', []) if u), None)
                    if not resource_url:
                        continue
                    if not access_token:
                        resource_url = re.sub('^https?://(?:.+).ykt.cbern.com.cn/(.+)$', 'https://c1.ykt.cbern.com.cn/\\1', resource_url)
                    log('DEBUG', '从 ti_storages 获取链接')
                return resource_url
        return None

    def _extract_cover_url(self, data: dict, content_id: str) -> Optional[str]:
        """从 API 返回的数据中提取封面 URL（Slide1）

        Args:
            data: API 返回的 JSON 数据
            content_id: 教材 contentId

        Returns:
            封面图片 URL，提取失败时返回 None
        """
        try:
            custom_props = data.get('custom_properties') or {}
            preview = custom_props.get('preview') or {}
            slide1 = preview.get('Slide1')
            if slide1:
                log('DEBUG', '从 preview.Slide1 提取封面 URL')
                return slide1
            ti_items = data.get('ti_items') or []
            for item in ti_items:
                if item.get('ti_file_flag') == 'cover':
                    storage = item.get('ti_storage') or next((u for u in item.get('ti_storages', []) if u), None)
                    if storage:
                        log('DEBUG', '从 ti_items 提取封面 URL')
                        return storage
        except Exception as e:
            log('WARNING', f'提取封面 URL 失败: {e}')
        return None

    def _extract_chapters(self, data: dict) -> List[Dict]:
        """提取书签/章节信息

        从资源数据中提取章节信息，包括：
        1. 从 ti_items 中找到 ebook_mapping 文件
        2. 获取映射数据，建立页码映射
        3. 获取目录树，构建章节结构
        4. 如果目录树获取失败，使用页码映射作为备选

        Args:
            data: 资源详情JSON数据

        Returns:
            章节列表，失败时返回空列表
        """
        chapters = []
        log('STEP', '开始获取书签信息...')
        try:
            mapping_url = None
            ti_items = data.get('ti_items') or []
            for item in ti_items:
                if item.get('ti_file_flag') == 'ebook_mapping':
                    mapping_url = item.get('ti_storage')
                    if mapping_url:
                        mapping_url = mapping_url.replace('cs_path:${ref-path}', 'https://r1-ndr-private.ykt.cbern.com.cn')
                    else:
                        mapping_url = next((u for u in item.get('ti_storages', []) if u), None)
                    break
            if mapping_url:
                map_data = self.resource_fetcher.fetch_mapping_data(mapping_url)
                if map_data is None:
                    return chapters
                ebook_id = map_data.get('ebook_id')
                log('DEBUG', f'ebook_id: {ebook_id}')
                page_map = []
                if map_data.get('mappings'):
                    for m in map_data['mappings']:
                        page_map.append({'node_id': m['node_id'], 'page_number': m.get('page_number', 1)})
                log('DEBUG', f'页码映射数量: {len(page_map)}')
                if ebook_id:
                    tree_data = self.resource_fetcher.fetch_tree_data(ebook_id)
                    if tree_data is not None:

                        def process_tree_nodes(nodes):
                            result = []
                            for node in nodes:
                                page_num = next((m['page_number'] for m in page_map if m['node_id'] == node['id']), None)
                                chapter_item = {'title': node['title'], 'page_index': page_num}
                                if node.get('child_nodes'):
                                    chapter_item['children'] = process_tree_nodes(node['child_nodes'])
                                result.append(chapter_item)
                            return result
                        if isinstance(tree_data, list):
                            chapters = process_tree_nodes(tree_data)
                        elif isinstance(tree_data, dict) and tree_data.get('child_nodes'):
                            chapters = process_tree_nodes(tree_data['child_nodes'])
                if not chapters:
                    log('WARNING', '目录树获取失败，使用页码映射作为备选')
                    page_map.sort(key=lambda x: x['page_number'])
                    for i, m in enumerate(page_map):
                        chapters.append({'title': f"第 {i + 1} 节 (P{m['page_number']})", 'page_index': m['page_number']})
                log('SUCCESS', f'获取到 {len(chapters)} 个章节')
        except Exception as e:
            log('WARNING', f'获取书签失败: {e}')
            chapters = []
        return chapters