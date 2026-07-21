# -*- coding: utf-8 -*-
"""测试设置页实例化与保存流程。"""
import sys
sys.path.insert(0, r"e:\hello\web\Smart-edu-downloader")

from PyQt5.QtWidgets import QApplication

from gui.pages.setting_page import SettingPage


def main():
    app = QApplication(sys.argv)
    page = SettingPage()

    # 模拟保存前收集设置
    page._collect_settings()
    print(f"收集到 {len(page.settings)} 项设置")

    # 验证关键下拉框设置值有效（不为 None/空）
    file_naming_rule = page.settings.get("file_naming_rule")
    categorize_rule = page.settings.get("categorize_rule")
    language = page.settings.get("language")
    search_mode = page.settings.get("search_mode")

    print(f"file_naming_rule: {file_naming_rule!r}")
    print(f"categorize_rule: {categorize_rule!r}")
    print(f"language: {language!r}")
    print(f"search_mode: {search_mode!r}")

    assert file_naming_rule is not None, "file_naming_rule 不应为 None"
    assert categorize_rule is not None, "categorize_rule 不应为 None"
    assert language, "language 不应为空"
    assert search_mode, "search_mode 不应为空"

    print("SettingPage 保存前收集测试通过")


if __name__ == "__main__":
    main()
