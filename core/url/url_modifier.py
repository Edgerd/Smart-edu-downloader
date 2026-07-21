"""URL修改器模块"""
from core.i18n import _
import os
import re
import json
import logging
import threading
import requests
from datetime import datetime
from typing import Dict, List
from core.infrastructure.exceptions import URLValidationError, RequestError
from core.infrastructure.version import VERSION
from core.infrastructure.path_resolver import get_url_history_file
from core.network.http_client import get_http_client
logger = logging.getLogger(__name__)
_MAX_HISTORY_RECORDS = 100

class URLModifier:
    """URL修改器类（单例模式）"""
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """初始化URL修改器"""
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.base_url = 'https://basic.smartedu.cn'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36', 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language': 'zh-CN,zh;q=0.9', 'Connection': 'keep-alive', 'Referer': 'https://basic.smartedu.cn/'}
        self.history_file = get_url_history_file()
        self._history_lock = threading.RLock()
        self.history = self._load_history()

    def _load_history(self) -> List[Dict]:
        """加载历史记录（线程安全）"""
        with self._history_lock:
            try:
                if os.path.exists(self.history_file):
                    with open(self.history_file, 'r', encoding='utf-8') as f:
                        return json.load(f)
            except Exception as e:
                logger.error(f"{_('core.url.url_modifier.fstr_002')}{str(e)}")
        return []

    def _save_history(self):
        """保存历史记录（线程安全）"""
        with self._history_lock:
            try:
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(self.history, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logger.error(f"{_('core.url.url_modifier.fstr_001')}{str(e)}")

    def _reload_history(self):
        """从文件重新加载历史记录（用于跨页面同步）"""
        with self._history_lock:
            try:
                if os.path.exists(self.history_file):
                    with open(self.history_file, 'r', encoding='utf-8') as f:
                        self.history = json.load(f)
                else:
                    self.history = []
            except Exception as e:
                logger.error(f"{_('core.url.url_modifier.fstr_005')}{str(e)}")
                self.history = []

    def validate_url(self, url: str) -> bool:
        """验证URL格式和有效性"""
        if not url or not isinstance(url, str):
            raise URLValidationError(_('core.url.empty_url'))
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            raise URLValidationError(_('core.url.invalid_protocol'))
        if 'smartedu.cn' not in url:
            raise URLValidationError(_('core.url.not_smartedu'))
        if len(url) > 2000:
            raise URLValidationError(_('core.url.too_long'))
        return True

    def fix_common_url_errors(self, url: str) -> str:
        """修复常见的URL错误

        Args:
            url: 待修复的URL

        Returns:
            str: 修复后的URL
        """
        if not url:
            return url
        url = url.strip()
        if url.startswith('http:/') and (not url.startswith('https:/')):
            url = url.replace('http:/', 'https:/', 1)
        if '://' not in url:
            url = 'https://' + url
        url = url.replace(' ', '')
        url = re.sub('[/\\\\]+', '/', url)
        return url

    def modify_url(self, url: str) -> str:
        """修改URL参数

        Args:
            url: 原始URL

        Returns:
            str: 修改后的URL
        """
        if 'goTip' in url:
            return url
        if '?' in url:
            if 'resType=' not in url:
                separator = '&' if '?' in url else '?'
                url += separator + 'resType=pdf'
        else:
            url += '?resType=pdf'
        if 'userInfo=' not in url:
            url += '&userInfo=1'
        if 'clientType=' not in url:
            url += '&clientType=1'
        self._add_to_history(url)
        return url

    def _add_to_history(self, url: str):
        """添加URL到历史记录(线程安全, 去重)"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        history_item = {'url': url, 'timestamp': timestamp}
        with self._history_lock:
            self.history = [h for h in self.history if h['url'] != url]
            self.history.insert(0, history_item)
            if len(self.history) > _MAX_HISTORY_RECORDS:
                self.history = self.history[:_MAX_HISTORY_RECORDS]
        self._save_history()

    def get_history(self) -> List[Dict]:
        """获取历史记录"""
        return self.history

    def clear_history(self):
        """清空历史记录"""
        self.history = []
        self._save_history()

    def show_history(self) -> str:
        """显示历史记录"""
        if not self.history:
            return _('core.url.no_history')
        result = [_('core.url.history_label')]
        for i, item in enumerate(self.history[:20], 1):
            result.append(f"{i}. {item['url']} ({item['timestamp']})")
        return '\n'.join(result)

    def get_final_download_url(self, url: str) -> str:
        """获取最终下载链接

        Args:
            url: 修改后的URL

        Returns:
            str: 最终下载链接
        """
        if 'goTip' in url:
            return self._parse_gotip_url(url)
        try:
            client = get_http_client()
            with client.get(url, headers=self.headers, timeout=15, allow_redirects=True) as response:
                response.raise_for_status()
                final_url = response.url
            if 'download' in final_url.lower() or '.pdf' in final_url.lower():
                return final_url
            if 'resType=pdf' not in final_url:
                if '?' in final_url:
                    final_url += '&resType=pdf'
                else:
                    final_url += '?resType=pdf'
            return final_url
        except requests.exceptions.RequestException as e:
            logger.error(f"{_('core.url.url_modifier.fstr_003')}{str(e)}")
            raise RequestError(_('core.url.fetch_failed', error=str(e)))

    def _parse_gotip_url(self, url: str) -> str:
        """解析goTip链接

        Args:
            url: goTip链接

        Returns:
            str: 解析后的下载链接
        """
        try:
            client = get_http_client()
            with client.get(url, headers=self.headers, timeout=15, allow_redirects=True) as response:
                response.raise_for_status()
                return response.url
        except requests.exceptions.RequestException as e:
            logger.error(f"{_('core.url.url_modifier.fstr_004')}{str(e)}")
            raise RequestError(_('core.url.parse_gotip_failed', error=str(e)))