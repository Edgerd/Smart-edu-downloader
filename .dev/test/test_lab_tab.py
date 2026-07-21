# -*- coding: utf-8 -*-
"""测试实验室标签页控件创建与开关样式切换。"""
import sys
sys.path.insert(0, r"e:\hello\web\Smart-edu-downloader")

from PyQt5.QtWidgets import QApplication

from gui.components.debug.lab_tab import LabTab


def main():
    app = QApplication(sys.argv)
    tab = LabTab()

    # 验证关键控件存在
    assert hasattr(tab, "switch_style_card")
    assert hasattr(tab, "title_bar_style_card")
    assert hasattr(tab, "custom_title_card")
    assert hasattr(tab, "bold_switch")
    assert hasattr(tab, "italic_switch")
    assert hasattr(tab, "scrollbar_theme_switch")
    assert hasattr(tab, "apply_card")

    # 验证开关样式下拉框选项与 currentData
    tab.switch_style_card.setCurrentIndex(0)
    value = tab.switch_style_card.currentData()
    print(f"switch_style currentData(0): {value!r}")
    assert value == "fluent", f"期望 fluent，实际 {value!r}"

    tab.switch_style_card.setCurrentIndex(1)
    value = tab.switch_style_card.currentData()
    print(f"switch_style currentData(1): {value!r}")
    assert value == "ios", f"期望 ios，实际 {value!r}"

    # 验证标题栏样式下拉框
    tab.title_bar_style_card.setCurrentIndex(0)
    value = tab.title_bar_style_card.currentData()
    print(f"title_bar_style currentData(0): {value!r}")
    assert value == "large", f"期望 large，实际 {value!r}"

    tab.title_bar_style_card.setCurrentIndex(1)
    value = tab.title_bar_style_card.currentData()
    print(f"title_bar_style currentData(1): {value!r}")
    assert value == "compact", f"期望 compact，实际 {value!r}"

    tab.title_bar_style_card.setCurrentIndex(2)
    value = tab.title_bar_style_card.currentData()
    print(f"title_bar_style currentData(2): {value!r}")
    assert value == "icon_only", f"期望 icon_only，实际 {value!r}"

    print("LabTab 测试通过")


if __name__ == "__main__":
    main()
