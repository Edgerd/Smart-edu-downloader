# -*- coding: utf-8 -*-
"""测试命名规则下拉框数据。"""
import sys
sys.path.insert(0, r"e:\hello\web\Smart-edu-downloader")

from PyQt5.QtWidgets import QApplication

from core.infrastructure.default_settings import get_all_default_settings
from gui.pages.settings.tabs.download_tab import DownloadSettingTab


def main():
    app = QApplication(sys.argv)
    tab = DownloadSettingTab({})
    settings = get_all_default_settings()
    tab.refresh_from(settings)

    print(f"naming_rule_card currentIndex: {tab.naming_rule_card.currentIndex()}")
    print(f"naming_rule_card currentText: {tab.naming_rule_card.currentText()!r}")
    print(f"naming_rule_card currentData: {tab.naming_rule_card.currentData()!r}")
    print(f"naming_rule_card findData default: {tab.naming_rule_card.findData('default')}")

    collected = {}
    tab.collect_settings(collected)
    print(f"file_naming_rule: {collected.get('file_naming_rule')!r}")


if __name__ == "__main__":
    main()
