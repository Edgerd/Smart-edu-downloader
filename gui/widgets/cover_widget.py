# -*- coding: utf-8 -*-
"""
封面显示控件
用于在主页和资源库页面展示教材封面图片。
"""
from core.i18n import _

import os
import threading
from typing import Optional

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QSize, pyqtSlot, QMetaObject, Q_ARG
from PyQt5.QtGui import QPixmap, QPainter, QPainterPath
from PyQt5 import sip

from gui.fonts import body_font
from gui.styles import load_primary_color, load_background_color


class CoverWidget(QFrame):
    """教材封面显示控件

    支持加载本地封面图片、异步下载封面、圆角边框、加载动画、占位符。
    固定尺寸：160x220。
    """

    COVER_WIDTH = 160
    COVER_HEIGHT = 220
    COVER_RADIUS = 4

    def __init__(self, parent=None):
        super().__init__(parent)
        self._content_id = None
        self._cover_path = None
        self._accent_color = load_primary_color()
        self._background_color = load_background_color()
        self._download_thread = None

        self._init_ui()

    def _init_ui(self):
        """初始化UI"""
        self.setFixedSize(self.COVER_WIDTH, self.COVER_HEIGHT)
        self._apply_rounded_border(self._background_color)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 图片标签
        self.cover_label = QLabel()
        self.cover_label.setAlignment(Qt.AlignCenter)
        self.cover_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.cover_label.setMinimumSize(
            self.COVER_WIDTH - self.COVER_RADIUS * 2,
            self.COVER_HEIGHT - self.COVER_RADIUS * 2
        )
        self.cover_label.setScaledContents(False)
        layout.addWidget(self.cover_label)

        # 占位符标签
        self.placeholder_label = QLabel()
        self.placeholder_label.setAlignment(Qt.AlignCenter)
        self.placeholder_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.placeholder_label.setFont(body_font())
        self.placeholder_label.setStyleSheet("""
            color: #999;
            font-size: 9pt;
        """)
        self.placeholder_label.setWordWrap(True)
        layout.addWidget(self.placeholder_label)

        self._show_placeholder()

    def _apply_rounded_border(self, background: str):
        """应用圆角背景样式（无边框）

        Args:
            background: 背景色，与页面主题背景保持一致
        """
        self.setStyleSheet(f"""
            QFrame {{
                background: {background};
                border: none;
                border-radius: {self.COVER_RADIUS}px;
            }}
        """)

    @pyqtSlot()
    def _show_placeholder(self):
        """显示占位符（书籍图标 + 封面文字）"""
        self.cover_label.hide()
        self.placeholder_label.show()

        # 使用 SVG 书籍图标或文本图标
        icon_pixmap = self._create_book_icon()
        if icon_pixmap and not icon_pixmap.isNull():
            self.placeholder_label.setPixmap(icon_pixmap)
        else:
            self.placeholder_label.setText(_("widgets.cover.cover_label"))
        self.placeholder_label.update()

    def _create_book_icon(self) -> Optional[QPixmap]:
        """创建书籍占位图标（48x48，使用主题色）"""
        try:
            from core import IconManager
            icon_mgr = IconManager()
            # 尝试加载现有的 SVG 图标
            pix = icon_mgr.load_title_svg("title_resource.svg", self._accent_color, size=(48, 48))
            if pix and not pix.isNull():
                return pix
        except Exception:
            pass
        return None

    def _show_loading(self):
        """显示加载中状态"""
        self.cover_label.hide()
        self.placeholder_label.show()
        self.placeholder_label.setText(_("widgets.cover.loading"))
        self.placeholder_label.setStyleSheet("""
            color: #666;
            font-size: 9pt;
        """)

    def _show_cover_image(self, pixmap: QPixmap):
        """显示封面图片（保持比例，居中裁剪填充并应用圆角遮罩）"""
        self.placeholder_label.hide()
        self.cover_label.show()

        # 计算缩放后的尺寸（保持比例，填充到可用区域）
        target_w = self.COVER_WIDTH - self.COVER_RADIUS * 2
        target_h = self.COVER_HEIGHT - self.COVER_RADIUS * 2
        scaled_pixmap = pixmap.scaled(
            target_w, target_h,
            Qt.KeepAspectRatioByExpanding,
            Qt.SmoothTransformation
        )

        # 居中裁剪
        cropped = scaled_pixmap.copy(
            (scaled_pixmap.width() - target_w) // 2,
            (scaled_pixmap.height() - target_h) // 2,
            target_w,
            target_h
        )
        self.cover_label.setPixmap(self._apply_rounded_mask(cropped))

    def _apply_rounded_mask(self, pixmap: QPixmap) -> QPixmap:
        """为封面图片应用圆角遮罩，确保圆角边框始终可见

        Args:
            pixmap: 原始封面图片

        Returns:
            应用圆角遮罩后的图片
        """
        rounded = QPixmap(pixmap.size())
        rounded.fill(Qt.transparent)

        painter = QPainter(rounded)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            path = QPainterPath()
            path.addRoundedRect(
                0, 0, pixmap.width(), pixmap.height(),
                self.COVER_RADIUS, self.COVER_RADIUS
            )
            painter.setClipPath(path)
            painter.drawPixmap(0, 0, pixmap)
        finally:
            if painter.isActive():
                painter.end()

        return rounded

    def _show_error(self):
        """显示加载失败状态"""
        self.cover_label.hide()
        self.placeholder_label.show()
        self.placeholder_label.setText(_("widgets.cover.load_failed"))
        self.placeholder_label.setStyleSheet("""
            color: #999;
            font-size: 9pt;
        """)

    @pyqtSlot(str)
    def load_cover(self, file_path: str):
        """从本地文件加载封面图片

        Args:
            file_path: 封面图片文件的绝对路径
        """
        if not file_path or not os.path.exists(file_path):
            self._show_placeholder()
            return

        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            self._show_error()
            return

        self._cover_path = file_path
        self._show_cover_image(pixmap)

    @pyqtSlot(str, str)
    def load_cover_from_url(self, cover_url: str, content_id: str):
        """异步下载封面并显示

        Args:
            cover_url: 封面图片 URL（Slide1）
            content_id: 教材 contentId
        """
        if not cover_url or not content_id:
            self._show_placeholder()
            return

        self._content_id = content_id
        self._show_loading()

        def _download_and_show():
            try:
                from core import get_cover_cache
                cache = get_cover_cache()
                cover_path = cache.download_cover(cover_url, content_id)
            except Exception as e:
                from core.infrastructure.logger import log
                log("WARNING", f"封面加载异常: {e}")
                cover_path = None

            if sip.isdeleted(self):
                return
            # 工作线程严禁直接操作 Qt 控件，统一通过 QueuedConnection 回到 GUI 线程执行，
            # 避免跨线程访问 QWidget 的未定义行为（偶发渲染错乱/崩溃）
            if cover_path:
                QMetaObject.invokeMethod(
                    self, "load_cover", Qt.QueuedConnection, Q_ARG(str, cover_path)
                )
            else:
                QMetaObject.invokeMethod(
                    self, "_show_placeholder", Qt.QueuedConnection
                )

        self._download_thread = threading.Thread(target=_download_and_show, daemon=True)
        self._download_thread.start()

    def show_placeholder(self):
        """公开方法：显示占位符（清除当前封面并恢复默认状态）"""
        self._show_placeholder()

    @pyqtSlot()
    def clear(self):
        """清除封面，显示占位符"""
        self._content_id = None
        self._cover_path = None
        self._show_placeholder()

    def sizeHint(self) -> QSize:
        """返回推荐尺寸"""
        return QSize(self.COVER_WIDTH, self.COVER_HEIGHT)

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新封面控件视觉元素

        Args:
            primary: 主题主色
            background: 主题背景色
        """
        self._accent_color = primary
        self._background_color = background
        self._apply_rounded_border(background)

        if self.placeholder_label.isVisible():
            self._show_placeholder()
        elif self.cover_label.isVisible() and self._cover_path:
            # 重新加载本地封面并应用新的圆角遮罩，避免多次切换后描边消失
            self.load_cover(self._cover_path)
