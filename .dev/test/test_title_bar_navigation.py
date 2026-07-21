# -*- coding: utf-8 -*-
"""验证标题栏导航按钮可点击并切换页面。

创建主窗口后，依次点击所有导航按钮，检查当前页面索引是否正确切换。
"""

import os
import sys
import json
import time

from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)
SETTINGS_FILE = os.path.join(
    os.environ.get("TEMP", "C:\\Users\\Administrator\\AppData\\Local\\Temp"),
    "Smart-edu-downloader", "settings", "settings.json"
)


def set_title_bar_style(mode):
    """临时设置标题栏样式。"""
    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    data["title_bar_style"] = mode
    data["first_run"] = True
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def test_navigation(mode):
    """测试指定模式下的导航按钮点击切换。

    Args:
        mode: "large" 或 "compact"。

    Returns:
        tuple: (是否全部通过, 结果列表)
    """
    set_title_bar_style(mode)

    app = QApplication(sys.argv)
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass

    from core.i18n import set_language
    set_language("zh_CN")

    from gui.fonts import init_fonts, body_font
    init_fonts()
    app.setFont(body_font())

    from gui import MainWindow
    window = MainWindow()
    window.show()
    app.processEvents()
    time.sleep(0.3)
    app.processEvents()

    nav_buttons = window.nav_buttons
    results = []
    all_passed = True

    for idx, btn in enumerate(nav_buttons):
        btn.click()
        app.processEvents()
        time.sleep(0.2)
        app.processEvents()

        current = window.stacked_widget.currentIndex()
        passed = current == idx
        results.append((idx, passed, current))
        if not passed:
            all_passed = False

    app.quit()
    return all_passed, results


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "large"
    passed, results = test_navigation(mode)
    print(f"\n[{mode} mode]")
    for idx, ok, current in results:
        status = "OK" if ok else "FAIL"
        print(f"  button {idx}: expected={idx} current={current} {status}")
    print(f"  overall: {'PASS' if passed else 'FAIL'}")
    sys.exit(0 if passed else 1)
