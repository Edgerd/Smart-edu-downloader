"""GUI 控件子模块。"""

from .switch_button import SwitchButton, SwitchWithLabel
from .custom_controls import NoWheelSpinBox, NoWheelComboBox, WheelComboBox, ChineseLineEdit
from .notification_widget import NotificationWidget, NotificationManager, show_notification
from .bottom_right_info_bar import BottomRightInfoBar, show_bottom_right_info
from .vertical_tab_widget import VerticalTabWidget
from .custom_context_menu import CustomContextMenu
from .material_menu import MaterialMenu, MaterialMenuAction
from .animated_gradient_edit import AnimatedGradientBorderEdit
from .hover_tooltip_mixin import HoverTooltipMixin
from .cover_widget import CoverWidget
from .crash_reporter_dialog import CrashReporterDialog

__all__ = [
    'SwitchButton',
    'SwitchWithLabel',
    'NoWheelSpinBox',
    'NoWheelComboBox',
    'WheelComboBox',
    'ChineseLineEdit',
    'NotificationWidget',
    'NotificationManager',
    'show_notification',
    'BottomRightInfoBar',
    'show_bottom_right_info',
    'VerticalTabWidget',
    'CustomContextMenu',
    'MaterialMenu',
    'MaterialMenuAction',
    'AnimatedGradientBorderEdit',
    'HoverTooltipMixin',
    'CoverWidget',
    'CrashReporterDialog',
]