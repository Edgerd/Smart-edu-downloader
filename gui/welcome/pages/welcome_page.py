# -*- coding: utf-8 -*-
"""欢迎向导首页。

居中展示程序图标、名称、主题色进入箭头，底部提供版本号、
数据迁移与语言设置入口。
"""

import os
from typing import Optional

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QMouseEvent
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFileDialog,
    QDialog,
    QPushButton,
    QMessageBox,
    QFrame,
)

from gui.utils.color_utils import darken

from core.i18n import _, get_available_languages, set_language, get_current_locale
from core.infrastructure.path_resolver import get_project_root
from core.settings.export import SettingsExporter
from core.config.settings_manager import get_settings_manager, set_setting
from gui.fonts import large_font, body_font, small_font
from gui.styles import load_primary_color
from gui.components.circle_nav_button import CircleNavButton
from gui.widgets import NoWheelComboBox
from gui.welcome.pages.base_page import BaseWelcomePage


class _LanguageSelectorDialog(QDialog):
    """语言选择弹窗。

    无边框卡片式弹窗，显示可用语言列表，确认后切换当前语言并保存到设置。

    属性:
        selected_locale: 用户选中的语言代码。
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化语言选择弹窗。"""
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(340, 180)
        self.selected_locale = get_current_locale()
        self._drag_pos = None
        self._init_ui()

    def _init_ui(self) -> None:
        """创建弹窗界面。"""
        self.setStyleSheet("QDialog { background: #FFFFFF; }")
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #FFFFFF;
                border-radius: 8px;
                border: none;
            }
        """)
        card.setFixedSize(self.width(), self.height())
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(12)
        card_layout.setContentsMargins(20, 20, 20, 20)
        layout.addWidget(card)

        label = QLabel(_("settings.interface.language_label"))
        label.setFont(body_font())
        label.setStyleSheet("color: #212121;")
        card_layout.addWidget(label)

        self.combo = NoWheelComboBox()
        self.combo.setFont(body_font())
        current_index = 0
        for index, lang in enumerate(get_available_languages()):
            self.combo.addItem(lang["name"], lang["code"])
            if lang["code"] == self.selected_locale:
                current_index = index
        self.combo.setCurrentIndex(current_index)
        card_layout.addWidget(self.combo)

        btn = QPushButton(_("common.ok"))
        btn.setFont(body_font())
        self._ok_btn = btn
        accent = load_primary_color()
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {accent};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                outline: none;
            }}
            QPushButton:hover {{
                background: {darken(accent, 15)};
            }}
            QPushButton:focus {{
                outline: none;
            }}
        """)
        btn.clicked.connect(self._on_confirm)
        card_layout.addWidget(btn, alignment=Qt.AlignRight)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """记录拖拽起始位置。"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """拖拽移动无边框弹窗。"""
        if self._drag_pos is not None and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """释放拖拽。"""
        self._drag_pos = None
        super().mouseReleaseEvent(event)

    def _on_confirm(self) -> None:
        """确认语言选择。"""
        code = self.combo.currentData()
        if code:
            self.selected_locale = code
            set_language(code)
            set_setting("language", code)
        self.accept()


class WelcomePage(BaseWelcomePage):
    """欢迎页。

    负责展示程序图标、名称、版本信息以及数据迁移/语言设置入口。

    信号:
        import_config_clicked(): 用户点击数据迁移按钮时发射。
        language_changed(): 用户更改语言时发射。
    """

    import_config_clicked = pyqtSignal()
    language_changed = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        """初始化欢迎页。"""
        super().__init__(parent)
        self._create_content()

    def _create_title(self) -> QLabel:
        """欢迎页标题为程序名。"""
        title = QLabel(_("welcome_onboarding.welcome.app_name"))
        title.setFont(large_font())
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #212121;")
        return title

    def _create_subtitle(self) -> QLabel:
        """欢迎页副标题为空（首页不使用副标题）。"""
        subtitle = QLabel("")
        subtitle.setFont(body_font())
        subtitle.hide()
        return subtitle

    def _create_content(self) -> None:
        """创建欢迎页内容。"""
        self.title_label.setText(_("welcome_onboarding.welcome.app_name"))

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(20)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setAlignment(Qt.AlignCenter)

        # 图标
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        icon_path = os.path.join(get_project_root(), "resources", "logo", "logo_48x48.ico")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            icon_label.setPixmap(pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        icon_label.setMinimumHeight(110)
        content_layout.addWidget(icon_label)

        # 主题色下一步箭头
        self.next_btn = CircleNavButton(
            icon_path=os.path.join("resources", "images", "welcome", "arrow_r.svg"),
            button_style=CircleNavButton.STYLE_ACCENT,
            tooltip=_("welcome_onboarding.welcome.next_tip"),
            parent=self,
        )
        self.next_btn.setAccentColor(self._accent_color)
        content_layout.addWidget(self.next_btn, 0, Qt.AlignCenter)

        # 底部版本号与操作按钮
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        from core.infrastructure.version import VERSION
        version_label = QLabel(f"{_('welcome_onboarding.welcome.version')} {VERSION}")
        version_label.setFont(small_font())
        version_label.setStyleSheet("color: #999999;")
        bottom_layout.addWidget(version_label)

        bottom_layout.addStretch()

        self.import_btn = QPushButton(_("welcome_onboarding.welcome.data_migration"))
        self.import_btn.setFont(body_font())
        self.import_btn.setCursor(Qt.PointingHandCursor)
        self.import_btn.setStyleSheet(self._link_button_style())
        self.import_btn.clicked.connect(self._on_import_config)
        bottom_layout.addWidget(self.import_btn)

        self.language_btn = QPushButton(_("welcome_onboarding.welcome.language_settings"))
        self.language_btn.setFont(body_font())
        self.language_btn.setCursor(Qt.PointingHandCursor)
        self.language_btn.setStyleSheet(self._link_button_style())
        self.language_btn.clicked.connect(self._on_language_settings)
        bottom_layout.addWidget(self.language_btn)

        content_layout.addLayout(bottom_layout)
        self.add_centered_content(content_widget)

    def _on_import_config(self) -> None:
        """点击数据迁移按钮：选择配置文件并导入。"""
        file_path, _selected_filter = QFileDialog.getOpenFileName(
            self,
            _("settings.common.import_dialog_title"),
            "",
            _("settings.common.json_filter"),
        )
        if not file_path:
            return
        settings_manager = get_settings_manager()
        settings = settings_manager.get_all()
        success = SettingsExporter.import_config(file_path, settings)
        if success:
            settings_manager.update(settings)
            self.import_config_clicked.emit()
            QMessageBox.information(
                self,
                _("common.success"),
                _("settings.common.import_success"),
            )
        else:
            QMessageBox.warning(
                self,
                _("common.error"),
                _("settings.common.import_failed"),
            )

    def _on_language_settings(self) -> None:
        """点击语言设置按钮：弹出语言选择弹窗。"""
        dialog = _LanguageSelectorDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.language_changed.emit()

    def _link_button_style(self) -> str:
        """返回底部链接按钮的样式表。"""
        return f"""
            QPushButton {{
                background: transparent;
                color: {self._accent_color};
                border: none;
                padding: 4px 8px;
                outline: none;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
            QPushButton:focus {{
                outline: none;
            }}
        """

    def set_accent_color(self, color: str) -> None:
        """更新页面主题色。

        Args:
            color: 新的主题色十六进制字符串。
        """
        super().set_accent_color(color)
        if hasattr(self, "next_btn") and self.next_btn:
            self.next_btn.setAccentColor(color)
        if hasattr(self, "import_btn") and self.import_btn:
            self.import_btn.setStyleSheet(self._link_button_style())
        if hasattr(self, "language_btn") and self.language_btn:
            self.language_btn.setStyleSheet(self._link_button_style())

    def reload_texts(self) -> None:
        """重新加载页面翻译文本。"""
        self.title_label.setText(_("welcome_onboarding.welcome.app_name"))
        if hasattr(self, "import_btn") and self.import_btn:
            self.import_btn.setText(_("welcome_onboarding.welcome.data_migration"))
        if hasattr(self, "language_btn") and self.language_btn:
            self.language_btn.setText(_("welcome_onboarding.welcome.language_settings"))
