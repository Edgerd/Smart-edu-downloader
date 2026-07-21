"""
控制台标签页组件

提供命令输入、执行和输出显示功能。
"""
from core.i18n import _
import ast
import os
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QMessageBox
from PyQt5.QtCore import Qt
from gui.fonts import monospace_font, get_pixel_family
from gui.styles import load_primary_color
from gui.widgets.custom_controls import ChineseLineEdit
from gui.widgets.material_button import MaterialButton
from gui.widgets import CustomContextMenu

class ConsoleTab(QWidget):
    """控制台标签页

    提供命令输入、执行和输出显示功能。
    """

    # 控制台固定深色主题色
    _CONSOLE_BG = "#0C0C0C"
    _CONSOLE_TEXT = "#00FF00"
    _CONSOLE_PROMPT = "#FFD700"
    _CONSOLE_ERROR = "#FF6B6B"
    _CONSOLE_BORDER = "#2D2D2D"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._accent_color = load_primary_color()
        self._init_ui()

    def _get_output_style(self) -> str:
        """获取控制台输出区域样式"""
        return f"""
            QTextEdit {{
                background: {self._CONSOLE_BG};
                color: {self._CONSOLE_TEXT};
                border: 1px solid {self._CONSOLE_BORDER};
                border-radius: 8px;
                padding: 8px;
                font-family: "{get_pixel_family()}";
            }}
        """

    def _get_input_style(self) -> str:
        """获取控制台输入框样式"""
        return f"""
            QLineEdit {{
                background: {self._CONSOLE_BG};
                color: {self._CONSOLE_TEXT};
                border: 1px solid {self._CONSOLE_BORDER};
                padding: 6px;
                border-radius: 8px;
                font-family: "{get_pixel_family()}";
            }}
            QLineEdit:focus {{
                border-color: {self._accent_color};
            }}
        """

    def _init_ui(self):
        """初始化UI"""
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(monospace_font())
        self.console_output.setStyleSheet(self._get_output_style())
        CustomContextMenu.setup_for_text_edit(self.console_output, monospace_font())
        layout.addWidget(self.console_output)
        input_layout = QHBoxLayout()
        self.console_input = ChineseLineEdit()
        self.console_input.setFont(monospace_font())
        self.console_input.setStyleSheet(self._get_input_style())
        self.console_input.setPlaceholderText(_('debug.console.placeholder'))
        self.console_input.returnPressed.connect(self.execute_command)
        input_layout.addWidget(self.console_input)
        self.execute_btn = MaterialButton(_('debug.console.execute'))
        self.execute_btn.setAccentColor(self._accent_color)
        self.execute_btn.setFixedWidth(60)
        self.execute_btn.setFixedHeight(32)
        self.execute_btn.clicked.connect(self.execute_command)
        input_layout.addWidget(self.execute_btn)
        layout.addLayout(input_layout)

    def console_log(self, message: str):
        """控制台输出"""
        self.console_output.append(message)
        self.console_output.ensureCursorVisible()

    def execute_command(self):
        """执行控制台命令"""
        command = self.console_input.text().strip()
        if not command:
            return
        self.console_input.clear()
        self.console_log(f'>>> {command}')
        cmd_lower = command.lower()
        if cmd_lower == 'hello world':
            self._show_easter_egg()
            return
        elif cmd_lower == 'help':
            self._show_help()
            return
        elif cmd_lower in ('close', 'exit', 'quit', 'q'):
            self._cmd_close()
            return
        elif cmd_lower == 'clear':
            self.console_output.clear()
            return
        elif cmd_lower == 'restart':
            self._cmd_restart()
            return
        elif cmd_lower == 'info':
            self._cmd_info()
            return
        elif cmd_lower == 'version':
            from core.infrastructure.version import VERSION
            self.console_log(f'SED - Smart-edu-downloader v{VERSION}')
            return
        elif cmd_lower == 'author':
            self.console_log(_('dialogs.about.author_name'))
            self.console_log(_('debug.console.bilibili_link_template', url='https://space.bilibili.com/3537111380658360'))
            return
        try:
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    result = ast.literal_eval(command)
                except (ValueError, SyntaxError):
                    restricted_globals = {'__name__': '__main__', '__builtins__': {'print': print, 'len': len, 'range': range, 'int': int, 'str': str, 'float': float, 'list': list, 'dict': dict, 'set': set, 'tuple': tuple, 'bool': bool, 'type': type, 'isinstance': isinstance, 'abs': abs, 'sum': sum, 'min': min, 'max': max, 'sorted': sorted, 'enumerate': enumerate, 'zip': zip, 'map': map, 'filter': filter}}
                    exec(command, restricted_globals)
                    result = restricted_globals.get('_', None)
            stdout_val = stdout_capture.getvalue()
            stderr_val = stderr_capture.getvalue()
            if stdout_val:
                self.console_log(stdout_val)
            if stderr_val:
                self.console_log(f'<span style="color: #FF6B6B;">{stderr_val}</span>')
            if result is not None:
                self.console_log(str(result))
        except Exception as e:
            self.console_log(f'<span style="color: #FF6B6B;">Error: {str(e)}</span>')

    def _show_help(self):
        """显示帮助信息"""
        help_text = _('gui.components.debug.console_tab.auto_001')
        self.console_log(help_text)

    def _cmd_close(self):
        """关闭程序命令"""
        self.console_log(_('gui.components.debug.console_tab.auto_002'))
        from gui.main_window import get_main_window
        main_window = get_main_window()
        if main_window:
            main_window.close()

    def _cmd_restart(self):
        """重启程序命令"""
        self.console_log(_('gui.components.debug.console_tab.auto_003'))
        from gui.main_window import get_main_window
        main_window = get_main_window()
        if main_window:
            main_window.close()
            os.execv(sys.executable, [sys.executable] + sys.argv)

    def _cmd_info(self):
        """显示程序信息"""
        import platform
        from core.infrastructure.version import VERSION
        from PyQt5.QtCore import QT_VERSION_STR
        info_text = _('debug.console.info_template', VERSION=VERSION, arg1=sys.version.split()[0], QT_VERSION_STR=QT_VERSION_STR, arg3=platform.system(), arg4=platform.release(), arg5=platform.machine())
        self.console_log(info_text)

    def _show_easter_egg(self):
        """显示彩蛋"""
        import random
        try:
            easter_egg_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'resources', 'hello world.txt')
            if os.path.exists(easter_egg_file):
                with open(easter_egg_file, 'r', encoding='utf-8') as f:
                    lines = [line.strip() for line in f.readlines() if line.strip()]
                if lines:
                    selected = random.choice(lines)
                    self.console_log('')
                    self.console_log(f'<span style="color: #00FFFF;">{selected}</span>')
                    self.console_log('')
                    return
            self.console_log('<span style="color: #00FFFF;">Hello World!</span>')
        except Exception as e:
            self.console_log(f'<span style="color: #00FFFF;">Hello World! ({e})</span>')

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新控制台标签页视觉元素。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色（控制台固定深色，不使用）。
        """
        self._accent_color = primary
        self.setStyleSheet("background: transparent;")
        if hasattr(self, 'execute_btn'):
            self.execute_btn.setAccentColor(primary)
        if hasattr(self, 'console_output'):
            self.console_output.setStyleSheet(self._get_output_style())
        if hasattr(self, 'console_input'):
            self.console_input.setStyleSheet(self._get_input_style())
