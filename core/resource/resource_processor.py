"""
资源处理器模块

负责资源列表的扁平化处理，将层级资源结构转换为扁平的搜索友好格式。
在递归遍历过程中自动识别教材版本、学科、年级信息。
"""
from core.i18n import _
from typing import List, Dict, Optional
from core.infrastructure.logger import log

class ResourceProcessor:
    """资源处理器

    负责将层级资源列表扁平化为搜索友好的格式。
    在递归遍历过程中自动识别教材版本信息（如"人教版"、"苏教版"等），
    并将其与学科、年级信息分离存储。
    """
    _MAX_FLATTEN_DEPTH = 50
    KNOWN_PUBLISHERS = ['冀教版', '人教版', '北师大版', '苏教版', '湘教版', '鲁教版', '沪科版', '浙教版', '华师大版', '沪教版', '教科版', '粤教版', '中图版', '地图版', '外研版', '译林版', '仁爱版', '科普版', '鲁科版', '川教版', '鄂教版', '粤沪版', '粤科技版', '青岛版', '沪粤版', '大象版', '西师大版', '语文版', '长春版', '河大版', '冀少版', '济南版', '沪科技版', '苏科版', '苏少版', '浙人版', '沪外版', '沪外教版', '湘少版', '湘美版', '湘科版', '湘文艺版', '沪教牛津版', '鲁美版', '鲁文艺版', '鲁外版', '粤教花城版', '粤教育版', '粤音版', '粤美版', '粤外版', '粤教科版', '鄂科版', '鄂美版', '鄂外版', '鄂音版', '鄂文艺版', '鄂教科版', '川科版', '川美版', '川外版', '川音版', '川文艺版', '川教科版', '辽教版', '辽科版', '辽美版', '辽外版', '辽音版', '辽文艺版', '辽教科版', '辽海版', '辽师大版', '闽教版', '闽科版', '闽美版', '闽外版', '闽音版', '闽文艺版', '闽教科版', '赣教版', '赣科版', '赣美版', '赣外版', '赣音版', '赣文艺版', '赣教科版']

    def __init__(self):
        self._flat_resources_cache: Optional[List[Dict]] = None
        self._resource_list: Optional[dict] = None

    def set_resource_list(self, resource_list: dict):
        """设置资源列表并清除扁平化缓存

        Args:
            resource_list: 层级资源列表
        """
        self._resource_list = resource_list
        self._flat_resources_cache = None

    def get_resource_list(self) -> Optional[dict]:
        """获取当前资源列表"""
        return self._resource_list

    def get_flat_resources(self) -> List[Dict]:
        """获取扁平化的资源列表（带缓存）

        Returns:
            扁平化后的资源列表，每个资源字典包含 id, title, subject, grade, publisher, url 字段
        """
        if self._flat_resources_cache is not None:
            return self._flat_resources_cache
        if not self._resource_list:
            return []
        self._flat_resources_cache = self._flatten_resources(self._resource_list)
        return self._flat_resources_cache

    def clear_cache(self):
        """清除扁平化缓存"""
        self._flat_resources_cache = None
        self._resource_list = None

    @staticmethod
    def get_resource_url(content_id: str, resource_type: str='assets_document') -> str:
        """根据资源ID构建资源URL"""
        return f'https://basic.smartedu.cn/tchMaterial/detail?contentType={resource_type}&contentId={content_id}&catalogType=tchMaterial&subCatalog=tchMaterial'

    @staticmethod
    def _extract_cover_url(value: Dict) -> Optional[str]:
        """从原始资源字典中提取封面图片 URL。

        优先读取 custom_properties.preview.Slide1，其次查找 ti_items 中
        ti_file_flag 为 cover 的存储地址。

        Args:
            value: 原始资源字典。

        Returns:
            封面 URL，未找到时返回 None。
        """
        try:
            custom_props = value.get('custom_properties') or {}
            preview = custom_props.get('preview') or {}
            slide1 = preview.get('Slide1')
            if slide1:
                return slide1
        except Exception:
            pass
        try:
            for item in value.get('ti_items', []):
                if item.get('ti_file_flag') == 'cover':
                    storage = item.get('ti_storage') or next(
                        (u for u in item.get('ti_storages', []) if u), None
                    )
                    if storage:
                        return storage
        except Exception:
            pass
        return None

    def _flatten_resources(self, resource_dict, subject=None, grade=None, publisher='', _depth=0) -> List[Dict]:
        """递归扁平化资源列表（带深度限制防止栈溢出）

        在递归遍历过程中自动识别教材版本信息（如"人教版"、"苏教版"等），
        并将其与学科、年级信息分离存储。同时提取教材封面 URL 供搜索预览使用。

        Args:
            resource_dict: 待扁平化的资源字典
            subject: 当前层级已识别的学科信息
            grade: 当前层级已识别的年级信息
            publisher: 当前层级已识别的教材版本信息
            _depth: 当前递归深度（内部使用，防止栈溢出）

        Returns:
            扁平化后的资源列表，每个资源字典包含 id, title, subject, grade, publisher, url, cover_url 字段
        """
        if _depth >= self._MAX_FLATTEN_DEPTH:
            log('WARNING', f'扁平化资源列表达到最大深度限制 ({self._MAX_FLATTEN_DEPTH})，停止递归')
            return []
        results = []
        for key, value in resource_dict.items():
            has_title = 'title' in value or 'name' in value
            has_id = 'id' in value
            if has_title and has_id:
                title = value.get('title') or value.get('name', '')
                result = {
                    'id': value.get('id'),
                    'title': title,
                    'subject': subject or '',
                    'grade': grade or '',
                    'publisher': publisher,
                    'url': self.get_resource_url(value.get('id'), value.get('resource_type_code', 'assets_document')),
                    'cover_url': self._extract_cover_url(value),
                }
                results.append(result)
            elif 'children' in value and value['children']:
                current_subject = subject
                current_grade = grade
                current_publisher = publisher
                display_name = value.get('display_name', '')
                if display_name in self.KNOWN_PUBLISHERS or display_name.endswith('版'):
                    current_publisher = display_name
                elif not current_subject and any((subj in display_name for subj in ['语文', '数学', '英语', '科学', '道德与法治', '音乐', '美术', '体育', '信息科技', '信息技术'])):
                    current_subject = display_name
                elif not current_grade and any((grd in display_name for grd in ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级', '七年级', '八年级', '九年级', '高一', '高二', '高三', '十年级', '十一年级', '十二年级'])):
                    current_grade = display_name
                results.extend(self._flatten_resources(value['children'], current_subject, current_grade, current_publisher, _depth=_depth + 1))
        return results