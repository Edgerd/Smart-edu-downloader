# -*- coding: utf-8 -*-
"""
域名白名单配置模块
集中管理内置的官方域名白名单配置
"""

from typing import List


# 内置的官方域名白名单（不可修改）
BUILTIN_ALLOWED_DOMAINS: List[str] = [
    'smartedu.cn',
    'ykt.cbern.com.cn',
    'c1.ykt.cbern.com.cn',
    'r1-ndr-private.ykt.cbern.com.cn',
    's-file-1.ykt.cbern.com.cn',
]


def get_builtin_allowed_domains() -> List[str]:
    """获取内置的官方域名白名单（返回副本，防止外部修改）
    
    Returns:
        内置域名白名单列表的副本
    """
    return list(BUILTIN_ALLOWED_DOMAINS)
