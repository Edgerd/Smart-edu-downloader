# -*- coding: utf-8 -*-
"""
统一 HTTP 客户端模块
集中管理 requests.Session、Access Token 清洗、请求头、代理与超时配置
消除 Downloader / ResourceLibrary 之间的 HTTP 通信重复
"""

import re
import ssl
import threading
from typing import Optional, Dict, Tuple, Any

import requests
import urllib3
from requests.adapters import HTTPAdapter

from core.infrastructure.logger import log

# 降低 OpenSSL 安全级别以兼容部分教育平台使用的弱证书（如 1024 位 RSA 密钥）。
# 该设置仅放宽密钥长度限制，不关闭证书链校验；如仍失败再由调用方按设置决定是否跳过验证。
try:
    urllib3.util.ssl_.DEFAULT_CIPHERS = 'DEFAULT:@SECLEVEL=1'
except Exception:
    pass


class _SSLAdapter(HTTPAdapter):
    """使用较低 OpenSSL 安全级别的自定义适配器。

    部分教育平台 CDN 仍使用 1024 位 RSA 证书，在 OpenSSL 3.0+ 默认策略下会触发
    ``SSLCertVerificationError: certificate key too weak``。通过显式设置
    ``DEFAULT:@SECLEVEL=1`` 兼容此类证书，同时保留证书链校验。
    """

    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        try:
            context.set_ciphers('DEFAULT:@SECLEVEL=1')
        except ssl.SSLError:
            pass
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)


class HttpClient:
    """统一 HTTP 客户端 - 单例模式

    职责:
    - 统一管理 requests.Session 实例（避免多 Session 资源浪费）
    - 集中 Access Token 的清洗、应用与失效
    - 统一 HTTP 请求头（X-ND-AUTH、User-Agent 等）
    - 统一代理配置应用
    - 提供 get / get_stream 统一入口

    使用方式:
        from core.network.http_client import get_http_client
        client = get_http_client()
        client.set_access_token("xxxx")
        response = client.get("https://basic.smartedu.cn/...")
    """

    _instance: Optional['HttpClient'] = None
    _lock = threading.Lock()

    DEFAULT_CONNECT_TIMEOUT = 30
    DEFAULT_READ_TIMEOUT = 60
    MAX_TOKEN_LENGTH = 512
    TOKEN_TRUNCATE_LENGTH = 64

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._session: Optional[requests.Session] = None
        self._access_token: Optional[str] = None
        self._headers: Dict[str, str] = {
            "X-ND-AUTH": 'MAC id="0",nonce="0",mac="0"',
        }
        self._proxies: Dict[str, str] = {}
        self._timeout: Tuple[int, int] = (self.DEFAULT_CONNECT_TIMEOUT, self.DEFAULT_READ_TIMEOUT)
        self._ssl_verify: bool = True

        self._ensure_session()
        self._initialized = True
        log("INFO", "HTTP 客户端已初始化")

    def _ensure_session(self) -> None:
        """确保 Session 实例存在并挂载自定义 SSL 适配器。"""
        if self._session is None:
            self._session = requests.Session()
            self._session.proxies = {}
            self._session.headers.update(self._headers)
            # 为所有 HTTPS 请求挂载兼容弱证书的适配器，同时保留 HTTP 默认适配器。
            self._session.mount('https://', _SSLAdapter())

    @staticmethod
    def _clean_token(token: Any) -> str:
        """清洗 Access Token

        处理策略:
        1. 去除换行 / 制表符 / 引号 / 反斜杠
        2. 压缩所有空白
        3. 仅保留 ASCII 可打印字符（HTTP header 要求）
        4. 截断超长 token（防止误粘贴 JS 代码）

        Args:
            token: 原始 token

        Returns:
            清洗后的安全 token 字符串
        """
        if not token:
            return ""
        try:
            text = str(token)
            text = re.sub(r'[\r\n\t"\\]', '', text).strip()
            text = re.sub(r'\s+', '', text)
            text = ''.join(c for c in text if 32 <= ord(c) < 127)
            if len(text) > HttpClient.MAX_TOKEN_LENGTH:
                log("WARNING", f"Token 长度异常 ({len(text)} 字符)，可能粘贴了 JS 代码，请重新复制 access_token")
                text = text[:HttpClient.TOKEN_TRUNCATE_LENGTH]
            return text
        except Exception as e:
            log("WARNING", f"Token 清洗失败: {e}")
            return ""

    def _build_auth_header(self, token: str) -> str:
        """根据 token 构造 X-ND-AUTH 请求头值"""
        if not token:
            return 'MAC id="0",nonce="0",mac="0"'
        return f'MAC id="{token}",nonce="0",mac="0"'

    def set_access_token(self, token: Optional[str]) -> None:
        """设置 Access Token（自动清洗 + 应用到所有后续请求）

        Args:
            token: 原始 Access Token，可以为 None 或空字符串
        """
        clean_token = self._clean_token(token)
        self._access_token = clean_token or None
        new_header = self._build_auth_header(clean_token)
        self._headers["X-ND-AUTH"] = new_header
        if self._session is not None:
            self._session.headers["X-ND-AUTH"] = new_header
        if clean_token:
            log("DEBUG", f"Access Token 已设置，清洗后长度: {len(clean_token)}")
        else:
            log("DEBUG", "Access Token 已清除")

    def get_access_token(self) -> Optional[str]:
        """获取当前生效的 Access Token（清洗后）"""
        return self._access_token

    def set_proxy(self, proxy_config: Optional[Dict[str, Any]]) -> None:
        """设置代理配置

        Args:
            proxy_config: 代理配置字典，包含 type / host / port / username / password
                          如果为 None 或 False 或不完整，则禁用代理
        """
        if proxy_config is None or proxy_config is False:
            self._proxies = {}
            self._apply_proxies()
            log("INFO", "代理已禁用")
            return

        proxy_type = proxy_config.get('type', 'http')
        host = proxy_config.get('host', '')
        port = proxy_config.get('port', '')
        username = proxy_config.get('username', '')
        password = proxy_config.get('password', '')

        if not host or not port:
            self._proxies = {}
            self._apply_proxies()
            log("WARNING", "代理配置不完整，已禁用代理")
            return

        auth_str = f'{username}:{password}@' if username and password else ''
        proxy_url = f'{proxy_type}://{auth_str}{host}:{port}'

        self._proxies = {
            'http': proxy_url,
            'https': proxy_url,
        }
        self._apply_proxies()
        log("INFO", f"代理已设置: {proxy_type}://{host}:{port}")

    def _apply_proxies(self) -> None:
        """将代理配置应用到当前 session"""
        if self._session is not None:
            self._session.proxies = self._proxies

    def set_ssl_verify(self, enabled: bool) -> None:
        """设置是否启用 SSL 证书验证。

        默认开启。关闭后将跳过证书验证，仅建议在教育平台 CDN 等
        可控场景下作为降级方案使用。

        Args:
            enabled: True 表示验证证书，False 表示跳过验证。
        """
        self._ssl_verify = bool(enabled)
        if not self._ssl_verify:
            # 关闭验证时屏蔽 urllib3 的证书警告，避免日志被重复刷屏。
            try:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            except Exception:
                pass
        log("INFO", f"SSL 证书验证已{'开启' if self._ssl_verify else '关闭'}")

    def get_ssl_verify(self) -> bool:
        """获取当前 SSL 证书验证开关状态。"""
        return self._ssl_verify

    def set_timeout(self, connect: int, read: int) -> None:
        """设置超时时间

        Args:
            connect: 连接超时（秒）
            read: 读取超时（秒）
        """
        try:
            connect = max(1, int(connect))
            read = max(1, int(read))
            self._timeout = (connect, read)
        except Exception:
            self._timeout = (self.DEFAULT_CONNECT_TIMEOUT, self.DEFAULT_READ_TIMEOUT)

    def get_timeout(self) -> Tuple[int, int]:
        """获取当前超时配置"""
        return self._timeout

    def get_headers(self) -> Dict[str, str]:
        """获取当前请求头（拷贝）"""
        return self._headers.copy()

    def get_session(self) -> requests.Session:
        """获取底层的 requests.Session（请勿直接修改）"""
        self._ensure_session()
        return self._session

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        """统一 GET 请求入口

        Args:
            url: 请求 URL
            **kwargs: 透传给 requests.Session.get 的参数
                      timeout 默认使用 self._timeout

        Returns:
            requests.Response 对象
        """
        self._ensure_session()
        kwargs.setdefault("timeout", self._timeout)
        kwargs.setdefault("verify", self._ssl_verify)
        return self._session.get(url, **kwargs)

    def get_stream(self, url: str, **kwargs: Any) -> requests.Response:
        """统一 GET 流式请求入口（用于大文件下载）

        Args:
            url: 请求 URL
            **kwargs: 透传给 requests.Session.get 的参数
                      timeout 默认使用 self._timeout

        Returns:
            requests.Response 对象（stream=True）
        """
        self._ensure_session()
        kwargs.setdefault("timeout", self._timeout)
        kwargs.setdefault("stream", True)
        kwargs.setdefault("verify", self._ssl_verify)
        return self._session.get(url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> requests.Response:
        """统一 POST 请求入口"""
        self._ensure_session()
        kwargs.setdefault("timeout", self._timeout)
        kwargs.setdefault("verify", self._ssl_verify)
        return self._session.post(url, **kwargs)

    def head(self, url: str, **kwargs: Any) -> requests.Response:
        """统一 HEAD 请求入口"""
        self._ensure_session()
        kwargs.setdefault("timeout", self._timeout)
        kwargs.setdefault("verify", self._ssl_verify)
        return self._session.head(url, **kwargs)

    def close(self) -> None:
        """关闭 Session 连接池，释放资源"""
        if self._session is not None:
            try:
                self._session.close()
                log("DEBUG", "HTTP Session 已关闭")
            except Exception as e:
                log("WARNING", f"关闭 HTTP Session 失败: {e}")


_http_client: Optional[HttpClient] = None


def get_http_client() -> HttpClient:
    """获取全局 HTTP 客户端实例"""
    global _http_client
    if _http_client is None:
        _http_client = HttpClient()
    return _http_client
