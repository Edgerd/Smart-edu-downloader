# -*- coding: utf-8 -*-
"""测试 ComboBoxCard.currentData 是否能正常调用。"""
import sys
sys.path.insert(0, r"e:\hello\web\Smart-edu-downloader")

from PyQt5.QtWidgets import QApplication
from qfluentwidgets import FluentIcon

from gui.pages.settings.components.combo_box_card import ComboBoxCard


def main():
    app = QApplication(sys.argv)
    card = ComboBoxCard(FluentIcon.LANGUAGE, "测试")
    card.addItem("默认", "default")
    card.addItem("自定义", "custom")
    card.setCurrentIndex(1)
    data = card.currentData()
    print("currentData:", data)
    assert data == "custom", f"期望 custom，实际 {data}"
    print("测试通过")


if __name__ == "__main__":
    main()
