# -*- coding: utf-8 -*-
"""测试开关样式切换功能。"""
import sys
sys.path.insert(0, r"e:\hello\web\Smart-edu-downloader")

from PyQt5.QtWidgets import QApplication

from gui.widgets.switch_button import SwitchWithLabel, refresh_all_switch_buttons


def main():
    app = QApplication(sys.argv)

    switch = SwitchWithLabel("测试开关", checked=True)
    print(f"初始风格: {switch._style}")

    # 切换到 Fluent 风格
    switch.setStyle("fluent")
    assert switch._style == "fluent"
    assert switch.isChecked() is True
    print("已切换到 Fluent 风格")

    # 切换回 iOS 风格
    switch.setStyle("ios")
    assert switch._style == "ios"
    assert switch.isChecked() is True
    print("已切换回 iOS 风格")

    # 测试全局刷新
    refresh_all_switch_buttons("fluent")
    assert switch._style == "fluent"
    print("全局刷新到 Fluent 风格")

    refresh_all_switch_buttons("ios")
    assert switch._style == "ios"
    print("全局刷新到 iOS 风格")

    print("SwitchWithLabel 样式切换测试通过")


if __name__ == "__main__":
    main()
