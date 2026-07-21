# -*- coding: utf-8 -*-
"""
状态栏组件
职责：状态栏 UI 创建、状态文本更新
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel

from gui.fonts import body_font
from core.infrastructure.version import VERSION_INFO
from core.i18n import _

class StatusBar(QWidget):
    """状态栏组件
    
    属性:
        status_label: 状态文本标签
        version_label: 版本信息标签
    """
    
    def __init__(self, parent=None):
        """初始化状态栏
        
        Args:
            parent: 父组件
        """
        super().__init__(parent)
        self.setFixedHeight(30)
        self.setObjectName("statusBar")
        self.setAttribute(Qt.WA_StyledBackground, True)

        self._create_layout()
        self._create_labels()
    
    def _create_layout(self):
        """创建状态栏布局"""
        self.status_layout = QHBoxLayout()
        self.status_layout.setContentsMargins(20, 0, 20, 0)
        self.setLayout(self.status_layout)
    
    def _create_labels(self):
        """创建状态标签和版本标签"""
        # 状态文本标签
        self.status_label = QLabel(_("common.status_ready"))
        self.status_label.setFont(body_font())
        self.status_label.setStyleSheet("color: #666; background: transparent;")
        
        # 版本信息标签
        version_major = f"{VERSION_INFO[0]}.{VERSION_INFO[1]}.{VERSION_INFO[2]}"
        if len(VERSION_INFO) >= 5 and VERSION_INFO[3]:  # 存在 Alpha/beta 等
            stage = VERSION_INFO[3]
            stage_num = VERSION_INFO[4] if len(VERSION_INFO) >= 5 else 0
            version_str = f"v{version_major} {stage} {stage_num}"
        else:
            version_str = f"v{version_major}"
        self.version_label = QLabel(_("widgets.status_bar.status_template", version_str=version_str))
        self.version_label.setFont(body_font())
        self.version_label.setStyleSheet("color: #888; background: transparent;")
        
        # 添加到布局
        self.status_layout.addWidget(self.status_label)
        self.status_layout.addStretch()
        self.status_layout.addWidget(self.version_label)
    
    def set_status(self, text):
        """设置状态文本
        
        Args:
            text: 状态文本
        """
        self.status_label.setText(text)
    
    def get_status(self):
        """获取当前状态文本
        
        Returns:
            str: 当前状态文本
        """
        return self.status_label.text()
