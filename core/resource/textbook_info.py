"""
教材信息提取模块
负责从URL中提取教材标题、封面图片等信息
整合自PCLL版本
"""
import requests
import re
from bs4 import BeautifulSoup
from typing import Optional, Dict, Any
from core.infrastructure.exceptions import RequestError
from core.infrastructure.logger import log
from core.network.http_client import get_http_client

# 教材标题清理常量（保持中文，不参与翻译）
TEXTBOOK_PLATFORM_NAME = '国家中小学智慧教育平台'
TEXTBOOK_UNKNOWN_TITLE = '未知教材'
TEXTBOOK_2022_EDITION = '（2022年版）'
TEXTBOOK_REVISED_EDITION = '（修订版）'
TEXTBOOK_CURRICULUM_REVISION = '（根据2022年版课程标准修订）'

class TextbookInfoExtractor:
    """教材信息提取器类"""

    def __init__(self):
        """初始化教材信息提取器"""
        self.config = {'timeout': 15, 'max_retries': 3, 'retry_interval': 2}
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'zh-CN,zh;q=0.9', 'Connection': 'keep-alive', 'Referer': 'https://basic.smartedu.cn/'}

    def get_textbook_info(self, url: str) -> Dict[str, Any]:
        """获取教材信息

        优先通过资源 API 获取标题和封面；若 API 返回不完整且 HTML
        详情页可访问，则回退到 HTML 解析补充缺失字段。

        Args:
            url: 教材URL

        Returns:
            包含教材信息的字典
        """
        try:
            from core.resource.resource_library import URLFixer
            content_id = URLFixer.extract_content_id(url)

            # 优先通过资源 API 获取封面和标题
            cover_url = None
            title = None
            if content_id:
                api_info = self._fetch_api_info(content_id)
                cover_url = api_info.get('cover_url')
                title = api_info.get('title')

            # API 已获取到有效信息时直接返回，避免 HTML 详情页 403 导致异常
            if title and cover_url:
                return {'title': title, 'cover_url': cover_url, 'url': url}

            # API 未返回或返回不完整时回退到 HTML 详情页解析
            try:
                client = get_http_client()
                with client.get(url, headers=self.headers, timeout=self.config['timeout']) as response:
                    response.raise_for_status()
                    html_content = response.text
                if not title:
                    title = self._extract_title(html_content)
                if not cover_url:
                    cover_url = self._extract_cover_url(html_content)
            except requests.exceptions.RequestException as html_err:
                log("DEBUG", f"HTML 详情页获取失败，使用 API 结果: {html_err}")

            return {'title': title or TEXTBOOK_UNKNOWN_TITLE, 'cover_url': cover_url, 'url': url}
        except requests.exceptions.RequestException as e:
            raise RequestError(f"获取教材信息时出错: {str(e)}")

    def _fetch_api_info(self, content_id: str) -> Dict[str, Any]:
        """通过资源 API 获取教材标题和封面。

        优先使用 ResourceFetcher 获取详情数据（内部已处理详情 API 403
        时回退到资源列表的逻辑），然后提取标题与封面。

        Args:
            content_id: 教材 contentId。

        Returns:
            包含 title 和 cover_url 的字典，失败时返回空字典。
        """
        info = {}
        try:
            from core.resource.resource_fetcher import ResourceFetcher
            fetcher = ResourceFetcher()
            data = fetcher.fetch_resource_data(content_id, 'assets_document')
            if not data:
                return info

            # 提取标题
            title = data.get('title') or data.get('name')
            if title:
                info['title'] = self._clean_title(title)

            # 提取封面（Slide1）
            custom_props = data.get('custom_properties') or {}
            preview = custom_props.get('preview') or {}
            slide1 = preview.get('Slide1')
            if slide1:
                info['cover_url'] = slide1
                return info

            for item in data.get('ti_items', []):
                if item.get('ti_file_flag') == 'cover':
                    storage = item.get('ti_storage') or next(
                        (u for u in item.get('ti_storages', []) if u), None
                    )
                    if storage:
                        info['cover_url'] = storage
                        break
        except Exception as e:
            log("DEBUG", f"通过 API 获取教材信息失败: {e}")
        return info

    def _extract_title(self, html_content: str) -> str:
        """从HTML内容中提取教材标题"""
        soup = BeautifulSoup(html_content, 'html.parser')
        h3_tags = soup.find_all('h3', class_=True)
        for h3 in h3_tags:
            title = h3.get_text(strip=True)
            if title and len(title) > 5:
                title = self._clean_title(title)
                return title
        title_match = re.search('<title>(.*?)</title>', html_content, re.IGNORECASE | re.DOTALL)
        if title_match:
            title = title_match.group(1).strip()
            title = title.replace(TEXTBOOK_PLATFORM_NAME, '').strip()
            if title and len(title) > 5:
                title = self._clean_title(title)
                return title
        meta_match = re.search('<meta name="description" content="(.*?)"', html_content, re.IGNORECASE | re.DOTALL)
        if meta_match:
            description = meta_match.group(1).strip()
            if description and len(description) > 5:
                title = self._clean_title(description[:100])
                return title
        possible_titles = []
        for tag_name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            tags = soup.find_all(tag_name)
            for tag in tags:
                text = tag.get_text(strip=True)
                if text and len(text) > 5 and (len(text) < 200):
                    possible_titles.append(text)
        title_divs = soup.find_all('div', class_=re.compile('title|name', re.IGNORECASE))
        for div in title_divs:
            text = div.get_text(strip=True)
            if text and len(text) > 5 and (len(text) < 200):
                possible_titles.append(text)
        if possible_titles:
            possible_titles.sort(key=len, reverse=True)
            title = self._clean_title(possible_titles[0])
            return title
        return TEXTBOOK_UNKNOWN_TITLE

    def _clean_title(self, title: str) -> str:
        """清理标题"""
        title = re.sub('\\s+', ' ', title)
        title = title.replace(TEXTBOOK_CURRICULUM_REVISION, '').strip()
        title = title.replace(TEXTBOOK_2022_EDITION, '').strip()
        title = title.replace(TEXTBOOK_REVISED_EDITION, '').strip()
        max_length = 100
        if len(title) > max_length:
            title = title[:max_length] + '...'
        return title

    def _extract_cover_url(self, html_content: str) -> Optional[str]:
        """从HTML内容中提取封面图片URL"""
        soup = BeautifulSoup(html_content, 'html.parser')
        try:
            divs = soup.find_all('div', recursive=True)
            for div in divs:
                imgs = div.find_all('img', src=True)
                for img in imgs:
                    src = img.get('src')
                    if src and ('http' in src or src.startswith('/')):
                        if any((keyword in src.lower() for keyword in ['cover', 'front', 'book', 'img'])):
                            if src.startswith('/'):
                                src = 'https://basic.smartedu.cn' + src
                            return src
        except Exception:
            pass
        img_tags = soup.find_all('img', src=True)
        for img in img_tags:
            src = img.get('src')
            if src and ('http' in src or src.startswith('/')):
                if len(src) > 20 and ('.jpg' in src or '.png' in src or '.jpeg' in src):
                    if src.startswith('/'):
                        src = 'https://basic.smartedu.cn' + src
                    return src
        img_match = re.search('src=["\\\'](https?:\\/\\/[^"\\\']+\\.(?:jpg|png|jpeg))["\\\']', html_content, re.IGNORECASE)
        if img_match:
            return img_match.group(1)
        return None

    def download_cover(self, cover_url: str, save_path: str) -> bool:
        """下载封面图片

        Args:
            cover_url: 封面图片URL
            save_path: 保存路径

        Returns:
            是否下载成功
        """
        try:
            if not cover_url:
                return False
            client = get_http_client()
            with client.get(cover_url, headers=self.headers, timeout=self.config['timeout']) as response:
                response.raise_for_status()
                content = response.content
            with open(save_path, 'wb') as f:
                f.write(content)
            return True
        except requests.exceptions.RequestException:
            return False

    def extract_cover_from_pdf(self, pdf_path: str, output_path: str) -> bool:
        """从PDF文件中提取第一页作为封面

        Args:
            pdf_path: PDF文件路径
            output_path: 输出图片路径

        Returns:
            是否提取成功
        """
        try:
            try:
                import fitz
            except ImportError:
                return False
            doc = fitz.open(pdf_path)
            try:
                if doc.page_count > 0:
                    page = doc.load_page(0)
                    zoom = 1.0
                    mat = fitz.Matrix(zoom, zoom)
                    pix = page.get_pixmap(matrix=mat)
                    pix.save(output_path)
                    return True
                return False
            finally:
                doc.close()
        except Exception:
            return False