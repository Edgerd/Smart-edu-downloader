# -*- coding: utf-8 -*-
"""关闭赞赏码对话框。"""
import time
import pyautogui
import pygetwindow as gw


def main():
    """查找 SED 窗口并点击关闭按钮（如果有弹窗）。"""
    windows = gw.getWindowsWithTitle("SED")
    if not windows:
        print("未找到 SED 窗口")
        return

    window = windows[0]
    try:
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(0.3)
    except Exception as e:
        print(f"激活窗口失败: {e}")
        return

    # 按 Esc 关闭弹窗
    pyautogui.press('esc')
    print("已按 Esc 键")


if __name__ == "__main__":
    main()
