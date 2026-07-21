"""
统一的水波纹效果组件。

支持"启用动画效果"和"动画速度"设置项。
"""
from core.i18n import _
from PyQt5.QtCore import QPointF, QTimer, Qt
from PyQt5.QtGui import QPainter, QColor

class RippleEffect:
    """水波纹效果"""
    SPEED_MULTIPLIERS = {_('gui.widgets.ripple_effect.key_003'): 0.5, _('gui.widgets.ripple_effect.key_001'): 1.0, _('gui.widgets.ripple_effect.key_002'): 2.0}

    def __init__(self, center: QPointF, radius: float, color: QColor, max_radius: float):
        """初始化水波纹效果

        Args:
            center: 水波纹中心点
            radius: 初始半径
            color: 水波纹颜色
            max_radius: 最大半径
        """
        self.center = center
        self.radius = radius
        self.max_radius = max_radius
        self.color = color
        self.alpha = 255
        self.finished = False
        self._animations_enabled = True
        self._speed_multiplier = 1.0
        self._load_animation_settings()
        base_speed = max(2.0, max_radius / 30)
        self.speed = base_speed * self._speed_multiplier

    def _load_animation_settings(self):
        """加载动画设置"""
        try:
            from gui.pages.setting_page import SettingPage
            settings = SettingPage.load_settings()
            self._animations_enabled = settings.get('animations_enabled', True)
            speed_setting = settings.get('animation_speed', _('common.medium'))
            self._speed_multiplier = self.SPEED_MULTIPLIERS.get(speed_setting, 1.0)
        except Exception:
            self._animations_enabled = True
            self._speed_multiplier = 1.0

    def update(self):
        """更新水波纹状态"""
        if not self._animations_enabled:
            self.finished = True
            return
        self.radius += self.speed
        progress = self.radius / self.max_radius
        self.alpha = int(255 * (1 - progress * progress))
        if self.radius >= self.max_radius or self.alpha <= 0:
            self.finished = True

    def estimated_duration_ms(self, update_interval_ms: int = 16) -> int:
        """估算当前水波纹从开始到结束的毫秒数。

        Args:
            update_interval_ms: 每次更新间隔，默认 16ms（约 60FPS）。

        Returns:
            预估动画时长（毫秒）。动画被禁用时返回 0。
        """
        if not self._animations_enabled or self.speed <= 0:
            return 0
        frames = (self.max_radius - self.radius) / self.speed
        return max(0, int(frames * update_interval_ms))

    def draw(self, painter: QPainter):
        """绘制水波纹"""
        if self.finished or self.radius <= 0:
            return
        color = QColor(self.color)
        color.setAlpha(max(0, self.alpha))
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.center, self.radius, self.radius)