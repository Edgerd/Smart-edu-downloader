# -*- coding: utf-8 -*-
"""主题选择器控件。

以单选按钮网格形式展示内置主题预设，并提供自定义主题 HSL、不透明度、
标题栏渐变开关与实时预览。可被 ``InterfaceSettingTab`` 与欢迎向导主题页复用。
"""

from typing import Any, Dict

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QLabel,
    QSlider,
    QRadioButton,
    QButtonGroup,
)

from core.config.theme_config import (
    SYSTEM_PRESET_KEY,
    apply_hsl,
    built_in_presets,
    build_custom_config,
    config_from_preset_key,
    primary_color,
)
from core.i18n import _
from core.infrastructure.logger import log
from gui.fonts import body_font
from gui.styles import load_primary_color
from gui.widgets import SwitchWithLabel
from gui.utils.color_utils import lighten, darken


class ThemeSelector(QWidget):
    """可复用的主题选择器。

    以单选按钮网格展示内置预设、自定义选项以及系统主题色（Beta）选项，
    通过 ``theme_changed`` 信号通知外部当前主题配置变化。

    信号:
        theme_changed(dict): 主题配置发生变化时发射，参数为完整主题配置字典。

    属性:
        theme_config: 当前选中的主题配置字典。
    """

    theme_changed = pyqtSignal(dict)

    # 每行显示的单选按钮数量
    COLUMNS = 5
    # 自定义预设占位（name 在 _init_ui 中动态获取）
    CUSTOM_PRESET = {
        "key": "custom",
        "primary": "#1277DD",
        "background": "#E8F4FD",
    }
    # 系统主题色预设占位（颜色会随系统强调色动态更新）
    SYSTEM_PRESET = {
        "key": SYSTEM_PRESET_KEY,
        "primary": "#888888",
        "background": "#E8F4FD",
    }
    # 系统主题色自动检测间隔（毫秒）
    SYSTEM_THEME_UPDATE_INTERVAL = 2000

    def __init__(
        self,
        parent: QWidget = None,
        initial_config: Dict[str, Any] = None,
        show_title: bool = True,
    ):
        """初始化主题选择器。

        Args:
            parent: 父组件。
            initial_config: 初始主题配置，为 None 时使用默认配置。
            show_title: 是否显示"主题"分组标题。在设置页等已有标题的场景可设为 False。
        """
        super().__init__(parent)
        self._accent_color = load_primary_color()
        self._radio_buttons: Dict[str, QRadioButton] = {}
        self._theme_config = initial_config or config_from_preset_key("jingdianlan")
        self._show_title = show_title
        self._system_primary_color: str = "#888888"

        self._init_ui()
        self._init_system_theme_timer()
        self.set_theme_config(self._theme_config)

    # ----- 公共 API -----

    def get_theme_config(self) -> Dict[str, Any]:
        """返回当前选中的主题配置字典副本。"""
        return self._theme_config.copy()

    def set_theme_config(self, config: Dict[str, Any]) -> None:
        """设置主题选择器状态。

        Args:
            config: 完整主题配置字典。
        """
        self._theme_config = config.copy() if config else config_from_preset_key("jingdianlan")
        key = self._theme_config.get("key", "jingdianlan")

        radio = self._radio_buttons.get(key)
        if radio:
            radio.setChecked(True)

        is_custom = key == "custom"
        is_system = key == SYSTEM_PRESET_KEY
        self._set_custom_visible(is_custom)
        self._set_system_theme_active(is_system)

        custom = (self._theme_config.get("custom") or {})
        self.opacity_slider.blockSignals(True)
        self.gradient_switch.blockSignals(True)

        self.opacity_slider.setValue(self._theme_config.get("opacity", 255))
        self.gradient_switch.setChecked(self._theme_config.get("use_gradient", False))

        self.opacity_slider.blockSignals(False)
        self.gradient_switch.blockSignals(False)

        if is_custom and custom:
            self.hue_slider.blockSignals(True)
            self.saturation_slider.blockSignals(True)
            self.lightness_slider.blockSignals(True)

            self.hue_slider.setValue(custom.get("h", 210))
            self.saturation_slider.setValue(custom.get("s", 75))
            self.lightness_slider.setValue(custom.get("l", 55))

            self.hue_slider.blockSignals(False)
            self.saturation_slider.blockSignals(False)
            self.lightness_slider.blockSignals(False)
            self._update_custom_preview()
        else:
            self._update_preview_from_config()
            if is_system:
                self._refresh_system_theme_color()

    def set_accent_color(self, color: str) -> None:
        """更新强调色（用于选中边框等）。

        Args:
            color: 十六进制颜色字符串。
        """
        self._accent_color = color
        self._update_radio_styles()
        self._update_preview_from_config()

    # ----- UI 创建 -----

    def _init_ui(self) -> None:
        """创建主题选择器界面。"""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self._create_preset_radios(layout)
        self._create_custom_section(layout)
        self._create_opacity_slider(layout)
        self._create_gradient_switch(layout)
        self._create_preview(layout)

    def _create_preset_radios(self, parent_layout: QVBoxLayout) -> None:
        """创建主题预设单选按钮网格。"""
        if self._show_title:
            title = QLabel(_("settings.interface.theme_label"))
            title.setFont(body_font())
            title.setStyleSheet("color: #212121;")
            parent_layout.addWidget(title)

        self.button_group = QButtonGroup(self)
        self.button_group.setExclusive(True)

        grid = QGridLayout()
        grid.setSpacing(8)
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        grid.setColumnStretch(3, 1)
        grid.setColumnStretch(4, 1)

        all_presets = built_in_presets() + [self.CUSTOM_PRESET, self.SYSTEM_PRESET]
        for index, preset in enumerate(all_presets):
            row = index // self.COLUMNS
            col = index % self.COLUMNS

            key = preset["key"]
            # 系统主题色使用独立翻译键
            name_key = (
                "theme.preset.system_theme"
                if key == SYSTEM_PRESET_KEY
                else "theme.preset." + key
            )
            radio = QRadioButton(_(name_key))
            radio.setFont(body_font())
            radio.setProperty("preset_key", key)
            radio.setProperty("preset_color", preset["primary"])
            radio.setCursor(Qt.PointingHandCursor)
            radio.setStyleSheet(self._radio_style(preset["primary"], False))

            self.button_group.addButton(radio)
            self._radio_buttons[key] = radio
            grid.addWidget(radio, row, col)

        self.button_group.buttonClicked.connect(self._on_preset_clicked)
        parent_layout.addLayout(grid)

    def _create_custom_section(self, parent_layout: QVBoxLayout) -> None:
        """创建自定义主题调节区域。"""
        self.custom_theme_widget = QWidget()
        custom_layout = QVBoxLayout(self.custom_theme_widget)
        custom_layout.setSpacing(10)
        custom_layout.setContentsMargins(0, 0, 0, 0)

        # 色相
        self.hue_label, self.hue_slider, self.hue_value_label = self._create_slider(
            _("settings.interface.hue"), 0, 360
        )
        self.hue_slider.valueChanged.connect(self._on_custom_value_changed)
        custom_layout.addLayout(
            self._slider_layout(self.hue_label, self.hue_slider, self.hue_value_label)
        )

        # 饱和度
        self.saturation_label, self.saturation_slider, self.saturation_value_label = \
            self._create_slider(_("settings.interface.saturation"), 0, 100)
        self.saturation_slider.valueChanged.connect(self._on_custom_value_changed)
        custom_layout.addLayout(
            self._slider_layout(
                self.saturation_label,
                self.saturation_slider,
                self.saturation_value_label,
            )
        )

        # 亮度
        self.lightness_label, self.lightness_slider, self.lightness_value_label = \
            self._create_slider(_("settings.interface.lightness"), 0, 100)
        self.lightness_slider.valueChanged.connect(self._on_custom_value_changed)
        custom_layout.addLayout(
            self._slider_layout(
                self.lightness_label,
                self.lightness_slider,
                self.lightness_value_label,
            )
        )

        parent_layout.addWidget(self.custom_theme_widget)
        self.custom_theme_widget.setVisible(
            self._theme_config.get("key") == "custom"
        )

    def _create_opacity_slider(self, parent_layout: QVBoxLayout) -> None:
        """创建标题栏不透明度滑块。"""
        self.opacity_label, self.opacity_slider, self.opacity_value_label = \
            self._create_slider(_("settings.interface.opacity"), 0, 255)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        parent_layout.addLayout(
            self._slider_layout(
                self.opacity_label,
                self.opacity_slider,
                self.opacity_value_label,
            )
        )

    def _create_gradient_switch(self, parent_layout: QVBoxLayout) -> None:
        """创建标题栏渐变开关。"""
        self.gradient_switch = SwitchWithLabel(_("settings.interface.use_gradient"), checked=False)
        self.gradient_switch.toggled.connect(self._on_gradient_changed)
        parent_layout.addWidget(self.gradient_switch)

    def _create_preview(self, parent_layout: QVBoxLayout) -> None:
        """创建标题栏预览条。"""
        preview_row = QHBoxLayout()
        preview_label = QLabel(_("settings.interface.preview"))
        preview_label.setFont(body_font())
        preview_row.addWidget(preview_label)

        self.theme_preview = QLabel()
        self.theme_preview.setFixedHeight(40)
        self.theme_preview.setStyleSheet("""
            QLabel {
                background: #E0E0E0;
                border-radius: 6px;
                border: 1px solid #CCCCCC;
            }
        """)
        preview_row.addWidget(self.theme_preview, 1)
        parent_layout.addLayout(preview_row)

    def _create_slider(self, label_text: str, min_value: int, max_value: int):
        """创建标签、滑块和数值标签三元组。

        Args:
            label_text: 标签文本。
            min_value: 滑块最小值。
            max_value: 滑块最大值。

        Returns:
            (QLabel, QSlider, QLabel) 元组。
        """
        label = QLabel(label_text)
        label.setFont(body_font())
        label.setFixedWidth(60)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_value, max_value)
        slider.setFont(body_font())

        value_label = QLabel(str(min_value))
        value_label.setFont(body_font())
        value_label.setFixedWidth(40)
        value_label.setAlignment(Qt.AlignCenter)

        slider.valueChanged.connect(lambda v: value_label.setText(str(v)))

        return label, slider, value_label

    def _slider_layout(self, label: QLabel, slider: QSlider, value_label: QLabel) -> QHBoxLayout:
        """返回滑块行布局。"""
        layout = QHBoxLayout()
        layout.setSpacing(8)
        layout.addWidget(label)
        layout.addWidget(slider, 1)
        layout.addWidget(value_label)
        return layout

    # ----- 回调 -----

    def _on_preset_clicked(self, radio: QRadioButton) -> None:
        """点击主题预设单选按钮。"""
        key = radio.property("preset_key")
        self._theme_config = config_from_preset_key(key)

        is_custom = key == "custom"
        is_system = key == SYSTEM_PRESET_KEY
        self._set_custom_visible(is_custom)
        self._set_system_theme_active(is_system)
        self._update_radio_styles()

        if is_custom:
            custom = (self._theme_config.get("custom") or {})
            self.hue_slider.blockSignals(True)
            self.saturation_slider.blockSignals(True)
            self.lightness_slider.blockSignals(True)

            self.hue_slider.setValue(custom.get("h", 210))
            self.saturation_slider.setValue(custom.get("s", 75))
            self.lightness_slider.setValue(custom.get("l", 55))

            self.hue_slider.blockSignals(False)
            self.saturation_slider.blockSignals(False)
            self.lightness_slider.blockSignals(False)
            self._update_custom_preview()
        elif is_system:
            self._refresh_system_theme_color()
            self._update_preview_from_config()
        else:
            self._update_preview_from_config()

        self.theme_changed.emit(self._theme_config.copy())

    def _on_custom_value_changed(self) -> None:
        """自定义滑块变化。"""
        if self._theme_config.get("key") != "custom":
            return

        h = self.hue_slider.value()
        s = self.saturation_slider.value()
        l = self.lightness_slider.value()
        opacity = self.opacity_slider.value()
        use_gradient = self.gradient_switch.isChecked()

        base = (self._theme_config.get("custom") or {}).get("base", "#1277DD")
        self._theme_config = build_custom_config(base, h, s, l, opacity, use_gradient)
        self._update_custom_preview()
        self.theme_changed.emit(self._theme_config.copy())

    def _on_opacity_changed(self) -> None:
        """不透明度滑块变化。"""
        self._theme_config["opacity"] = self.opacity_slider.value()
        self._update_preview_from_config()
        self.theme_changed.emit(self._theme_config.copy())

    def _on_gradient_changed(self, checked: bool) -> None:
        """渐变开关变化。"""
        if self._theme_config.get("key") == "custom":
            self._on_custom_value_changed()
            return
        self._theme_config["use_gradient"] = checked
        self._update_preview_from_config()
        self.theme_changed.emit(self._theme_config.copy())

    # ----- 内部方法 -----

    def _set_custom_visible(self, visible: bool) -> None:
        """设置自定义区域可见性。"""
        self.custom_theme_widget.setVisible(visible)

    def _init_system_theme_timer(self) -> None:
        """初始化系统主题色自动检测定时器。"""
        self._system_theme_timer = QTimer(self)
        self._system_theme_timer.setInterval(self.SYSTEM_THEME_UPDATE_INTERVAL)
        self._system_theme_timer.timeout.connect(self._on_system_theme_timer_timeout)

    def _set_system_theme_active(self, active: bool) -> None:
        """启用或停止系统主题色自动检测。

        Args:
            active: 是否激活自动检测。
        """
        if active:
            if not self._system_theme_timer.isActive():
                self._system_theme_timer.start()
        else:
            if self._system_theme_timer.isActive():
                self._system_theme_timer.stop()

    def _refresh_system_theme_color(self) -> None:
        """立即读取系统主题色并更新当前配置。"""
        try:
            from core.ui.system_theme_reader import get_system_theme_config
            config = get_system_theme_config()
            if config is None:
                return
            self._theme_config = config
            self._system_primary_color = config.get("primary", "#888888")
            self._update_system_radio_color()
        except Exception as e:
            log("WARNING", f"读取系统主题色失败: {e}")

    def _on_system_theme_timer_timeout(self) -> None:
        """定时检测系统主题色是否变化，变化时自动更新。"""
        if self._theme_config.get("key") != SYSTEM_PRESET_KEY:
            self._set_system_theme_active(False)
            return

        try:
            from core.ui.system_theme_reader import get_system_accent_color
            current_color = get_system_accent_color()
            if not current_color:
                return
            if current_color.upper() == self._system_primary_color.upper():
                return

            self._refresh_system_theme_color()
            self._update_preview_from_config()
            self.theme_changed.emit(self._theme_config.copy())
        except Exception as e:
            log("WARNING", f"自动更新系统主题色失败: {e}")

    def _update_system_radio_color(self) -> None:
        """更新系统主题色单选按钮的指示器颜色。"""
        radio = self._radio_buttons.get(SYSTEM_PRESET_KEY)
        if radio is None:
            return
        radio.setProperty("preset_color", self._system_primary_color)
        radio.setStyleSheet(
            self._radio_style(self._system_primary_color, radio.isChecked())
        )

    def _radio_style(self, color: str, checked: bool) -> str:
        """生成单选按钮样式表。"""
        border_color = self._accent_color if checked else "transparent"
        text_color = self._accent_color if checked else "#333333"
        return f"""
            QRadioButton {{
                color: {text_color};
                spacing: 8px;
                outline: none;
                font-family: "{body_font().family() or "HarmonyOS Sans"}";
            }}
            QRadioButton::indicator {{
                width: 16px;
                height: 16px;
                border-radius: 4px;
                background: {color};
                border: 2px solid {border_color};
            }}
            QRadioButton::indicator:hover {{
                border: 2px solid {self._accent_color};
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid {self._accent_color};
            }}
        """

    def _update_radio_styles(self) -> None:
        """更新所有单选按钮选中状态样式。"""
        for key, radio in self._radio_buttons.items():
            color = radio.property("preset_color") or "#1277DD"
            radio.setStyleSheet(self._radio_style(color, radio.isChecked()))

    def _update_preview_from_config(self) -> None:
        """根据当前配置更新预览条。"""
        primary = primary_color(self._theme_config)
        use_gradient = self._theme_config.get("use_gradient", False)

        if use_gradient:
            h, s, l = self._hex_to_hsl(primary)
            start = darken(primary, 20) if l > 50 else lighten(primary, 20)
            end = primary
            self.theme_preview.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {start}, stop:1 {end});
                    border-radius: 6px;
                    border: 1px solid #CCCCCC;
                }}
            """)
        else:
            self.theme_preview.setStyleSheet(f"""
                QLabel {{
                    background: {primary};
                    border-radius: 6px;
                    border: 1px solid #CCCCCC;
                }}
            """)

    def _update_custom_preview(self) -> None:
        """根据当前自定义滑块更新预览。"""
        h = self.hue_slider.value()
        s = self.saturation_slider.value()
        l = self.lightness_slider.value()
        use_gradient = self.gradient_switch.isChecked()

        base = (self._theme_config.get("custom") or {}).get("base", "#1277DD")
        primary = apply_hsl(base, h, s, l)

        if use_gradient:
            start = apply_hsl(primary, None, None, max(0, l - 20))
            end = primary
            self.theme_preview.setStyleSheet(f"""
                QLabel {{
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                        stop:0 {start}, stop:1 {end});
                    border-radius: 6px;
                    border: 1px solid #CCCCCC;
                }}
            """)
        else:
            self.theme_preview.setStyleSheet(f"""
                QLabel {{
                    background: {primary};
                    border-radius: 6px;
                    border: 1px solid #CCCCCC;
                }}
            """)

    @staticmethod
    def _hex_to_hsl(hex_color: str):
        """辅助：十六进制转 HSL。"""
        try:
            from core.config.theme_config import hex_to_hsl
            return hex_to_hsl(hex_color)
        except Exception:
            return (210, 75, 55)
