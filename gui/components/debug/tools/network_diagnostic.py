"""
网络诊断工具组件

提供HTTP连接测试、DNS解析测试、延迟测试和代理配置显示功能。
"""
import socket
import time
from datetime import datetime
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGroupBox, QTextEdit, QGridLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from gui.fonts import body_font, small_font
from gui.widgets.material_button import MaterialButton
from gui.styles import load_primary_color
from core.i18n import _
from core.network.http_client import get_http_client
import requests

class NetworkTestThread(QThread):
    """网络测试线程"""
    finished = pyqtSignal(str)

    def __init__(self, test_type, target=''):
        super().__init__()
        self.test_type = test_type
        self.target = target
        self._running = True

    def stop(self):
        """请求线程协作式停止。"""
        self._running = False

    def is_running(self):
        """返回线程是否仍在运行。"""
        return self._running

    def run(self):
        """执行测试"""
        try:
            if self.test_type == 'http':
                result = self._test_http()
            elif self.test_type == 'dns':
                result = self._test_dns()
            elif self.test_type == 'latency':
                result = self._test_latency()
            elif self.test_type == 'proxy':
                result = self._test_proxy()
            else:
                result = _('debug.tools.network.unknown_test_template', test_type=self.test_type)
        except Exception as e:
            result = _('debug.tools.network.test_failed_template', arg0=str(e))
        if self._running:
            self.finished.emit(result)

    def _test_http(self):
        """测试HTTP连接"""
        start = time.time()
        try:
            client = get_http_client()
            with client.get('https://www.baidu.com', timeout=10) as response:
                elapsed = (time.time() - start) * 1000
                return f"{_('gui.components.debug.tools.network_diagnostic.fstr_014')}{response.status_code}{_('gui.components.debug.tools.network_diagnostic.fstr_005')}{elapsed:.2f}{_('gui.components.debug.tools.network_diagnostic.fstr_012')}{datetime.now().strftime('%H:%M:%S')}"
        except requests.exceptions.RequestException as e:
            return f"{_('gui.components.debug.tools.network_diagnostic.fstr_017')}{str(e)}"

    def _test_dns(self):
        """测试DNS解析"""
        domain = self.target or 'www.baidu.com'
        start = time.time()
        try:
            ip = socket.gethostbyname(domain)
            elapsed = (time.time() - start) * 1000
            return f"{_('gui.components.debug.tools.network_diagnostic.fstr_013')}{domain}{_('gui.components.debug.tools.network_diagnostic.fstr_003')}{ip}{_('gui.components.debug.tools.network_diagnostic.fstr_008')}{elapsed:.2f}{_('gui.components.debug.tools.network_diagnostic.fstr_012')}{datetime.now().strftime('%H:%M:%S')}"
        except socket.gaierror as e:
            return f"{_('gui.components.debug.tools.network_diagnostic.fstr_016')}{domain}{_('gui.components.debug.tools.network_diagnostic.fstr_009')}{str(e)}"

    def _test_latency(self):
        """测试网络延迟"""
        times = []
        for i in range(3):
            if not self._running:
                break
            start = time.time()
            try:
                client = get_http_client()
                with client.head('https://www.baidu.com', timeout=5):
                    elapsed = (time.time() - start) * 1000
                    times.append(elapsed)
            except requests.exceptions.RequestException:
                pass
            if self._running and i < 2:
                time.sleep(0.5)
        if times:
            avg = sum(times) / len(times)
            min_t = min(times)
            max_t = max(times)
            return f"{_('gui.components.debug.tools.network_diagnostic.fstr_015')}{len(times)}{_('gui.components.debug.tools.network_diagnostic.fstr_006')}{avg:.2f}{_('gui.components.debug.tools.network_diagnostic.fstr_011')}{min_t:.2f}{_('gui.components.debug.tools.network_diagnostic.fstr_010')}{max_t:.2f}{_('gui.components.debug.tools.network_diagnostic.fstr_012')}{datetime.now().strftime('%H:%M:%S')}"
        else:
            return _('gui.components.debug.tools.network_diagnostic.auto_018')

    def _test_proxy(self):
        """显示代理配置"""
        import os
        http_proxy = os.environ.get('HTTP_PROXY', os.environ.get('http_proxy', _('gui.components.debug.tools.network_diagnostic.auto_020')))
        https_proxy = os.environ.get('HTTPS_PROXY', os.environ.get('https_proxy', _('gui.components.debug.tools.network_diagnostic.auto_020')))
        no_proxy = os.environ.get('NO_PROXY', os.environ.get('no_proxy', _('gui.components.debug.tools.network_diagnostic.auto_020')))
        return f"{_('gui.components.debug.tools.network_diagnostic.fstr_018')}" * 40 + f"{_('gui.components.debug.tools.network_diagnostic.fstr_002')}{http_proxy}{_('gui.components.debug.tools.network_diagnostic.fstr_001')}{https_proxy}{_('gui.components.debug.tools.network_diagnostic.fstr_004')}{no_proxy}{_('gui.components.debug.tools.network_diagnostic.fstr_007')}{datetime.now().strftime('%H:%M:%S')}"

class NetworkDiagnosticWidget(QWidget):
    """网络诊断工具组件"""

    def __init__(self, parent=None, show_title: bool = True):
        super().__init__(parent)
        self._show_title = show_title
        self._init_ui()
        self.current_thread = None

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        accent_color = load_primary_color()
        if self._show_title:
            title = QLabel(_('debug.tools.network.title'))
            title.setFont(body_font())
            title.setStyleSheet('font-weight: bold; color: #333;')
            layout.addWidget(title)
        grid = QGridLayout()
        grid.setSpacing(10)
        self.btn_http = MaterialButton(_('debug.tools.network.test_http'), variant=MaterialButton.VARIANT_OUTLINED)
        self.btn_http.setAccentColor(accent_color)
        self.btn_http.setFixedHeight(36)
        self.btn_http.clicked.connect(lambda: self._start_test('http'))
        grid.addWidget(self.btn_http, 0, 0)
        self.btn_dns = MaterialButton(_('debug.tools.network.test_dns'), variant=MaterialButton.VARIANT_OUTLINED)
        self.btn_dns.setAccentColor(accent_color)
        self.btn_dns.setFixedHeight(36)
        self.btn_dns.clicked.connect(lambda: self._start_test('dns'))
        grid.addWidget(self.btn_dns, 0, 1)
        self.btn_latency = MaterialButton(_('debug.tools.network.test_latency'), variant=MaterialButton.VARIANT_OUTLINED)
        self.btn_latency.setAccentColor(accent_color)
        self.btn_latency.setFixedHeight(36)
        self.btn_latency.clicked.connect(lambda: self._start_test('latency'))
        grid.addWidget(self.btn_latency, 1, 0)
        self.btn_proxy = MaterialButton(_('debug.tools.network.view_proxy'), variant=MaterialButton.VARIANT_OUTLINED)
        self.btn_proxy.setAccentColor(accent_color)
        self.btn_proxy.setFixedHeight(36)
        self.btn_proxy.clicked.connect(lambda: self._start_test('proxy'))
        grid.addWidget(self.btn_proxy, 1, 1)
        layout.addLayout(grid)
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setFont(small_font())
        self.result_text.setStyleSheet('\n            QTextEdit {\n                background: #F8FAFC;\n                border: 1px solid #E0E8F0;\n                border-radius: 4px;\n                padding: 10px;\n                color: #333;\n            }\n        ')
        self.result_text.setPlaceholderText(_('debug.tools.network.placeholder'))
        layout.addWidget(self.result_text)

    def _start_test(self, test_type):
        """开始测试"""
        self.result_text.setText(_('debug.tools.network.testing'))
        if self.current_thread and self.current_thread.isRunning():
            self.current_thread.stop()
            self.current_thread.wait(1000)
        self.current_thread = NetworkTestThread(test_type)
        self.current_thread.finished.connect(self._on_test_finished)
        self.current_thread.start()

    def _on_test_finished(self, result):
        """测试完成回调"""
        self.result_text.setText(result)

    def update_theme_colors(self, primary: str, background: str):
        """响应主题色变化，刷新网络诊断工具视觉元素。

        Args:
            primary: 新的主题主色。
            background: 新的内容区背景色。
        """
        for btn in (getattr(self, 'btn_http', None),
                    getattr(self, 'btn_dns', None),
                    getattr(self, 'btn_latency', None),
                    getattr(self, 'btn_proxy', None)):
            if btn is not None:
                btn.setAccentColor(primary)