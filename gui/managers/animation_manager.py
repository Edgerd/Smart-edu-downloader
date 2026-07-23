# -*- coding: utf-8 -*-
"""动画管理器 - 悬停动画、切换动画、动画设置加载"""

from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import QGraphicsOpacityEffect

from core.i18n import _


class AnimationManager:
    """动画管理器"""

    def __init__(self, main_window):
        """初始化"""
        self.main_window = main_window
        self.animations_enabled = True
        self.animation_speed = 20
        self._settings_loaded = False
    
    def set_enabled(self, enabled):
        """设置动画是否启用"""
        self.animations_enabled = enabled
    
    def load_animation_settings(self):
        """加载动画设置（缓存结果，避免重复读取）"""
        if self._settings_loaded:
            return
            
        self.animations_enabled = True
        self.animation_speed = 20
        
        try:
            from gui.pages.setting_page import SettingPage
            settings = SettingPage.load_settings()
            self.animations_enabled = settings.get("animations_enabled", True)
            speed = settings.get("animation_speed", _("common.medium"))
            if speed == _("common.slow"):
                self.animation_speed = 40
            elif speed == _("common.medium"):
                self.animation_speed = 20
            elif speed == _("common.fast"):
                self.animation_speed = 10
            self._settings_loaded = True
        except Exception:
            pass
    
    def reset_settings_cache(self):
        """重置设置缓存"""
        self._settings_loaded = False
    
    def add_hover_effect(self, button):
        """为按钮添加淡入淡出效果"""
        self.load_animation_settings()
        
        if not self.animations_enabled:
            opacity = QGraphicsOpacityEffect(button)
            opacity.setOpacity(1.0)
            button.setGraphicsEffect(opacity)
            return
            
        duration = 150
        if self.animation_speed == 40:
            duration = 300
        elif self.animation_speed == 10:
            duration = 75
            
        opacity = QGraphicsOpacityEffect(button)
        opacity.setOpacity(0.7)
        button.setGraphicsEffect(opacity)

        fade_animation_in = QPropertyAnimation(opacity, b"opacity")
        fade_animation_in.setDuration(duration)
        fade_animation_in.setStartValue(0.7)
        fade_animation_in.setEndValue(1.0)
        fade_animation_in.setEasingCurve(QEasingCurve.InOutQuad)
        button._fade_animation_in = fade_animation_in

        fade_animation_out = QPropertyAnimation(opacity, b"opacity")
        fade_animation_out.setDuration(duration)
        fade_animation_out.setStartValue(1.0)
        fade_animation_out.setEndValue(0.7)
        fade_animation_out.setEasingCurve(QEasingCurve.InOutQuad)
        button._fade_animation_out = fade_animation_out

        button.setMouseTracking(True)

        # 保留按钮原有的 enterEvent/leaveEvent（如 TitleBarButton 的圆形悬停高亮），
        # 否则覆写后会丢失原逻辑，导致标题栏按钮悬停高亮永久失效。
        orig_enter = getattr(button, '_orig_enter_event', button.enterEvent)
        orig_leave = getattr(button, '_orig_leave_event', button.leaveEvent)
        button._orig_enter_event = orig_enter
        button._orig_leave_event = orig_leave

        def enter_event(event):
            orig_enter(event)
            if hasattr(button, '_fade_animation_out') and button._fade_animation_out.state() == QPropertyAnimation.Running:
                button._fade_animation_out.stop()
            if hasattr(button, '_fade_animation_in'):
                button._fade_animation_in.start()

        def leave_event(event):
            orig_leave(event)
            if hasattr(button, '_fade_animation_in') and button._fade_animation_in.state() == QPropertyAnimation.Running:
                button._fade_animation_in.stop()
            if hasattr(button, '_fade_animation_out'):
                button._fade_animation_out.start()

        button.enterEvent = enter_event
        button.leaveEvent = leave_event
    
    def add_nav_hover_effect(self, button, page_index):
        """为导航按钮添加悬停效果"""
        self.load_animation_settings()
        
        if not self.animations_enabled:
            return
            
        button.setMouseTracking(True)

        def enter_event(event):
            if page_index != self.main_window.navigation_manager.get_current_index():
                if not self.main_window.page_manager.is_page_loaded(page_index):
                    self.main_window.page_manager.preload_page(page_index)

        button.enterEvent = enter_event
        button.leaveEvent = lambda event: None
    
    def animate_tab_switch(self, old_index, new_index):
        """执行标签页切换动画"""
        self.load_animation_settings()
        
        self.main_window.navigation_manager.update_button_styles(new_index)
