"""通知弹窗组件"""
from core.i18n import _
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QApplication
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from core.config.settings_manager import get_settings_manager
from gui.styles import load_primary_color

class NotificationWidget(QWidget):
    """通知弹窗组件"""
    closed = pyqtSignal()

    def __init__(self, title='', message='', icon='info', parent=None):
        super().__init__(parent)
        self._title = title
        self._message = message
        self._icon = icon
        self._current_opacity = 0.0
        self._target_opacity = 0.0
        self._is_closing = False
        self._animation_timer = None
        self._close_timer = None
        self._theme_color = load_primary_color()
        self._animations_enabled = True
        self._animation_speed = 0.2
        self._load_animation_settings()
        self._load_theme_color()
        self._init_ui()
        self.destroyed.connect(self._stop_timers)

    @property
    def title_text(self):
        """获取通知标题"""
        return self._title

    @title_text.setter
    def title_text(self, value):
        """设置通知标题"""
        self._title = value

    @property
    def message_text(self):
        """获取通知消息"""
        return self._message

    @message_text.setter
    def message_text(self, value):
        """设置通知消息"""
        self._message = value

    def _load_theme_color(self):
        """加载主题色"""
        try:
            self._theme_color = load_primary_color()
        except Exception:
            pass

    def _adjust_color(self, hex_color, offset):
        """调整颜色亮度"""
        hex_color = hex_color.lstrip('#')
        r = max(0, min(255, int(hex_color[0:2], 16) + offset))
        g = max(0, min(255, int(hex_color[2:4], 16) + offset))
        b = max(0, min(255, int(hex_color[4:6], 16) + offset))
        return f'#{r:02x}{g:02x}{b:02x}'

    def _init_ui(self):
        """初始化UI"""
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(320)
        layout = QVBoxLayout()
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(8)
        container = QWidget()
        container.setObjectName('notificationContainer')
        darker_color = self._adjust_color(self._theme_color, -30)
        container.setStyleSheet(f'\n            #notificationContainer {{\n                background: {self._theme_color};\n                border-radius: 10px;\n                border: 1px solid {darker_color};\n            }}\n        ')
        inner_layout = QVBoxLayout()
        inner_layout.setContentsMargins(12, 10, 12, 10)
        inner_layout.setSpacing(6)
        container.setLayout(inner_layout)
        title_label = QLabel(self.title_text)
        from gui.fonts import bold_font
        title_label.setFont(bold_font())
        title_label.setStyleSheet('color: #FFFFFF;')
        title_label.setWordWrap(True)
        message_label = QLabel(self.message_text)
        from gui.fonts import body_font
        message_label.setFont(body_font())
        message_label.setStyleSheet('color: #E2E8F0;')
        message_label.setWordWrap(True)
        inner_layout.addWidget(title_label)
        inner_layout.addWidget(message_label)
        layout.addWidget(container)
        self.setLayout(layout)

    def show_notification(self, duration=4000):
        """显示通知"""
        try:
            sm = get_settings_manager()
            position = sm.get('notification_position', _('common.top_right'))
            size_key = sm.get('notification_size', _('common.medium'))
            notification_duration = int(sm.get('notification_duration', 5))
            never_hide = sm.get('notification_never_hide', False)
        except Exception:
            position = _('common.top_right')
            size_key = _('common.medium')
            notification_duration = 5
            never_hide = False
        size_map = {_('gui.widgets.notification_widget.key_005'): 280, _('gui.widgets.notification_widget.key_001'): 320, _('gui.widgets.notification_widget.key_004'): 400}
        self.setFixedWidth(size_map.get(size_key, 320))
        self._current_opacity = 0.0
        self._target_opacity = 1.0
        self.setWindowOpacity(self._current_opacity)
        self.show()
        self.adjustSize()
        screen = QApplication.primaryScreen().availableGeometry()
        screen_w = screen.width()
        screen_h = screen.height()
        w = self.width()
        h = self.height()
        position_coords = {_('gui.widgets.notification_widget.key_006'): (20, 20), _('gui.widgets.notification_widget.key_002'): (screen_w - w - 20, 20), _('gui.widgets.notification_widget.key_007'): (20, screen_h - h - 20), _('gui.widgets.notification_widget.key_003'): (screen_w - w - 20, screen_h - h - 20)}
        x, y = position_coords.get(position, (screen_w - w - 20, 20))
        self.move(x, y)
        self._start_animation()
        if never_hide:
            duration = 0
        else:
            duration = notification_duration * 1000
        if duration > 0:
            self._close_timer = QTimer(self)
            self._close_timer.setSingleShot(True)
            self._close_timer.timeout.connect(self._start_close_animation)
            self._close_timer.start(duration)

    def _start_close_animation(self):
        """开始关闭动画"""
        self._is_closing = True
        self._target_opacity = 0.0
        self._start_animation()

    def _start_animation(self):
        """启动动画定时器"""
        if self._animation_timer is None:
            self._animation_timer = QTimer(self)
            self._animation_timer.timeout.connect(self._animate_step)
            self._animation_timer.start(16)

    def _stop_timers(self):
        """停止所有定时器"""
        if self._animation_timer is not None:
            self._animation_timer.stop()
            self._animation_timer = None
        if self._close_timer is not None:
            self._close_timer.stop()
            self._close_timer = None

    def _load_animation_settings(self):
        """加载动画设置"""
        try:
            from gui.pages.setting_page import SettingPage
            settings = SettingPage.load_settings()
            self._animations_enabled = settings.get('animations_enabled', True)
            speed = settings.get('animation_speed', _('common.medium'))
            if speed == _('common.slow'):
                self._animation_speed = 0.1
            elif speed == _('common.medium'):
                self._animation_speed = 0.2
            elif speed == _('common.fast'):
                self._animation_speed = 0.4
        except Exception:
            pass

    def _animate_step(self):
        """动画步进"""
        if not self._animations_enabled:
            self._current_opacity = self._target_opacity
            self.setWindowOpacity(self._current_opacity)
            if self._animation_timer:
                self._animation_timer.stop()
                self._animation_timer = None
            if self._is_closing:
                self.hide()
                self.closed.emit()
                self.deleteLater()
            return
        diff = self._target_opacity - self._current_opacity
        if abs(diff) < 0.01:
            self._current_opacity = self._target_opacity
            self.setWindowOpacity(self._current_opacity)
            if self._animation_timer:
                self._animation_timer.stop()
                self._animation_timer = None
            if self._is_closing:
                self.hide()
                self.closed.emit()
                self.deleteLater()
        else:
            self._current_opacity += diff * self._animation_speed
            self.setWindowOpacity(self._current_opacity)

    def mousePressEvent(self, event):
        """点击关闭通知"""
        self._start_close_animation()

class NotificationManager:
    """通知管理器"""
    _instance = None
    _notifications = []
    _parent = None

    def __new__(cls, parent=None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            if parent:
                cls._parent = parent
        return cls._instance

    def __init__(self, parent=None):
        if parent and self._parent is None:
            self._parent = parent

    def show_notification(self, title=_('widgets.notification.default_title'), message='', duration=4000):
        """显示通知"""
        notification = NotificationWidget(title, message, self._parent)
        self._notifications.append(notification)
        notification.closed.connect(lambda: self._remove_notification(notification))
        notification.show_notification(duration)

    def _remove_notification(self, notification):
        """移除通知"""
        if notification in self._notifications:
            self._notifications.remove(notification)
_notification_manager = None

def get_notification_manager(parent=None):
    """获取通知管理器单例"""
    global _notification_manager
    if _notification_manager is None:
        try:
            from gui.main_window import get_main_window
            main_window = get_main_window()
            if main_window:
                _notification_manager = NotificationManager(main_window)
        except Exception:
            pass
    if _notification_manager is None and parent is not None:
        _notification_manager = NotificationManager(parent)
    return _notification_manager

def show_notification(title=_('widgets.notification.default_title'), message='', duration=4000):
    """快捷函数：显示通知"""
    manager = get_notification_manager()
    if manager:
        manager.show_notification(title, message, duration)