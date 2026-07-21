# -*- coding: utf-8 -*-
"""临时截图脚本，用于验证 SED 主窗口显示。"""
import os
import time
import pyautogui
import pygetwindow as gw


def main():
    """查找 SED 窗口并截图。"""
    output_dir = os.path.dirname(os.path.abspath(__file__))

    window = None
    for _ in range(20):
        try:
            windows = gw.getWindowsWithTitle("SED")
            for w in windows:
                if w.title and "SED" in w.title and w.width > 0 and w.height > 0:
                    window = w
                    break
            if window:
                break
        except Exception:
            pass
        time.sleep(0.5)

    if not window:
        print("未找到 SED 窗口")
        return

    try:
        if window.isMinimized:
            window.restore()
        window.activate()
        time.sleep(0.5)
    except Exception as e:
        print(f"激活窗口失败: {e}")

    screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))
    output_path = os.path.join(output_dir, "sed_screenshot.png")
    screenshot.save(output_path)
    print(f"截图已保存: {output_path}")
    print(f"窗口标题: {window.title}")
    print(f"窗口尺寸: {window.width}x{window.height}")


if __name__ == "__main__":
    main()
