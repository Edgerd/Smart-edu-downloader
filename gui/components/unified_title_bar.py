# -*- coding: utf-8 -*-
"""统一标题栏组件。

将标题栏与导航栏合并为单一组件，支持 large（上下组合）与 compact（单行）
两种模式，并提供统一的信号与主题色接口。
"""

import os

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QRect
from PyQt5.QtGui import QIcon, QFontMetrics

from gui.widgets.title_bar_button import TitleBarButton
from gui.components.nav_bar import NavButton
from gui.fonts import title_font, nav_font, subtitle_font, get_harmonyos_family
from gui.styles import load_primary_color, load_background_color
from core.ui.icon_manager import IconManager, NAV_ICONS
from core.i18n import _


class UnifiedTitleBar(QWidget):
    """统一标题栏组件。

    支持 large、compact 与 icon_only 三种显示模式，集成窗口控制按钮与导航按钮，
    并统一处理主题色、标题文本、字体样式等状态。

    信号:
        minimize_requested: 最小化按钮被点击。
        maximize_requested: 最大化按钮被点击。
        close_requested: 关闭按钮被点击。
        page_switch_requested(int): 导航按钮被点击，携带目标页面索引。
    """

    minimize_requested = pyqtSignal()
    maximize_requested = pyqtSignal()
    close_requested = pyqtSignal()
    page_switch_requested = pyqtSignal(int)

    # 默认标题
    _DEFAULT_TITLE_LARGE = "SED - Smart-edu-downloader"
    _DEFAULT_TITLE_COMPACT = "SED"

    # 非激活状态图标/文字颜色（与现有 NavBar 保持一致）
    _COLOR_INACTIVE = "#FFFFFF"

    def __init__(
        self,
        mode: str = "large",
        custom_title_text: str = "",
        title_font_styles: list = None,
        parent=None,
    ):
        """初始化统一标题栏。

        Args:
            mode: 显示模式，"large"、"compact" 或 "icon_only"。
            custom_title_text: 自定义标题文本；为空时按模式显示默认标题。
            title_font_styles: 标题字体样式列表，可包含 "bold"、"italic"。
            parent: 父组件。
        """
        super().__init__(parent)

        self._mode = mode if mode in ("large", "compact", "icon_only") else "large"
        self._custom_title_text = custom_title_text or ""
        self._title_font_styles = list(title_font_styles or [])
        self._accent_color = load_primary_color()
        self._background_color = load_background_color()
        self._bar_background = None
        self._corner_radius = 12
        self._active_index = 0

        self._nav_buttons = []
        self._nav_icon_labels = []
        self._nav_text_labels = []
        self._nav_configs = list(NAV_ICONS)
        self._control_buttons = {}
        self._title_icon_label = None
        self._title_text_label = None

        # 当前导航按钮样式参数（用于主题色切换时重建样式表）
        self._nav_style_radius = 20
        self._nav_style_font_size = 11

        self._icon_manager = IconManager()
        self._app_root = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )

        self.setObjectName("unifiedTitleBar")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self._update_style_sheet()
        self._build_ui()
        self._apply_title_state()
        self.set_active_button(self._active_index)

    def _update_style_sheet(self):
        """根据下发背景与圆角更新顶层样式表。"""
        radius = self._corner_radius
        bg = self._bar_background if self._bar_background is not None else self._accent_color
        self.setStyleSheet(f"""
            QWidget#unifiedTitleBar {{
                background: {bg};
                border-top-left-radius: {radius}px;
                border-top-right-radius: {radius}px;
            }}
        """)

    def set_bar_background(self, background: str):
        """设置标题栏背景（支持纯色或渐变 CSS）。

        Args:
            background: CSS background 值，如 rgba(...) 或 qlineargradient(...)。
        """
        self._bar_background = background
        self._update_style_sheet()

    def _get_fallback_icon_size(self) -> int:
        """获取当前模式下图标尺寸回退值。

        Returns:
            int: 图标尺寸（像素）。
        """
        if self._mode == "icon_only":
            return 24
        if self._mode == "compact":
            return 22
        return 30

    def _build_ui(self):
        """根据当前模式构建 UI。"""
        if self._mode == "compact":
            self._build_compact()
        elif self._mode == "icon_only":
            self._build_icon_only()
        else:
            self._build_large()

    def _build_large(self):
        """构建 large 模式：标题栏与导航栏上下组合。"""
        self.setFixedHeight(105)
        self._nav_style_radius = 20
        self._nav_style_font_size = 11

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        title_row = self._create_title_row(height=50, left_margin=20, right_margin=10)
        main_layout.addWidget(title_row)

        nav_row = self._create_nav_row(height=55, left_margin=20, right_margin=20)
        main_layout.addWidget(nav_row)

    def _build_compact(self):
        """构建 compact 模式：标题、导航按钮、窗口控制按钮合并为单行。"""
        self.setFixedHeight(62)
        self._nav_style_radius = 18
        self._nav_style_font_size = 11

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(14, 0, 10, 0)
        main_layout.setSpacing(8)
        self.setLayout(main_layout)

        title_widget = self._create_title_widget(icon_size=22)
        main_layout.addWidget(title_widget)

        nav_container = self._create_compact_nav_container()
        nav_container.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        main_layout.addWidget(nav_container, 1)

        controls = self._create_control_buttons(icon_size=16, button_size=32)
        for btn in controls:
            main_layout.addWidget(btn)

    def _build_icon_only(self):
        """构建 icon_only 模式：标题、圆形图标导航按钮、窗口控制按钮合并为单行。"""
        self.setFixedHeight(56)
        self._nav_style_radius = 22

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(14, 0, 10, 0)
        main_layout.setSpacing(8)
        self.setLayout(main_layout)

        title_widget = self._create_title_widget(icon_size=22)
        main_layout.addWidget(title_widget)

        nav_container = self._create_icon_only_nav_container()
        nav_container.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        main_layout.addWidget(nav_container, 1)

        controls = self._create_control_buttons(icon_size=16, button_size=32)
        for btn in controls:
            main_layout.addWidget(btn)

    def _create_icon_only_nav_container(self):
        """创建 icon_only 模式圆形图标导航按钮容器（居中排列）。

        Returns:
            QWidget: 导航容器。
        """
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        container.setLayout(layout)

        layout.addStretch(1)

        self._nav_buttons = []
        self._nav_icon_labels = []
        self._nav_text_labels = []
        for i, config in enumerate(self._nav_configs):
            btn = self._create_icon_only_nav_button(i, config)
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch(1)

        return container

    def _create_icon_only_nav_button(self, index: int, config: dict):
        """创建 icon_only 模式圆形图标导航按钮。

        Args:
            index: 按钮索引。
            config: 按钮配置字典。

        Returns:
            NavButton: 圆形图标导航按钮实例。
        """
        button_size = 44
        icon_size = 24
        radius = button_size // 2

        btn = NavButton(active_color=self._accent_color, radius=radius)
        btn.setFixedSize(button_size, button_size)
        btn.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setObjectName(f"navBtn_{index}")
        btn.setProperty("active", index == self._active_index)
        btn.setToolTip(config["name"])
        btn.setContentsMargins(0, 0, 0, 0)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.setAlignment(Qt.AlignCenter)

        icon_color = self._accent_color if index == self._active_index else self._COLOR_INACTIVE
        icon_pixmap = self._icon_manager.load_colored_pixmap(
            config["icon_file"], icon_color, size=(icon_size, icon_size)
        )

        icon_label = QLabel()
        icon_label.setFixedSize(icon_size, icon_size)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setObjectName(f"navIcon_{index}")
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        if icon_pixmap:
            icon_label.setPixmap(icon_pixmap)
        layout.addWidget(icon_label)
        self._nav_icon_labels.append(icon_label)

        # icon_only 模式不显示文字标签，但保留空列表以兼容外部接口
        self._nav_text_labels.append(None)

        btn.setLayout(layout)
        btn.setStyleSheet(self._get_nav_button_style())
        btn.clicked.connect(lambda _, idx=index: self.page_switch_requested.emit(idx))

        return btn

    def _create_title_row(self, height: int, left_margin: int, right_margin: int):
        """创建 large 模式标题行（含窗口控制按钮）。

        Args:
            height: 行高度。
            left_margin: 左侧边距。
            right_margin: 右侧边距。

        Returns:
            QWidget: 标题行容器。
        """
        row = QWidget()
        row.setFixedHeight(height)
        row.setAttribute(Qt.WA_TransparentForMouseEvents, False)

        layout = QHBoxLayout()
        layout.setContentsMargins(left_margin, 0, right_margin, 0)
        layout.setSpacing(10)
        row.setLayout(layout)

        title_widget = self._create_title_widget(icon_size=24)
        layout.addWidget(title_widget)
        layout.addStretch()

        controls = self._create_control_buttons(icon_size=20, button_size=36)
        for btn in controls:
            layout.addWidget(btn)

        return row

    def _create_nav_row(self, height: int, left_margin: int, right_margin: int):
        """创建 large 模式导航行。

        Args:
            height: 行高度。
            left_margin: 左侧边距。
            right_margin: 右侧边距。

        Returns:
            QWidget: 导航行容器。
        """
        row = QWidget()
        row.setFixedHeight(height)

        layout = QHBoxLayout()
        layout.setContentsMargins(left_margin, 0, right_margin, 0)
        layout.setSpacing(15)
        row.setLayout(layout)

        self._nav_buttons = []
        self._nav_icon_labels = []
        self._nav_text_labels = []
        for i, config in enumerate(self._nav_configs):
            btn = self._create_nav_button(
                i,
                config,
                button_height=40,
                min_width=0,
                icon_size=30,
                font_size=11,
                margin_h=15,
                radius=20,
            )
            self._nav_buttons.append(btn)
            layout.addWidget(btn)
        layout.addStretch()

        return row

    def _create_compact_nav_container(self):
        """创建 compact 模式导航按钮容器（居中排列）。

        Returns:
            QWidget: 导航容器。
        """
        container = QWidget()
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        container.setLayout(layout)

        layout.addStretch(1)

        self._nav_buttons = []
        self._nav_icon_labels = []
        self._nav_text_labels = []
        for i, config in enumerate(self._nav_configs):
            btn = self._create_nav_button(
                i,
                config,
                button_height=40,
                min_width=0,
                icon_size=22,
                font_size=11,
                margin_h=12,
                radius=18,
            )
            self._nav_buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch(1)

        return container

    def _create_title_widget(self, icon_size: int):
        """创建标题图标与文本组合组件。

        Args:
            icon_size: 标题图标尺寸。

        Returns:
            QWidget: 标题组件。
        """
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        widget.setLayout(layout)

        icon_pixmap = self._icon_manager.load_title_svg(
            "title_books.svg", self._COLOR_INACTIVE, size=(icon_size, icon_size)
        )
        self._title_icon_label = QLabel()
        self._title_icon_label.setFixedSize(icon_size, icon_size)
        if icon_pixmap:
            self._title_icon_label.setPixmap(icon_pixmap)
        layout.addWidget(self._title_icon_label)

        self._title_text_label = QLabel()
        self._title_text_label.setStyleSheet("color: white; background: transparent;")
        layout.addWidget(self._title_text_label)

        return widget

    def _create_control_buttons(self, icon_size: int, button_size: int):
        """创建窗口控制按钮（最小化、最大化、关闭）。

        Args:
            icon_size: 图标尺寸。
            button_size: 按钮尺寸。

        Returns:
            list: 控制按钮列表，顺序为最小化、最大化、关闭。
        """
        resources_dir = os.path.join(self._app_root, "resources", "images")
        configs = [
            ("min", "s.png", self.minimize_requested, _("core.status_bar.minimize_tooltip")),
            ("max", "b.png", self.maximize_requested, _("core.status_bar.maximize_tooltip")),
            ("close", "c.png", self.close_requested, _("core.status_bar.close_tooltip")),
        ]

        buttons = []
        for key, icon_name, signal, tooltip in configs:
            btn = TitleBarButton()
            btn.setFixedSize(button_size, button_size)
            btn.setCursor(Qt.PointingHandCursor)

            if key == "close":
                btn.setHoverBackground("#E81123")
                btn.setPressedBackground("#B20E1C")
            else:
                btn.setHoverBackground("rgba(255, 255, 255, 40)")
                btn.setPressedBackground("rgba(255, 255, 255, 60)")

            icon_path = os.path.join(resources_dir, icon_name)
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(icon_size, icon_size))

            btn.setToolTip(tooltip)
            btn.clicked.connect(signal.emit)

            self._control_buttons[key] = btn
            buttons.append(btn)

        return buttons

    def _create_nav_button(
        self,
        index: int,
        config: dict,
        button_height: int,
        min_width: int,
        icon_size: int,
        font_size: int,
        margin_h: int,
        radius: int,
    ):
        """创建单个导航按钮。

        Args:
            index: 按钮索引。
            config: 按钮配置字典。
            button_height: 按钮高度。
            min_width: 按钮最小宽度。
            icon_size: 图标尺寸。
            font_size: 文字字号。
            margin_h: 水平内边距。
            radius: 圆角半径。

        Returns:
            NavButton: 导航按钮实例。
        """
        btn = NavButton(active_color=self._accent_color, radius=radius)
        btn.setFixedHeight(button_height)
        btn.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setObjectName(f"navBtn_{index}")
        btn.setProperty("active", index == self._active_index)
        btn.setToolTip(config["tip"])
        btn.setContentsMargins(0, 0, 0, 0)

        layout = QHBoxLayout()
        layout.setContentsMargins(margin_h, 0, margin_h, 0)
        layout.setSpacing(6)
        layout.setAlignment(Qt.AlignCenter)

        icon_color = self._accent_color if index == self._active_index else self._COLOR_INACTIVE
        icon_pixmap = self._icon_manager.load_colored_pixmap(
            config["icon_file"], icon_color, size=(icon_size, icon_size)
        )

        icon_label = QLabel()
        icon_label.setFixedSize(icon_size, icon_size)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setObjectName(f"navIcon_{index}")
        icon_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        if icon_pixmap:
            icon_label.setPixmap(icon_pixmap)
        layout.addWidget(icon_label)
        self._nav_icon_labels.append(icon_label)

        text_label = QLabel(config["name"])
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setObjectName(f"navText_{index}")
        text_label.setProperty("active", index == self._active_index)
        text_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        text_label.setWordWrap(False)
        text_label.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        text_label.setToolTip(config["tip"])

        font = nav_font()
        font.setPointSize(font_size)
        text_label.setFont(font)
        layout.addWidget(text_label)
        self._nav_text_labels.append(text_label)

        btn.setLayout(layout)

        # 手动计算按钮宽度：左右边距 + 图标 + 间距 + 文字宽度
        font_metrics = QFontMetrics(font)
        text_width = font_metrics.horizontalAdvance(config["name"])
        calculated_width = margin_h * 2 + icon_size + 6 + text_width + 4
        actual_min_width = max(min_width, calculated_width)
        btn.setMinimumWidth(actual_min_width)

        btn.setStyleSheet(self._get_nav_button_style())
        btn.clicked.connect(lambda _, idx=index: self.page_switch_requested.emit(idx))

        return btn

    def _get_nav_button_style(self):
        """获取当前导航按钮样式表。"""
        font_family = get_harmonyos_family()
        radius = self._nav_style_radius
        font_size = self._nav_style_font_size

        default_style = f"""
            QPushButton[objectName^="navBtn_"] {{
                background: transparent;
                border: none;
                border-radius: {radius}px;
            }}
            QPushButton[objectName^="navBtn_"]:hover {{
                background: rgba(255, 255, 255, 0.12);
            }}
            QPushButton[objectName^="navBtn_"]:pressed {{
                background: rgba(255, 255, 255, 0.20);
            }}
            QLabel[objectName^="navText_"] {{
                color: #FFFFFF;
                font-family: "{font_family}";
                font-size: {font_size}pt;
                font-weight: 500;
            }}
        """

        active_style = f"""
            QPushButton[objectName^="navBtn_"][active="true"] {{
                background: rgba(255, 255, 255, 0.95);
            }}
            QPushButton[objectName^="navBtn_"][active="true"]:hover {{
                background: rgba(255, 255, 255, 1);
            }}
            QPushButton[objectName^="navBtn_"][active="true"]:pressed {{
                background: rgba(230, 230, 230, 0.95);
            }}
            QLabel[objectName^="navText_"][active="true"] {{
                color: {self._accent_color};
                font-weight: 600;
            }}
        """

        return default_style + active_style

    def _apply_title_state(self):
        """应用当前标题文本与字体样式到标题标签。"""
        if self._title_text_label is None:
            return

        if self._custom_title_text:
            text = self._custom_title_text
        elif self._mode == "compact":
            text = self._DEFAULT_TITLE_COMPACT
        else:
            text = self._DEFAULT_TITLE_LARGE
        self._title_text_label.setText(text)

        if self._mode == "compact":
            font = subtitle_font()
            font.setPointSize(13)
        else:
            font = title_font()

        if "bold" in self._title_font_styles:
            font.setBold(True)
        if "italic" in self._title_font_styles:
            font.setItalic(True)

        self._title_text_label.setFont(font)

    def _rebuild_layout(self):
        """清除现有布局并重建 UI。"""
        self._nav_buttons = []
        self._nav_icon_labels = []
        self._nav_text_labels = []
        self._control_buttons = {}
        self._title_icon_label = None
        self._title_text_label = None

        old_layout = self.layout()
        if old_layout is not None:
            while old_layout.count():
                item = old_layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
            QWidget().setLayout(old_layout)

        self._build_ui()

    def set_mode(self, mode: str):
        """切换显示模式并重建内部布局。

        Args:
            mode: "large" 或 "compact"。
        """
        if mode not in ("large", "compact"):
            return
        if self._mode == mode:
            return

        self._mode = mode
        self._rebuild_layout()
        self._apply_title_state()
        self.set_active_button(self._active_index)
        self._update_style_sheet()

    def set_active_button(self, index: int):
        """设置当前激活的导航按钮。

        若按钮正在播放水波纹，则延迟切换 active 状态，等水波纹动画
        基本结束后再改变背景色和图标颜色。

        Args:
            index: 要激活的按钮索引。
        """
        self._active_index = index

        def _apply_state(i: int, btn, is_active: bool):
            if btn.property("active") == is_active:
                return

            btn.setProperty("active", is_active)
            btn.style().unpolish(btn)
            btn.style().polish(btn)

            text_label = btn.findChild(QLabel, f"navText_{i}")
            if text_label:
                text_label.setProperty("active", is_active)
                text_label.style().unpolish(text_label)
                text_label.style().polish(text_label)

            icon_label = btn.findChild(QLabel, f"navIcon_{i}")
            if icon_label:
                icon_color = self._accent_color if is_active else self._COLOR_INACTIVE
                new_pixmap = self._icon_manager.load_colored_pixmap(
                    self._nav_configs[i]["icon_file"],
                    icon_color,
                    size=(icon_label.width(), icon_label.height()),
                )
                if new_pixmap:
                    icon_label.setPixmap(new_pixmap)

        for i, btn in enumerate(self._nav_buttons):
            is_active = i == index
            if btn.property("active") == is_active:
                continue

            delay = btn.ripple_remaining_ms()
            if delay > 0:
                QTimer.singleShot(delay, lambda idx=i, b=btn, active=is_active: _apply_state(idx, b, active))
            else:
                _apply_state(i, btn, is_active)

    def set_title_text(self, text: str):
        """设置自定义标题文本。

        Args:
            text: 标题文本；为空时使用模式默认标题。
        """
        self._custom_title_text = text or ""
        self._apply_title_state()

    def set_title_font_styles(self, styles: list):
        """设置标题字体样式。

        Args:
            styles: 样式列表，可包含 "bold"、"italic"。
        """
        self._title_font_styles = list(styles or [])
        self._apply_title_state()

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新背景与导航按钮样式。

        Args:
            primary: 主题主色。
            background: 主题背景色。
        """
        self._accent_color = primary
        self._background_color = background
        self._update_style_sheet()

        radius = self._nav_style_radius
        for i, btn in enumerate(self._nav_buttons):
            btn.set_active_color(primary)
            btn.set_radius(radius)
            btn.setStyleSheet(self._get_nav_button_style())

            icon_label = btn.findChild(QLabel, f"navIcon_{i}")
            if icon_label:
                is_active = btn.property("active") is True
                icon_color = primary if is_active else self._COLOR_INACTIVE
                icon_size = icon_label.width() or self._get_fallback_icon_size()
                new_pixmap = self._icon_manager.load_colored_pixmap(
                    self._nav_configs[i]["icon_file"],
                    icon_color,
                    size=(icon_size, icon_size),
                )
                if new_pixmap:
                    icon_label.setPixmap(new_pixmap)

    def setCornerRadius(self, radius: int):
        """设置标题栏顶部圆角半径。

        Args:
            radius: 圆角半径，最大化时通常设为 0。
        """
        self._corner_radius = radius
        self._update_style_sheet()
