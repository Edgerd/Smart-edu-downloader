# -*- coding: utf-8 -*-
"""检查 SED 窗口状态与已有截图。"""

import os
import sys
import glob

try:
    import win32gui
    import win32con
    HAS_WIN32 = True
except Exception:
    HAS_WIN32 = False


def find_sed_window():
    """查找可见的 SED 窗口句柄。"""
    result = []

    def enum(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            text = win32gui.GetWindowText(hwnd)
            if 'SED' in text or 'Smart' in text or 'smart' in text:
                result.append((hwnd, text))

    win32gui.EnumWindows(enum, None)
    return result


def main():
    print('HAS_WIN32:', HAS_WIN32)

    if HAS_WIN32:
        windows = find_sed_window()
        print('SED windows:', windows)
        if windows:
            hwnd, text = windows[0]
            rect = win32gui.GetWindowRect(hwnd)
            print('window:', text, 'rect:', rect)
            print('placement:', win32gui.GetWindowPlacement(hwnd))

    screenshot_dir = r'C:\Users\Administrator\AppData\Local\Temp\Smart-edu-downloader\verification_screenshots'
    print('screenshot_dir exists:', os.path.isdir(screenshot_dir))
    if os.path.isdir(screenshot_dir):
        files = sorted(glob.glob(os.path.join(screenshot_dir, '*.png')))
        for f in files:
            print('existing:', f, os.path.getsize(f))


if __name__ == '__main__':
    main()
