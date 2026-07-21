# -*- coding: utf-8 -*-
"""将 SED 主窗口截屏保存到指定路径。"""
import sys
import pyautogui
import win32gui
import win32con

def find_sed_window():
    result = []
    def enum(hwnd, _):
        if win32gui.IsWindowVisible(hwnd):
            t = win32gui.GetWindowText(hwnd)
            if 'SED' in t or 'Smart' in t:
                result.append(hwnd)
    win32gui.EnumWindows(enum, None)
    return result[0] if result else None

hwnd = find_sed_window()
if not hwnd:
    print('SED window not found')
    sys.exit(1)
win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
win32gui.SetForegroundWindow(hwnd)
rect = win32gui.GetWindowRect(hwnd)
left, top, right, bottom = rect
path = sys.argv[1]
img = pyautogui.screenshot(region=(left, top, right-left, bottom-top))
img.save(path)
print('saved', path, rect)
