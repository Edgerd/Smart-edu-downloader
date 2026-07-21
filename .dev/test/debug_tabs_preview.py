# -*- coding: utf-8 -*-
"""调试面板标签页视觉验证。

以较小窗口尺寸展示实验室和信息标签页，验证：
- 实验室标签页在内容超出可视区域时支持垂直滚动；
- 信息标签页长文本值自动换行并完整显示。
"""
import sys
import os

# 将项目根目录加入路径（脚本位于 .dev/test/，需向上三级）
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.chdir(project_root)

from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QTabWidget

from qfluentwidgets import setTheme, Theme
from gui.components.debug.lab_tab import LabTab
from gui.components.debug.info_tab import InfoTab


def main():
    app = QApplication(sys.argv)
    setTheme(Theme.LIGHT)

    window = QWidget()
    window.setWindowTitle("Debug Tabs Preview")
    # 使用较小高度强制触发滚动
    window.resize(700, 420)

    layout = QVBoxLayout(window)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)

    tabs = QTabWidget()
    tabs.setDocumentMode(True)

    lab_tab = LabTab()
    info_tab = InfoTab()

    tabs.addTab(lab_tab, "实验室")
    tabs.addTab(info_tab, "信息")

    layout.addWidget(tabs)
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
