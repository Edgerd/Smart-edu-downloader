# -*- coding: utf-8 -*-
"""用户协议对话框。

使用 qfluentwidgets.Dialog 展示 ``resources/docs/user_agreement.md`` 内容，
提供生效日期与关闭按钮，遵循微软流畅设计规范。
"""

import os
import sys
from typing import Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTextBrowser, QVBoxLayout, QWidget

from core.i18n import _
from core.infrastructure.logger import log
from core.infrastructure.path_resolver import get_project_root
from gui.fonts import body_font, small_font, title_font
from gui.styles import load_primary_color

# 静默导入 qfluentwidgets，避免其 Pro 提示输出到控制台
_old_stdout = sys.stdout
sys.stdout = __import__('io').StringIO()
try:
    from qfluentwidgets import Dialog
finally:
    sys.stdout = _old_stdout


class UserAgreementDialog(Dialog):
    """用户协议对话框。

    自动从 ``resources/docs/user_agreement.md`` 读取内容并渲染展示，
    使用 qfluentwidgets 的 Dialog 保持与程序其他弹窗风格一致。

    属性:
        effective_date: 用户协议生效日期字符串。
    """

    def __init__(self, accent_color: str = "", parent: Optional[QWidget] = None):
        """初始化用户协议对话框。

        Args:
            accent_color: 主题色十六进制字符串，为空时自动读取当前主题色。
            parent: 父窗口。
        """
        self._accent_color = accent_color or load_primary_color()
        self.effective_date = "2026-07-11"

        title = _("welcome_onboarding.user_agreement.title")
        content = _("welcome_onboarding.user_agreement.effective_date")
        super().__init__(title, f"{content}：{self.effective_date}", parent)

        self._init_ui()
        self._load_content()

    def _init_ui(self) -> None:
        """调整 Dialog 默认布局，将文本标签替换为可滚动 Markdown 浏览器。"""
        self.setFixedSize(660, 520)
        self.setWindowTitle(_("welcome_onboarding.user_agreement.title"))

        # 隐藏默认内容标签，使用 QTextBrowser 展示 Markdown
        self.contentLabel.hide()

        self.text_browser = QTextBrowser()
        self.text_browser.setFont(body_font())
        self.text_browser.setStyleSheet("""
            QTextBrowser {
                background: #F8F9FA;
                border: none;
                border-radius: 6px;
                padding: 10px;
                color: #333333;
                outline: none;
            }
            QTextBrowser:focus {
                outline: none;
            }
        """)

        # 将 QTextBrowser 插入到标题与按钮之间的文本区域
        self.textLayout.addWidget(self.text_browser)

        # 调整按钮文本
        self.yesButton.setText(_("welcome_onboarding.user_agreement.close"))
        self.hideCancelButton()

    def _load_content(self) -> None:
        """加载并显示用户协议 Markdown 内容。"""
        file_path = os.path.join(get_project_root(), "resources", "docs", "user_agreement.md")
        content = ""
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception as e:
                log("WARNING", f"读取用户协议文件失败: {e}")
                content = ""
        if not content:
            content = _("welcome_onboarding.user_agreement.title")

        if hasattr(self.text_browser, "setMarkdown"):
            self.text_browser.setMarkdown(content)
        else:
            self.text_browser.setPlainText(content)
