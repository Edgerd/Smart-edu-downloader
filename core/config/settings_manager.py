# -*- coding: utf-8 -*-
"""
设置管理器模块

提供线程安全的设置读写、变更通知、热缓存优化、监听器回调等功能。
"""
import os
import json
import threading
from typing import Any, Dict, Optional, Callable

from PyQt5.QtCore import QObject, pyqtSignal, QTimer

from core.infrastructure.logger import log
from core.infrastructure.default_settings import get_all_default_settings, get_hot_cache_keys
from core.infrastructure.path_resolver import get_settings_file, migrate_old_settings, TEXTBOOK_DOWNLOAD_DIR_NAME
from core.infrastructure.platform_utils import get_system_downloads_dir
from core.config.theme_config import migrate_old_theme_settings


class SettingsManager(QObject):
    """设置管理器（单例模式，线程安全）"""
    
    # 设置变更信号
    setting_changed = pyqtSignal(str, object)
    
    _instance: Optional['SettingsManager'] = None
    _rw_lock = threading.RLock()
    _singleton_lock = threading.Lock()
    
    # 延迟保存时间（毫秒）
    _SAVE_DELAY_MS = 1000
    
    def __new__(cls):
        # 双重检查锁定实现线程安全单例
        if cls._instance is None:
            with cls._singleton_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        super().__init__()
        # 用单例锁保护初始化，避免多线程并发首访时重复初始化/重复写盘
        with self._singleton_lock:
            if getattr(self, '_initialized', False):
                return
            self._initialized = True
        self._settings: Dict[str, Any] = {}
        self._hot_cache: Dict[str, Any] = {}
        self._listeners: Dict[str, list] = {}
        
        # 延迟保存定时器，合并短时间内的多次写入
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._do_save)
        self._pending_save = False
        
        # 先执行旧数据迁移，再确定设置文件路径
        migrate_old_settings()
        self._settings_file = get_settings_file()
        
        self._load()
        # 初始化热缓存
        for key in get_hot_cache_keys():
            if key in self._settings:
                self._hot_cache[key] = self._settings[key]
        log("INFO", f"设置管理器初始化完成: {self._settings_file}")
    
    def _load(self) -> None:
        """从文件加载设置"""
        defaults = get_all_default_settings()
        try:
            if os.path.exists(self._settings_file):
                with open(self._settings_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                # 合并默认设置（确保新增的设置项存在）
                for key, value in defaults.items():
                    if key not in saved:
                        saved[key] = value
                # 迁移旧版 theme_color/accent_color
                migrate_old_theme_settings(saved)
                self._settings = saved
                self._save()
                log("INFO", f"已加载设置文件 ({len(self._settings)} 项)")
            else:
                self._settings = defaults.copy()
                self._save()
                log("INFO", "设置文件不存在，已创建默认设置")
        except Exception as e:
            log("WARNING", f"加载设置文件失败，使用默认设置: {e}")
            self._settings = defaults.copy()
    
    def _save(self) -> None:
        """保存设置到文件

        先加读锁拷贝快照再写入，避免与 ``set``/``update`` 的并发写入竞争
        （否则 ``json.dump`` 遍历字典时可能被并发修改而抛异常或写出脏数据）。
        """
        with self._rw_lock:
            settings_snapshot = self._settings.copy()
        try:
            os.makedirs(os.path.dirname(self._settings_file), exist_ok=True)
            with open(self._settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings_snapshot, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log("ERROR", f"保存设置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取设置值"""
        with self._rw_lock:
            return self._settings.get(key, default)
    
    def fast_get(self, key: str) -> Any:
        """热缓存快速读取（适用于高频读取路径，无锁）"""
        return self._hot_cache.get(key)
    
    def set(self, key: str, value: Any, auto_save: bool = True) -> None:
        """设置单个值"""
        with self._rw_lock:
            self._settings[key] = value
            # 更新热缓存
            if key in get_hot_cache_keys():
                self._hot_cache[key] = value
        self.setting_changed.emit(key, value)
        self._notify_listeners(key, value)
        if auto_save:
            # 延迟保存，合并多次变更
            self._pending_save = True
            self._save_timer.start(self._SAVE_DELAY_MS)
    
    def update(self, settings: Dict[str, Any], auto_save: bool = True) -> None:
        """批量更新设置"""
        with self._rw_lock:
            for key, value in settings.items():
                self._settings[key] = value
                if key in get_hot_cache_keys():
                    self._hot_cache[key] = value
        for key in settings:
            self.setting_changed.emit(key, settings[key])
            self._notify_listeners(key, settings[key])
        if auto_save:
            self._pending_save = True
            self._save_timer.start(self._SAVE_DELAY_MS)
    
    def _do_save(self):
        """执行实际的保存操作（延迟保存定时器回调）"""
        if self._pending_save:
            self._pending_save = False
            self._save()
    
    def save_now(self):
        """立即保存设置（用于程序退出前等需要确保数据落盘的场景）"""
        if self._save_timer.isActive():
            self._save_timer.stop()
        self._pending_save = False
        self._save()
    
    def get_all(self) -> Dict[str, Any]:
        """获取所有设置"""
        with self._rw_lock:
            return self._settings.copy()
    
    def reset_to_default(self, keys: Optional[list] = None) -> None:
        """重置设置到默认值"""
        defaults = get_all_default_settings()
        with self._rw_lock:
            if keys is None:
                self._settings = defaults.copy()
                for key in get_hot_cache_keys():
                    self._hot_cache[key] = defaults.get(key)
            else:
                for key in keys:
                    if key in defaults:
                        self._settings[key] = defaults[key]
                        if key in get_hot_cache_keys():
                            self._hot_cache[key] = defaults[key]
        self._save()
    
    def add_listener(self, key: str, callback: Callable) -> None:
        """添加设置变更监听器"""
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)
    
    def remove_listener(self, key: str, callback: Callable) -> None:
        """移除设置变更监听器"""
        if key in self._listeners:
            self._listeners[key] = [c for c in self._listeners[key] if c != callback]
    
    def _notify_listeners(self, key: str, value: Any) -> None:
        """通知监听器"""
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(key, value)
                except Exception as e:
                    log("ERROR", f"设置监听器回调失败 ({key}): {e}")


_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """获取设置管理器单例"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def get_setting(key: str, default: Any = None) -> Any:
    """便捷函数：获取设置值"""
    return get_settings_manager().get(key, default)


def set_setting(key: str, value: Any, auto_save: bool = True) -> None:
    """便捷函数：设置值"""
    get_settings_manager().set(key, value, auto_save)


def get_default_download_dir() -> str:
    """获取默认下载目录"""
    downloads = get_system_downloads_dir()
    return os.path.join(downloads, TEXTBOOK_DOWNLOAD_DIR_NAME)
