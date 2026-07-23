# -*- coding: utf-8 -*-
"""
实验室标签页组件

提供实验性功能的占位页面，目前支持读取系统主题色并应用为程序主题色、
标题栏实验功能、滚动条跟随主题色以及开关样式切换。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSizePolicy, QScrollArea,
)
from PyQt5.QtCore import Qt

from qfluentwidgets import LineEdit, FluentIcon as FIF

from gui.fonts import body_font
from gui.styles import load_primary_color
from gui.pages.settings.components.setting_group import SettingGroup
from gui.pages.settings.components.switch_card import SwitchWithLabelSettingCard
from gui.pages.settings.components.combo_box_card import ComboBoxCard
from gui.pages.settings.components.line_edit_card import LineEditCard
from gui.pages.settings.components.push_card import PushCard
from gui.widgets.switch_button import refresh_all_switch_buttons
from gui.widgets.bottom_right_info_bar import BottomRightInfoBar
from core.i18n import _
from core.infrastructure.logger import log
from core.ui.system_theme_reader import get_system_theme_config


class LabTab(QWidget):
    """实验室标签页

    用于展示实验性功能，当前提供读取并应用系统主题色、标题栏自定义、
    滚动条主题色以及全局开关样式切换能力。
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._accent_color = load_primary_color()
        self._background_color = "transparent"
        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setStyleSheet("background: transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 使用滚动区域承载实验室内容，避免分组过多时显示不全
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(15, 15, 15, 15)
        scroll_layout.setSpacing(0)

        # 系统主题色功能区
        self.theme_group = self._create_group(_("debug.lab.title"))
        self._setup_system_theme_section(self.theme_group)
        scroll_layout.addWidget(self.theme_group)

        # 标题栏实验功能区
        self.title_bar_group = self._create_group(_("debug.lab.title_bar_group"))
        self._setup_title_bar_section(self.title_bar_group)
        scroll_layout.addWidget(self.title_bar_group)

        # 滚动条跟随主题色
        self.scrollbar_group = self._create_group(
            _("debug.lab.scrollbar_follow_theme_group")
        )
        self._setup_scrollbar_section(self.scrollbar_group)
        scroll_layout.addWidget(self.scrollbar_group)

        # 开关样式实验功能区
        self.switch_style_group = self._create_group(
            _("debug.lab.switch_style_group")
        )
        self._setup_switch_style_section(self.switch_style_group)
        scroll_layout.addWidget(self.switch_style_group)

        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setFont(body_font())
        self.status_label.setStyleSheet("color: #999999; background: transparent;")
        self.status_label.setWordWrap(True)
        scroll_layout.addWidget(self.status_label)

        scroll_layout.addStretch()

        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)

        self._load_title_bar_settings()
        self._load_switch_style_setting()
        self._refresh_system_theme_preview()

    def _create_group(self, title: str) -> SettingGroup:
        """创建卡片式分组容器。"""
        return SettingGroup(title, self._accent_color, self)

    def _setup_system_theme_section(self, group: SettingGroup):
        """设置系统主题色实验区。"""
        row = QHBoxLayout()
        row.setSpacing(12)

        self.color_preview = QLabel()
        self.color_preview.setFixedSize(32, 32)
        self.color_preview.setStyleSheet(self._get_preview_style("#CCCCCC"))
        self.color_preview.setToolTip(_("debug.lab.system_theme_preview"))

        self.color_value_label = QLabel(_("debug.lab.system_theme_none"))
        self.color_value_label.setFont(body_font())
        self.color_value_label.setStyleSheet("color: #666666; background: transparent;")
        self.color_value_label.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Preferred
        )

        self.apply_card = PushCard(
            FIF.PALETTE,
            _("debug.lab.apply_system_theme"),
            _("debug.lab.apply_system_theme_desc"),
            button_text=_("debug.lab.apply_system_theme"),
        )
        self.apply_card.setAccentColor(self._accent_color)
        self.apply_card.clicked.connect(self._on_apply_system_theme)

        row.addWidget(self.color_preview)
        row.addWidget(self.color_value_label)
        row.addWidget(self.apply_card)
        group.add_layout(row)

    def _setup_title_bar_section(self, group: SettingGroup):
        """设置标题栏实验区。"""
        self.title_bar_style_card = ComboBoxCard(
            FIF.FULL_SCREEN,
            _("debug.lab.title_bar_style"),
            _("debug.lab.title_bar_style_desc"),
        )
        self.title_bar_style_card.addItem(
            _("debug.lab.title_bar_style_large"), "large"
        )
        self.title_bar_style_card.addItem(
            _("debug.lab.title_bar_style_compact"), "compact"
        )
        self.title_bar_style_card.addItem(
            _("debug.lab.title_bar_style_icon_only"), "icon_only"
        )
        self.title_bar_style_card.currentIndexChanged.connect(
            self._on_title_bar_style_changed
        )
        group.add_widget(self.title_bar_style_card)

        self.custom_title_card = LineEditCard(
            FIF.EDIT,
            _("debug.lab.custom_title_text"),
            _("debug.lab.custom_title_text_desc"),
        )
        self.custom_title_card.setPlaceholderText(
            _("debug.lab.custom_title_placeholder")
        )
        self.custom_title_card.line_edit().editingFinished.connect(
            self._on_custom_title_finished
        )
        group.add_widget(self.custom_title_card)

        self.bold_switch = SwitchWithLabelSettingCard(
            FIF.FONT,
            _("debug.lab.title_font_bold"),
            _("debug.lab.title_font_bold_desc"),
            checked=False,
        )
        self.bold_switch.toggled.connect(self._on_title_font_styles_changed)
        group.add_widget(self.bold_switch)

        self.italic_switch = SwitchWithLabelSettingCard(
            FIF.FONT,
            _("debug.lab.title_font_italic"),
            _("debug.lab.title_font_italic_desc"),
            checked=False,
        )
        self.italic_switch.toggled.connect(self._on_title_font_styles_changed)
        group.add_widget(self.italic_switch)

    def _setup_scrollbar_section(self, group: SettingGroup):
        """设置滚动条跟随主题色实验区。"""
        self.scrollbar_theme_switch = SwitchWithLabelSettingCard(
            FIF.SCROLL,
            _("debug.lab.scrollbar_follow_theme"),
            _("debug.lab.scrollbar_follow_theme_desc"),
            checked=self._load_scrollbar_follow_theme(),
        )
        self.scrollbar_theme_switch.toggled.connect(self._on_scrollbar_theme_toggled)
        group.add_widget(self.scrollbar_theme_switch)

    def _setup_switch_style_section(self, group: SettingGroup):
        """设置开关样式切换实验区。"""
        self.switch_style_card = ComboBoxCard(
            FIF.BRIGHTNESS,
            _("debug.lab.switch_style_label"),
            _("debug.lab.switch_style_label_desc"),
        )
        self.switch_style_card.addItem(
            _("debug.lab.switch_style_fluent"), "fluent"
        )
        self.switch_style_card.addItem(
            _("debug.lab.switch_style_ios"), "ios"
        )
        self.switch_style_card.currentIndexChanged.connect(
            self._on_switch_style_changed
        )
        group.add_widget(self.switch_style_card)

    def _get_preview_style(self, color: str) -> str:
        """获取颜色预览方块样式。"""
        return f"""
            QLabel {{
                background: {color};
                border: 1px solid #E0E8F0;
                border-radius: 6px;
            }}
        """

    def _load_scrollbar_follow_theme(self) -> bool:
        """读取滚动条跟随主题色设置"""
        try:
            from core.config.settings_manager import get_settings_manager
            return bool(get_settings_manager().get("scrollbar_follow_theme", False))
        except Exception:
            return False

    def _load_title_bar_settings(self):
        """从设置读取标题栏实验功能初始状态并更新控件（不触发信号）。"""
        try:
            from core.config.settings_manager import get_settings_manager
            settings = get_settings_manager()
            style = settings.get("title_bar_style", "large")
            custom_title = settings.get("custom_title_text", "")
            font_styles = settings.get("title_font_styles", []) or []
        except Exception:
            style = "large"
            custom_title = ""
            font_styles = []

        self.title_bar_style_card.blockSignals(True)
        index = self.title_bar_style_card.findData(style)
        if index >= 0:
            self.title_bar_style_card.setCurrentIndex(index)
        self.title_bar_style_card.blockSignals(False)

        self.custom_title_card.line_edit().blockSignals(True)
        self.custom_title_card.setText(custom_title)
        self.custom_title_card.line_edit().blockSignals(False)

        self.bold_switch.blockSignals(True)
        self.bold_switch.setChecked("bold" in font_styles)
        self.bold_switch.blockSignals(False)

        self.italic_switch.blockSignals(True)
        self.italic_switch.setChecked("italic" in font_styles)
        self.italic_switch.blockSignals(False)

    def _load_switch_style_setting(self):
        """读取全局开关样式设置并同步下拉框状态。"""
        try:
            from core.config.settings_manager import get_settings_manager
            style = get_settings_manager().get("switch_button_style", "ios")
        except Exception:
            style = "ios"

        self.switch_style_card.blockSignals(True)
        index = self.switch_style_card.findData(style)
        if index >= 0:
            self.switch_style_card.setCurrentIndex(index)
        self.switch_style_card.blockSignals(False)

    def _on_title_bar_style_changed(self, index: int):
        """标题栏样式下拉选项变更时保存设置并应用到主窗口。

        Args:
            index: 当前选中的下拉索引。
        """
        value = self.title_bar_style_card.currentData()
        if value not in ("large", "compact", "icon_only"):
            return

        try:
            from core.config.settings_manager import get_settings_manager
            get_settings_manager().set("title_bar_style", value)

            from gui.main_window import get_main_window
            main_window = get_main_window()
            if main_window is not None:
                main_window.set_title_bar_style(value)

            self.status_label.setText(_("debug.lab.title_bar_style_applied"))
            self.status_label.setStyleSheet(
                "color: #43A047; background: transparent;"
            )
            log("INFO", f"标题栏样式已切换为: {value}")
        except Exception as e:
            self.status_label.setText(
                _("debug.lab.title_bar_style_failed").replace("{error}", str(e))
            )
            self.status_label.setStyleSheet(
                "color: #E53935; background: transparent;"
            )
            log("ERROR", f"切换标题栏样式失败: {e}")

    def _on_custom_title_finished(self):
        """自定义标题输入完成或失去焦点时保存并应用。"""
        text = self.custom_title_card.text().strip()

        try:
            from core.config.settings_manager import get_settings_manager
            get_settings_manager().set("custom_title_text", text)

            from gui.main_window import get_main_window
            main_window = get_main_window()
            if main_window is not None:
                main_window.set_title_bar_title(text)

            self.status_label.setText(_("debug.lab.custom_title_applied"))
            self.status_label.setStyleSheet(
                "color: #43A047; background: transparent;"
            )
            log("INFO", "自定义标题已更新")
        except Exception as e:
            self.status_label.setText(
                _("debug.lab.custom_title_failed").replace("{error}", str(e))
            )
            self.status_label.setStyleSheet(
                "color: #E53935; background: transparent;"
            )
            log("ERROR", f"更新自定义标题失败: {e}")

    def _on_title_font_styles_changed(self):
        """粗体/斜体开关变更时构造样式列表并应用。"""
        styles = []
        if self.bold_switch.isChecked():
            styles.append("bold")
        if self.italic_switch.isChecked():
            styles.append("italic")

        try:
            from core.config.settings_manager import get_settings_manager
            get_settings_manager().set("title_font_styles", styles)

            from gui.main_window import get_main_window
            main_window = get_main_window()
            if main_window is not None:
                main_window.set_title_bar_font_styles(styles)

            self.status_label.setText(_("debug.lab.title_font_styles_applied"))
            self.status_label.setStyleSheet(
                "color: #43A047; background: transparent;"
            )
            log("INFO", f"标题字体样式已更新: {styles}")
        except Exception as e:
            self.status_label.setText(
                _("debug.lab.title_font_styles_failed").replace("{error}", str(e))
            )
            self.status_label.setStyleSheet(
                "color: #E53935; background: transparent;"
            )
            log("ERROR", f"更新标题字体样式失败: {e}")

    def _on_scrollbar_theme_toggled(self, checked: bool):
        """切换滚动条跟随主题色设置并刷新全局样式"""
        try:
            from core.config.settings_manager import get_settings_manager
            get_settings_manager().set("scrollbar_follow_theme", bool(checked))

            from gui.main_window import get_main_window
            main_window = get_main_window()
            if main_window is not None:
                main_window._apply_styles()

            from gui.debug_panel import DebugPanel
            panel = DebugPanel()
            if panel.isVisible():
                panel.update_theme_colors(self._accent_color, self._background_color)

            self.status_label.setText(_("debug.lab.scrollbar_theme_applied"))
            self.status_label.setStyleSheet("color: #43A047; background: transparent;")
            log("INFO", f"滚动条跟随主题色已{'开启' if checked else '关闭'}")
        except Exception as e:
            self.status_label.setText(
                _("debug.lab.scrollbar_theme_failed").replace("{error}", str(e))
            )
            self.status_label.setStyleSheet("color: #E53935; background: transparent;")
            log("ERROR", f"切换滚动条主题色失败: {e}")

    def _on_switch_style_changed(self, index: int):
        """开关样式下拉选项变更时保存设置并全局刷新开关外观。

        Args:
            index: 当前选中的下拉索引。
        """
        value = self.switch_style_card.currentData()
        if value not in ("ios", "fluent"):
            return

        try:
            from core.config.settings_manager import get_settings_manager
            get_settings_manager().set("switch_button_style", value)

            refresh_all_switch_buttons(value)

            self.status_label.setText(
                _("debug.lab.switch_style_applied").replace("{style}", value)
            )
            self.status_label.setStyleSheet(
                "color: #43A047; background: transparent;"
            )

            # 通过右下角信息提示反馈切换结果
            try:
                BottomRightInfoBar.success(
                    title=_("common.success"),
                    content=_("debug.lab.switch_style_applied").replace(
                        "{style}", value
                    ),
                    parent=self.window(),
                    duration=2000,
                )
            except Exception:
                pass

            log("INFO", f"全局开关样式已切换为: {value}")
        except Exception as e:
            self.status_label.setText(
                _("debug.lab.switch_style_failed").replace("{error}", str(e))
            )
            self.status_label.setStyleSheet(
                "color: #E53935; background: transparent;"
            )
            log("ERROR", f"切换开关样式失败: {e}")

    def _refresh_system_theme_preview(self):
        """读取并刷新系统主题色预览，不改变程序当前主题。"""
        try:
            config = get_system_theme_config()
            if config is None:
                self.color_preview.setStyleSheet(self._get_preview_style("#CCCCCC"))
                self.color_value_label.setText(_("debug.lab.system_theme_none"))
                return

            primary = config["primary"]
            self.color_preview.setStyleSheet(self._get_preview_style(primary))
            self.color_value_label.setText(primary)
        except Exception:
            self.color_preview.setStyleSheet(self._get_preview_style("#CCCCCC"))
            self.color_value_label.setText(_("debug.lab.system_theme_none"))

    def _on_apply_system_theme(self):
        """读取系统主题色并应用到程序。"""
        try:
            config = get_system_theme_config()
            if config is None:
                self.status_label.setText(_("debug.lab.system_theme_unavailable"))
                self.status_label.setStyleSheet("color: #E53935; background: transparent;")
                log("WARNING", "读取系统主题色失败或当前平台不支持")
                return

            primary = config["primary"]
            self._refresh_system_theme_preview()

            from core.config.settings_manager import get_settings_manager
            from gui.main_window import get_main_window

            get_settings_manager().set("theme_color", config)
            main_window = get_main_window()
            if main_window is not None:
                main_window._update_theme_color(config)

            self.status_label.setText(
                _("debug.lab.system_theme_applied").replace("{color}", primary)
            )
            self.status_label.setStyleSheet("color: #43A047; background: transparent;")
            log("INFO", f"已应用系统主题色: {primary}")
        except Exception as e:
            self.status_label.setText(
                _("debug.lab.system_theme_failed").replace("{error}", str(e))
            )
            self.status_label.setStyleSheet("color: #E53935; background: transparent;")
            log("ERROR", f"应用系统主题色失败: {e}")

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新实验室标签页视觉元素。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        self._accent_color = primary
        self._background_color = background
        self.setStyleSheet("background: transparent;")

        for group in [self.theme_group, self.title_bar_group, self.scrollbar_group, self.switch_style_group]:
            if group and hasattr(group, "update_accent_color"):
                group.update_accent_color(primary)

        if hasattr(self, "apply_card"):
            self.apply_card.setAccentColor(primary)
