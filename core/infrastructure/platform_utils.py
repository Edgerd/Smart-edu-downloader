# -*- coding: utf-8 -*-
"""跨平台工具模块。

集中封装与操作系统相关的常用操作，包括打开文件/目录、获取系统特殊目录、
清理跨平台非法文件名、重启应用等，避免各 GUI/核心模块直接依赖 Windows
特有 API（如 ``os.startfile``、``winreg``）。
"""

import os
import platform
import shutil
import subprocess
import sys
from typing import Optional

from core.infrastructure.logger import log

# 平台标识在进程生命周期内不变，缓存避免重复调用 platform.system()
_PLATFORM = platform.system()


def get_platform() -> str:
    """获取当前操作系统标识（结果在模块加载时缓存）。

    Returns:
        str: ``windows``、``darwin`` 或 ``linux``。
    """
    system = _PLATFORM
    if system == "Windows":
        return "windows"
    if system == "Darwin":
        return "darwin"
    return "linux"


def _get_windows_known_folder(folder_id: str) -> Optional[str]:
    """通过 Windows 注册表读取已知文件夹路径。

    Args:
        folder_id: 注册表中的 Shell Folders 键名。

    Returns:
        str: 文件夹绝对路径；读取失败返回 ``None``。
    """
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders",
        )
        path = winreg.QueryValueEx(key, folder_id)[0]
        winreg.CloseKey(key)
        return path
    except Exception:
        return None


def get_system_downloads_dir() -> str:
    """获取系统默认下载目录。

    Windows 优先读取注册表 ``{374DE290-123F-4565-9164-39C4925E467B}``，
    失败或跨平台时回退到 ``~/Downloads``。

    Returns:
        str: 下载目录绝对路径。
    """
    if get_platform() == "windows":
        path = _get_windows_known_folder(
            "{374DE290-123F-4565-9164-39C4925E467B}"
        )
        if path:
            return path
    return os.path.join(os.path.expanduser("~"), "Downloads")


def get_system_desktop_dir() -> str:
    """获取系统桌面目录。

    Returns:
        str: 桌面目录绝对路径；无法获取时回退到用户主目录。
    """
    if get_platform() == "windows":
        path = _get_windows_known_folder("Desktop")
        if path:
            return path
    elif get_platform() == "darwin":
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.isdir(desktop):
            return desktop
    else:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        if os.path.isdir(desktop):
            return desktop
    return os.path.expanduser("~")


def get_system_start_menu_dir() -> Optional[str]:
    """获取开始菜单程序目录（仅 Windows 有效）。

    Returns:
        str: 开始菜单 ``Programs`` 目录；非 Windows 返回 ``None``。
    """
    if get_platform() != "windows":
        return None
    path = _get_windows_known_folder("Start Menu")
    if path:
        return os.path.join(path, "Programs")
    return None


def open_file(file_path: str) -> bool:
    """使用系统默认应用打开文件。

    Args:
        file_path: 要打开的文件路径。

    Returns:
        bool: 是否成功发起打开操作。
    """
    if not os.path.exists(file_path):
        return False
    try:
        if get_platform() == "windows":
            os.startfile(file_path)
        elif get_platform() == "darwin":
            subprocess.Popen(["open", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["xdg-open", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        log("WARNING", f"打开文件失败: {file_path} - {e}")
        return False


def open_directory(directory_path: str, select_file: Optional[str] = None) -> bool:
    """使用文件管理器打开目录，并尽可能选中指定文件。

    Args:
        directory_path: 要打开的目录路径。
        select_file: 要选中的文件路径（可选，仅 Windows 支持精确选中）。

    Returns:
        bool: 是否成功发起打开操作。
    """
    if select_file and os.path.exists(select_file):
        directory_path = os.path.dirname(select_file)
    if not os.path.isdir(directory_path):
        return False
    try:
        if get_platform() == "windows":
            if select_file and os.path.exists(select_file):
                subprocess.Popen(
                    ["explorer", f"/select,{os.path.normpath(select_file)}"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            else:
                os.startfile(os.path.normpath(directory_path))
        elif get_platform() == "darwin":
            target = select_file if select_file and os.path.exists(select_file) else directory_path
            subprocess.Popen(["open", target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.Popen(["xdg-open", directory_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception as e:
        log("WARNING", f"打开目录失败: {directory_path} - {e}")
        return False


def get_executable_path() -> str:
    """获取当前可执行文件路径。

    源码运行时返回 Python 解释器路径，PyInstaller 打包后返回 ``sys.executable``。

    Returns:
        str: 可执行文件绝对路径。
    """
    return sys.executable


def get_application_entry() -> str:
    """获取应用入口脚本或程序包路径。

    Returns:
        str: 源码运行时为 ``main.py`` 绝对路径；打包运行时为 ``sys.executable``。
    """
    if getattr(sys, "frozen", False):
        return sys.executable
    from core.infrastructure.path_resolver import get_project_root
    return os.path.join(get_project_root(), "main.py")


def restart_application() -> bool:
    """重启当前应用程序。

    根据运行环境构造正确的启动命令，并通过 ``subprocess.Popen`` 启动新进程。

    Returns:
        bool: 是否成功启动新进程。
    """
    try:
        executable = get_executable_path()
        entry = get_application_entry()
        if getattr(sys, "frozen", False):
            subprocess.Popen([executable], cwd=os.path.dirname(executable))
        else:
            subprocess.Popen([executable, entry], cwd=os.path.dirname(entry))
        return True
    except Exception as e:
        log("ERROR", f"重启应用失败: {e}")
        return False


def sanitize_filename(filename: str, max_length: int = 100) -> str:
    """清理文件名中的非法字符。

    统一替换 Windows、macOS、Linux 中可能导致路径问题或不可移植的字符，
    确保生成的文件名在主流文件系统上均可安全使用。

    Args:
        filename: 原始文件名（不含目录）。
        max_length: 最大允许长度，超出时截断。

    Returns:
        str: 清理后的文件名。
    """
    if not filename:
        return filename
    illegal_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
    for char in illegal_chars:
        filename = filename.replace(char, "_")
    filename = filename.strip()
    if len(filename) > max_length:
        filename = filename[:max_length]
    return filename


def get_default_ui_font_family() -> str:
    """获取跨平台默认 UI 字体族名称。

    当项目内置字体加载失败时，用于兜底显示。

    Returns:
        str: 适合当前平台的默认无衬线字体名称。
    """
    system = get_platform()
    if system == "windows":
        return "Microsoft YaHei"
    if system == "darwin":
        return "PingFang SC"
    return "Noto Sans CJK SC"


def get_default_monospace_font_family() -> str:
    """获取跨平台默认等宽字体族名称。

    Returns:
        str: 适合当前平台的默认等宽字体名称。
    """
    system = get_platform()
    if system == "windows":
        return "Consolas"
    if system == "darwin":
        return "Menlo"
    return "DejaVu Sans Mono"


def get_available_sound_players() -> list:
    """获取当前平台可用的外部音频播放器命令列表。

    Returns:
        list: 按优先级排序的命令名称列表。
    """
    if get_platform() == "darwin":
        return ["afplay"]
    if get_platform() == "linux":
        players = []
        for candidate in ["paplay", "aplay", "ffplay", "mpv"]:
            if shutil.which(candidate):
                players.append(candidate)
        return players
    return []
