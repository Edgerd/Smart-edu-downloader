"""水波纹动画混入类。

提供通用的水波纹动画逻辑，供需要水波纹效果的组件继承使用。
"""
from PyQt5.QtCore import QPointF, QTimer, Qt
from PyQt5.QtGui import QColor, QPainter, QPainterPath
from gui.widgets.ripple_effect import RippleEffect
from gui.utils.color_utils import ripple_tint


class RippleMixin:
    """水波纹动画混入类。
    
    提供通用的水波纹动画逻辑，子类需要实现以下方法：
    - _get_ripple_color() -> QColor: 返回水波纹颜色
    - _get_ripple_shape() -> QPainterPath: 返回水波纹裁剪形状（可选，默认为矩形）
    
    使用示例：
        class MyButton(QPushButton, RippleMixin):
            def __init__(self):
                super().__init__()
                self._init_ripple()
                self._accent_color = '#2078DA'
            
            def _get_ripple_color(self):
                return QColor(ripple_tint(self._accent_color))
            
            def mousePressEvent(self, event):
                self._start_ripple(event.pos())
                super().mousePressEvent(event)
            
            def paintEvent(self, event):
                super().paintEvent(event)
                painter = QPainter(self)
                self._draw_ripples(painter)
    """
    
    def _init_ripple(self, timer_interval: int = 33):
        """初始化水波纹系统。
        
        Args:
            timer_interval: 动画定时器间隔（毫秒），默认33ms（约30FPS）
        """
        self._ripples = []
        self._ripple_timer = QTimer(self)
        self._ripple_timer.timeout.connect(self._update_ripples)
        self._ripple_timer_interval = timer_interval
    
    def _get_ripple_color(self) -> QColor:
        """获取水波纹颜色。
        
        子类必须实现此方法。
        
        Returns:
            QColor: 水波纹颜色
        """
        raise NotImplementedError("子类必须实现 _get_ripple_color 方法")
    
    def _get_ripple_shape(self) -> QPainterPath:
        """获取水波纹裁剪形状。
        
        子类可以重写此方法来自定义水波纹形状。
        默认返回 None，表示不裁剪（矩形）。
        
        Returns:
            QPainterPath: 水波纹裁剪路径，或 None 表示不裁剪
        """
        return None
    
    def _start_ripple(self, pos):
        """启动水波纹动画。
        
        Args:
            pos: 鼠标点击位置（QPoint 或 QPointF）
        """
        if not isinstance(pos, QPointF):
            pos = QPointF(pos)
        
        # 计算最大半径（确保能覆盖整个控件）
        max_radius = max(self.width(), self.height()) * 1.5
        
        # 创建水波纹效果
        ripple_color = self._get_ripple_color()
        ripple = RippleEffect(pos, 0, ripple_color, max_radius)
        self._ripples.append(ripple)
        
        # 启动定时器（如果未启动）
        if not self._ripple_timer.isActive():
            self._ripple_timer.start(self._ripple_timer_interval)
    
    def _update_ripples(self):
        """更新水波纹动画状态。"""
        # 更新所有水波纹
        for ripple in self._ripples[:]:
            ripple.update()
            if ripple.finished:
                self._ripples.remove(ripple)
        
        # 触发重绘
        self.update()
        
        # 如果没有水波纹了，停止定时器
        if not self._ripples:
            self._ripple_timer.stop()
    
    def _draw_ripples(self, painter: QPainter):
        """绘制所有水波纹。
        
        Args:
            painter: QPainter 对象
        """
        if not self._ripples:
            return
        
        # 保存 painter 状态
        painter.save()
        
        # 应用裁剪形状（如果有）
        shape = self._get_ripple_shape()
        if shape is not None:
            painter.setClipPath(shape)
        
        # 绘制所有水波纹
        for ripple in self._ripples:
            ripple.draw(painter)
        
        # 恢复 painter 状态
        painter.restore()
    
    def _stop_ripples(self):
        """停止所有水波纹动画。"""
        self._ripples.clear()
        if self._ripple_timer.isActive():
            self._ripple_timer.stop()

    def _ripple_remaining_ms(self) -> int:
        """获取当前所有活跃水波纹的最长剩余动画时长（毫秒）。

        用于在需要等待水波纹播放完成后再切换状态（如选中、激活）的
        场景中计算延迟时间。

        Returns:
            最长剩余动画时长（毫秒）。没有活跃水波纹时返回 0。
        """
        if not self._ripples:
            return 0
        update_interval = getattr(self, '_ripple_timer_interval', 16)
        return max(
            ripple.estimated_duration_ms(update_interval)
            for ripple in self._ripples
        )
