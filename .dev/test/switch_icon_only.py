# -*- coding: utf-8 -*-
"""切换到仅图标标题栏模式并截图。"""
import os
import time
import pyautogui
import pygetwindow as gw


def main():
    sed = gw.getWindowsWithTitle("SED")
    if not sed:
        print("未找到 SED 窗口")
        return
    sed = sed[0]

    debug = gw.getWindowsWithTitle("调试面板")
    if not debug:
        print("未找到调试面板窗口")
        return
    debug = debug[0]

    if debug.isMinimized:
        debug.restore()
    debug.activate()
    time.sleep(0.3)

    # 切换到实验室标签页（最后一个）
    pyautogui.click(debug.left + 70, debug.top + 295)
    time.sleep(0.5)

    # 点击标题栏样式下拉框（根据截图估算位置）
    pyautogui.click(debug.left + 620, debug.top + 220)
    time.sleep(0.4)

    # 用键盘选择最后一个"仅图标"
    pyautogui.press('down', presses=2, interval=0.05)
    pyautogui.press('enter')
    time.sleep(1.0)

    if sed.isMinimized:
        sed.restore()
    sed.activate()
    time.sleep(0.5)

    output_dir = os.path.dirname(os.path.abspath(__file__))
    screenshot = pyautogui.screenshot(region=(sed.left, sed.top, sed.width, 80))
    path = os.path.join(output_dir, "icon_only_header2.png")
    screenshot.save(path)
    print(f"截图已保存: {path}")


if __name__ == "__main__":
    main()
