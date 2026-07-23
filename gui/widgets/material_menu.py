# -*- coding: utf-8 -*-
"""Material Design 3 风格自定义右键菜单组件。

完全使用 QWidget 实现，提供圆角、阴影、主题色高亮、点击水波纹、
子菜单和键盘导航等现代交互效果。
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy,
    QApplication, QGraphicsDropShadowEffect
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer, QPoint, QRect, QRectF, QSize, QEvent, QEventLoop
from PyQt5.QtGui import QPainter, QColor, QFont, QFontMetrics, QPen, QPainterPath

from gui.utils.color_utils import ripple_tint
from gui.fonts import body_font
from gui.styles import load_primary_color


class MaterialMenuAction:
    """MaterialMenu 的菜单项数据。"""

    def __init__(self, text: str = "", callback=None, shortcut: str = "",
                 enabled: bool = True, checked: bool = False):
        self.text = text
        self.callback = callback
        self.shortcut = shortcut
        self.enabled = enabled
        self.checked = checked

    def trigger(self):
        """触发菜单项回调。"""
        if self.enabled and self.callback is not None:
            self.callback()


class MaterialMenuItem(QWidget):
    """Material Design 风格的单个菜单项控件。"""

    triggered = pyqtSignal()
    hovered = pyqtSignal()

    def __init__(self, action: MaterialMenuAction, parent=None,
                 accent_color: str = None, has_submenu: bool = False):
        super().__init__(parent)
        self._action = action
        self._accent_color = QColor(accent_color or load_primary_color())
        self._has_submenu = has_submenu
        self._hovered = False
        self._pressed = False
        self._ripples = []
        self._ripple_timer = QTimer(self)
        self._ripple_timer.timeout.connect(self._update_ripples)
        self.setAttribute(Qt.WA_Hover, True)
        self.setCursor(Qt.PointingHandCursor if action.enabled else Qt.ArrowCursor)
        self._setup_ui()
        self.setEnabled(action.enabled)

    def _setup_ui(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(16, 0, 16, 0)
        self._layout.setSpacing(12)

        self._text_label = QLabel(self._action.text)
        self._text_label.setFont(body_font())
        self._text_label.setStyleSheet("color: #202124;")
        self._text_label.setEnabled(self._action.enabled)
        self._layout.addWidget(self._text_label)

        self._layout.addStretch()

        if self._action.shortcut:
            self._shortcut_label = QLabel(self._action.shortcut)
            shortcut_font = body_font()
            shortcut_font.setPointSize(max(8, shortcut_font.pointSize() - 1))
            self._shortcut_label.setFont(shortcut_font)
            self._shortcut_label.setStyleSheet("color: #9AA0A6;")
            self._shortcut_label.setEnabled(self._action.enabled)
            self._layout.addWidget(self._shortcut_label)

        if self._has_submenu:
            self._arrow_label = QLabel("›")
            arrow_font = body_font()
            arrow_font.setPointSize(14)
            self._arrow_label.setFont(arrow_font)
            self._arrow_label.setStyleSheet("color: #5F6368;")
            self._arrow_label.setEnabled(self._action.enabled)
            self._layout.addWidget(self._arrow_label)

        self.setFixedHeight(40)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_accent_color(self, color: str):
        """更新主题色。"""
        self._accent_color = QColor(color)
        self.update()

    def action(self) -> MaterialMenuAction:
        """返回绑定的动作数据。"""
        return self._action

    def enterEvent(self, event):
        if self._action.enabled:
            self._hovered = True
            self.hovered.emit()
            self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self._pressed = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self._action.enabled:
            self._pressed = True
            self._add_ripple(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self._pressed:
            self._pressed = False
            self.update()
            self.triggered.emit()

    def _add_ripple(self, pos: QPoint):
        max_radius = max(
            pos.x(), self.width() - pos.x(),
            pos.y(), self.height() - pos.y()
        ) * 1.5
        self._ripples.append({
            'center': pos,
            'radius': 0.0,
            'alpha': 255,
            'max_radius': max_radius,
        })
        if not self._ripple_timer.isActive():
            self._ripple_timer.start(16)

    def _update_ripples(self):
        for ripple in self._ripples[:]:
            ripple['radius'] += max(2.5, ripple['max_radius'] / 28)
            progress = ripple['radius'] / ripple['max_radius']
            ripple['alpha'] = int(255 * (1 - progress * progress))
            if ripple['radius'] >= ripple['max_radius'] or ripple['alpha'] <= 0:
                self._ripples.remove(ripple)
        self.update()
        if not self._ripples:
            self._ripple_timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        try:
            # 悬停背景（主题色淡化）
            if self._hovered and self._action.enabled:
                bg_color = QColor(self._accent_color)
                bg_color.setAlpha(38)
                painter.fillRect(self.rect(), bg_color)

            # 水波纹
            if self._ripples and self._action.enabled:
                painter.save()
                clip_path = QPainterPath()
                clip_path.addRoundedRect(QRectF(self.rect()), 6, 6)
                painter.setClipPath(clip_path)
                ripple_color = QColor(ripple_tint(self._accent_color.name()))
                for ripple in self._ripples:
                    color = QColor(ripple_color)
                    color.setAlpha(max(0, ripple['alpha']))
                    painter.setBrush(color)
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(ripple['center'], ripple['radius'], ripple['radius'])
                painter.restore()

            # 禁用状态文字颜色
            if not self._action.enabled:
                self._text_label.setStyleSheet("color: #BBBBBB;")
            elif self._hovered:
                self._text_label.setStyleSheet(f"color: {self._accent_color.name()};")
            else:
                self._text_label.setStyleSheet("color: #202124;")
        finally:
            if painter.isActive():
                painter.end()

    def sizeHint(self) -> QSize:
        fm = QFontMetrics(body_font())
        width = fm.horizontalAdvance(self._action.text) + 32
        if self._action.shortcut:
            width += QFontMetrics(body_font()).horizontalAdvance(self._action.shortcut) + 24
        if self._has_submenu:
            width += 20
        return QSize(max(width, 180), 40)


class MaterialMenuSeparator(QWidget):
    """菜单分隔线。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(9)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(224, 224, 224))
            rect = self.rect().adjusted(12, 4, -12, -4)
            painter.drawRect(rect)
        finally:
            if painter.isActive():
                painter.end()


class MaterialMenu(QWidget):
    """Material Design 风格弹出菜单。"""

    closed = pyqtSignal()

    def __init__(self, parent=None, accent_color: str = None):
        super().__init__(parent)
        self._accent_color = accent_color or load_primary_color()
        self._items = []
        self._submenus = []
        self._hovered_index = -1
        self._active_submenu = None
        self._submenu_timer = QTimer(self)
        self._submenu_timer.setSingleShot(True)
        self._submenu_timer.timeout.connect(self._close_active_submenu)
        self._event_loop = None
        self._result_action = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose, False)

        # 外层布局留出阴影边距
        self._outer_layout = QVBoxLayout(self)
        self._outer_layout.setContentsMargins(12, 12, 12, 12)
        self._outer_layout.setSpacing(0)

        self._container = QFrame(self)
        self._container.setObjectName("materialMenuContainer")
        self._container.setStyleSheet("""
            QFrame#materialMenuContainer {
                background: #FFFFFF;
                border-radius: 8px;
                border: 1px solid #E8EAED;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self._container)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 50))
        shadow.setOffset(0, 6)
        self._container.setGraphicsEffect(shadow)

        self._outer_layout.addWidget(self._container)

        self._items_layout = QVBoxLayout(self._container)
        self._items_layout.setContentsMargins(4, 4, 4, 4)
        self._items_layout.setSpacing(0)
        self._items_layout.addStretch()

    def _recompute_size(self):
        """根据内容重新计算并设置菜单尺寸。"""
        height = 8  # 上下内边距
        width = 180
        for item in self._items:
            if isinstance(item, MaterialMenuItem):
                hint = item.sizeHint()
                height += hint.height()
                width = max(width, hint.width())
            elif isinstance(item, MaterialMenuSeparator):
                height += item.height()
        self.setFixedSize(width + 32, height + 24)  # 加上阴影边距

    def addAction(self, text: str, callback=None, shortcut: str = "",
                  enabled: bool = True) -> MaterialMenuAction:
        """添加普通菜单项。"""
        action = MaterialMenuAction(text, callback, shortcut, enabled)
        item = MaterialMenuItem(action, self._container, self._accent_color)
        item.triggered.connect(lambda: self._on_item_triggered(action))
        item.hovered.connect(lambda idx=len(self._items): self._on_item_hovered(idx))
        self._items_layout.insertWidget(len(self._items), item)
        self._items.append(item)
        self._recompute_size()
        return action

    def addMenu(self, text: str) -> "MaterialMenu":
        """添加子菜单并返回子菜单实例。"""
        submenu = MaterialMenu(self, self._accent_color)
        submenu.closed.connect(self._on_submenu_closed)
        self._submenus.append(submenu)

        action = MaterialMenuAction(text, None, "", True)
        action.submenu = submenu
        item = MaterialMenuItem(action, self._container, self._accent_color, has_submenu=True)
        item.hovered.connect(lambda idx=len(self._items): self._on_item_hovered(idx))
        item.triggered.connect(lambda: self._open_submenu_for_item(item))
        self._items_layout.insertWidget(len(self._items), item)
        self._items.append(item)
        self._recompute_size()
        return submenu

    def addSeparator(self):
        """添加分隔线。"""
        sep = MaterialMenuSeparator(self._container)
        self._items_layout.insertWidget(len(self._items), sep)
        self._items.append(sep)
        self._recompute_size()

    def setAccentColor(self, color: str):
        """更新菜单主题色。"""
        self._accent_color = color
        for item in self._items:
            if isinstance(item, MaterialMenuItem):
                item.set_accent_color(color)
        for submenu in self._submenus:
            submenu.setAccentColor(color)

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新菜单主题色。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        self.setAccentColor(primary)

    def _on_item_hovered(self, index: int):
        """处理菜单项悬停。"""
        self._hovered_index = index
        item = self._items[index] if 0 <= index < len(self._items) else None

        # 悬停到新的子菜单项时打开对应子菜单
        if isinstance(item, MaterialMenuItem):
            submenu = getattr(item.action(), 'submenu', None)
            if submenu is not None and item.action().enabled:
                if self._active_submenu is not submenu:
                    self._close_active_submenu()
                    self._open_submenu(submenu, item)
                self._submenu_timer.stop()
                return

        # 悬停到普通项时，延迟关闭当前子菜单
        if self._active_submenu is not None:
            self._submenu_timer.start(250)

    def _open_submenu_for_item(self, item):
        """打开指定项的子菜单。"""
        if not isinstance(item, MaterialMenuItem):
            return
        submenu = getattr(item.action(), 'submenu', None)
        if submenu is None:
            return
        self._open_submenu(submenu, item)

    def _open_submenu(self, submenu: "MaterialMenu", item: MaterialMenuItem):
        """打开子菜单到指定项右侧。"""
        self._active_submenu = submenu
        global_pos = self.mapToGlobal(item.pos())
        target_pos = QPoint(global_pos.x() + self._container.width() - 4, global_pos.y())
        # 延迟执行，避免在事件处理中重入阻塞
        QTimer.singleShot(0, lambda: submenu.exec(target_pos))

    def _close_active_submenu(self):
        """关闭当前子菜单。"""
        if self._active_submenu is not None and self._active_submenu.isVisible():
            self._active_submenu.close()
        self._active_submenu = None

    def _on_submenu_closed(self):
        """子菜单关闭回调。"""
        if self._active_submenu is not None:
            result = self._active_submenu._result_action
            if result is not None:
                self._result_action = result
                self.close()

    def _on_item_triggered(self, action: MaterialMenuAction):
        """菜单项被触发。"""
        if not action.enabled:
            return
        self._result_action = action
        action.trigger()
        self.close()

    def exec(self, pos: QPoint) -> MaterialMenuAction:
        """在全局坐标处显示菜单并阻塞等待选择。"""
        adjusted = self._ensure_on_screen(pos)
        self.move(adjusted)
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.PopupFocusReason)

        self._event_loop = QEventLoop(self)
        self._event_loop.exec()
        return self._result_action

    exec_ = exec

    def _ensure_on_screen(self, pos: QPoint) -> QPoint:
        """确保菜单显示在屏幕范围内，返回调整后的新坐标。"""
        adjusted = QPoint(pos)
        screen = QApplication.primaryScreen().availableGeometry()
        if adjusted.x() + self.width() > screen.right():
            adjusted.setX(screen.right() - self.width() - 8)
        if adjusted.y() + self.height() > screen.bottom():
            adjusted.setY(screen.bottom() - self.height() - 8)
        adjusted.setX(max(screen.left() + 4, adjusted.x()))
        adjusted.setY(max(screen.top() + 4, adjusted.y()))
        return adjusted

    def closeEvent(self, event):
        """关闭时退出事件循环并发射关闭信号。"""
        self._close_active_submenu()
        if self._event_loop is not None and self._event_loop.isRunning():
            self._event_loop.quit()
            self._event_loop = None
        self.closed.emit()
        super().closeEvent(event)

    def keyPressEvent(self, event):
        """键盘导航。"""
        key = event.key()
        if key in (Qt.Key_Down, Qt.Key_Up):
            self._navigate(key == Qt.Key_Down)
        elif key in (Qt.Key_Return, Qt.Key_Enter, Qt.Key_Space):
            self._activate_current()
        elif key == Qt.Key_Escape:
            self.close()
        elif key == Qt.Key_Right:
            self._open_submenu_for_current()
        elif key == Qt.Key_Left:
            self.close()
        else:
            super().keyPressEvent(event)

    def _get_selectable_indices(self):
        """返回可选菜单项索引列表。"""
        return [i for i, item in enumerate(self._items)
                if isinstance(item, MaterialMenuItem) and item.action().enabled]

    def _navigate(self, direction_down: bool):
        """上下方向键导航。"""
        selectable = self._get_selectable_indices()
        if not selectable:
            return
        if self._hovered_index < 0:
            new_index = selectable[0]
        else:
            current = self._hovered_index
            if direction_down:
                candidates = [i for i in selectable if i > current]
                new_index = candidates[0] if candidates else selectable[0]
            else:
                candidates = [i for i in selectable if i < current]
                new_index = candidates[-1] if candidates else selectable[-1]
        self._set_hovered_index(new_index)

    def _set_hovered_index(self, index: int):
        """设置当前悬停项。"""
        for i, item in enumerate(self._items):
            if isinstance(item, MaterialMenuItem):
                item._hovered = (i == index)
                item.update()
        self._hovered_index = index

    def _activate_current(self):
        """激活当前悬停项。"""
        if 0 <= self._hovered_index < len(self._items):
            item = self._items[self._hovered_index]
            if isinstance(item, MaterialMenuItem) and item.action().enabled:
                self._on_item_triggered(item.action())

    def _open_submenu_for_current(self):
        """为当前项打开子菜单。"""
        if 0 <= self._hovered_index < len(self._items):
            item = self._items[self._hovered_index]
            self._open_submenu_for_item(item)
