# -*- coding: utf-8 -*-
"""测试右下角信息提示组件创建。"""
import sys
sys.path.insert(0, r"e:\hello\web\Smart-edu-downloader")

from PyQt5.QtWidgets import QApplication, QWidget

from gui.widgets.bottom_right_info_bar import BottomRightInfoBar


def main():
    app = QApplication(sys.argv)
    parent = QWidget()
    parent.resize(800, 600)
    parent.show()

    # 验证四种信息提示都能创建（不实际显示也可测试构造）
    for kind in ("success", "warning", "error", "info"):
        method = getattr(BottomRightInfoBar, kind)
        method(f"{kind} 标题", f"{kind} 内容", parent=parent, duration=1000)
        print(f"{kind} 信息提示已创建")

    print("BottomRightInfoBar 测试通过")


if __name__ == "__main__":
    main()
