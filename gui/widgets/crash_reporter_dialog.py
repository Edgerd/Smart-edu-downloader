"""崩溃提示对话框。

提供程序崩溃后的可视化提示窗口，展示崩溃原因、出错位置以及完整堆栈，
并支持打开日志目录、复制错误信息、重新启动和关闭对话框。
"""
from core.i18n import _
import os
import subprocess
import sys
import threading
import webbrowser
from typing import Optional, Tuple
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QApplication, QDialog, QHBoxLayout, QLabel, QPlainTextEdit, QPushButton, QSizePolicy, QVBoxLayout, QWidget
try:
    from gui.fonts import body_font, monospace_font, title_font
except Exception:

    def body_font():
        """正文字体回退。"""
        return QFont('Microsoft YaHei', 10)

    def title_font():
        """标题字体回退。"""
        return QFont('Microsoft YaHei', 15, QFont.Bold)

    def monospace_font():
        """等宽字体回退。"""
        return QFont('Consolas', 10)
try:
    from gui.widgets.material_button import MaterialButton
except Exception:
    MaterialButton = None
def _load_primary_color() -> str:
    """加载当前主题主色，失败时回退到项目默认值。"""
    try:
        from gui.styles import load_primary_color
        return load_primary_color()
    except Exception:
        return '#1277DD'


def _load_background_color() -> str:
    """加载当前内容区背景色，失败时回退到项目默认值。"""
    try:
        from gui.styles import load_background_color
        return load_background_color()
    except Exception:
        return '#E8F4FD'


BUTTON_HEIGHT = 34
WINDOW_WIDTH = 520
WINDOW_HEIGHT = 380
WINDOW_HEIGHT_EXPANDED = 520


class _ProcessReaper:
    """异步回收通过 Popen 启动的外部进程，避免产生僵尸进程。"""

    _processes = []
    _lock = threading.Lock()

    @classmethod
    def watch(cls, process: subprocess.Popen) -> None:
        """监控一个 Popen 进程并在退出后回收。"""
        with cls._lock:
            cls._processes.append(process)

        def _wait_and_remove():
            try:
                process.wait(timeout=30)
            except Exception:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception:
                    pass
            with cls._lock:
                if process in cls._processes:
                    cls._processes.remove(process)

        threading.Thread(target=_wait_and_remove, daemon=True).start()


class CrashReporterDialog(QDialog):
    """崩溃提示对话框。"""

    _open_url_signal = pyqtSignal(str)

    def __init__(self, crash_log_path: str, project_root: Optional[str]=None, parent: Optional[QWidget]=None) -> None:
        """初始化崩溃提示对话框。"""
        super().__init__(parent)
        self._accent_color = _load_primary_color()
        self._background_color = _load_background_color()
        self._crash_log_path = crash_log_path
        self._project_root = project_root or self._calculate_project_root()
        self._summary = ''
        self._stack_text = ''
        self._exc_type = _('gui.widgets.crash_reporter_dialog.auto_003')
        self._exc_message = ''
        self._location = ''
        self._lineno = 0
        self._parse_log()
        self._init_ui()
        self._open_url_signal.connect(self._open_url)

    @staticmethod
    def _calculate_project_root() -> str:
        """基于当前文件位置推导项目根目录。"""
        current_file = os.path.realpath(__file__)
        return os.path.dirname(os.path.dirname(os.path.dirname(current_file)))

    def _parse_log(self) -> None:
        """解析崩溃日志文件。"""
        try:
            with open(self._crash_log_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            content = ''
        lines = content.splitlines()
        if not lines or not content.strip():
            self._summary = _('gui.widgets.crash_reporter_dialog.auto_001')
            self._stack_text = self._crash_log_path
            return
        self._summary = lines[0].strip()
        self._stack_text = '\n'.join(lines[1:]).strip()
        exc_type, exc_message, filepath, lineno = self._parse_summary(self._summary)
        self._exc_type = exc_type
        self._exc_message = exc_message
        self._location = filepath
        self._lineno = lineno

    @staticmethod
    def _parse_summary(summary: str) -> Tuple[str, str, str, int]:
        """从摘要行解析异常类型、消息、文件路径和行号。"""
        exc_type = _('gui.widgets.crash_reporter_dialog.auto_003')
        exc_message = summary
        filepath = ''
        lineno = 0
        if ' at ' not in summary:
            return (exc_type, exc_message, filepath, lineno)
        left, right = summary.rsplit(' at ', 1)
        if ':' not in right:
            return (exc_type, exc_message, filepath, lineno)
        path_part, line_part = right.rsplit(':', 1)
        try:
            lineno = int(line_part)
        except ValueError:
            path_part = right
        filepath = path_part
        exc_part = left
        if ': ' in exc_part:
            exc_type, exc_message = exc_part.split(': ', 1)
        else:
            exc_type = exc_part
        return (exc_type, exc_message, filepath, lineno)

    def _init_ui(self) -> None:
        """初始化界面。"""
        self.setWindowTitle(_('dialogs.crash_reporter.title'))
        self.setWindowFlags(Qt.Dialog | Qt.WindowCloseButtonHint | Qt.WindowStaysOnTopHint)
        self.setFixedSize(WINDOW_WIDTH, WINDOW_HEIGHT)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.setStyleSheet(f'QDialog {{ background-color: {self._background_color}; }}')
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(20, 20, 20, 16)
        self.setLayout(main_layout)
        self._build_header(main_layout)
        self._build_cause_section(main_layout)
        self._build_log_path_section(main_layout)
        self._build_detail_section(main_layout)
        self._build_button_section(main_layout)

    def _build_header(self, layout: QVBoxLayout) -> None:
        """构建顶部标题与提示语。"""
        self._title_label = QLabel(_('dialogs.crash_reporter.title'))
        self._title_label.setFont(title_font())
        self._title_label.setStyleSheet(f'color: {self._accent_color}; font-weight: bold;')
        layout.addWidget(self._title_label)
        hint_label = QLabel(_('dialogs.crash_reporter.intro'))
        hint_label.setFont(body_font())
        hint_label.setWordWrap(True)
        hint_label.setStyleSheet('color: #666;')
        layout.addWidget(hint_label)

    def _build_cause_section(self, layout: QVBoxLayout) -> None:
        """构建崩溃原因区域。"""
        cause_title = QLabel(_('dialogs.crash_reporter.cause_label'))
        cause_title.setFont(body_font())
        cause_title.setStyleSheet('color: #333; font-weight: bold;')
        layout.addWidget(cause_title)
        location_text = self._location or _('gui.widgets.crash_reporter_dialog.auto_002')
        if self._lineno > 0:
            location_text = f'{location_text}:{self._lineno}'
        cause_value = QLabel(_('dialogs.crash_reporter.exception_details_template', _exc_type=self._exc_type, _exc_message=self._exc_message, location_text=location_text))
        cause_value.setFont(body_font())
        cause_value.setWordWrap(True)
        cause_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        cause_value.setStyleSheet('color: #333;')
        layout.addWidget(cause_value)

    def _build_log_path_section(self, layout: QVBoxLayout) -> None:
        """构建崩溃日志路径标签区域。"""
        path_title = QLabel(_('dialogs.crash_reporter.log_path_label'))
        path_title.setFont(body_font())
        path_title.setStyleSheet('color: #333; font-weight: bold;')
        layout.addWidget(path_title)
        path_value = QLabel(self._crash_log_path)
        path_value.setFont(body_font())
        path_value.setWordWrap(True)
        path_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        path_value.setStyleSheet('color: #333;')
        layout.addWidget(path_value)

    def _build_detail_section(self, layout: QVBoxLayout) -> None:
        """构建可展开/折叠的详情区域。"""
        self._detail_edit = QPlainTextEdit(self)
        self._detail_edit.setFont(monospace_font())
        self._detail_edit.setReadOnly(True)
        self._detail_edit.setPlainText(self._stack_text or self._summary)
        self._detail_edit.setMinimumHeight(80)
        self._detail_edit.setVisible(False)
        self._detail_edit.setStyleSheet('\n            QPlainTextEdit {\n                background: #F8FAFC;\n                border: 1px solid #E0E8F0;\n                border-radius: 8px;\n                padding: 8px;\n                color: #333;\n            }\n        ')
        layout.addWidget(self._detail_edit, 1)
        self._toggle_btn = self._create_button(_('dialogs.crash_reporter.view_details'), primary=False)
        self._toggle_btn.clicked.connect(self._toggle_details)
        layout.addWidget(self._toggle_btn, 0, Qt.AlignLeft)

    def _build_button_section(self, layout: QVBoxLayout) -> None:
        """构建底部操作按钮区域。"""
        layout.addStretch(1)
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        open_log_btn = self._create_button(_('debug.tools.open_log_dir'))
        open_log_btn.clicked.connect(self._open_log_dir)
        button_layout.addWidget(open_log_btn)
        copy_btn = self._create_button(_('dialogs.crash_reporter.copy_error'))
        copy_btn.clicked.connect(self._copy_error_info)
        button_layout.addWidget(copy_btn)
        self._report_bug_btn = self._create_button(_('dialogs.crash_reporter.report_bug'), primary=False)
        self._report_bug_btn.clicked.connect(self._on_report_bug)
        button_layout.addWidget(self._report_bug_btn)
        restart_btn = self._create_button(_('dialogs.crash_reporter.restart'))
        restart_btn.clicked.connect(self._restart_app)
        button_layout.addWidget(restart_btn)
        close_btn = self._create_button(_('common.close'), primary=False)
        close_btn.clicked.connect(self.reject)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

    def _create_button(self, text: str, primary: bool=True) -> QPushButton:
        """创建操作按钮，优先使用 MaterialButton，失败回退到 QPushButton。"""
        if MaterialButton is not None:
            btn = MaterialButton(text, self)
            if not primary:
                btn.setVariant(MaterialButton.VARIANT_OUTLINED)
            btn.setFixedHeight(BUTTON_HEIGHT)
            return btn
        btn = QPushButton(text, self)
        btn.setFixedHeight(BUTTON_HEIGHT)
        if primary:
            btn.setStyleSheet(f'\n                QPushButton {{\n                    background: {self._accent_color};\n                    color: #FFFFFF;\n                    border: none;\n                    border-radius: 8px;\n                    padding: 0 14px;\n                    font-size: 12px;\n                }}\n                QPushButton:hover {{\n                    background: #1A6BC0;\n                }}\n                QPushButton:pressed {{\n                    background: #155A9E;\n                }}\n            ')
        else:
            btn.setStyleSheet(f'\n                QPushButton {{\n                    background: #FFFFFF;\n                    color: {self._accent_color};\n                    border: 1px solid {self._accent_color};\n                    border-radius: 8px;\n                    padding: 0 14px;\n                    font-size: 12px;\n                }}\n                QPushButton:hover {{\n                    background: #E8F4FD;\n                }}\n            ')
        return btn

    def update_theme_colors(self, primary: str, background: str) -> None:
        """响应主题色变化，刷新标题、背景和按钮颜色。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        self._accent_color = primary
        self._background_color = background
        if hasattr(self, '_title_label') and self._title_label is not None:
            self._title_label.setStyleSheet(f'color: {primary}; font-weight: bold;')
        self.setStyleSheet(f'QDialog {{ background-color: {background}; }}')
        # 已创建的按钮为 QPushButton 或 MaterialButton，重新应用样式较复杂；
        # 崩溃提示对话框通常在崩溃后显示，按钮会在下次创建时读取新主题色。

    def _toggle_details(self) -> None:
        """展开/折叠详细堆栈信息。"""
        visible = not self._detail_edit.isVisible()
        self._detail_edit.setVisible(visible)
        self._toggle_btn.setText(_('dialogs.crash_reporter.hide_details') if visible else _('dialogs.crash_reporter.view_details'))
        new_height = WINDOW_HEIGHT_EXPANDED if visible else WINDOW_HEIGHT
        self.setFixedSize(WINDOW_WIDTH, new_height)

    def _open_log_dir(self) -> None:
        """打开崩溃日志所在目录。"""
        log_dir = os.path.dirname(self._crash_log_path)
        if not os.path.isdir(log_dir):
            log_dir = self._project_root
        if sys.platform == 'win32':
            self._open_log_dir_windows(log_dir)
        elif sys.platform == 'darwin':
            self._run_command(['open', log_dir])
        else:
            self._open_log_dir_linux(log_dir)

    def _open_log_dir_windows(self, log_dir: str) -> None:
        """在 Windows 上打开日志目录或选中日志文件。"""
        if os.path.exists(self._crash_log_path):
            self._run_command(['explorer', f'/select,{os.path.normpath(self._crash_log_path)}'])
        else:
            self._run_command(['explorer', os.path.normpath(log_dir)])

    def _open_log_dir_linux(self, log_dir: str) -> None:
        """在 Linux 上打开日志目录。"""
        try:
            self._run_command(['xdg-open', log_dir])
        except Exception:
            webbrowser.open(f'file://{log_dir}')

    @staticmethod
    def _run_command(cmd: list) -> None:
        """以分离方式运行外部命令，忽略输出与错误。"""
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
        _ProcessReaper.watch(process)

    def _copy_error_info(self) -> None:
        """复制错误信息到剪贴板。"""
        text = _('dialogs.crash_reporter.summary_template', _summary=self._summary, arg1=self._stack_text or self._summary)
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            clipboard.setText(text)

    def _restart_app(self) -> None:
        """重新启动主程序并关闭对话框。"""
        main_path = os.path.join(self._project_root, 'main.py')
        try:
            process = subprocess.Popen([sys.executable, main_path], cwd=self._project_root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)
            _ProcessReaper.watch(process)
        except Exception:
            pass
        self.accept()

    def _on_report_bug(self) -> None:
        """点击“给作者捉虫”按钮后，后台检测网络并跳转反馈入口。"""
        if hasattr(self, '_report_bug_btn') and self._report_bug_btn is not None:
            self._report_bug_btn.setEnabled(False)
        threading.Thread(target=self._check_network_and_open, daemon=True).start()

    def _check_network_and_open(self) -> None:
        """检测 github.com 连通性，并通过信号回到主线程打开反馈链接。"""
        url = self._choose_report_url()
        self._open_url_signal.emit(url)

    def _choose_report_url(self) -> str:
        """根据 github.com 的连通性选择反馈链接。"""
        if self._can_reach_github():
            return 'https://github.com/Edgerd/Smart-edu-downloader/issues'
        return 'https://message.bilibili.com/#/whisper/mid3537111380658360'

    def _can_reach_github(self) -> bool:
        """通过 ping 检测是否可以访问 github.com。"""
        if sys.platform == 'win32':
            cmd = ['ping', 'github.com', '-n', '1', '-w', '2000']
        else:
            cmd = ['ping', 'github.com', '-c', '1', '-W', '2']
        try:
            result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            return result.returncode == 0
        except Exception:
            return False

    def _open_url(self, url: str) -> None:
        """在主线程中打开反馈链接并恢复按钮状态。"""
        try:
            webbrowser.open(url)
        except Exception:
            pass
        if hasattr(self, '_report_bug_btn') and self._report_bug_btn is not None:
            self._report_bug_btn.setEnabled(True)

def main() -> int:
    """独立测试入口。"""
    from PyQt5.QtWidgets import QApplication
    _ = QApplication(sys.argv)
    dialog = CrashReporterDialog('test.log')
    return dialog.exec()
if __name__ == '__main__':
    sys.exit(main())
