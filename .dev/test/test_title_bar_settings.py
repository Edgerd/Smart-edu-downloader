# -*- coding: utf-8 -*-
"""测试标题栏设置功能。"""
import os
import time
import pyautogui
import pygetwindow as gw


def get_debug_window():
    """获取调试面板窗口。"""
    windows = gw.getWindowsWithTitle("调试面板")
    return windows[0] if windows else None


def get_sed_window():
    """获取 SED 主窗口。"""
    windows = gw.getWindowsWithTitle("SED")
    for w in windows:
        if w.title and "SED" in w.title:
            return w
    return None


def screenshot_window(window, filename):
    """截图指定窗口。"""
    output_dir = os.path.dirname(os.path.abspath(__file__))
    screenshot = pyautogui.screenshot(region=(window.left, window.top, window.width, window.height))
    path = os.path.join(output_dir, filename)
    screenshot.save(path)
    print(f"截图已保存: {path}")
    return path


def main():
    """测试标题栏自定义和字体样式。"""
    sed = get_sed_window()
    if not sed:
        print("未找到 SED 窗口")
        return

    # 确保调试面板打开
    debug = get_debug_window()
    if not debug:
        sed.activate()
        time.sleep(0.3)
        pyautogui.press('f12')
        time.sleep(1.0)
        debug = get_debug_window()

    if not debug:
        print("无法打开调试面板")
        return

    debug.activate()
    time.sleep(0.3)

    # 点击实验室标签（左侧底部区域）
    lab_x = debug.left + 50
    lab_y = debug.top + debug.height - 50
    pyautogui.click(lab_x, lab_y)
    time.sleep(0.5)

    # 截图实验室页面
    screenshot_window(debug, "lab_tab.png")

    # 点击自定义标题输入框（右侧中间区域）
    input_x = debug.left + 280
    input_y = debug.top + 180
    pyautogui.tripleClick(input_x, input_y)
    time.sleep(0.2)
    pyautogui.typewrite("HelloSED", interval=0.01)
    pyautogui.press('tab')
    time.sleep(0.5)

    # 截图主窗口验证标题
    sed.activate()
    time.sleep(0.3)
    screenshot_window(sed, "sed_custom_title.png")

    # 重新激活调试面板，勾选粗体
    debug.activate()
    time.sleep(0.3)
    # 粗体复选框在输入框下方
    bold_x = debug.left + 280
    bold_y = debug.top + 220
    pyautogui.click(bold_x, bold_y)
    time.sleep(0.3)

    # 截图主窗口验证粗体
    sed.activate()
    time.sleep(0.3)
    screenshot_window(sed, "sed_bold.png")

    # 勾选斜体
    debug.activate()
    time.sleep(0.3)
    italic_x = debug.left + 360
    italic_y = debug.top + 220
    pyautogui.click(italic_x, italic_y)
    time.sleep(0.3)

    # 截图主窗口验证粗体+斜体
    sed.activate()
    time.sleep(0.3)
    screenshot_window(sed, "sed_bold_italic.png")

    print("标题栏设置测试完成")


if __name__ == "__main__":
    main()
