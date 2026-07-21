# -*- coding: utf-8 -*-
"""
快捷操作面板组件

提供重启应用、打开配置目录、打开日志目录、检查更新等快捷操作。
"""
from core.i18n import _

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt, QCoreApplication

from gui.fonts import body_font
from gui.widgets.material_button import MaterialButton
from gui.styles import load_primary_color
from core.infrastructure.path_resolver import get_settings_dir, get_logs_dir
from core.infrastructure.platform_utils import open_directory, restart_application


class QuickActionsWidget(QWidget):
    """快捷操作面板组件"""
    
    def __init__(self, parent=None, show_title: bool = True):
        super().__init__(parent)
        self._show_title = show_title
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        
        # 标题
        if self._show_title:
            title = QLabel(_("debug.tools.quick_actions_title"))
            title.setFont(body_font())
            title.setStyleSheet("font-weight: bold; color: #333;")
            layout.addWidget(title)
        
        # 从设置读取主题色
        accent_color = load_primary_color()

        # 按钮网格
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(10)

        # 第一行按钮
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self.restart_btn = MaterialButton(_("debug.tools.restart_app"), variant=MaterialButton.VARIANT_OUTLINED)
        self.restart_btn.setAccentColor(accent_color)
        self.restart_btn.setFixedHeight(40)
        self.restart_btn.clicked.connect(self._restart_application)
        row1.addWidget(self.restart_btn)

        self.open_config_btn = MaterialButton(_("debug.tools.open_config_dir"), variant=MaterialButton.VARIANT_OUTLINED)
        self.open_config_btn.setAccentColor(accent_color)
        self.open_config_btn.setFixedHeight(40)
        self.open_config_btn.clicked.connect(self._open_config_directory)
        row1.addWidget(self.open_config_btn)

        btn_layout.addLayout(row1)

        # 第二行按钮
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        self.open_log_btn = MaterialButton(_("debug.tools.open_log_dir"), variant=MaterialButton.VARIANT_OUTLINED)
        self.open_log_btn.setAccentColor(accent_color)
        self.open_log_btn.setFixedHeight(40)
        self.open_log_btn.clicked.connect(self._open_log_directory)
        row2.addWidget(self.open_log_btn)

        check_update_btn = MaterialButton(_("debug.tools.check_update"), variant=MaterialButton.VARIANT_OUTLINED)
        check_update_btn.setAccentColor("#28A745")
        check_update_btn.setFixedHeight(40)
        check_update_btn.clicked.connect(self._check_for_updates)
        row2.addWidget(check_update_btn)

        btn_layout.addLayout(row2)
        
        layout.addLayout(btn_layout)
        
        # 提示信息
        hint_label = QLabel(_("debug.tools.restart_hint"))
        hint_label.setFont(body_font())
        hint_label.setStyleSheet("color: #888; margin-top: 10px;")
        hint_label.setWordWrap(True)
        layout.addWidget(hint_label)
        
        layout.addStretch()
    
    def _restart_application(self):
        """重启应用程序"""
        reply = QMessageBox.question(
            self, _("debug.tools.confirm_restart_title"),
            _("debug.tools.confirm_restart_message"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                if restart_application():
                    QCoreApplication.quit()
                else:
                    QMessageBox.critical(
                        self,
                        _("common.error"),
                        _("debug.tools.quick_actions.restart_failed", error=_("common.status_failed")),
                    )
            except Exception as e:
                QMessageBox.critical(self, _("common.error"), _("debug.tools.quick_actions.restart_failed", error=str(e)))

    def _open_config_directory(self):
        """打开配置目录"""
        try:
            config_dir = get_settings_dir()
            if not open_directory(config_dir):
                QMessageBox.critical(
                    self,
                    _("common.error"),
                    _("debug.tools.quick_actions.open_config_failed", error=_("common.open_failed")),
                )
        except Exception as e:
            QMessageBox.critical(self, _("common.error"), _("debug.tools.quick_actions.open_config_failed", error=str(e)))

    def _open_log_directory(self):
        """打开日志目录"""
        try:
            log_dir = get_logs_dir()
            if not open_directory(log_dir):
                QMessageBox.critical(
                    self,
                    _("common.error"),
                    _("debug.tools.log.open_log_dir_failed", error=_("common.open_failed")),
                )
        except Exception as e:
            QMessageBox.critical(self, _("common.error"), _("debug.tools.log.open_log_dir_failed", error=str(e)))

    def _check_for_updates(self):
        """检查更新"""
        try:
            from core.infrastructure.version import VERSION
            
            # 这里可以集成实际的更新检查逻辑
            # 暂时只显示当前版本信息
            QMessageBox.information(
                self, _("debug.tools.check_update"),
                _("debug.tools.update_result_template", VERSION=VERSION)
            )
            
        except Exception as e:
            QMessageBox.critical(self, _("common.error"), _("debug.tools.quick_actions.check_update_failed", error=str(e)))

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新快捷操作面板视觉元素。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        for btn in (getattr(self, 'restart_btn', None),
                    getattr(self, 'open_config_btn', None),
                    getattr(self, 'open_log_btn', None)):
            if btn is not None:
                btn.setAccentColor(primary)
