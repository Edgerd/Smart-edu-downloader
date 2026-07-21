# -*- coding: utf-8 -*-
"""打开调试面板并截图。"""
import os
import time
import pyautogui
import pygetwindow as gw


def main():
    """按 F12 打开调试面板并截图。"""
    output_dir = os.path.dirname(os.path.abspath(__file__))

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

    pyautogui.press('f12')
    time.sleep(1.5)

    # 查找调试面板窗口
    debug_windows = gw.getWindowsWithTitle("调试面板")
    if not debug_windows:
        print("未找到调试面板窗口")
        # 截主窗口
        screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))
        screenshot.save(os.path.join(output_dir, "debug_panel_search.png"))
        print("已保存主窗口截图")
        return

    debug = debug_windows[0]
    screenshot = pyautogui.screenshot(region=(debug.left, debug.top, debug.width, debug.height))
    output_path = os.path.join(output_dir, "debug_panel.png")
    screenshot.save(output_path)
    print(f"调试面板截图已保存: {output_path}")
    print(f"调试面板尺寸: {debug.width}x{debug.height}")


if __name__ == "__main__":
    main()
