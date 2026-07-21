# -*- coding: utf-8 -*-
"""
通用工具模块包

提供日志、图标管理、音效播放、状态栏、下载器、资源库等核心功能。
"""

# 延迟导入，避免 __init__.py 执行时的循环依赖问题
def __getattr__(name):
    """按需导入，避免循环依赖"""
    if name == 'log' or name == 'setup_gui_logging':
        from core.infrastructure.logger import log, setup_gui_logging
        return log if name == 'log' else setup_gui_logging
    elif name == 'IconManager' or name == 'NAV_ICONS':
        from core.ui.icon_manager import IconManager, NAV_ICONS
        return IconManager if name == 'IconManager' else NAV_ICONS
    elif name == 'SoundPlayer':
        from core.download.sound_player import SoundPlayer
        return SoundPlayer
    elif name == 'StatusBarManager' or name == 'get_status_manager':
        from core.ui.status_bar import StatusBarManager, get_status_manager
        return StatusBarManager if name == 'StatusBarManager' else get_status_manager
    elif name == 'Downloader':
        from core.download.downloader import Downloader
        return Downloader
    elif name == 'ResourceLibrary':
        from core.resource.resource_library import ResourceLibrary
        return ResourceLibrary
    elif name == 'HttpClient' or name == 'get_http_client':
        from core.network.http_client import HttpClient, get_http_client
        return HttpClient if name == 'HttpClient' else get_http_client
    elif name == 'SettingsManager' or name == 'get_settings_manager':
        from core.config.settings_manager import SettingsManager, get_settings_manager
        return SettingsManager if name == 'SettingsManager' else get_settings_manager
    elif name == 'get_setting' or name == 'set_setting':
        from core.config.settings_manager import get_setting, set_setting
        return get_setting if name == 'get_setting' else set_setting
    elif name == 'normalize_domain' or name == 'is_valid_domain':
        from core.config.custom_domain_whitelist import normalize_domain, is_valid_domain
        return normalize_domain if name == 'normalize_domain' else is_valid_domain
    elif name == 'get_effective_allowed_domains' or name == 'is_url_allowed':
        from core.config.custom_domain_whitelist import get_effective_allowed_domains, is_url_allowed
        return get_effective_allowed_domains if name == 'get_effective_allowed_domains' else is_url_allowed
    elif name == 'add_custom_domain' or name == 'remove_custom_domain':
        from core.config.custom_domain_whitelist import add_custom_domain, remove_custom_domain
        return add_custom_domain if name == 'add_custom_domain' else remove_custom_domain
    elif name == 'clear_custom_domains' or name == 'set_allow_any_domain':
        from core.config.custom_domain_whitelist import clear_custom_domains, set_allow_any_domain
        return clear_custom_domains if name == 'clear_custom_domains' else set_allow_any_domain
    elif name == 'CoverCache' or name == 'get_cover_cache':
        from core.cover_cache import CoverCache, get_cover_cache
        return CoverCache if name == 'CoverCache' else get_cover_cache
    raise AttributeError(f"module 'core' has no attribute '{name}'")

__all__ = [
    'log',
    'setup_gui_logging',
    'IconManager',
    'NAV_ICONS',
    'SoundPlayer',
    'StatusBarManager',
    'get_status_manager',
    'Downloader',
    'ResourceLibrary',
    'HttpClient',
    'get_http_client',
    'SettingsManager',
    'get_settings_manager',
    'get_setting',
    'set_setting',
    'normalize_domain',
    'is_valid_domain',
    'get_effective_allowed_domains',
    'is_url_allowed',
    'add_custom_domain',
    'remove_custom_domain',
    'clear_custom_domains',
    'set_allow_any_domain',
    'CoverCache',
    'get_cover_cache',
]
