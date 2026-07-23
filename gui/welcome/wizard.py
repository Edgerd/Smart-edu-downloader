# -*- coding: utf-8 -*-
"""新手引导向导主窗口。

管理 9 屏欢迎引导页面的堆叠切换、淡入淡出动画以及设置收集与持久化。
"""

from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QStackedWidget,
    QWidget,
    QGraphicsOpacityEffect,
    QFrame,
    QLabel,
    QPushButton,
)
from gui.fonts import small_font

from core.config.settings_manager import get_settings_manager
from core.config.theme_config import primary_color, background_color, get_theme_config
from core.i18n import _
from core.infrastructure.logger import log
from gui.styles import load_primary_color, load_background_color
from gui.welcome.pages.welcome_page import WelcomePage
from gui.welcome.pages.license_page import LicensePage
from gui.welcome.pages.basic_settings_page import BasicSettingsPage
from gui.welcome.pages.token_page import TokenPage
from gui.welcome.pages.theme_page import ThemePage
from gui.welcome.pages.system_page import SystemPage
from gui.welcome.pages.tutorial_page import TutorialPage
from gui.welcome.pages.finish_page import FinishPage
from gui.welcome.pages.donation_page import DonationPage


class WelcomeWizard(QDialog):
    """新手引导向导主窗口。

    以模态对话框形式展示 10 屏引导流程，支持页面间淡入淡出切换，
    完成时将所有配置批量写入设置文件。最后一屏为赞助页面。

    属性:
        page_count: 引导页面总数。
        current_index: 当前显示的页面索引。

    页面索引定义:
        0 - 欢迎页
        1 - 许可条款页
        2 - 基本设置页
        3 - Access Token 页
        4 - 主题设置页
        5 - 系统快捷方式页
        6 - 教程页 1
        7 - 教程页 2
        8 - 完成页
        9 - 赞助页
    """

    # 窗口尺寸
    WINDOW_WIDTH = 860
    WINDOW_HEIGHT = 600
    # 右下角付费提示横幅尺寸
    BANNER_WIDTH = 360
    BANNER_HEIGHT = 78
    # 单次淡入/淡出动画时长（毫秒）
    FADE_DURATION = 250

    PAGE_WELCOME = 0
    PAGE_LICENSE = 1
    PAGE_BASIC = 2
    PAGE_TOKEN = 3
    PAGE_THEME = 4
    PAGE_SYSTEM = 5
    PAGE_TUTORIAL_1 = 6
    PAGE_TUTORIAL_2 = 7
    PAGE_FINISH = 8
    PAGE_DONATION = 9

    def __init__(self, parent: Optional[QWidget] = None, is_first_run: bool = True):
        """初始化欢迎向导窗口。

        Args:
            parent: 父窗口。
            is_first_run: 是否为首次运行模式。非首次运行模式不会修改
                ``first_run`` 设置项，并从当前设置加载已有配置作为默认值。
        """
        super().__init__(parent)
        self._is_first_run = is_first_run
        self._settings = get_settings_manager().get_all() if not is_first_run else {}
        theme_config = get_theme_config(self._settings)
        self._accent_color = primary_color(theme_config)
        self._background_color = background_color(theme_config)
        self._current_index = 0
        self._is_animating = False
        self._target_index = 0

        self._init_ui()
        self._init_pages()
        self._connect_buttons()
        self._apply_theme_colors()
        self._load_existing_settings()

    # ----- 公共 API -----

    def set_page(self, index: int) -> None:
        """切换到指定页面，并播放淡入淡出动画。

        Args:
            index: 目标页面索引。
        """
        if index < 0 or index >= len(self._pages):
            return
        if index == self._current_index:
            return
        if self._is_animating:
            return

        self._target_index = index
        self._is_animating = True
        self._fade_out()

    def next_page(self) -> None:
        """前进到下一页。"""
        self.set_page(self._current_index + 1)

    def prev_page(self) -> None:
        """返回到上一页。"""
        self.set_page(self._current_index - 1)

    def finish(self) -> None:
        """完成引导，收集配置并保存到设置文件。"""
        try:
            settings: Dict[str, Any] = {}

            basic_page = self._pages[self.PAGE_BASIC]
            settings["download_dir"] = basic_page.get_download_dir()
            settings["ask_download_dir"] = basic_page.get_ask_download_dir()

            token_page = self._pages[self.PAGE_TOKEN]
            raw_token = token_page.get_access_token().strip()
            if raw_token:
                from core.network.token_crypto import encrypt_token
                settings["access_token"] = encrypt_token(raw_token)
            else:
                settings["access_token"] = ""

            theme_page = self._pages[self.PAGE_THEME]
            settings["theme_color"] = theme_page.get_theme_config()

            system_page = self._pages[self.PAGE_SYSTEM]
            shortcuts = system_page.get_shortcuts()
            settings.update(shortcuts)

            if self._is_first_run:
                settings["first_run"] = True

            get_settings_manager().update(settings)

            # 根据用户选择实际创建/删除系统快捷方式
            from core.infrastructure.shortcut_manager import create_shortcuts
            create_shortcuts(
                create_desktop=shortcuts.get("create_desktop_shortcut", False),
                create_start_menu=shortcuts.get("create_start_menu_shortcut", False),
            )

            self.accept()
        except Exception as e:
            log("ERROR", f"完成新手引导时失败: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(
                self,
                _("common.error"),
                _("welcome_onboarding.common.save_failed"),
            )

    # ----- UI 初始化 -----

    def _init_ui(self) -> None:
        """初始化向导窗口外观与主布局。"""
        self.setWindowTitle(_("welcome_onboarding.welcome.app_name"))
        self.setWindowFlags(Qt.Dialog | Qt.MSWindowsFixedSizeDialogHint)
        self.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        self.setModal(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # 主容器：stack + 右下角横幅
        main_widget = QWidget()
        main_widget.setStyleSheet("background: transparent; border: none;")
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background: transparent; border: none;")
        self.stack.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        main_layout.addWidget(self.stack)

        layout.addWidget(main_widget)

        # 右下角持久化横幅
        self._payment_banner = self._create_payment_banner()
        self._payment_banner.setParent(self)
        self._payment_banner.move(
            self.WINDOW_WIDTH - self.BANNER_WIDTH - 20,
            self.WINDOW_HEIGHT - self.BANNER_HEIGHT - 20
        )
        self._payment_banner.show()
        self._payment_banner.raise_()

        self._opacity_effect: Optional[QGraphicsOpacityEffect] = None
        self._fade_animation: Optional[QPropertyAnimation] = None

    def _init_pages(self) -> None:
        """创建所有引导页面并加入堆叠容器。"""
        self._pages: List[QWidget] = [
            WelcomePage(self),
            LicensePage(self),
            BasicSettingsPage(self),
            TokenPage(self),
            ThemePage(self),
            SystemPage(self),
            TutorialPage(1, self),
            TutorialPage(2, self),
            FinishPage(self),
            DonationPage(self),
        ]

        for page in self._pages:
            page.setStyleSheet("background: transparent;")
            self.stack.addWidget(page)

        self._current_index = 0
        self.stack.setCurrentIndex(self._current_index)

    def _connect_buttons(self) -> None:
        """连接各页面的导航按钮到向导控制方法。"""
        for page in self._pages:
            if hasattr(page, "next_btn") and page.next_btn is not None:
                page.next_btn.clicked.connect(self.next_page)
            if hasattr(page, "prev_btn") and page.prev_btn is not None:
                page.prev_btn.clicked.connect(self.prev_page)
            if hasattr(page, "finish_btn") and page.finish_btn is not None:
                page.finish_btn.clicked.connect(self.finish)

        welcome_page = self._pages[self.PAGE_WELCOME]
        welcome_page.language_changed.connect(self._on_language_changed)
        welcome_page.import_config_clicked.connect(self._on_import_config)

        theme_page = self._pages[self.PAGE_THEME]
        theme_page.theme_selector.theme_changed.connect(self._on_theme_changed)

    def _apply_theme_colors(self) -> None:
        """将当前主题色与背景色应用到窗口及所有页面。"""
        self.setStyleSheet(f"QDialog {{ background: {self._background_color}; }}")
        for page in self._pages:
            if hasattr(page, "set_accent_color"):
                page.set_accent_color(self._accent_color)
        # 更新横幅链接颜色
        if hasattr(self, "_payment_banner") and self._payment_banner:
            text_label = self._payment_banner.findChild(QLabel)
            if text_label:
                text_label.setText(self._build_banner_text())

    def _create_payment_banner(self) -> QFrame:
        """创建右下角常驻付费提示横幅。"""
        banner = QFrame()
        banner.setFixedSize(self.BANNER_WIDTH, self.BANNER_HEIGHT)
        banner.setStyleSheet("""
            QFrame {
                background: #FFF4CE;
                border-radius: 8px;
                border: none;
            }
        """)
        layout = QHBoxLayout(banner)
        layout.setSpacing(8)
        layout.setContentsMargins(10, 6, 6, 6)

        text_label = QLabel()
        text_label.setFont(small_font())
        text_label.setWordWrap(True)
        text_label.setTextFormat(Qt.RichText)
        text_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        text_label.setOpenExternalLinks(True)
        text_label.setStyleSheet("color: #6B4A00;")
        text_label.setText(self._build_banner_text())
        layout.addWidget(text_label, 1)

        close_btn = QPushButton("×")
        close_btn.setFont(small_font())
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #9D5D00;
                border: none;
                font-weight: bold;
                font-size: 14px;
                outline: none;
            }
            QPushButton:hover {
                background: #F9D99A;
                border-radius: 10px;
            }
            QPushButton:focus {
                outline: none;
            }
        """)
        close_btn.clicked.connect(lambda: banner.hide())
        layout.addWidget(close_btn, alignment=Qt.AlignTop)

        return banner

    def _build_banner_text(self) -> str:
        """组装付费提示横幅富文本内容。

        Returns:
            包含 Bilibili 超链接的富文本字符串。
        """
        link_text = _("welcome_onboarding.license.bilibili_link")
        link_html = (
            f'<a href="https://space.bilibili.com/3537111380658360" '
            f'style="color: {self._accent_color}; text-decoration: none;">'
            f"{link_text}</a>"
        )
        content = _("welcome_onboarding.license.anti_fraud_content")
        if "{link}" in content:
            return content.replace("{link}", link_html)
        return f"{content}{link_html}。"

    # ----- 动画 -----

    def _fade_out(self) -> None:
        """播放当前页面淡出动画。"""
        current_page = self.stack.widget(self._current_index)
        if current_page is None:
            self._on_fade_out_finished()
            return
        self._opacity_effect = QGraphicsOpacityEffect(current_page)
        self._opacity_effect.setOpacity(1.0)
        current_page.setGraphicsEffect(self._opacity_effect)

        self._fade_animation = QPropertyAnimation(
            self._opacity_effect, b"opacity", self
        )
        self._fade_animation.setDuration(self.FADE_DURATION)
        self._fade_animation.setStartValue(1.0)
        self._fade_animation.setEndValue(0.0)
        self._fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._fade_animation.finished.connect(self._on_fade_out_finished)
        self._fade_animation.start()

    def _on_fade_out_finished(self) -> None:
        """淡出完成后切换页面并开始淡入。"""
        old_page = self.stack.widget(self._current_index)
        if old_page is not None:
            old_page.setGraphicsEffect(None)
        self._current_index = self._target_index
        self.stack.setCurrentIndex(self._current_index)
        self._fade_in()

    def _fade_in(self) -> None:
        """播放新页面淡入动画。"""
        current_page = self.stack.widget(self._current_index)
        if current_page is None:
            self._on_fade_in_finished()
            return
        self._opacity_effect = QGraphicsOpacityEffect(current_page)
        self._opacity_effect.setOpacity(0.0)
        current_page.setGraphicsEffect(self._opacity_effect)

        self._fade_animation = QPropertyAnimation(
            self._opacity_effect, b"opacity", self
        )
        self._fade_animation.setDuration(self.FADE_DURATION)
        self._fade_animation.setStartValue(0.0)
        self._fade_animation.setEndValue(1.0)
        self._fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self._fade_animation.finished.connect(self._on_fade_in_finished)
        self._fade_animation.start()

    def _on_fade_in_finished(self) -> None:
        """淡入完成后允许下一次切换并清理效果。"""
        current_page = self.stack.widget(self._current_index)
        if current_page is not None:
            current_page.setGraphicsEffect(None)
        self._opacity_effect = None
        self._fade_animation = None
        self._is_animating = False

    # ----- 事件回调 -----

    def _on_theme_changed(self, config: Dict[str, Any]) -> None:
        """主题选择器配置变化时同步刷新全局主题色。

        Args:
            config: 新的主题配置字典。
        """
        self._accent_color = primary_color(config)
        self._background_color = background_color(config)
        self._apply_theme_colors()

    def _on_language_changed(self) -> None:
        """语言切换后刷新窗口标题与各页面文本。"""
        self.setWindowTitle(_("welcome_onboarding.welcome.app_name"))
        self.reload_page_texts()

    def _on_import_config(self) -> None:
        """数据迁移导入成功后重新加载当前设置并刷新向导显示。"""
        self._settings = get_settings_manager().get_all()
        theme_config = get_theme_config(self._settings)
        self._accent_color = primary_color(theme_config)
        self._background_color = background_color(theme_config)
        self._apply_theme_colors()
        self._load_existing_settings()

    def _load_existing_settings(self) -> None:
        """将当前设置加载到各页面作为默认值（非首次运行模式）。"""
        if not self._settings:
            return
        if hasattr(self._pages[self.PAGE_BASIC], "set_initial_values"):
            self._pages[self.PAGE_BASIC].set_initial_values(self._settings)
        if hasattr(self._pages[self.PAGE_TOKEN], "set_initial_values"):
            self._pages[self.PAGE_TOKEN].set_initial_values(self._settings)
        if hasattr(self._pages[self.PAGE_THEME], "set_initial_values"):
            self._pages[self.PAGE_THEME].set_initial_values(self._settings)
        if hasattr(self._pages[self.PAGE_SYSTEM], "set_initial_values"):
            self._pages[self.PAGE_SYSTEM].set_initial_values(self._settings)

    def reload_page_texts(self) -> None:
        """重新加载所有页面的翻译文本。"""
        for page in self._pages:
            if hasattr(page, "reload_texts"):
                page.reload_texts()
