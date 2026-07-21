# -*- coding: utf-8 -*-
"""预览仅图标标题栏模式。"""
import sys
import os

# 将项目根目录加入路径（脚本位于 .dev/test/，需向上三级）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.chdir(project_root)

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt

from gui.components.unified_title_bar import UnifiedTitleBar


def main():
    app = QApplication(sys.argv)

    window = QWidget()
    window.setWindowTitle("Icon Only Title Bar Preview")
    window.resize(900, 120)
    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    title_bar = UnifiedTitleBar(mode="icon_only")
    title_bar.setCornerRadius(0)
    layout.addWidget(title_bar)

    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
