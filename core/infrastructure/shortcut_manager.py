# -*- coding: utf-8 -*-
"""系统快捷方式管理模块。

提供跨平台能力，在 Windows、macOS、Linux 的桌面和启动菜单创建/删除
应用程序快捷入口。
"""

import os
import stat
import sys
from typing import Dict, Optional

from core.infrastructure.logger import log
from core.infrastructure.path_resolver import get_project_root
from core.infrastructure.platform_utils import get_platform


_APP_NAME = "Smart edu downloader"
_APP_BUNDLE_ID = "com.smartedu.downloader"


def _get_executable_path() -> str:
    """返回当前可执行文件路径。

    Returns:
        可执行文件绝对路径。
    """
    if getattr(sys, "frozen", False):
        return sys.executable
    return sys.executable


def _get_script_path() -> Optional[str]:
    """返回项目入口脚本路径（源码运行时）。

    Returns:
        入口脚本绝对路径；打包运行时返回 ``None``。
    """
    if getattr(sys, "frozen", False):
        return None
    project_root = get_project_root()
    candidate = os.path.join(project_root, "main.py")
    if os.path.exists(candidate):
        return candidate
    return None


def _resolve_icon_path() -> Optional[str]:
    """解析用于快捷方式的图标路径。

    Returns:
        图标绝对路径；不存在时返回 ``None``。
    """
    project_root = get_project_root()
    candidates = [
        os.path.join(project_root, "resources", "logo", "logo_48x48.ico"),
        os.path.join(project_root, "resources", "logo", "logo_48x48.png"),
        os.path.join(project_root, "resources", "logo", "logo.svg"),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    return None


def _get_desktop_dir() -> Optional[str]:
    """获取当前用户桌面目录路径。

    Returns:
        桌面目录绝对路径；获取失败返回 ``None``。
    """
    system = get_platform()
    if system == "windows":
        return _get_windows_known_folder("Desktop")
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if os.path.isdir(desktop):
        return desktop
    return None


def _get_start_menu_dir() -> Optional[str]:
    """获取当前用户开始菜单/应用菜单目录路径。

    Returns:
        启动菜单目录绝对路径；获取失败返回 ``None``。
    """
    system = get_platform()
    if system == "windows":
        path = _get_windows_known_folder("Start Menu")
        if path:
            return os.path.join(path, "Programs")
        return None
    if system == "darwin":
        return os.path.join(os.path.expanduser("~"), "Applications")
    # Linux 遵循 XDG 规范
    data_home = os.environ.get(
        "XDG_DATA_HOME", os.path.join(os.path.expanduser("~"), ".local", "share")
    )
    return os.path.join(data_home, "applications")


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
    except Exception as e:
        log("WARNING", f"获取 Windows 已知文件夹失败: {e}")
        return None


def _create_windows_shortcut(
    shortcut_path: str,
    target_path: str,
    arguments: str = "",
    working_dir: str = "",
    icon_path: str = "",
    description: str = _APP_NAME,
) -> bool:
    """在 Windows 上创建一个 ``.lnk`` 快捷方式。

    Args:
        shortcut_path: 快捷方式保存路径（需以 ``.lnk`` 结尾）。
        target_path: 快捷方式指向的目标程序。
        arguments: 启动参数。
        working_dir: 工作目录。
        icon_path: 图标路径。
        description: 快捷方式描述。

    Returns:
        创建成功返回 ``True``，否则返回 ``False``。
    """
    try:
        import win32com.client
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortcut(shortcut_path)
        shortcut.TargetPath = target_path
        if arguments:
            shortcut.Arguments = arguments
        if working_dir:
            shortcut.WorkingDirectory = working_dir
        if icon_path:
            shortcut.IconLocation = icon_path
        shortcut.Description = description
        shortcut.save()
        return True
    except Exception as e:
        log("WARNING", f"创建快捷方式失败 ({shortcut_path}): {e}")
        return False


def _create_macos_shortcut(
    shortcut_path: str,
    target_path: str,
    arguments: str = "",
    working_dir: str = "",
    icon_path: str = "",
    description: str = _APP_NAME,
) -> bool:
    """在 macOS 上创建可执行启动脚本（``.command``）。

    源码运行时生成调用 Python 解释器的脚本；打包运行时直接打开 app bundle。

    Args:
        shortcut_path: 快捷方式保存路径（需以 ``.command`` 结尾）。
        target_path: 可执行文件路径。
        arguments: 启动参数。
        working_dir: 工作目录。
        icon_path: 图标路径（暂不使用）。
        description: 描述（写入脚本注释）。

    Returns:
        创建成功返回 ``True``，否则返回 ``False``。
    """
    try:
        lines = [
            "#!/bin/bash",
            f"# {description}",
            "cd \"{0}\"".format(working_dir or os.path.dirname(target_path)),
        ]
        if arguments:
            lines.append('"{0}" {1} &'.format(target_path, arguments))
        else:
            lines.append('"{0}" &'.format(target_path))
        lines.append("exit 0")
        with open(shortcut_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        os.chmod(shortcut_path, os.stat(shortcut_path).st_mode | stat.S_IXUSR)
        return True
    except Exception as e:
        log("WARNING", f"创建 macOS 快捷方式失败 ({shortcut_path}): {e}")
        return False


def _create_linux_shortcut(
    shortcut_path: str,
    target_path: str,
    arguments: str = "",
    working_dir: str = "",
    icon_path: str = "",
    description: str = _APP_NAME,
) -> bool:
    """在 Linux 上创建一个 ``.desktop`` 启动器。

    Args:
        shortcut_path: 快捷方式保存路径（需以 ``.desktop`` 结尾）。
        target_path: 可执行文件路径。
        arguments: 启动参数。
        working_dir: 工作目录。
        icon_path: 图标路径。
        description: 快捷方式描述。

    Returns:
        创建成功返回 ``True``，否则返回 ``False``。
    """
    try:
        exec_line = f'"{target_path}"'
        if arguments:
            exec_line = f'"{target_path}" {arguments}'
        content = [
            "[Desktop Entry]",
            f"Name={_APP_NAME}",
            f"Comment={description}",
            f"Exec={exec_line}",
            f"Icon={icon_path or 'application-x-executable'}",
            "Type=Application",
            "Terminal=false",
        ]
        if working_dir:
            content.append(f"Path={working_dir}")
        with open(shortcut_path, "w", encoding="utf-8") as f:
            f.write("\n".join(content) + "\n")
        os.chmod(
            shortcut_path,
            os.stat(shortcut_path).st_mode | stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR,
        )
        return True
    except Exception as e:
        log("WARNING", f"创建 Linux 快捷方式失败 ({shortcut_path}): {e}")
        return False


def _create_shortcut(
    shortcut_path: str,
    target_path: str,
    arguments: str = "",
    working_dir: str = "",
    icon_path: str = "",
    description: str = _APP_NAME,
) -> bool:
    """根据当前平台创建对应格式的快捷方式。

    Returns:
        创建成功返回 ``True``，否则返回 ``False``。
    """
    system = get_platform()
    if system == "windows":
        return _create_windows_shortcut(
            shortcut_path, target_path, arguments, working_dir, icon_path, description
        )
    if system == "darwin":
        return _create_macos_shortcut(
            shortcut_path, target_path, arguments, working_dir, icon_path, description
        )
    return _create_linux_shortcut(
        shortcut_path, target_path, arguments, working_dir, icon_path, description
    )


def create_shortcuts(
    create_desktop: bool = False,
    create_start_menu: bool = False,
) -> Dict[str, bool]:
    """按需创建桌面和/或启动菜单快捷方式。

    Args:
        create_desktop: 是否在桌面创建快捷方式。
        create_start_menu: 是否在启动菜单创建快捷方式。

    Returns:
        包含 ``desktop`` 与 ``start_menu`` 创建结果的字典。
    """
    results: Dict[str, bool] = {"desktop": False, "start_menu": False}
    if not (create_desktop or create_start_menu):
        return results

    target_path = _get_executable_path()
    arguments = ""
    working_dir = os.path.dirname(target_path)
    script_path = _get_script_path()
    if script_path:
        arguments = f'"{script_path}"'
        working_dir = get_project_root()

    icon_path = _resolve_icon_path() or ""
    system = get_platform()

    if create_desktop:
        desktop_dir = _get_desktop_dir()
        if desktop_dir:
            if system == "windows":
                shortcut_path = os.path.join(desktop_dir, f"{_APP_NAME}.lnk")
            elif system == "darwin":
                shortcut_path = os.path.join(desktop_dir, f"{_APP_NAME}.command")
            else:
                shortcut_path = os.path.join(desktop_dir, f"{_APP_NAME}.desktop")
            results["desktop"] = _create_shortcut(
                shortcut_path,
                target_path,
                arguments,
                working_dir,
                icon_path,
            )

    if create_start_menu:
        start_menu_dir = _get_start_menu_dir()
        if start_menu_dir:
            os.makedirs(start_menu_dir, exist_ok=True)
            if system == "windows":
                shortcut_path = os.path.join(
                    start_menu_dir, _APP_NAME, f"{_APP_NAME}.lnk"
                )
            elif system == "darwin":
                shortcut_path = os.path.join(start_menu_dir, f"{_APP_NAME}.command")
            else:
                shortcut_path = os.path.join(start_menu_dir, f"{_APP_NAME}.desktop")
            os.makedirs(os.path.dirname(shortcut_path), exist_ok=True)
            results["start_menu"] = _create_shortcut(
                shortcut_path,
                target_path,
                arguments,
                working_dir,
                icon_path,
            )

    return results


def remove_shortcuts(
    remove_desktop: bool = False,
    remove_start_menu: bool = False,
) -> Dict[str, bool]:
    """按需删除桌面和/或启动菜单快捷方式。

    Args:
        remove_desktop: 是否删除桌面快捷方式。
        remove_start_menu: 是否删除开始菜单快捷方式。

    Returns:
        包含 ``desktop`` 与 ``start_menu`` 删除结果的字典。
    """
    results: Dict[str, bool] = {"desktop": False, "start_menu": False}
    system = get_platform()

    if remove_desktop:
        desktop_dir = _get_desktop_dir()
        if desktop_dir:
            if system == "windows":
                shortcut_path = os.path.join(desktop_dir, f"{_APP_NAME}.lnk")
            elif system == "darwin":
                shortcut_path = os.path.join(desktop_dir, f"{_APP_NAME}.command")
            else:
                shortcut_path = os.path.join(desktop_dir, f"{_APP_NAME}.desktop")
            try:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    results["desktop"] = True
            except Exception as e:
                log("WARNING", f"删除桌面快捷方式失败: {e}")

    if remove_start_menu:
        start_menu_dir = _get_start_menu_dir()
        if start_menu_dir:
            if system == "windows":
                shortcut_path = os.path.join(
                    start_menu_dir, _APP_NAME, f"{_APP_NAME}.lnk"
                )
            elif system == "darwin":
                shortcut_path = os.path.join(start_menu_dir, f"{_APP_NAME}.command")
            else:
                shortcut_path = os.path.join(start_menu_dir, f"{_APP_NAME}.desktop")
            try:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    results["start_menu"] = True
                folder = os.path.dirname(shortcut_path)
                if os.path.isdir(folder) and not os.listdir(folder):
                    os.rmdir(folder)
            except Exception as e:
                log("WARNING", f"删除启动菜单快捷方式失败: {e}")

    return results
