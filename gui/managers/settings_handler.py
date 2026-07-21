# -*- coding: utf-8 -*-
"""设置处理器 - 设置应用回调、主题色、状态栏、DPI缩放"""

import weakref
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from core.config.theme_config import (
    background_color,
    get_theme_config,
    opacity,
    primary_color,
    title_bar_gradient,
)
from core.i18n import _
from core.infrastructure.logger import log
from core.config.settings_manager import get_settings_manager
from gui.styles import load_theme_color


class SettingsHandler:
    """设置处理器"""

    # 主题更新去抖动延迟（毫秒），避免拖动滑块时频繁刷新
    _THEME_DEBOUNCE_MS = 80

    def __init__(self, main_window):
        """初始化"""
        self.main_window = main_window
        # 主题更新去抖动：缓存待应用的配置，通过定时器合并
        self._pending_theme_config = None
        self._theme_debounce_timer = QTimer()
        self._theme_debounce_timer.setSingleShot(True)
        self._theme_debounce_timer.timeout.connect(self._flush_pending_theme)
        # 缓存需要主题更新的控件弱引用列表（避免每次遍历 allWidgets）
        self._theme_aware_widgets = []
        # 缓存 VerticalTabWidget 弱引用列表
        self._vertical_tabs = []
        # 缓存是否已初始化
        self._widget_cache_initialized = False
        # 缓存上次应用的主题签名，避免相同主题重复刷新
        self._last_theme_signature = None
        self._connect_settings_signals()
    
    def _connect_settings_signals(self):
        """连接设置变更信号"""
        settings_mgr = get_settings_manager()
        settings_mgr.setting_changed.connect(self._on_setting_changed)
    
    def _schedule_theme_update(self, settings):
        """调度主题更新（去抖动）。

        在 _THEME_DEBOUNCE_MS 毫秒内的多次调用只会被执行一次，
        最后一次调用配置覆盖之前的。
        """
        self._pending_theme_config = settings
        self._theme_debounce_timer.start(self._THEME_DEBOUNCE_MS)

    def _flush_pending_theme(self):
        """执行待处理的主题更新。"""
        config = self._pending_theme_config
        if config is not None:
            self._pending_theme_config = None
            self._do_apply_theme_colors(config)

    def _on_setting_changed(self, key, value):
        """设置变更回调"""
        if key == 'theme_color':
            # 使用去抖动：将主题更新延迟合批处理
            self._schedule_theme_update({'theme_color': value})
        elif key == 'show_status_bar':
            self.toggle_status_bar(value)
        elif key == 'window_shadow':
            self.toggle_window_shadow(value)
        elif key == 'minimize_to_tray':
            self._update_tray_visibility(value)
        elif key == 'interface_scale':
            if value != 100:
                self.apply_dpi_scale(value)
        elif key == 'animations_enabled':
            self._apply_animation_setting(value)
        elif key == 'cache_cleanup_period':
            # 缓存清理周期变更时立即按新策略清理过期封面
            self._trigger_cover_cache_cleanup()
        elif key == 'language':
            # 语言设置只需保存，重启后生效，不立即重载界面
            pass

    def _trigger_cover_cache_cleanup(self):
        """触发封面缓存清理（在后台线程执行，避免阻塞 UI）。"""
        def _cleanup():
            try:
                from core import get_cover_cache
                count = get_cover_cache().clear_expired_covers()
                if count > 0:
                    log("INFO", f"缓存清理周期变更，已清理 {count} 个过期封面")
            except Exception as e:
                log("WARNING", f"缓存清理周期变更后清理封面失败: {e}")
        from core.infrastructure.thread_pool import submit_task
        submit_task(_cleanup)
    
    def _update_tray_visibility(self, minimize_to_tray):
        """更新托盘可见性"""
        if self.main_window.tray_manager:
            if minimize_to_tray:
                self.main_window.tray_manager.show_tray()
            else:
                self.main_window.tray_manager.hide_tray()
    
    def _apply_animation_setting(self, enabled):
        """应用动画设置"""
        if hasattr(self.main_window, 'animation_manager'):
            self.main_window.animation_manager.set_enabled(enabled)
    
    def on_settings_saved(self):
        """设置保存后应用新设置"""
        try:
            from core.config.settings_manager import get_settings_manager
            settings = get_settings_manager().get_all()
            
            self.apply_theme_colors(settings)
            
            self.toggle_status_bar(settings.get('show_status_bar', True))
            
            self.toggle_window_shadow(settings.get('window_shadow', True))
            
            interface_scale = settings.get('interface_scale', 100)
            if interface_scale != 100:
                self.apply_dpi_scale(interface_scale)
            
            self.update_tray_settings(settings)
            
            log("INFO", "设置已成功应用")
            
        except Exception as e:
            log("ERROR", f"应用设置失败: {e}")
    
    def _build_widget_cache(self):
        """构建主题感知控件缓存。

        扫描一次所有控件，缓存实现了 update_theme_colors 的控件
        和 VerticalTabWidget 实例的弱引用。
        """
        from gui.widgets.vertical_tab_widget import VerticalTabWidget

        theme_aware = []
        vertical_tabs = []

        app = QApplication.instance()
        if app is None:
            return

        for widget in app.allWidgets():
            # 缓存主题感知控件
            if hasattr(widget, 'update_theme_colors'):
                ref = weakref.ref(widget, lambda r: self._invalidate_widget_cache())
                theme_aware.append(ref)
            # 缓存 VerticalTabWidget
            if isinstance(widget, VerticalTabWidget):
                ref = weakref.ref(widget, lambda r: self._invalidate_widget_cache())
                vertical_tabs.append(ref)

        self._theme_aware_widgets = theme_aware
        self._vertical_tabs = vertical_tabs
        self._widget_cache_initialized = True
        log("DEBUG", f"主题控件缓存已构建: {len(theme_aware)} 个主题感知控件, "
                     f"{len(vertical_tabs)} 个 VerticalTabWidget")

    def _invalidate_widget_cache(self):
        """标记控件缓存失效（当缓存的控件被销毁时触发）。"""
        self._widget_cache_initialized = False
        # 缓存失效后下次应用应重新刷新控件
        self._last_theme_signature = None

    def _get_live_widgets(self, ref_list):
        """从弱引用列表中获取仍然存活的控件。"""
        live = []
        for ref in ref_list:
            widget = ref()
            if widget is not None:
                live.append(widget)
        return live

    def _ensure_widget_cache(self):
        """确保主题感知控件缓存已构建。"""
        if not self._widget_cache_initialized:
            self._build_widget_cache()

    @staticmethod
    def _compute_theme_signature(config: dict) -> str:
        """计算主题配置签名，用于快速比较两次配置是否相同。

        Args:
            config: 主题配置字典。

        Returns:
            str: 主题签名字符串。
        """
        gradient = config.get("gradient")
        gradient_str = ""
        if isinstance(gradient, dict):
            gradient_str = f"{gradient.get('start', '')}|{gradient.get('end', '')}"
        return (
            f"{config.get('primary', '')}|"
            f"{config.get('background', '')}|"
            f"{config.get('opacity', 255)}|"
            f"{config.get('use_gradient', False)}|"
            f"{gradient_str}"
        )

    def _compute_bar_background(self, config: dict) -> str:
        """根据主题配置计算标题栏/导航栏背景。

        渐变色开关开启时返回渐变背景（优先使用预设渐变，否则使用主色加深渐变）；
        关闭时返回纯色主色背景。

        Args:
            config: 主题配置字典。

        Returns:
            str: CSS background 值（rgba 或 qlineargradient）。
        """
        primary = primary_color(config)
        alpha = opacity(config)
        gradient = title_bar_gradient(config)

        if config.get("use_gradient"):
            if gradient:
                start = gradient.get("start", primary)
                end = gradient.get("end", primary)
                start_rgba = self._hex_to_rgba(start, alpha)
                end_rgba = self._hex_to_rgba(end, alpha)
                return (
                    f"qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                    f"stop:0 {start_rgba}, stop:1 {end_rgba})"
                )
            darker = self.adjust_color(primary, -20)
            primary_rgba = self._hex_to_rgba(primary, alpha)
            darker_rgba = self._hex_to_rgba(darker, alpha)
            return (
                f"qlineargradient(x1:0, y1:0, x2:1, y2:0, "
                f"stop:0 {darker_rgba}, stop:1 {primary_rgba})"
            )
        return self._hex_to_rgba(primary, alpha)

    def _apply_bar_background(self, bar_bg: str) -> None:
        """将计算好的背景统一应用到标题栏与导航栏组件。"""
        title_bar = self.main_window.title_bar
        nav_bar = self.main_window.nav_bar

        if hasattr(title_bar, 'set_bar_background'):
            title_bar.set_bar_background(bar_bg)
        else:
            title_bar.setStyleSheet(
                f"QWidget#titleBar {{"
                f"background: {bar_bg};"
                f"border-top-left-radius: 12px;"
                f"border-top-right-radius: 12px;"
                f"}}"
            )

        if nav_bar is not title_bar:
            if hasattr(nav_bar, 'set_bar_background'):
                nav_bar.set_bar_background(bar_bg)
            else:
                nav_bar.setStyleSheet(
                    f"QWidget#navBar {{"
                    f"background: {bar_bg};"
                    f"}}"
                )

    def _do_apply_theme_colors(self, settings):
        """实际执行主题色应用（优化版）。"""
        self._ensure_widget_cache()

        config = get_theme_config(settings)
        if not isinstance(config, dict):
            config = get_theme_config(None)

        # 计算主题签名，与上次应用相同时直接跳过，避免重复重绘
        signature = self._compute_theme_signature(config)
        if signature == self._last_theme_signature:
            return

        primary = primary_color(config)
        bg = background_color(config)
        bar_bg = self._compute_bar_background(config)

        # 批量更新期间禁用主窗口重绘，减少闪烁与提升性能
        self.main_window.setUpdatesEnabled(False)
        try:
            # 同步更新 qfluentwidgets 全局主题色，确保 ComboBox、Switch 等
            # Fluent 风格控件随主题变化。
            try:
                import sys
                import io
                _old_stdout = sys.stdout
                sys.stdout = io.StringIO()
                from qfluentwidgets import setThemeColor
                sys.stdout = _old_stdout
                setThemeColor(primary)
            except Exception as e:
                log("DEBUG", f"同步 Fluent 主题色失败: {e}")

            # 1. 批量设置标题栏和导航栏背景
            self._apply_bar_background(bar_bg)

            # 2. 触发主窗口全局样式重载（传入已计算的 config 避免重复读文件）
            if hasattr(self.main_window, '_apply_styles'):
                self.main_window._cached_theme_color = config
                self.main_window._apply_styles()

            # 4. 使用缓存更新 VerticalTabWidget 背景色
            self._apply_cached_vertical_tabs(bg)

            # 5. 更新调试面板背景色
            self._apply_background_to_debug_panel(bg)

            # 6. 更新导航按钮高亮色
            self.main_window.navigation_manager.update_button_styles(
                self.main_window.navigation_manager.get_current_index()
            )

            # 7. 使用缓存通知主题感知控件
            self._notify_cached_theme_color_changed(primary, bg)

            self._last_theme_signature = signature
            log("INFO", f"主题色已更新: {primary} / {bg}")
        except Exception as e:
            log("WARNING", f"应用主题色失败: {e}")
        finally:
            self.main_window.setUpdatesEnabled(True)

    def _apply_cached_vertical_tabs(self, bg: str):
        """使用缓存更新 VerticalTabWidget 背景色。"""
        if not self._widget_cache_initialized:
            self._build_widget_cache()

        try:
            for widget in self._get_live_widgets(self._vertical_tabs):
                widget.setBackgroundColor(bg)
        except Exception as e:
            log("WARNING", f"同步 VerticalTabWidget 背景色失败: {e}")

    def _notify_cached_theme_color_changed(self, primary: str, bg: str):
        """使用缓存通知主题感知控件。"""
        if not self._widget_cache_initialized:
            self._build_widget_cache()

        try:
            for widget in self._get_live_widgets(self._theme_aware_widgets):
                try:
                    widget.update_theme_colors(primary, bg)
                except Exception as e:
                    log("WARNING",
                        f"通知控件 {type(widget).__name__} 主题色更新失败: {e}")
        except Exception as e:
            log("WARNING", f"通知主题色更新失败: {e}")

    def apply_theme_colors(self, settings):
        """应用主题色（公共接口，保持向后兼容）。

        首次调用时构建控件缓存，后续调用使用缓存。
        通过主题签名比较避免相同主题重复刷新。
        """
        self._do_apply_theme_colors(settings)

    def _apply_background_to_debug_panel(self, bg: str):
        """将背景色同步到调试面板。"""
        try:
            from gui.debug_panel import DebugPanel
            panel = DebugPanel._instance
            if panel is not None:
                panel._background_color = bg
                panel.setStyleSheet(panel._get_panel_style())
                panel.nav_bar.setBackgroundColor(bg)
        except Exception as e:
            log("WARNING", f"同步调试面板背景色失败: {e}")

    def _notify_theme_color_changed(self, primary: str, bg: str):
        """通知所有实现主题色刷新接口的页面/控件。

        Args:
            primary: 新的主题主色。
            bg: 新的内容区背景色。
        """
        try:
            app = QApplication.instance()
            if app is None:
                return
            for widget in app.allWidgets():
                if hasattr(widget, 'update_theme_colors'):
                    try:
                        widget.update_theme_colors(primary, bg)
                    except Exception as e:
                        log("WARNING", f"通知控件 {type(widget).__name__} 主题色更新失败: {e}")
        except Exception as e:
            log("WARNING", f"通知主题色更新失败: {e}")

    @staticmethod
    def _hex_to_rgba(hex_color: str, alpha: int = 255) -> str:
        """将 #RRGGBB 转换为 rgba(R,G,B,A)。"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"rgba({r}, {g}, {b}, {alpha})"
        except Exception:
            return hex_color
    
    def toggle_status_bar(self, visible):
        """显示/隐藏状态栏"""
        if hasattr(self.main_window, 'status_bar'):
            if visible:
                self.main_window.status_bar.show()
            else:
                self.main_window.status_bar.hide()
            if hasattr(self.main_window, '_update_corner_styles'):
                self.main_window._update_corner_styles()
            log("INFO", f"状态栏已{'显示' if visible else '隐藏'}")
    
    def init_status_bar_visibility(self):
        """初始化状态栏可见性"""
        try:
            from core.config.settings_manager import get_settings_manager
            settings = get_settings_manager().get_all()
            self.toggle_status_bar(settings.get('show_status_bar', True))
        except Exception as e:
            log("ERROR", f"初始化状态栏可见性失败: {e}")
    
    def init_window_shadow(self):
        """初始化窗口阴影"""
        try:
            from core.config.settings_manager import get_settings_manager
            settings = get_settings_manager().get_all()
            self.toggle_window_shadow(settings.get('window_shadow', True))
        except Exception as e:
            log("ERROR", f"初始化窗口阴影失败: {e}")
    
    def init_tray_visibility(self):
        """初始化托盘可见性"""
        try:
            from core.config.settings_manager import get_settings_manager
            settings = get_settings_manager().get_all()
            
            minimize_to_tray = settings.get('minimize_to_tray', True)
            tray_notifications = settings.get('tray_notifications', True)
            tray_show_progress = settings.get('tray_show_progress', True)
            
            self.main_window._tray_notifications = tray_notifications
            self.main_window._tray_show_progress = tray_show_progress
            self.main_window._tray_enabled = minimize_to_tray
            
            if self.main_window.tray_manager:
                if minimize_to_tray:
                    self.main_window.tray_manager.show_tray()
                else:
                    self.main_window.tray_manager.hide_tray()
                
            log("INFO", f"托盘设置已初始化: 最小化到托盘={minimize_to_tray}, 通知={tray_notifications}, 进度={tray_show_progress}")
            
        except Exception as e:
            log("ERROR", f"初始化托盘可见性失败: {e}")
    
    def toggle_window_shadow(self, enabled):
        """显示/隐藏窗口阴影"""
        if hasattr(self.main_window, 'set_window_shadow'):
            self.main_window.set_window_shadow(enabled)
            log("INFO", f"窗口阴影已{'启用' if enabled else '禁用'}")
    
    def update_tray_settings(self, settings):
        """更新系统托盘行为"""
        minimize_to_tray = settings.get('minimize_to_tray', True)
        tray_notifications = settings.get('tray_notifications', True)
        tray_show_progress = settings.get('tray_show_progress', True)
        
        # 更新标志
        self.main_window._tray_notifications = tray_notifications
        self.main_window._tray_enabled = minimize_to_tray
        
        if not self.main_window.tray_manager:
            return
        
        if minimize_to_tray:
            self.main_window.tray_manager.show_tray()
        else:
            self.main_window.tray_manager.hide_tray()
        
        log("INFO", f"托盘设置已更新: 最小化到托盘={minimize_to_tray}, 通知={tray_notifications}, 进度={tray_show_progress}")
    
    def apply_interface_scale_from_settings(self):
        """从设置应用界面缩放"""
        try:
            from core.config.settings_manager import get_settings_manager
            settings = get_settings_manager().get_all()
            interface_scale = settings.get('interface_scale', 100)
            if interface_scale != 100:
                self.apply_dpi_scale(interface_scale)
        except Exception as e:
            log("ERROR", f"应用界面缩放失败: {e}")
    
    def apply_dpi_scale(self, scale_percent):
        """应用DPI缩放"""
        try:
            scale_factor = scale_percent / 100.0
            
            # 设置字体大小
            app_font = QApplication.font()
            new_point_size = int(app_font.pointSize() * scale_factor)
            if new_point_size > 0:
                app_font.setPointSize(new_point_size)
                QApplication.setFont(app_font)
            
            self.main_window.setProperty("windowScale", scale_factor)
            
            base_width = 1000
            base_height = 650
            new_width = max(800, int(base_width * scale_factor))
            new_height = max(550, int(base_height * scale_factor))
            self.main_window.resize(new_width, new_height)
            self.main_window.setMinimumSize(int(800 * scale_factor), int(550 * scale_factor))
            
            log("INFO", f"DPI缩放已应用: {scale_percent}% (字体: {new_point_size}pt)")
            
        except Exception as e:
            log("ERROR", f"应用DPI缩放失败: {e}")
    
    @staticmethod
    def adjust_color(color, delta):
        """调整颜色亮度"""
        try:
            r = int(color[1:3], 16)
            g = int(color[3:5], 16)
            b = int(color[5:7], 16)
            
            r = max(0, min(255, r + delta))
            g = max(0, min(255, g + delta))
            b = max(0, min(255, b + delta))
            
            return f"#{r:02X}{g:02X}{b:02X}"
        except Exception:
            return color
