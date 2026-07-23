# -*- coding: utf-8 -*-
"""
Smart-edu-downloader
作者: Edgerd
B站主页: https://space.bilibili.com/3537111380658360
"""

import sys
import os
import importlib
import platform
import subprocess

# 过滤 MMKV 日志（调试期间临时禁用以便查看错误）
if platform.system() == 'Windows' and False:
    try:
        import ctypes
        from ctypes import wintypes

        STD_OUTPUT_HANDLE = -11
        STD_ERROR_HANDLE = -12

        kernel32 = ctypes.windll.kernel32
        stdout_handle = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        stderr_handle = kernel32.GetStdHandle(STD_ERROR_HANDLE)

        INVALID_HANDLE_VALUE = wintypes.HANDLE(-1).value
        null_handle = kernel32.CreateFileW(
            'NUL',
            0x40000000,
            0x00000001 | 0x00000002,
            None,
            3,
            0x00000080,
            None
        )

        if null_handle != INVALID_HANDLE_VALUE:
            kernel32.SetStdHandle(STD_OUTPUT_HANDLE, null_handle)
            kernel32.SetStdHandle(STD_ERROR_HANDLE, null_handle)
    except Exception as e:
        print(f"过滤 MMKV 日志失败: {e}")


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 静默导入 qfluentwidgets，避免其 Pro 提示输出到控制台
import io
_old_stdout = sys.stdout
sys.stdout = io.StringIO()
try:
    import qfluentwidgets
except Exception:
    pass
finally:
    sys.stdout = _old_stdout

from core.infrastructure.version import VERSION
from core.infrastructure.logger import log

APP_NAME = f"SED - Smart-edu-downloader {VERSION} | 作者: Edgerd"


def check_dependencies():
    """检查项目依赖"""
    log("STEP", "检查依赖项...")
    
    required_packages = {
        'PyQt5': 'PyQt5库',
        'requests': '网络请求库',
        'bs4': 'HTML解析库',
        'fitz': 'PyMuPDF'
    }

    missing_packages = []
    for package, description in required_packages.items():
        try:
            importlib.import_module(package)
        except ImportError:
            missing_packages.append((package, description))

    if missing_packages:
        log("ERROR", "缺少依赖项:")
        for package, description in missing_packages:
            log("ERROR", f"  - {package}: {description}")
        log("ERROR", "请运行: pip install -r resources/requirements.txt")
        sys.exit(1)


def setup_dpi_awareness():
    """设置Windows DPI感知"""
    if platform.system() != "Windows":
        return
    
    try:
        import ctypes
        awareness = ctypes.c_int()
        try:
            ctypes.windll.shcore.GetProcessDpiAwareness(0, ctypes.byref(awareness))
            if awareness.value < 2:
                ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception as e:
        log("WARNING", f"DPI 设置失败: {e}")


def load_access_token():
    """加载Access Token"""
    try:
        from core.config.settings_manager import get_settings_manager
        settings_mgr = get_settings_manager()
        encrypted_token = settings_mgr.get("access_token", "")
        
        if not encrypted_token:
            return None
        
        try:
            from core.network.token_crypto import decrypt_token
            return decrypt_token(encrypted_token) or None
        except Exception:
            return encrypted_token or None
    except Exception as e:
        log("WARNING", f"加载 Access Token 失败: {e}")
        return None


def load_settings():
    """加载设置"""
    from core.config.settings_manager import get_settings_manager
    return get_settings_manager().get_all()


def save_settings(settings):
    """保存设置"""
    from core.config.settings_manager import get_settings_manager
    return get_settings_manager().update(settings)


def check_and_show_tip(skip_popup: bool = False):
    """检查并显示赞赏码。

    Args:
        skip_popup: 为 True 时仅递增启动次数，不弹出赞助对话框。
    """
    try:
        settings = load_settings()
        if not settings.get("show_tips_switch", True):
            return

        launch_count = settings.get("launch_count", 0) + 1
        settings["launch_count"] = launch_count
        save_settings(settings)

        if skip_popup:
            return

        should_show = launch_count == 1 or (launch_count >= 5 and (launch_count - 1) % 5 == 0)
        if should_show:
            from gui.widgets.donation_dialog import show_donation_dialog
            show_donation_dialog()
    except Exception as e:
        log("WARNING", f"显示赞赏码失败: {e}")


def main():
    """主函数"""
    settings = load_settings()
    is_first_run = not settings.get("first_run", False)

    check_dependencies()
    setup_dpi_awareness()

    from PyQt5.QtWidgets import QApplication, QDialog, QMessageBox
    from PyQt5.QtCore import Qt, QTimer, QTranslator, QLocale, QLibraryInfo
    from PyQt5.QtGui import QIcon

    app = QApplication(sys.argv)

    def _log_except_hook(exc_type, exc_value, exc_tb):
        import traceback, datetime
        with open('uncaught.log', 'a', encoding='utf-8') as f:
            f.write(f'{datetime.datetime.now()} UNCAUGHT EXCEPTION:\n')
            traceback.print_exception(exc_type, exc_value, exc_tb, file=f)
    sys.excepthook = _log_except_hook

    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)

    translator = QTranslator()
    qt_trans_dir = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    if translator.load(QLocale(QLocale.Chinese, QLocale.China), "qt", "_", qt_trans_dir):
        app.installTranslator(translator)

    from core.infrastructure.path_resolver import get_project_root
    icon_path = os.path.join(get_project_root(), "resources", "logo", "logo_48x48.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    from gui.fonts import init_fonts, body_font
    init_fonts()
    app.setFont(body_font())

    from core.i18n import set_language, _
    set_language(settings.get("language", "zh_CN"))

    # 初始化 Fluent 主题
    try:
        from qfluentwidgets import setTheme, Theme, setThemeColor
        from gui.styles import load_primary_color, apply_global_message_box_style

        accent_color = load_primary_color()
        setTheme(Theme.LIGHT)
        setThemeColor(accent_color)
        apply_global_message_box_style(app, accent_color)
    except Exception as e:
        log("ERROR", f"初始化 Fluent 主题失败: {e}")
        QMessageBox.critical(
            None,
            _("common.error"),
            _("main.init_fluent_theme_failed", error=str(e))
        )

    # 首次启动时弹出新手引导向导
    if is_first_run:
        from gui.welcome.wizard import WelcomeWizard

        wizard = WelcomeWizard()
        if wizard.exec() != QDialog.Accepted:
            reply = QMessageBox.question(
                None,
                _("common.confirm"),
                _("welcome_onboarding.common.exit_confirm"),
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                sys.exit(0)
            # 选择「否」则进入主界面，但保持首次运行状态，下次启动仍会弹出引导
        # 向导已持久化配置，重新加载设置以确保主窗口读取最新值
        settings = load_settings()

    from gui import MainWindow
    window = MainWindow()

    screen = app.primaryScreen().geometry()
    window_width = window.width()
    window_height = window.height()
    x = (screen.width() - window_width) // 2
    y = (screen.height() - window_height) // 2
    window.setGeometry(x, y, window_width, window_height)

    window.show()
    app.processEvents()
    window.setWindowState(window.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
    window.raise_()
    window.activateWindow()
    app.processEvents()

    def _start_crash_guard():
        """启动崩溃守护子进程，确保致命崩溃后提示工具能被触发。"""
        try:
            from core.infrastructure.path_resolver import get_crash_logs_dir
            crash_dir = get_crash_logs_dir()
            guard_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'core', 'infrastructure', 'crash_guard.py'
            )
            if not os.path.exists(guard_path):
                return
            kwargs = {
                'stdout': subprocess.DEVNULL,
                'stderr': subprocess.DEVNULL,
                'stdin': subprocess.DEVNULL,
            }
            if sys.platform == 'win32':
                kwargs['creationflags'] = (
                    subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
                )
            subprocess.Popen(
                [sys.executable, guard_path, '--parent-pid', str(os.getpid()),
                 '--crash-dir', crash_dir],
                **kwargs,
            )
        except Exception:
            pass

    def delayed_init():
        """延迟初始化。

        将耗时较长的核心模块创建、缓存清理等操作放到后台线程执行，
        避免阻塞 GUI 主线程导致窗口显示后未响应。
        """
        try:
            from core.infrastructure.path_resolver import migrate_all_old_data
            migrate_all_old_data()
        except Exception as e:
            log("ERROR", f"数据迁移失败: {e}")
            QMessageBox.warning(
                None,
                _("common.warning"),
                _("main.data_migration_failed", error=str(e))
            )

        from core.infrastructure.logger import setup_gui_logging
        setup_gui_logging()

        from core.ui.status_bar import get_status_manager
        status_manager = get_status_manager(window)
        status_manager.update_all_tooltips(window)

        def on_core_modules_ready(downloader, resource_lib):
            """核心模块后台初始化完成后的主线程回调。"""
            if downloader and resource_lib:
                try:
                    window.set_shared_instances(downloader, resource_lib)
                except Exception as e:
                    log("ERROR", f"注入核心实例失败: {e}")
            else:
                log("ERROR", "核心模块后台初始化失败，部分功能可能不可用")

            token = load_access_token()
            if not token and hasattr(window, 'navigate_to_setting_and_highlight_token'):
                QTimer.singleShot(500, window.navigate_to_setting_and_highlight_token)

            # 首次启动已在欢迎向导末尾展示赞助页面，不再弹出赞助弹窗
            check_and_show_tip(skip_popup=is_first_run)
            status_manager.set_ready_status()

        def on_initialization_error(message):
            log("ERROR", message)
            status_manager.set_error_status(message)
            status_manager.set_ready_status()

        from core.infrastructure.startup_initializer import StartupInitializer
        initializer = StartupInitializer(window)
        initializer.core_modules_ready.connect(on_core_modules_ready)
        initializer.error_occurred.connect(on_initialization_error)
        initializer.start()
    
    QTimer.singleShot(50, delayed_init)

    # 启动崩溃守护子进程，监控主进程异常退出并启动崩溃提示工具
    _start_crash_guard()

    rc = app.exec_()
    sys.exit(rc)


def example_switch_theme():
    """开关按钮主题色演示示例"""
    from gui.examples.switch_theme_demo import run_demo
    run_demo()


def example_qfluent_widgets():
    """qfluentwidgets 推荐组件综合演示"""
    from gui.examples.qfluent_widgets_demo import run_demo
    run_demo()


if __name__ == '__main__':
    from core.infrastructure.crash_handler import install_crash_handler
    install_crash_handler()
    main()
