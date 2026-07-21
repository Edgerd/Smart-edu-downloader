# -*- coding: utf-8 -*-
"""测试 SVG 图标颜色替换是否正确。"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.chdir(project_root)

from PyQt5.QtWidgets import QApplication
app = QApplication(sys.argv)

from core.ui.icon_manager import IconManager

mgr = IconManager()
for color in ["#282A30", "#B49C26", "#1277DD"]:
    pix = mgr.load_title_svg("title_home.svg", color, size=(28, 28))
    print(f"{color}: pixmap {'ok' if pix and not pix.isNull() else 'fail'} ({pix.width()}x{pix.height()})")

# 验证替换后的 SVG 内容（通过内部读取）
content = mgr._read_title_svg_content("title_home.svg")
print("\n替换前 fill 颜色:", content.count('fill="#1A82E2"'))
