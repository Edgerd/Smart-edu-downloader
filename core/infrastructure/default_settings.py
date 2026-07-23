# -*- coding: utf-8 -*-
"""
默认设置配置模块
集中定义应用所有设置项的默认值及其详细说明
"""
from core.i18n import _
from core.resource.search_engine import SEARCH_MODE_APPROXIMATE
from core.infrastructure.logger import LOG_LEVEL_INFO
from core.infrastructure.path_resolver import TEXTBOOK_DOWNLOAD_DIR_NAME
from core.infrastructure.platform_utils import get_system_downloads_dir
from core.download.file_categorizer import CATEGORIZE_BY_SUBJECT
import os
from typing import Any, Callable, Dict


def get_default_download_dir() -> str:
    """
    获取默认下载目录路径

    使用系统默认下载目录，并在其下创建应用专用子目录。
    若该目录不存在，首次下载时会自动创建。

    Returns:
        str: 默认下载目录的绝对路径
    """
    downloads_dir = get_system_downloads_dir()
    return os.path.join(downloads_dir, TEXTBOOK_DOWNLOAD_DIR_NAME)


# ==================== 基础设置 ====================
# 这些设置控制应用的基础行为和启动选项

DEFAULT_SETTINGS: Dict[str, Any] = {
    # 是否显示使用提示（首次启动引导等）
    "show_tips_switch": True,
    # 程序累计启动次数（用于统计或显示特定提示）
    "launch_count": 0,
    # 是否自动恢复上次未完成的下载任务
    "auto_recover_tasks": True,
    
    # ==================== 系统托盘设置 ====================
    # 点击关闭按钮时是否最小化到系统托盘而非退出程序
    "minimize_to_tray": False,
    # 是否允许系统托盘通知（如下载完成等）
    "tray_notifications": False,
    # 系统托盘图标是否显示下载进度
    "tray_show_progress": False,
    
    # ==================== 声音设置 ====================
    # 是否启用声音功能（总开关）
    "sound_enabled": True,
    # 下载完成时是否播放提示音
    "download_complete_sound": True,
    
    # ==================== 显示设置 ====================
    # 是否显示程序启动耗时
    "show_startup_time": False,
    # 是否自动清理临时文件
    "auto_clean_temp": True,
}


# ==================== 下载设置 ====================
# 这些设置控制下载行为、网络配置和文件管理

DEFAULT_SETTINGS.update({
    # 默认下载文件保存目录
    "download_dir": get_default_download_dir(),
    # 首次运行时是否弹出下载目录选择对话框
    "ask_download_dir": True,
    # 下载完成后是否自动打开所在文件夹
    "open_folder_after_download": False,
    # 最大并发下载数量
    "max_concurrent_downloads": 5,
    # 单个下载任务的线程数（多线程分段下载）
    "download_threads": 10,
    # 速度限制（0 表示不限制，单位：KB/s）
    "speed_limit": 0,
    # 下载失败后的重试次数
    "retry_count": 3,
    # 重试间隔时间（单位：秒）
    "retry_interval": 5,
    # 网络连接超时时间（单位：秒）
    "connect_timeout": 30,
    # 数据读取超时时间（单位：秒）
    "read_timeout": 60,
    
    # ==================== 文件命名与分类设置 ====================
    # 文件名冲突时是否自动重命名（添加序号后缀）
    "auto_rename_duplicates": True,
    # 文件命名规则（default / custom 等）
    "file_naming_rule": "default",
    # 是否在文件名中包含章节信息
    "include_chapter_info": False,
    # 是否在文件名中包含时间戳
    "include_timestamp": False,
    # 是否自动按规则对下载文件进行分类
    "auto_categorize": False,
    # 分类规则（by_subject / by_grade / by_version / by_subject_and_grade）
    "categorize_rule": CATEGORIZE_BY_SUBJECT,
    
    # ==================== 断点续传与校验设置 ====================
    # 是否启用断点续传功能
    "resume_download": True,
    # 断点续传阈值（文件差异小于此百分比时尝试续传）
    "resume_threshold": 10,
    # 是否自动删除下载失败的任务
    "auto_delete_failed": False,
    # 下载完成后是否自动进行文件完整性校验
    "auto_verify": False,
    # 校验失败时是否自动重试下载
    "retry_on_verify_fail": False,
})


# ==================== 界面设置 ====================
# 这些设置控制界面的外观和交互行为

DEFAULT_SETTINGS.update({
    # 应用显示语言（语言代码，如 "zh_CN" 表示简体中文）
    "language": "zh_CN",
    # 界面缩放比例（百分比，如 100 表示 100%）
    "interface_scale": 100,
    # 是否启用界面动画效果
    "animations_enabled": True,
    # 动画播放速度（"快" / "中" / "慢"）
    "animation_speed": _("common.medium"),
    # 是否显示详细信息面板
    "show_details": False,
    # 下载列表排序方式（"按时间" / "按名称" / "按大小" 等）
    "list_sort": _("common.by_time"),
    # 下载列表视图模式（"详细列表" / "简洁列表" / "图标" 等）
    "list_view": _("settings.interface.detailed_list"),
    # 是否显示底部状态栏
    "show_status_bar": False,
    # 标题栏样式（"large" 大号分离式 / "compact" 精简合并式）
    "title_bar_style": "large",
    # 标题栏自定义标题文本（空字符串时使用默认标题）
    "custom_title_text": "",
    # 标题栏标题字体样式列表（可包含 "bold" 加粗 / "italic" 倾斜）
    "title_font_styles": [],
    # 主题配置（包含主题色、背景色、不透明度、渐变等）
    "theme_color": {
        "key": "jingdianlan",
        "preset": _("theme.preset.jingdianlan"),
        "primary": "#1277DD",
        "background": "#E8F4FD",
        "opacity": 255,
        "use_gradient": False,
        "gradient": None,
        "custom": None,
    },
    # 窗口是否显示阴影效果
    "window_shadow": True,
    # 滚动条滑块是否跟随主题色（实验性功能）
    "scrollbar_follow_theme": False,
    # 开关按钮样式（"ios" 程序内建 iOS 风格 / "fluent" qfluentwidgets 风格）
    "switch_button_style": "ios",
})


# ==================== 网络与代理设置 ====================
# 这些设置控制代理服务器、SSL 证书和网络连接配置

DEFAULT_SETTINGS.update({
    # 是否启用代理
    "proxy_enabled": False,
    # 代理类型（"http" / "https" / "socks5" 等）
    "proxy_type": "http",
    # 代理服务器主机地址
    "proxy_host": "",
    # 代理服务器端口号
    "proxy_port": "",
    # 代理认证用户名
    "proxy_username": "",
    # 代理认证密码（加密存储）
    "proxy_password": "",
    # 是否启用 SSL 证书验证
    # True 表示校验服务器证书；False 表示跳过验证，用于兼容部分教育平台 CDN 的弱证书。
    "ssl_verify": True,
})


# ==================== 缓存与日志设置 ====================
# 这些设置控制缓存管理和日志记录行为

DEFAULT_SETTINGS.update({
    # 是否启用缓存功能
    "cache_enabled": True,
    # 缓存大小限制（单位：MB）
    "cache_size_limit": 500,
    # 缓存自动清理周期（"每天" / "每周" / "每月"）
    "cache_cleanup_period": _("common.every_week"),
    # 日志文件保留天数
    "log_retention_days": 7,
    # 日志自动清理周期（"每天" / "每周" / "每月"）
    "log_cleanup_period": _("common.every_week"),
    # API 请求超时时间（单位：秒）
    "api_timeout": 30,
    # API 请求失败重试次数
    "api_retry_count": 3,
    # 日志记录级别（DEBUG / INFO / WARNING / ERROR）
    "log_level": LOG_LEVEL_INFO,
    # 是否启用调试模式（输出更详细的日志信息）
    "debug_mode": True,
})


# ==================== 配置管理设置 ====================
# 这些设置控制应用配置文件的导出和管理

DEFAULT_SETTINGS.update({
    # 是否自动导出配置文件（用于备份）
    "auto_export_config": False,
    # 配置自动导出间隔（"每天" / "每周" / "每月"）
    "export_interval": _("common.every_week"),
})


# ==================== 账号与安全设置 ====================
# 这些设置控制用户认证信息和隐私保护功能

DEFAULT_SETTINGS.update({
    # 用户访问令牌（加密存储）
    "access_token": "",
    # 是否自动保存访问令牌
    "auto_save_token": True,
    # 清除历史按钮引用（用于界面控制）
    "clear_history_btn": None,
    # 历史记录保留时间（"7天" / "30天" / "永久" 等）
    "history_retention": _("common.seven_days"),
    # 是否自动清理过期历史记录
    "auto_clear_history": True,
    # 是否启用隐私保护模式（隐藏敏感信息）
    "privacy_protection": False,
    # 是否启用安全下载模式（额外校验和加密）
    "safe_download_mode": False,
})


# ==================== 下载白名单设置 ====================
# 这些设置控制自定义域名白名单和下载确认行为

DEFAULT_SETTINGS.update({
    # 是否允许任意域名下载（关闭后仅允许白名单域名）
    "allow_any_domain_download": True,
    # 非白名单域名下载时是否弹出确认对话框
    "confirm_non_whitelist_download": True,
    # 自定义允许下载的域名列表
    "custom_allowed_domains": [],
})


# ==================== 通知设置 ====================
# 这些设置控制通知的显示位置、时长和样式

DEFAULT_SETTINGS.update({
    # 通知弹出位置（"左上" / "右上" / "左下" / "右下"）
    "notification_position": _("common.bottom_right"),
    # 通知显示持续时间（单位：秒）
    "notification_duration": 19,
    # 是否永不隐藏通知（需要手动关闭）
    "notification_never_hide": True,
    # 通知窗口尺寸（"小" / "中" / "大"）
    "notification_size": _("common.large"),
    # 自定义通知提示音文件路径（空字符串表示使用默认音）
    "notification_custom_sound": "",
})


# ==================== 搜索设置 ====================
# 这些设置控制应用内搜索功能和行为

DEFAULT_SETTINGS.update({
    # 搜索匹配模式（"精确匹配" / "大致匹配" / "模糊匹配"）
    "search_mode": SEARCH_MODE_APPROXIMATE,
    # 是否启用搜索建议（输入时自动提示）
    "search_suggestions_enabled": True,
    # 搜索结果最大返回数量
    "search_max_results": 100,
    # 是否启用智能搜索修复（自动纠正输入错误）
    "search_smart_repair": True,
})


# ==================== 首次运行与剪贴板设置 ====================

DEFAULT_SETTINGS.update({
    # 是否为首次运行（False 表示首次启动，需显示新手引导）
    "first_run": False,
    # 是否启用剪贴板监控
    "clipboard_monitor_enabled": True,
    # 剪贴板检测间隔（毫秒）
    "clipboard_check_interval": 1000,
})


# ==================== 高频缓存键集合 ====================
# 这些设置在热路径中被高频访问，需要特殊缓存优化

HOT_CACHE_KEYS = {
    "max_concurrent_downloads",  # 最大并发下载数
    "download_threads",          # 下载线程数
    "speed_limit",               # 速度限制
    "download_dir",              # 下载目录
    "resume_download",           # 断点续传开关
    "theme_color",               # 主题配置
}


def get_all_default_settings() -> Dict[str, Any]:
    """获取所有默认设置的深拷贝"""
    return DEFAULT_SETTINGS.copy()


def get_hot_cache_keys() -> set:
    """获取高频缓存键集合"""
    return HOT_CACHE_KEYS.copy()
