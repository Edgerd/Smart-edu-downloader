# -*- coding: utf-8 -*-
"""
自定义下载域名白名单管理模块

提供：
- 域名规范化（去除协议、路径、转小写）
- 添加 / 移除 / 清空自定义白名单
- 检查 URL 是否被允许下载（合并内置 + 自定义白名单 + 允许任意域名开关）
"""

from typing import List, Optional


def normalize_domain(domain: str) -> str:
    """规范化域名：去除协议、路径与首尾空白，转小写"""
    if not domain:
        return ""
    d = domain.strip().lower()
    for prefix in ("http://", "https://"):
        if d.startswith(prefix):
            d = d[len(prefix):]
            break
    for sep in ("/", "?", "#"):
        if sep in d:
            d = d.split(sep, 1)[0]
            break
    return d.strip()


def is_valid_domain(domain: str) -> bool:
    """校验域名格式是否合法"""
    if not domain:
        return False
    if "." not in domain:
        return False
    if any(c.isspace() for c in domain):
        return False
    return True


def get_effective_allowed_domains() -> List[str]:
    """获取当前生效的下载域名白名单（内置 + 用户自定义）。

    Returns:
        包含所有允许域名的列表（已转小写、去重）。
    """
    from core.config.domain_config import get_builtin_allowed_domains
    domains = get_builtin_allowed_domains()
    try:
        from core.config.settings_manager import get_settings_manager
        custom = get_settings_manager().get("custom_allowed_domains", []) or []
        if isinstance(custom, (list, tuple)):
            for item in custom:
                if isinstance(item, str) and item.strip():
                    domains.append(item.strip().lower())
    except Exception:
        pass
    # 去重并保持顺序
    seen = set()
    result = []
    for d in domains:
        if d and d not in seen:
            seen.add(d)
            result.append(d)
    return result


def is_url_allowed(url: str) -> bool:
    """检查给定 URL 是否在允许下载的域名白名单内。

    Args:
        url: 待检查的完整 URL。

    Returns:
        True 表示允许下载，False 表示被白名单拦截。
    """
    if not url:
        return False
    try:
        # 优先检查"允许任意域名下载"开关
        from core.config.settings_manager import get_settings_manager
        if get_settings_manager().get("allow_any_domain_download", False):
            return True
    except Exception:
        pass

    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
    except Exception:
        return False
    domain = (parsed.netloc or "").lower()
    if not domain:
        return False

    for allowed in get_effective_allowed_domains():
        if domain == allowed or domain.endswith(f".{allowed}"):
            return True
    return False


def add_custom_domain(domain: str) -> Optional[List[str]]:
    """添加一个自定义域名到白名单（已存在则忽略）。

    Args:
        domain: 域名或 URL 字符串，将被规范化。

    Returns:
        添加成功（不论是否重复）后的最新白名单列表；若失败返回 None。
    """
    normalized = normalize_domain(domain)
    if not is_valid_domain(normalized):
        return None
    try:
        from core.config.settings_manager import get_settings_manager
        mgr = get_settings_manager()
        current = mgr.get("custom_allowed_domains", []) or []
        if not isinstance(current, list):
            current = []
        if normalized not in current:
            current.append(normalized)
            mgr.set("custom_allowed_domains", current)
        return current
    except Exception:
        return None


def remove_custom_domain(domain: str) -> Optional[List[str]]:
    """从白名单中移除一个自定义域名。

    Args:
        domain: 域名或 URL 字符串，将被规范化。

    Returns:
        移除成功后的最新白名单列表；若失败返回 None。
    """
    normalized = normalize_domain(domain)
    try:
        from core.config.settings_manager import get_settings_manager
        mgr = get_settings_manager()
        current = mgr.get("custom_allowed_domains", []) or []
        if not isinstance(current, list):
            current = []
        if normalized in current:
            current.remove(normalized)
            mgr.set("custom_allowed_domains", current)
        return current
    except Exception:
        return None


def clear_custom_domains() -> Optional[List[str]]:
    """清空所有自定义域名白名单。

    Returns:
        清空后的白名单列表（即空列表）；若失败返回 None。
    """
    try:
        from core.config.settings_manager import get_settings_manager
        mgr = get_settings_manager()
        mgr.set("custom_allowed_domains", [])
        return []
    except Exception:
        return None


def set_allow_any_domain(enabled: bool) -> bool:
    """设置"允许任意域名下载"开关。

    Args:
        enabled: True 表示开启，False 表示关闭。

    Returns:
        操作是否成功。
    """
    try:
        from core.config.settings_manager import get_settings_manager
        return get_settings_manager().set("allow_any_domain_download", bool(enabled)) is None
    except Exception:
        return False
