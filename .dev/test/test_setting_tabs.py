# -*- coding: utf-8 -*-
"""测试设置页各标签页能否正常收集设置。"""
import sys
sys.path.insert(0, r"e:\hello\web\Smart-edu-downloader")

from PyQt5.QtWidgets import QApplication

from core.infrastructure.default_settings import get_all_default_settings
from gui.pages.settings.tabs.basic_tab import BasicSettingTab
from gui.pages.settings.tabs.download_tab import DownloadSettingTab
from gui.pages.settings.tabs.interface_tab import InterfaceSettingTab
from gui.pages.settings.tabs.advanced_tab import AdvancedSettingTab
from gui.pages.settings.tabs.privacy_tab import PrivacySettingTab


TABS = [
    ("basic", BasicSettingTab),
    ("download", DownloadSettingTab),
    ("interface", InterfaceSettingTab),
    ("advanced", AdvancedSettingTab),
    ("privacy", PrivacySettingTab),
]


def main():
    app = QApplication(sys.argv)
    callbacks = {}
    settings = get_all_default_settings()

    for name, cls in TABS:
        tab = cls(callbacks)
        tab.refresh_from(settings)
        collected = {}
        tab.collect_settings(collected)
        print(f"{name}: 收集到 {len(collected)} 项")
        for key, value in collected.items():
            print(f"  {key}: {value!r}")
        print()

    print("所有标签页 collect_settings 测试通过")


if __name__ == "__main__":
    main()
