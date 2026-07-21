# -*- coding: utf-8 -*-
"""主窗口模块"""


from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout,
                             QStackedWidget, QApplication, QShortcut,
                             QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt, QPoint, QEvent, QSize, QRect
from PyQt5.QtGui import QKeySequence, QColor, QBitmap, QPainter
from core.config.theme_config import (
    background_color,
    built_in_presets,
    config_from_preset_key,
    config_from_preset_name,
    get_theme_config,
    primary_color,
)
from core.infrastructure.logger import log
from core.infrastructure.thread_pool import shutdown_pool
from gui.styles import get_global_scrollbar_style
from core.network.http_client import get_http_client
from core.settings import TokenManager
from core.i18n import _

_global_main_window = None


def get_main_window():
    """获取全局主窗口实例"""
    return _global_main_window


class RoundedContainer(QWidget):
    """带圆角遮罩的容器部件"""

    def __init__(self, radius: int = 12, parent=None):
        """初始化"""
        super().__init__(parent)
        self._radius = radius

    def resizeEvent(self, event):
        """尺寸变化时重新应用圆角遮罩"""
        super().resizeEvent(event)
        self._apply_rounded_mask()

    def _apply_rounded_mask(self):
        """根据当前尺寸应用圆角遮罩"""
        width = self.width()
        height = self.height()
        if width <= 0 or height <= 0:
            return
        bitmap = QBitmap(QSize(width, height))
        # 默认全透明
        bitmap.fill(Qt.color0)
        painter = QPainter(bitmap)
        try:
            painter.setRenderHint(QPainter.Antialiasing, True)
            # 用前景色绘制圆角矩形
            painter.setBrush(Qt.color1)
            painter.setPen(Qt.color1)
            painter.drawRoundedRect(0, 0, width, height, self._radius, self._radius)
        finally:
            painter.end()
        self.setMask(bitmap)

    def setRadius(self, radius: int):
        """修改圆角半径"""
        self._radius = radius
        self._apply_rounded_mask()


class MainWindow(QMainWindow):
    """主窗口类 - 窗口创建、组件组合、事件分发"""

    def __init__(self, downloader=None, resource_lib=None):
        """初始化主窗口"""
        super().__init__()
        self.downloader = downloader
        self.resource_lib = resource_lib
        global _global_main_window
        _global_main_window = self
        self._hover_tooltips = {}
        self._current_hover_widget = None
        self._minimized_to_tray = False
        self._tray_notifications = True
        self._tray_show_progress = True
        self._window_shadow = None
        self.tray_manager = None
        self._cached_theme_color = None
        self._corner_radius = 12
        self._window_margin = 10
        self._title_bar_style = "large"

        self._init_managers()

        self._init_variables()
        self._setup_window()
        self._create_ui()
        self._connect_settings_signals()
        self._init_navigation()
        self._init_debug_shortcut()
        self._init_notification_manager()
        self._init_clipboard_monitor()
        self.settings_handler.init_status_bar_visibility()
        self.settings_handler.init_window_shadow()
        self.tray_handler.init_system_tray()
        self.settings_handler.init_tray_visibility()
        self.settings_handler.apply_interface_scale_from_settings()

        # 同步应用当前主题色，确保启动时 Fluent 控件（如下拉框）和
        # 自定义图标都使用正确的主题色，避免显示默认橙色。
        # 先从设置文件读取实际主题配置，避免传入 None 导致使用默认蓝色。
        try:
            from gui.pages.setting_page import SettingPage
            initial_settings = SettingPage.load_settings()
            self._cached_theme_color = get_theme_config(initial_settings)
        except Exception:
            pass
        self.settings_handler.apply_theme_colors({'theme_color': self._cached_theme_color})

        self.page_manager.load_page(0)

    def _init_managers(self):
        """初始化所有管理器"""
        from gui.managers.page_manager import PageManager
        from gui.managers.navigation_manager import NavigationManager
        from gui.managers.animation_manager import AnimationManager
        from gui.managers.settings_handler import SettingsHandler
        from gui.managers.tray_handler import TrayHandler

        self.page_manager = PageManager(self)
        self.navigation_manager = NavigationManager(self)
        self.animation_manager = AnimationManager(self)
        self.settings_handler = SettingsHandler(self)
        self.tray_handler = TrayHandler(self)

    def _add_hover_tooltip(self, widget, tooltip):
        """添加鼠标悬停提示"""
        self._hover_tooltips[widget] = tooltip
        widget.setMouseTracking(True)
        widget.installEventFilter(self)

    def eventFilter(self, obj, event):
        """事件过滤器 - 处理鼠标悬停"""
        if obj in self._hover_tooltips:
            if event.type() == QEvent.Enter:
                self._current_hover_widget = obj
                if hasattr(self, 'status_label'):
                    self.status_label.setText(self._hover_tooltips[obj])
                return False
            elif event.type() == QEvent.Leave:
                self._current_hover_widget = None
                if hasattr(self, 'status_label'):
                    self.status_label.setText(_("main_window.status_ready"))
                return False
        return super().eventFilter(obj, event)
    
    def _init_notification_manager(self):
        """初始化通知管理器"""
        try:
            from gui.widgets.notification_widget import NotificationManager
            self.notification_manager = NotificationManager(self)
        except Exception as e:
            log("ERROR", f"初始化通知管理器失败: {e}")

    def show_info_toast(self, kind: str, title: str, content: str = "",
                        duration: int = 2500):
        """在程序窗口右下角显示信息提示。

        Args:
            kind: 提示类型， success / warning / error / info。
            title: 提示标题。
            content: 提示内容。
            duration: 显示时长（毫秒）。
        """
        try:
            from gui.widgets.bottom_right_info_bar import BottomRightInfoBar
            BottomRightInfoBar._show(kind, title, content, self, duration)
        except Exception as e:
            log("ERROR", f"显示右下角信息提示失败: {e}")

    def _init_clipboard_monitor(self):
        """初始化剪贴板监控器"""
        try:
            from core.cache.clipboard_monitor import ClipboardManager
            self.clipboard_manager = ClipboardManager.get_instance()
            self.clipboard_monitor = self.clipboard_manager.get_monitor()
            
            # 连接URL检测信号
            self.clipboard_monitor.url_detected.connect(self._on_clipboard_url_detected)
            
            # 默认启动监控
            self.clipboard_manager.start_monitor()
            log("SUCCESS", "剪贴板监控已初始化")
        except Exception as e:
            log("ERROR", f"初始化剪贴板监控失败: {e}")
            self.clipboard_monitor = None
    
    def _on_clipboard_url_detected(self, url):
        """剪贴板检测到URL时的处理"""
        try:
            self._bring_to_foreground()
            self._auto_fill_url(url)
            
            if hasattr(self, 'notification_manager'):
                self.notification_manager.show_notification(
                    _("notifications.clipboard_url_detected_title"),
                    _("notifications.clipboard_url_detected_message", url=url[:60])
                )
            
            log("SUCCESS", f"自动填入URL: {url[:80]}...")
        except Exception as e:
            log("ERROR", f"处理剪贴板URL失败: {e}")
    
    def _bring_to_foreground(self):
        """将程序前台唤醒"""
        try:
            if self._minimized_to_tray:
                self._minimized_to_tray = False
                self.showNormal()
                self.show()
                self.activateWindow()
                self.raise_()
            elif self.isMinimized():
                self.showNormal()
                self.activateWindow()
                self.raise_()
            elif not self.isVisible():
                self.show()
                self.activateWindow()
                self.raise_()
            else:
                self.activateWindow()
                self.raise_()
            
            log("INFO", "程序已前台唤醒")
        except Exception as e:
            log("ERROR", f"前台唤醒失败: {e}")
    
    def _auto_fill_url(self, url):
        """自动填充URL到主页输入框"""
        try:
            if hasattr(self, 'page_manager'):
                self.page_manager.load_page(0)
                self.navigation_manager.switch_page(0)
            
            home_page = self.page_manager.get_page(0)
            if home_page and hasattr(home_page, 'url_input'):
                home_page.url_input.setPlainText(url)
                log("INFO", "URL已自动填入主页输入框")
        except Exception as e:
            log("ERROR", f"自动填充URL失败: {e}")

    def set_shared_instances(self, downloader, resource_lib):
        """设置共享实例 - 由 main.py 延迟调用"""
        self.downloader = downloader
        self.resource_lib = resource_lib
        
        try:
            from gui.pages.setting_page import SettingPage
            access_token = SettingPage.load_access_token()
            if access_token:
                access_token = TokenManager.decrypt(access_token)
            if access_token:
                self.downloader.set_access_token(access_token)
                self.resource_lib.set_access_token(access_token)
                log("SUCCESS", f"Access Token 已加载，长度: {len(access_token)}")
        except Exception as e:
            log("WARNING", f"加载 Access Token 失败: {e}")
        
        for i in range(self.page_manager.PAGE_COUNT):
            if self.page_manager.is_page_loaded(i):
                self.page_manager.update_page_instances(i)
        
        try:
            resource_page_index = 1
            if self.page_manager.is_page_loaded(resource_page_index):
                resource_page = self.page_manager.get_page(resource_page_index)
                if resource_page and hasattr(resource_page, '_resource_list_loaded') and not resource_page._resource_list_loaded:
                    log("DEBUG", "触发资源页面延迟加载")
                    resource_page._load_resource_list_async()
                    resource_page._resource_list_loaded = True
        except Exception as e:
            log("WARNING", f"资源页面延迟加载失败: {e}")
        
        self.tray_handler.connect_downloader_signals()
        
        try:
            self.downloader.play_download_sound_signal.connect(self._play_download_sound)
        except Exception as e:
            log("WARNING", f"连接下载器GUI信号失败: {e}")

    def _init_debug_shortcut(self):
        """初始化调试快捷键"""
        self.f12_shortcut = QShortcut(QKeySequence("F12"), self)
        self.f12_shortcut.activated.connect(self._toggle_debug_panel)

    def _toggle_debug_panel(self):
        """切换调试面板"""
        from gui.debug_panel import get_debug_manager
        dm = get_debug_manager()
        dm.toggle_panel()

    def _init_variables(self):
        """初始化成员变量"""
        self.drag_position = QPoint()
        self.title_text = "SED - Smart-edu-downloader"
        self._tray_enabled = True

    def _setup_window(self):
        """设置窗口基本属性"""
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle(self.title_text)
        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()
        if screen_width <= 1366:
            window_width = min(900, screen_width - 40)
            window_height = min(600, screen_height - 80)
        else:
            window_width = 1000
            window_height = 650
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.setGeometry(x, y, window_width, window_height)
        self.setMinimumSize(800, 550)

    def _create_ui(self):
        """创建UI界面"""
        central_widget = QWidget()
        central_widget.setAttribute(Qt.WA_TranslucentBackground)
        self.setCentralWidget(central_widget)
        self._main_layout = QVBoxLayout()
        self._main_layout.setContentsMargins(self._window_margin, self._window_margin,
                                              self._window_margin, self._window_margin)
        self._main_layout.setSpacing(0)
        central_widget.setLayout(self._main_layout)

        self._content_container = RoundedContainer(radius=12)
        self._content_container.setObjectName("contentContainer")
        container_layout = QVBoxLayout()
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        self._content_container.setLayout(container_layout)
        
        self._main_layout.addWidget(self._content_container)

        self._create_title_bar_area(container_layout)
        self._create_content_area(container_layout)
        self._create_status_bar_component(container_layout)

        self._content_container.setStyleSheet("""
            #contentContainer {
                background: #F5F9FC;
                border-radius: 12px;
            }
        """)

        self._apply_styles()

        self._update_corner_styles()
    
    def _get_title_bar_style(self):
        """从设置中读取标题栏样式。

        Returns:
            str: "large"、"compact" 或 "icon_only"，读取失败时返回 "large"。
        """
        from core.config.settings_manager import get_settings_manager
        style = get_settings_manager().get("title_bar_style", "large")
        if style not in ("large", "compact", "icon_only"):
            style = "large"
        return style

    def _create_title_bar_area(self, parent_layout):
        """根据设置创建标题栏区域（大号分离式、精简合并式或仅图标合并式）。

        Args:
            parent_layout: 内容容器布局。
        """
        self._title_bar_style = self._get_title_bar_style()
        if self._title_bar_style == "compact":
            self._create_compact_title_bar_component(parent_layout)
        elif self._title_bar_style == "icon_only":
            self._create_icon_only_title_bar_component(parent_layout)
        else:
            self._create_large_title_bar_component(parent_layout)

    def _create_large_title_bar_component(self, parent_layout):
        """创建大号分离式标题栏组件（标题栏 + 导航栏）。

        Args:
            parent_layout: 内容容器布局。
        """
        self._create_title_bar_component(parent_layout)
        self._create_navigation_bar_component(parent_layout)

    def _create_compact_title_bar_component(self, parent_layout):
        """创建精简合并式标题栏组件。

        Args:
            parent_layout: 内容容器布局。
        """
        from gui.components.unified_title_bar import UnifiedTitleBar
        from core.config.settings_manager import get_settings_manager

        settings = get_settings_manager().get_all()
        custom_title = settings.get("custom_title_text", "")
        font_styles = settings.get("title_font_styles", [])

        self.unified_title_bar = UnifiedTitleBar(
            mode="compact",
            custom_title_text=custom_title,
            title_font_styles=font_styles,
        )
        self.unified_title_bar.minimize_requested.connect(self.showMinimized)
        self.unified_title_bar.maximize_requested.connect(self._toggle_maximize)
        self.unified_title_bar.close_requested.connect(self.close)
        self.unified_title_bar.page_switch_requested.connect(
            self.navigation_manager.switch_page
        )

        self.title_bar = self.unified_title_bar
        self.nav_bar = self.unified_title_bar
        self.nav_buttons = self.unified_title_bar._nav_buttons

        parent_layout.addWidget(self.unified_title_bar)

    def _create_icon_only_title_bar_component(self, parent_layout):
        """创建仅图标合并式标题栏组件。

        Args:
            parent_layout: 内容容器布局。
        """
        from gui.components.unified_title_bar import UnifiedTitleBar
        from core.config.settings_manager import get_settings_manager

        settings = get_settings_manager().get_all()
        custom_title = settings.get("custom_title_text", "")
        font_styles = settings.get("title_font_styles", [])

        self.unified_title_bar = UnifiedTitleBar(
            mode="icon_only",
            custom_title_text=custom_title,
            title_font_styles=font_styles,
        )
        self.unified_title_bar.minimize_requested.connect(self.showMinimized)
        self.unified_title_bar.maximize_requested.connect(self._toggle_maximize)
        self.unified_title_bar.close_requested.connect(self.close)
        self.unified_title_bar.page_switch_requested.connect(
            self.navigation_manager.switch_page
        )

        self.title_bar = self.unified_title_bar
        self.nav_bar = self.unified_title_bar
        self.nav_buttons = self.unified_title_bar._nav_buttons

        parent_layout.addWidget(self.unified_title_bar)

    def _create_title_bar_component(self, parent_layout):
        """创建传统标题栏组件。

        Args:
            parent_layout: 内容容器布局。
        """
        from gui.components.title_bar import TitleBar

        self.title_bar = TitleBar(
            title_text=self.title_text,
            add_hover_effect_fn=self.animation_manager.add_hover_effect,
            add_hover_tooltip_fn=self._add_hover_tooltip
        )

        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.maximize_requested.connect(self._toggle_maximize)
        self.title_bar.close_requested.connect(self.close)

        parent_layout.addWidget(self.title_bar)

    def _create_navigation_bar_component(self, parent_layout):
        """创建传统导航栏组件。

        Args:
            parent_layout: 内容容器布局。
        """
        from gui.components.nav_bar import NavBar

        self.nav_bar = NavBar(
            add_nav_hover_effect_fn=self.animation_manager.add_nav_hover_effect,
            add_hover_tooltip_fn=self._add_hover_tooltip
        )

        self.nav_bar.page_switch_requested.connect(self.navigation_manager.switch_page)
        self.nav_buttons = self.nav_bar.nav_buttons

        parent_layout.addWidget(self.nav_bar)

    def _destroy_title_bar_components(self, parent_layout):
        """销毁当前标题栏相关组件。

        Args:
            parent_layout: 标题栏所在布局。
        """
        seen = set()
        for attr in ('title_bar', 'nav_bar', 'unified_title_bar'):
            widget = getattr(self, attr, None)
            if widget is None or id(widget) in seen:
                setattr(self, attr, None)
                continue
            seen.add(id(widget))
            parent_layout.removeWidget(widget)
            widget.setParent(None)
            widget.deleteLater()
            setattr(self, attr, None)
        self.nav_buttons = []

    def rebuild_title_bar(self):
        """根据当前标题栏样式设置重建标题栏组件。"""
        if not hasattr(self, '_content_container'):
            return

        container_layout = self._content_container.layout()

        content_area = self.stacked_widget
        status_bar = self.status_bar
        container_layout.removeWidget(content_area)
        container_layout.removeWidget(status_bar)

        self._destroy_title_bar_components(container_layout)

        if self._title_bar_style == "compact":
            self._create_compact_title_bar_component(container_layout)
        elif self._title_bar_style == "icon_only":
            self._create_icon_only_title_bar_component(container_layout)
        else:
            self._create_large_title_bar_component(container_layout)

        container_layout.addWidget(content_area, 1)
        container_layout.addWidget(status_bar)

        current_index = self.navigation_manager.get_current_index()
        if hasattr(self.nav_bar, 'set_active_button'):
            self.nav_bar.set_active_button(current_index)

        self._apply_title_bar_theme_colors()
        self._update_title_bar_corner_radius()
        self._apply_styles()

    def set_title_bar_style(self, style: str):
        """切换标题栏样式并重建组件。

        Args:
            style: "large"、"compact" 或 "icon_only"。
        """
        if style not in ("large", "compact", "icon_only"):
            return
        if self._title_bar_style == style:
            return
        self._title_bar_style = style
        self.rebuild_title_bar()

    def set_title_bar_title(self, text: str):
        """热更新标题栏标题文本。

        Args:
            text: 标题文本；为空时使用默认标题。
        """
        if (self._title_bar_style == "large" and hasattr(self, 'title_bar')
                and hasattr(self.title_bar, 'set_title_text')):
            self.title_bar.set_title_text(text)
        elif hasattr(self, 'unified_title_bar'):
            self.unified_title_bar.set_title_text(text)

    def set_title_bar_font_styles(self, styles: list):
        """热更新标题栏标题字体样式。

        Args:
            styles: 字体样式列表，可包含 "bold"、"italic"。
        """
        if (self._title_bar_style == "large" and hasattr(self, 'title_bar')
                and hasattr(self.title_bar, 'set_title_font_styles')):
            self.title_bar.set_title_font_styles(styles)
        elif hasattr(self, 'unified_title_bar'):
            self.unified_title_bar.set_title_font_styles(styles)

    def _apply_title_bar_theme_colors(self):
        """将当前缓存主题色与背景下发到当前标题栏组件。"""
        if self._cached_theme_color is None:
            return
        from core.config.theme_config import primary_color, background_color
        primary = primary_color(self._cached_theme_color)
        bg = background_color(self._cached_theme_color)

        bar_bg = self.settings_handler._compute_bar_background(self._cached_theme_color)
        self.settings_handler._apply_bar_background(bar_bg)

        if hasattr(self.title_bar, 'update_theme_colors'):
            self.title_bar.update_theme_colors(primary, bg)
        if (self.nav_bar is not self.title_bar and
                hasattr(self.nav_bar, 'update_theme_colors')):
            self.nav_bar.update_theme_colors(primary, bg)

    def _update_title_bar_corner_radius(self):
        """将当前圆角半径应用到当前标题栏组件。"""
        if hasattr(self, 'title_bar') and self.title_bar is not None:
            self.title_bar.setCornerRadius(self._corner_radius)

    def _connect_settings_signals(self):
        """连接设置变更信号以支持标题栏热更新。"""
        from core.config.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        settings_mgr.setting_changed.connect(self._on_setting_changed)

    def _on_setting_changed(self, key, value):
        """处理标题栏相关设置变更。

        Args:
            key: 变更的设置键。
            value: 变更后的值。
        """
        if key == "title_bar_style":
            self.set_title_bar_style(value)
        elif key == "custom_title_text":
            self.set_title_bar_title(value)
        elif key == "title_font_styles":
            self.set_title_bar_font_styles(value)

    def _create_content_area(self, parent_layout):
        """创建内容区域"""
        self.stacked_widget = QStackedWidget()
        self.stacked_widget.setObjectName("contentArea")
        parent_layout.addWidget(self.stacked_widget, 1)
    
    def _create_status_bar_component(self, parent_layout):
        """创建状态栏组件"""
        from gui.components.status_bar import StatusBar
        
        self.status_bar = StatusBar()
        self.status_label = self.status_bar.status_label
        
        parent_layout.addWidget(self.status_bar)

    def _apply_styles(self):
        """应用样式（使用缓存避免重复读取设置文件）"""
        if self._cached_theme_color is not None:
            config = self._cached_theme_color
        else:
            try:
                from gui.pages.setting_page import SettingPage
                settings = SettingPage.load_settings()
                config = get_theme_config(settings)
                self._cached_theme_color = config
            except Exception:
                config = get_theme_config(None)
                self._cached_theme_color = config

        bg = background_color(config)
        primary = primary_color(config)

        style_sheet = f"""
            QMainWindow {{
                background: transparent;
            }}

            #titleBar {{
                border-top-left-radius: {self._corner_radius}px;
                border-top-right-radius: {self._corner_radius}px;
            }}

            #navBar {{
            }}

            #contentArea {{
                background: {bg};
            }}

            {get_global_scrollbar_style(primary)}
        """
        self.setStyleSheet(style_sheet)

        # 同步更新内容容器背景
        if hasattr(self, 'stacked_widget'):
            self.stacked_widget.setStyleSheet(f"""
                #contentArea {{
                    background: {bg};
                }}
            """)

    def _init_navigation(self):
        """初始化导航状态"""
        self.navigation_manager.update_button_styles(0)

    def _toggle_maximize(self):
        """切换最大化状态"""
        if self.isMaximized():
            self._update_maximize_state(False)
            self.showNormal()
        else:
            self._update_maximize_state(True)
            self.showMaximized()

    def _update_maximize_state(self, maximized: bool):
        """根据最大化状态更新窗口圆角、边距与阴影

        Args:
            maximized: 是否为最大化状态
        """
        if maximized:
            self._corner_radius = 0
            self._window_margin = 0
        else:
            self._corner_radius = 12
            self._window_margin = 10

        # 更新内容容器遮罩与样式
        if hasattr(self, '_content_container'):
            self._content_container.setRadius(self._corner_radius)
            self._content_container.setStyleSheet(f"""
                #contentContainer {{
                    background: #F5F9FC;
                    border-radius: {self._corner_radius}px;
                }}
            """)

        # 更新标题栏圆角
        self._update_title_bar_corner_radius()

        # 更新主窗口边距
        if hasattr(self, '_main_layout'):
            self._main_layout.setContentsMargins(
                self._window_margin, self._window_margin,
                self._window_margin, self._window_margin
            )

        # 最大化时隐藏阴影，还原时恢复用户设置
        if maximized:
            if self._window_shadow is not None:
                self.set_window_shadow(False)
        else:
            self.settings_handler.init_window_shadow()

        self._apply_styles()
        self._update_corner_styles()

    def changeEvent(self, event):
        """窗口状态变化事件，捕获系统最大化的场景"""
        if event.type() == QEvent.WindowStateChange:
            is_max = self.isMaximized()
            expected_radius = 0 if is_max else 12
            if self._corner_radius != expected_radius:
                self._update_maximize_state(is_max)
        super().changeEvent(event)

    def _get_drag_area(self):
        """获取可用于拖动窗口的区域（标题栏与导航栏的并集）。

        Returns:
            QRect: 可拖动区域（主窗口坐标系）。
        """
        if not hasattr(self, 'title_bar') or self.title_bar is None:
            return QRect()

        title_bar = self.title_bar
        nav_bar = getattr(self, 'nav_bar', None)

        title_geo = QRect(
            title_bar.mapTo(self, QPoint(0, 0)),
            title_bar.size()
        )

        if nav_bar is None or nav_bar is title_bar:
            return title_geo

        nav_geo = QRect(
            nav_bar.mapTo(self, QPoint(0, 0)),
            nav_bar.size()
        )
        return title_geo.united(nav_geo)

    def mousePressEvent(self, event):
        """鼠标按下事件：在标题栏或导航栏区域按下可拖动窗口。"""
        if event.button() == Qt.LeftButton:
            if self._get_drag_area().contains(event.pos()):
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def mouseReleaseEvent(self, event):
        """释放鼠标"""
        self.drag_position = QPoint()
    
    def closeEvent(self, event):
        """处理窗口关闭事件"""
        if self.tray_handler.handle_close_event(event):
            return
        
        self._cleanup_and_quit()
        event.accept()
    
    def _cleanup_and_quit(self):
        """清理资源并退出"""
        try:
            self._save_all_table_column_widths()
            self.tray_handler.cleanup()

            # 立即保存设置（确保延迟保存的数据落盘）
            try:
                from core.config.settings_manager import get_settings_manager
                get_settings_manager().save_now()
            except Exception as e:
                log("WARNING", f"保存设置失败: {e}")

            if hasattr(self, 'downloader') and self.downloader:
                self.downloader.shutdown(timeout=5.0)

            try:
                shutdown_pool(wait=True)
            except Exception as e:
                log("WARNING", f"关闭线程池失败: {e}")

            try:
                get_http_client().close()
            except Exception as e:
                log("WARNING", f"关闭 HTTP Session 失败: {e}")

            log("INFO", "程序正在退出...")
        except Exception as e:
            log("ERROR", f"清理资源失败: {e}")
        finally:
            QApplication.instance().quit()
    
    def _save_all_table_column_widths(self):
        """保存所有表格列宽配置"""
        try:
            from core.ui.table_column_manager import (
                save_table_widths_to_settings,
                save_tree_widths_to_settings
            )
            from core.config.settings_manager import get_settings_manager
            settings_mgr = get_settings_manager()
            
            if hasattr(self, 'page_manager') and self.page_manager:
                # 页面索引：0主页、1资源库、2下载、3设置、4更多
                download_page = self.page_manager.get_page(2)
                if download_page and hasattr(download_page, 'download_table'):
                    save_table_widths_to_settings(download_page.download_table, "table_width_download_page")

                resource_page = self.page_manager.get_page(1)
                if resource_page:
                    if hasattr(resource_page, 'search_result_table'):
                        save_table_widths_to_settings(resource_page.search_result_table, "table_width_resource_search")
                    if hasattr(resource_page, 'chapter_tree'):
                        save_tree_widths_to_settings(resource_page.chapter_tree, "tree_width_resource_chapter")

                more_page = self.page_manager.get_page(4)
                if more_page:
                    if hasattr(more_page, 'download_history_table'):
                        save_table_widths_to_settings(more_page.download_history_table, "table_width_more_download_history")
                    if hasattr(more_page, 'link_history_table'):
                        save_table_widths_to_settings(more_page.link_history_table, "table_width_more_link_history")
                    if hasattr(more_page, 'search_history_table'):
                        save_table_widths_to_settings(more_page.search_history_table, "table_width_more_search_history")

                home_page = self.page_manager.get_page(0)
                if home_page:
                    if hasattr(home_page, 'download_history_table'):
                        save_table_widths_to_settings(home_page.download_history_table, "table_width_home_download_history")
                    if hasattr(home_page, 'link_history_table'):
                        save_table_widths_to_settings(home_page.link_history_table, "table_width_home_link_history")
                    if hasattr(home_page, 'search_history_table'):
                        save_table_widths_to_settings(home_page.search_history_table, "table_width_home_search_history")
            
            settings_mgr._save()
        except Exception as e:
            log("ERROR", f"保存表格列宽配置失败: {e}")

    def set_status(self, text):
        """设置状态栏文本"""
        self.status_label.setText(text)

    def _play_download_sound(self, sound_config):
        """播放下载完成声音"""
        try:
            from core.download.sound_player import SoundPlayer
            if sound_config.get("sound_enabled", False) and sound_config.get("download_complete_sound", False):
                SoundPlayer.play_completion_sound()
        except Exception as e:
            log("ERROR", f"播放下载声音失败: {e}")
    
    def show(self):
        """显示窗口"""
        self._minimized_to_tray = False
        super().show()
    
    def close(self):
        """关闭窗口"""
        super().close()
    
    def _on_settings_saved(self):
        """设置保存后的回调"""
        self.settings_handler.on_settings_saved()
    
    def navigate_to_setting_and_highlight_token(self):
        """跳转到设置页面并高亮Token输入框"""
        self.navigation_manager.navigate_to_setting_and_highlight_token()
    
    def set_window_shadow(self, enabled):
        """设置窗口阴影"""
        try:
            if enabled:
                shadow = QGraphicsDropShadowEffect(self)
                shadow.setBlurRadius(20)
                shadow.setOffset(0, 3)
                shadow.setColor(QColor(0, 0, 0, 60))
                self._content_container.setGraphicsEffect(shadow)
                self._window_shadow = shadow
                log("INFO", "窗口阴影已启用")
            else:
                if hasattr(self, '_content_container'):
                    self._content_container.setGraphicsEffect(None)
                self._window_shadow = None
                log("INFO", "窗口阴影已禁用")
        except Exception as e:
            log("ERROR", f"设置窗口阴影失败: {e}")

    def _update_corner_styles(self):
        """更新圆角样式（使用主题背景色）"""
        if not hasattr(self, 'stacked_widget') or not hasattr(self, 'status_bar'):
            return

        config = get_theme_config(None)
        if self._cached_theme_color is not None:
            config = self._cached_theme_color

        bg = background_color(config)
        status_visible = self.status_bar.isVisible()
        radius = self._corner_radius

        if status_visible:
            self.stacked_widget.setStyleSheet(f"""
                #contentArea {{
                    background: {bg};
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                }}
            """)
            self.status_bar.setStyleSheet(f"""
                #statusBar {{
                    background: {bg};
                    border-bottom-left-radius: {radius}px;
                    border-bottom-right-radius: {radius}px;
                }}
            """)
        else:
            self.stacked_widget.setStyleSheet(f"""
                #contentArea {{
                    background: {bg};
                    border-bottom-left-radius: {radius}px;
                    border-bottom-right-radius: {radius}px;
                }}
            """)
            self.status_bar.setStyleSheet(f"""
                #statusBar {{
                    background: {bg};
                    border-bottom-left-radius: 0px;
                    border-bottom-right-radius: 0px;
                }}
            """)

    def _update_theme_color(self, config):
        """更新主题配置"""
        self._cached_theme_color = config
        self.settings_handler.apply_theme_colors({'theme_color': config})

    def _toggle_theme(self):
        """循环切换内置主题预设。"""
        from core.config.settings_manager import get_settings_manager
        from gui.pages.setting_page import SettingPage

        settings = SettingPage.load_settings()
        config = get_theme_config(settings)
        current_key = config.get("key", "jikelan")

        presets = [preset["key"] for preset in built_in_presets()]
        if not presets:
            presets = ["jikelan"]

        try:
            idx = presets.index(current_key)
        except ValueError:
            idx = -1
        next_key = presets[(idx + 1) % len(presets)]

        new_config = config_from_preset_key(next_key)
        get_settings_manager().set("theme_color", new_config)
        self._update_theme_color(new_config)
