# -*- coding: utf-8 -*-
"""验证 Beta 19 修改：实验室滚动、信息完整显示、仅图标布局。"""
import os
import time
import pyautogui
import pygetwindow as gw


def _find_window(title):
    windows = gw.getWindowsWithTitle(title)
    return windows[0] if windows else None


def _activate(window):
    if window.isMinimized:
        window.restore()
    window.activate()
    time.sleep(0.3)


def _screenshot(window, filename, height=None):
    output_dir = os.path.dirname(os.path.abspath(__file__))
    h = window.height if height is None else height
    screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, h))
    path = os.path.join(output_dir, filename)
    screenshot.save(path)
    print(f"截图已保存: {path}")
    return path


def _click_tab(debug, y_offset):
    pyautogui.click(debug.left + 70, debug.top + y_offset)
    time.sleep(0.5)


def main():
    sed = _find_window("SED")
    if not sed:
        print("未找到 SED 窗口")
        return
    _activate(sed)

    # 打开调试面板
    pyautogui.press('f12')
    time.sleep(1.5)

    debug = _find_window("调试面板")
    if not debug:
        print("未找到调试面板窗口")
        return
    _activate(debug)

    # 切换到实验室标签页（最后一个）
    _click_tab(debug, 295)
    _screenshot(debug, "lab_tab.png")

    # 切换到信息标签页
    _click_tab(debug, 215)
    _screenshot(debug, "info_tab.png")

    # 激活主窗口，准备切换标题栏样式
    _activate(sed)
    time.sleep(0.3)

    # 打开设置（假设导航到设置页）
    # 更简单的做法：直接通过设置文件修改标题栏样式并触发刷新
    # 这里我们返回调试面板，从实验室下拉框选择"仅图标"
    _activate(debug)
    _click_tab(debug, 295)
    time.sleep(0.3)

    # 点击标题栏样式下拉框（估算位置）
    pyautogui.click(debug.left + 400, debug.top + 220)
    time.sleep(0.3)
    # 选择最后一个"仅图标"
    pyautogui.click(debug.left + 400, debug.top + 280)
    time.sleep(1.0)

    _activate(sed)
    time.sleep(0.3)
    _screenshot(sed, "icon_only_header.png", height=80)


if __name__ == "__main__":
    main()
