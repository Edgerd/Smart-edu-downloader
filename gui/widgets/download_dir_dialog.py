# -*- coding: utf-8 -*-
"""下载位置询问对话框"""
from core.i18n import _

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QFileDialog, QCheckBox, QFrame)
from PyQt5.QtCore import Qt

from gui.fonts import body_font, bold_font, small_font
from gui.widgets.material_button import MaterialButton
from gui.styles import load_primary_color


class DownloadDirDialog(QDialog):
    """下载位置询问对话框"""
    
    def __init__(self, parent=None, title=_("common.unnamed")):
        super().__init__(parent)
        self.title = title
        self.selected_dir = None
        self.disable_ask = False
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle(_("dialogs.download_dir.title"))
        self.setModal(True)
        self.setMinimumWidth(500)
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.setLayout(main_layout)

        accent_color = load_primary_color()

        # 标题
        title_label = QLabel(_("dialogs.download_dir.title"))
        title_label.setFont(bold_font())
        title_label.setStyleSheet(f"color: {accent_color};")
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 提示文本
        hint_frame = QFrame()
        hint_frame.setObjectName("hintFrame")
        hint_frame.setStyleSheet("""
            #hintFrame {
                background: #F0F8FF;
                border: 1px solid #B8D4F0;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        hint_layout = QVBoxLayout()
        hint_layout.setContentsMargins(0, 0, 0, 0)
        hint_frame.setLayout(hint_layout)
        
        hint_label = QLabel(_("dialogs.download_dir.prepare_template", title=self.title))
        hint_label.setFont(body_font())
        hint_label.setStyleSheet("color: #333;")
        hint_label.setWordWrap(True)
        hint_layout.addWidget(hint_label)
        
        main_layout.addWidget(hint_frame)
        
        # 当前默认目录显示
        dir_label = QLabel(_("dialogs.download_dir.current_default_dir"))
        dir_label.setFont(small_font())
        dir_label.setStyleSheet("color: #666;")
        main_layout.addWidget(dir_label)
        
        from gui.pages.setting_page import SettingPage
        settings = SettingPage.load_settings()
        default_dir = settings.get("download_dir", "")
        
        self.default_dir_label = QLabel(default_dir)
        self.default_dir_label.setFont(small_font())
        self.default_dir_label.setStyleSheet("""
            QLabel {
                color: #333;
                background: #F8FAFC;
                border: 1px solid #E0E8F0;
                border-radius: 4px;
                padding: 8px;
            }
        """)
        self.default_dir_label.setWordWrap(True)
        main_layout.addWidget(self.default_dir_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # 浏览按钮
        browse_btn = MaterialButton(_("dialogs.download_dir.browse_button"))
        browse_btn.setAccentColor(accent_color)
        browse_btn.setFixedHeight(40)
        browse_btn.clicked.connect(self._browse_dir)
        button_layout.addWidget(browse_btn, 1)
        
        # 使用默认目录按钮
        default_btn = MaterialButton(_("dialogs.download_dir.use_default_button"))
        default_btn.setVariant(MaterialButton.VARIANT_TONAL)
        default_btn.setAccentColor("#28A745")
        default_btn.setContainerColor("#E8F5E9")
        default_btn.setOnContainerColor("#1B5E20")
        default_btn.setFixedHeight(40)
        default_btn.clicked.connect(self._use_default)
        button_layout.addWidget(default_btn, 1)
        
        main_layout.addLayout(button_layout)
        
        # 取消按钮
        cancel_btn = MaterialButton(_("dialogs.download_dir.cancel_download_button"), variant=MaterialButton.VARIANT_OUTLINED)
        cancel_btn.setAccentColor("#6C757D")
        cancel_btn.setFixedHeight(36)
        cancel_btn.clicked.connect(self.reject)
        main_layout.addWidget(cancel_btn, 0, Qt.AlignCenter)
        
        # 不再提示复选框
        self.disable_checkbox = QCheckBox(_("dialogs.download_dir.do_not_ask_again"))
        self.disable_checkbox.setFont(small_font())
        self.disable_checkbox.setStyleSheet("color: #666;")
        main_layout.addWidget(self.disable_checkbox)
    
    def _browse_dir(self):
        """浏览选择目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, 
            _("settings.common.select_download_dir"), 
            self.default_dir_label.text()
        )
        if dir_path:
            self.selected_dir = dir_path
            self.disable_ask = self.disable_checkbox.isChecked()
            self.accept()
    
    def _use_default(self):
        """使用默认目录"""
        self.selected_dir = self.default_dir_label.text()
        self.disable_ask = self.disable_checkbox.isChecked()
        self.accept()
    
    def get_result(self):
        """获取选择结果"""
        return self.selected_dir, self.disable_ask
