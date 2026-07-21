# -*- coding: utf-8 -*-
"""苹果风格开关控件"""
import sys
import io

from core.i18n import _
from core.config.theme_config import get_theme_config, primary_color

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt5.QtGui import QPainter, QColor, QBrush, QRadialGradient, QPen, QPainterPath, QCursor

# 静默导入 qfluentwidgets，避免其 Pro 提示输出到控制台
_old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    from qfluentwidgets import SwitchButton as FluentSwitchButton
finally:
    sys.stdout = _old_stdout


def get_switch_button_style() -> str:
    """读取当前全局开关按钮样式设置。

    Returns:
        str: "ios" 或 "fluent"，读取失败时返回 "ios"。
    """
    try:
        from core.config.settings_manager import get_settings_manager
        style = get_settings_manager().get("switch_button_style", "ios")
        if style in ("ios", "fluent"):
            return style
    except Exception:
        pass
    return "ios"


def refresh_all_switch_buttons(style: str = None):
    """全局刷新所有 SwitchWithLabel 开关风格。

    Args:
        style: 目标风格，None 时从设置读取。
    """
    if style is None:
        style = get_switch_button_style()
    if style not in ("ios", "fluent"):
        style = "ios"

    try:
        from PyQt5.QtWidgets import QApplication
        for widget in QApplication.instance().allWidgets():
            if isinstance(widget, SwitchWithLabel):
                widget.setStyle(style)
    except Exception:
        pass


class SwitchButton(QWidget):
    """现代苹果风格开关按钮"""
    
    toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None, checked=False, accent_color=None):
        super().__init__(parent)
        self._checked = checked
        self._hovered = False
        self._pressed = False
        self._circle_x = 22 if checked else 2
        self._target_x = self._circle_x

        self._animation_timer = None
        self._hover_animation_timer = None
        self._click_effect_timer = None

        self._current_hover_progress = 0.0
        self._target_hover_progress = 0.0

        self._click_effect_active = False
        self._click_effect_radius = 0
        self._click_effect_alpha = 0

        self._elastic_animation_active = False
        self._elastic_target_x = 0
        self._elastic_velocity = 0
        self._elastic_damping = 0.85
        self._elastic_timer = None

        self._load_animation_settings()

        self._press_start_pos = QPoint(0, 0)
        self._drag_start_x = self._circle_x  # 记录拖拽开始时的位置
        self._current_drag_distance = 0  # 当前拖拽距离
        self._is_light_click = False  # 标记是否为轻点操作
        self._was_dragging = False  # 标记是否进行过拖拽操作

        # iOS风格尺寸：51x31 (符合iOS人机界面指南)
        self.setFixedSize(51, 31)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

        self._on_color = None
        self._off_color = None
        self._default_on_color = QColor("#34C759")
        self._apply_accent_color(accent_color)
        
    def paintEvent(self, a0):
        """绘制开关 - 现代iOS风格"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        try:
            # 绘制背景轨道 - 使用iOS标准圆角 (高度的一半)
            track_radius = self.height() // 2
            path = QPainterPath()
            path.addRoundedRect(0, 0, self.width(), self.height(), track_radius, track_radius)

            # 计算悬停插值进度
            hover_factor = self._current_hover_progress if self._hovered else (1.0 - self._current_hover_progress)
            hover_factor = max(0.0, min(1.0, hover_factor))

            if self._checked:
                custom = self._on_color
                defaults = (QColor("#34C759"), QColor("#2AC14E"), QColor("#4CD964"))
            else:
                custom = self._off_color
                defaults = (QColor("#AAAAAA"), QColor("#999999"), QColor("#BBBBBB"))

            if custom:
                base_color = custom
                pressed_color = self._adjust_brightness(base_color, -20)
                hover_color = self._adjust_brightness(base_color, 20)
            else:
                base_color, pressed_color, hover_color = defaults

            if self._pressed:
                bg_color = pressed_color
            else:
                r = int(base_color.red() + (hover_color.red() - base_color.red()) * hover_factor)
                g = int(base_color.green() + (hover_color.green() - base_color.green()) * hover_factor)
                b = int(base_color.blue() + (hover_color.blue() - base_color.blue()) * hover_factor)
                bg_color = QColor(r, g, b)

            painter.fillPath(path, bg_color)

            # 添加微妙的内阴影效果，增强立体感
            if not self._checked:
                # 关闭状态添加轻微内阴影
                shadow_path = QPainterPath()
                shadow_path.addRoundedRect(1, 1, self.width()-2, self.height()-2, track_radius-1, track_radius-1)
                shadow_pen = QPen(QColor(0, 0, 0, 15))
                shadow_pen.setWidth(1)
                painter.strokePath(shadow_path, shadow_pen)

            # 计算实际显示的圆点位置
            display_circle_x = self._circle_x

            # 圆点尺寸优化：直径27px，符合iOS比例
            circle_diameter = 27
            circle_radius = circle_diameter // 2
            circle_y = (self.height() - circle_diameter) // 2  # 垂直居中

            # 计算拖拽形变效果
            deformation_factor = 0.0
            if self._pressed and abs(self._current_drag_distance) > 1:
                # 拖拽距离越大，形变越明显，但更加克制
                deformation_factor = min(0.15, abs(self._current_drag_distance) * 0.015)

                # 统一左右拖拽的形变效果 - 只在拖拽方向上进行压缩/拉伸
                # 向右拖拽时，滑块受到向右的力，产生向右的拉伸
                # 向左拖拽时，滑块受到向左的力，产生向左的压缩
                if self._current_drag_distance > 0:
                    # 向右拖拽：横向拉伸，高度略微减少
                    ellipse_width = circle_diameter * (1 + deformation_factor)
                    ellipse_height = circle_diameter * (1 - deformation_factor * 0.3)
                else:
                    # 向左拖拽：横向压缩，高度略微增加
                    ellipse_width = circle_diameter * (1 - deformation_factor)
                    ellipse_height = circle_diameter * (1 + deformation_factor * 0.3)

                # 保持滑块居中
                ellipse_x = display_circle_x - (ellipse_width - circle_diameter) / 2
                ellipse_y = circle_y - (ellipse_height - circle_diameter) / 2
            else:
                # 无拖拽或拖拽距离很小时，保持圆形
                ellipse_width = circle_diameter
                ellipse_height = circle_diameter
                ellipse_x = display_circle_x
                ellipse_y = circle_y

            # 绘制变形后的圆圈滑块
            circle_path = QPainterPath()
            circle_path.addEllipse(int(ellipse_x), int(ellipse_y), int(ellipse_width), int(ellipse_height))

            current_state_for_style = self._checked or (self._pressed and display_circle_x > 12)

            if current_state_for_style:
                # 开启状态 - 使用更精致的渐变效果
                gradient = QRadialGradient(int(display_circle_x) + circle_radius, circle_y + circle_radius, circle_radius)
                gradient.setColorAt(0, QColor(255, 255, 255, 255))
                gradient.setColorAt(0.7, QColor(250, 250, 250, 230))
                gradient.setColorAt(1, QColor(240, 240, 240, 200))
                painter.fillPath(circle_path, QBrush(gradient))

                # 添加精致的高光效果（根据形变调整）
                if deformation_factor > 0:
                    highlight_width = 10 * (1 + deformation_factor * 0.5)
                    highlight_height = 8 * (1 - deformation_factor * 0.3)
                    highlight_x = int(display_circle_x) + 6 - (highlight_width - 10) / 2
                    highlight_y = circle_y + 5 - (highlight_height - 8) / 2
                else:
                    highlight_width = 10
                    highlight_height = 8
                    highlight_x = int(display_circle_x) + 6
                    highlight_y = circle_y + 5

                highlight_path = QPainterPath()
                highlight_path.addEllipse(int(highlight_x), int(highlight_y), int(highlight_width), int(highlight_height))
                painter.fillPath(highlight_path, QColor(255, 255, 255, 160))

                # 绘制点击光效（仅在开启状态下且非拖拽时）
                if self._click_effect_active and not self._pressed:
                    effect_path = QPainterPath()
                    effect_center_x = int(display_circle_x) + circle_radius
                    effect_center_y = circle_y + circle_radius
                    effect_path.addEllipse(effect_center_x - self._click_effect_radius,
                                         effect_center_y - self._click_effect_radius,
                                         self._click_effect_radius * 2,
                                         self._click_effect_radius * 2)
                    effect_color = QColor(100, 255, 180, self._click_effect_alpha)
                    painter.fillPath(effect_path, effect_color)
            else:
                # 关闭状态 - 更柔和的白色，带微妙阴影
                gradient = QRadialGradient(int(display_circle_x) + circle_radius, circle_y + circle_radius, circle_radius)
                gradient.setColorAt(0, QColor(255, 255, 255, 255))
                gradient.setColorAt(0.7, QColor(252, 252, 252, 235))
                gradient.setColorAt(1, QColor(245, 245, 245, 215))
                painter.fillPath(circle_path, QBrush(gradient))

                # 添加微妙的外阴影，增强浮起效果（根据形变调整）
                if deformation_factor > 0:
                    shadow_width = (circle_diameter - 2) * (1 - deformation_factor * 0.3)
                    shadow_height = (circle_diameter - 2) * (1 + deformation_factor * 0.2)
                    shadow_x = int(display_circle_x) + 1 + (circle_diameter - 2 - shadow_width) / 2
                    shadow_y = circle_y + 1 - (shadow_height - (circle_diameter - 2)) / 2
                else:
                    shadow_width = circle_diameter - 2
                    shadow_height = circle_diameter - 2
                    shadow_x = int(display_circle_x) + 1
                    shadow_y = circle_y + 1

                shadow_path = QPainterPath()
                shadow_path.addEllipse(int(shadow_x), int(shadow_y), int(shadow_width), int(shadow_height))
                painter.fillPath(shadow_path, QColor(0, 0, 0, 25))
        finally:
            if painter.isActive():
                painter.end()

    def _safe_update(self):
        """安全触发重绘，控件已销毁时停止相关动画定时器。"""
        try:
            self.update()
        except RuntimeError:
            self._stop_all_animations()

    def mousePressEvent(self, a0):
        """鼠标按下"""
        if a0.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            # 记录全局鼠标按下位置
            self._press_global_pos = QCursor.pos()
            self._drag_start_x = self._circle_x  # 记录拖拽起始位置
            self._current_drag_distance = 0
            self._is_light_click = False
            self._was_dragging = False  # 重置拖拽标记
            
            # 开启鼠标跟踪，确保能收到移动事件
            self.setMouseTracking(True)
            # 捕获鼠标，确保即使移出控件外也能收到事件
            self.grabMouse()
            
            # 停止所有正在进行的动画
            self._stop_all_animations()
                
            self.update()
            
    def mouseMoveEvent(self, a0):
        """鼠标移动（拖拽）"""
        if self._pressed:
            # 计算全局鼠标移动的距离
            current_global_pos = QCursor.pos()
            move_x = current_global_pos.x() - self._press_global_pos.x()
            
            # 记录真实的鼠标移动距离（不受 clamping 影响）
            self._current_drag_distance = move_x
            
            # 标记发生了拖拽
            if abs(move_x) > 2:
                self._was_dragging = True
            
            # 根据拖拽起始位置计算新的圆点位置
            new_circle_x = self._drag_start_x + move_x
            
            # 限制在有效范围内 [2, 22] - 根据新尺寸调整
            self._circle_x = max(2, min(22, new_circle_x))
            
            self.update()
            
    def leaveEvent(self, a0):
        """鼠标离开"""
        # 如果正在拖拽中，不处理 leaveEvent
        if self._pressed:
            self.update()
            return
        self._hovered = False
        self._target_hover_progress = 0.0
        self._start_hover_animation()
        self.update()

    def _handle_drag_release(self):
        """处理拖拽释放：根据最终位置决定状态并触发弹性动画"""
        target_checked = self._circle_x > 12

        # 无论鼠标在哪里释放，都触发弹性动画
        if self._checked != target_checked:
            # 状态改变，触发弹性动画
            self._trigger_elastic_animation(target_checked)
        else:
            # 状态未改变，但需要弹性吸附到正确位置
            target_x = 22 if self._checked else 2
            # 只要不在目标位置，就触发弹性动画（包括拖拽到边界的情况）
            if abs(self._circle_x - target_x) > 0.1:
                self._trigger_elastic_animation(self._checked)
            else:
                # 已经在目标位置，但仍需要确保滑块正确归位
                self._circle_x = target_x
                self.update()

    def mouseReleaseEvent(self, a0):
        """鼠标释放"""
        if a0.button() == Qt.MouseButton.LeftButton and self._pressed:
            # 判断是否为轻点（移动距离很小）
            current_global_pos = QCursor.pos()
            move_distance = abs(current_global_pos.x() - self._press_global_pos.x())
            self._is_light_click = move_distance < 5

            if self._is_light_click:
                # 轻点直接切换
                if self._checked:
                    self._trigger_click_effect()  # 触发光效
                self.toggle()
            else:
                # 拖拽操作 - 根据最终位置决定状态并触发弹性动画
                self._handle_drag_release()

            self._pressed = False
            self._current_drag_distance = 0
            self._was_dragging = False

            # 释放鼠标捕获和鼠标跟踪
            self.releaseMouse()
            self.setMouseTracking(False)

            self.update()
        elif a0.button() == Qt.MouseButton.LeftButton:
            # 鼠标在按钮外释放时，grabMouse 可能失效导致 _pressed 已被重置
            # 通过 _was_dragging 判断是否需要进行弹性动画
            if self._was_dragging:
                self._is_light_click = False
                self._handle_drag_release()

            self._pressed = False
            self._current_drag_distance = 0
            self._was_dragging = False
            self.releaseMouse()
            self.setMouseTracking(False)
            self.update()

    def enterEvent(self, a0):
        """鼠标进入"""
        self._hovered = True
        self._target_hover_progress = 1.0
        self._start_hover_animation()
        self.update()

    def _stop_all_animations(self):
        """停止所有正在进行的动画"""
        if self._animation_timer:
            self._animation_timer.stop()
            self._animation_timer = None
        if self._hover_animation_timer:
            self._hover_animation_timer.stop()
            self._hover_animation_timer = None
        if self._click_effect_timer:
            self._click_effect_timer.stop()
            self._click_effect_timer = None
        if self._elastic_timer:
            self._elastic_timer.stop()
            self._elastic_timer = None
        self._elastic_animation_active = False
        self._click_effect_active = False
        
    def _start_hover_animation(self):
        """启动悬停动画"""
        if self._hover_animation_timer is None:
            self._hover_animation_timer = QTimer(self)
            self._hover_animation_timer.timeout.connect(self._animate_hover_step)
            self._hover_animation_timer.start(16)
            
    def _animate_hover_step(self):
        """悬停动画步进"""
        if not self._animations_enabled:
            self._current_hover_progress = self._target_hover_progress
            if self._hover_animation_timer:
                self._hover_animation_timer.stop()
                self._hover_animation_timer = None
            self.update()
            return
            
        diff = self._target_hover_progress - self._current_hover_progress
        if abs(diff) < 0.01:
            self._current_hover_progress = self._target_hover_progress
            if self._hover_animation_timer:
                self._hover_animation_timer.stop()
                self._hover_animation_timer = None
        else:
            self._current_hover_progress += diff * self._animation_speed
        self.update()
        
    def _trigger_click_effect(self):
        """触发动态光效"""
        self._click_effect_active = True
        self._click_effect_radius = 0
        self._click_effect_alpha = 120
        
        if self._click_effect_timer is None:
            self._click_effect_timer = QTimer(self)
            self._click_effect_timer.timeout.connect(self._animate_click_effect)
            self._click_effect_timer.start(16)
            
    def _animate_click_effect(self):
        """动画光效"""
        if not self._animations_enabled:
            self._click_effect_radius = 25
            self._click_effect_active = False
            if self._click_effect_timer:
                self._click_effect_timer.stop()
                self._click_effect_timer = None
            self.update()
            return
            
        speed_factor = 1.0
        if self._animation_speed == 0.15:
            speed_factor = 0.5
        elif self._animation_speed == 0.6:
            speed_factor = 2.0
            
        self._click_effect_radius += 2.5 * speed_factor
        self._click_effect_alpha = int(120 * (1 - self._click_effect_radius / 25))  # 更平滑的透明度衰减
        
        if self._click_effect_radius >= 25:
            self._click_effect_radius = 25
            self._click_effect_active = False
            if self._click_effect_timer:
                self._click_effect_timer.stop()
                self._click_effect_timer = None
        self.update()
        
    def _trigger_elastic_animation(self, target_checked):
        """触发弹性动画"""
        if self._is_light_click:
            # 点击操作：使用简单的线性插值动画，无任何弹性效果
            self._checked = target_checked
            self._animate_to_position(22 if target_checked else 2)
            self.toggled.emit(self._checked)
        else:
            # 拖拽操作：使用弹性动画（固定弹性幅度）
            self._elastic_animation_active = True
            self._elastic_target_x = 22 if target_checked else 2
            self._elastic_velocity = 0
            
            # 计算到目标位置的距离，使用固定的弹性速度
            distance = self._elastic_target_x - self._circle_x
            # 固定弹性系数，不再根据拖拽距离变化
            self._elastic_velocity = distance * 0.8
            self._elastic_damping = 0.85
            
            if self._elastic_timer is None:
                self._elastic_timer = QTimer(self)
                self._elastic_timer.timeout.connect(self._animate_elastic_step)
                self._elastic_timer.start(16)
                
            # 更新状态
            if self._checked != target_checked:
                self._checked = target_checked
                self.toggled.emit(self._checked)
        
    def _animate_elastic_step(self):
        """弹性动画步进"""
        if not self._animations_enabled:
            self._circle_x = self._elastic_target_x
            self._elastic_animation_active = False
            if self._elastic_timer:
                self._elastic_timer.stop()
                self._elastic_timer = None
            self.update()
            return
            
        # 更新位置
        self._circle_x += self._elastic_velocity
        
        # 计算到目标位置的距离
        distance_to_target = self._elastic_target_x - self._circle_x
        
        # 应用阻尼和弹簧力
        if self._is_light_click:
            # 点击操作：几乎无弹簧力，避免任何反弹
            spring_force = distance_to_target * 0.1  # 极弱弹簧强度（原来是0.3）
        else:
            # 拖拽操作：增强弹簧强度以提高响应速度
            spring_force = distance_to_target * 0.8  # 增强弹簧强度（原来是0.6）
            
        self._elastic_velocity += spring_force
        self._elastic_velocity *= self._elastic_damping  # 阻尼
        
        # 检查是否接近目标位置且速度很慢
        if abs(distance_to_target) < 0.3 and abs(self._elastic_velocity) < 0.1:  # 更严格的停止条件
            self._circle_x = self._elastic_target_x
            self._elastic_animation_active = False
            if self._elastic_timer:
                self._elastic_timer.stop()
                self._elastic_timer = None
        self.update()
        
    def _animate_to_position(self, target_x):
        """动画移动到指定位置（用于程序化设置）"""
        self._target_x = target_x
        if self._animation_timer is None:
            self._animation_timer = QTimer(self)
            self._animation_timer.timeout.connect(self._animate_step)
            self._animation_timer.start(16)
            
    def _load_animation_settings(self):
        """加载动画设置"""
        self._animations_enabled = True
        self._animation_speed = 0.35  # 默认中速

        try:
            from core.config.settings_manager import get_settings_manager
            settings = get_settings_manager().get_all()
            self._animations_enabled = settings.get("animations_enabled", True)
            speed = settings.get("animation_speed", _("common.medium"))
            if speed == _("common.slow"):
                self._animation_speed = 0.15
            elif speed == _("common.medium"):
                self._animation_speed = 0.35
            elif speed == _("common.fast"):
                self._animation_speed = 0.6
        except Exception:
            pass
    
    def _animate_step(self):
        """动画步进"""
        if not self._animations_enabled:
            self._circle_x = self._target_x
            if self._animation_timer:
                self._animation_timer.stop()
                self._animation_timer = None
            self.update()
            return
            
        diff = self._target_x - self._circle_x
        if abs(diff) < 0.5:
            self._circle_x = self._target_x
            if self._animation_timer:
                self._animation_timer.stop()
                self._animation_timer = None
        else:
            self._circle_x += diff * self._animation_speed
        self.update()
        
    def _setCheckedDirectly(self, checked):
        """直接设置状态，不触发动画（备用方法）"""
        if self._checked != checked:
            self._checked = checked
            self._circle_x = 22 if checked else 2
            self._target_x = self._circle_x
            self.toggled.emit(self._checked)
        else:
            self._circle_x = 22 if checked else 2
            self._target_x = self._circle_x
        
    def toggle(self):
        """切换状态"""
        self.setChecked(not self._checked)
        
    def isChecked(self):
        return self._checked
        
    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            # 使用弹性动画进行状态切换
            self._trigger_elastic_animation(checked)

    def _apply_accent_color(self, accent_color):
        """应用主题强调色，未提供时从主题配置读取主色"""
        if accent_color is not None:
            self._on_color = QColor(accent_color) if isinstance(accent_color, str) else accent_color
            return
        try:
            from core.config.settings_manager import get_settings_manager
            color = primary_color(get_theme_config(get_settings_manager().get_all()))
            self._on_color = QColor(color)
        except Exception:
            self._on_color = self._default_on_color

    def set_on_color(self, color):
        """设置开启状态颜色"""
        self._on_color = QColor(color) if isinstance(color, str) else color
        self.update()

    def set_off_color(self, color):
        """设置关闭状态颜色"""
        self._off_color = QColor(color) if isinstance(color, str) else color
        self.update()

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新开关开启状态颜色

        Args:
            primary: 主题主色
            background: 主题背景色
        """
        self._apply_accent_color(primary)
        self.update()

    @staticmethod
    def _adjust_brightness(color, delta):
        """调整颜色亮度

        Args:
            color: 原始颜色
            delta: 亮度调整值（正数变亮，负数变暗）

        Returns:
            调整后的 QColor
        """
        h, s, l, a = color.getHsl()
        l = max(0, min(255, l + delta))
        adjusted = QColor()
        adjusted.setHsl(h, s, l, a)
        return adjusted


class SwitchWithLabel(QWidget):
    """带标签的开关控件 - 支持 iOS / Fluent 双风格。"""

    toggled = pyqtSignal(bool)

    def __init__(self, text="", parent=None, checked=False, accent_color=None,
                 style: str = None):
        super().__init__(parent)
        self._text = text
        self._style = style or get_switch_button_style()

        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(0, 0, 0, 0)

        self.label = QLabel(text)
        from gui.fonts import body_font
        self.label.setFont(body_font())
        self.label.setStyleSheet("color: #333333; font-weight: 500;")

        self.switch = self._create_switch(checked, accent_color)
        self._connect_switch_signal()

        layout.addWidget(self.label)
        layout.addWidget(self.switch)
        layout.addStretch()

        self.setLayout(layout)

    def _create_switch(self, checked: bool, accent_color):
        """根据当前风格创建内部开关控件。"""
        if self._style == "fluent":
            switch = FluentSwitchButton(self)
            switch.setChecked(checked)
            return switch
        switch = SwitchButton(checked=checked, accent_color=accent_color)
        return switch

    def _connect_switch_signal(self):
        """连接内部开关状态变化信号到统一 toggled 信号。"""
        if isinstance(self.switch, FluentSwitchButton):
            self.switch.checkedChanged.connect(self.toggled.emit)
        else:
            self.switch.toggled.connect(self.toggled.emit)

    def isChecked(self):
        return self.switch.isChecked()

    def setChecked(self, checked):
        self.switch.setChecked(checked)

    def setText(self, text):
        """设置标签文本"""
        self.label.setText(text)

    def setStyle(self, style: str):
        """切换开关显示风格并重建内部控件。

        Args:
            style: "ios" 或 "fluent"。
        """
        style = style if style in ("ios", "fluent") else "ios"
        if self._style == style:
            return
        self._style = style

        checked = self.isChecked()
        old_switch = self.switch
        self.switch = self._create_switch(checked, None)
        self.layout().replaceWidget(old_switch, self.switch)
        old_switch.deleteLater()
        self._connect_switch_signal()

        # 重建后同步当前主题色，避免新控件颜色与当前主题脱节
        try:
            from gui.styles import load_primary_color, load_background_color
            self.update_theme_colors(load_primary_color(), load_background_color())
        except Exception:
            pass

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新内部开关颜色。

        Args:
            primary: 主题主色
            background: 主题背景色
        """
        if isinstance(self.switch, SwitchButton):
            self.switch.update_theme_colors(primary, background)