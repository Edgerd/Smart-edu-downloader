"""
下载管理模块
"""
from core.i18n import _
import os
import time
import threading
import traceback

import requests
from PyQt5.QtCore import QObject, pyqtSignal

from core.infrastructure.logger import log
from core.infrastructure.path_resolver import get_download_tasks_file, get_project_root
from core.download.sound_player import SoundPlayer
from core.download.file_naming import FileNameGenerator
from core.download.file_categorizer import FileCategorizer
from core.download.download_verifier import DownloadVerifier
from core.download.download_history import DownloadHistory, DownloadRecord
from core.resource.resource_library import URLFixer
from core.network.http_client import get_http_client

def format_bytes(size: float) -> str:
    """将数据单位进行格式化 - 完全按照原版 format_bytes()"""
    for x in [_('core.download.downloader.auto_004'), 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f'{size:3.1f} {x}'
        size /= 1024.0
    return f'{size:3.1f} PB'

def add_bookmarks(pdf_path: str, chapters: list) -> None:
    """给 PDF 添加书签 - 使用 PyMuPDF"""
    try:
        if not chapters:
            log('INFO', '书签章节列表为空，跳过添加')
            return
        import fitz
        doc = fitz.open(pdf_path)
        try:
            toc = []

            def build_toc(chapter_list, level=1):
                for chapter in chapter_list:
                    title = chapter.get('title', _('core.download.downloader.auto_007'))
                    p_index = chapter.get('page_index')
                    if p_index is None:
                        log('WARNING', f'章节 "{title}" 的页码索引无效，已跳过')
                        continue
                    try:
                        page_num = int(p_index)
                    except (ValueError, TypeError) as e:
                        log('WARNING', f'章节 "{title}" 页码转换失败: {e}')
                        continue
                    if page_num < 1 or page_num > doc.page_count:
                        log('WARNING', f'章节 "{title}" 的页码 {page_num} 超出范围(1-{doc.page_count})，已跳过')
                        continue
                    toc.append([level, title, page_num])
                    if chapter.get('children'):
                        build_toc(chapter['children'], level + 1)
            build_toc(chapters)
            if toc:
                doc.set_toc(toc)
                try:
                    doc.save(pdf_path, incremental=True, encryption=fitz.PDF_ENCRYPT_KEEP)
                except Exception as first_err:
                    log('DEBUG', f'增量保存失败，回退到临时文件方式: {first_err}')
                    tmp_path = pdf_path + '.tmp'
                    try:
                        doc.save(tmp_path, garbage=0, encryption=fitz.PDF_ENCRYPT_KEEP)
                        os.replace(tmp_path, pdf_path)
                        log('SUCCESS', f'已添加 {len(toc)} 个书签到 PDF（临时文件回退方式）')
                        return
                    except Exception as fallback_err:
                        try:
                            if os.path.exists(tmp_path):
                                os.remove(tmp_path)
                        except Exception:
                            pass
                        raise fallback_err
                log('SUCCESS', f'已添加 {len(toc)} 个书签到 PDF')
            else:
                log('WARNING', '没有有效的书签条目可添加')
        finally:
            doc.close()
    except Exception as e:
        log('ERROR', f'添加书签出错: {e}')
        traceback.print_exc()

class Downloader(QObject):
    """下载管理器 - 完全按照原版逻辑实现"""
    task_added = pyqtSignal(str)
    task_updated = pyqtSignal(str)
    task_completed = pyqtSignal(str)
    task_failed = pyqtSignal(str, str)
    all_tasks_completed = pyqtSignal()
    progress_updated = pyqtSignal(float, str)
    ask_download_dir = pyqtSignal(str, str)
    play_download_sound_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.tasks = {}
        self.task_list = []
        self.download_states = {}
        self._http = get_http_client()
        self.access_token = self._http.get_access_token()
        self.headers = self._http.get_headers()
        self._is_running = False
        self._worker_thread = None
        self._lock = threading.Lock()
        self._state_lock = threading.Lock()
        self._worker_lock = threading.Lock()
        self._cancel_events = {}
        self.app_closing = False
        self._task_event = threading.Event()
        self._cached_all_downloaded = 0
        self._cached_all_total = 0
        self._cached_finished_count = 0
        self._download_dir = None
        self._tasks_file = get_download_tasks_file()
        self.max_queue_size = 500
        self._pending_dir_selections = {}
        self._dir_selection_results = {}
        self._last_emitted_progress = -1.0
        self._load_download_dir()
        self._load_ssl_verify()
        self._load_tasks()

    def _load_ssl_verify(self):
        """从设置加载 SSL 证书验证开关并应用到 HTTP 客户端。"""
        try:
            from core.config.settings_manager import get_settings_manager
            settings_mgr = get_settings_manager()
            ssl_verify = settings_mgr.get('ssl_verify', True)
            self._http.set_ssl_verify(bool(ssl_verify))
            log('DEBUG', f"从设置加载 SSL 验证开关: {ssl_verify}")
        except Exception as e:
            log('WARNING', f'加载 SSL 验证设置失败: {e}')

    def _is_url_allowed(self, url: str) -> bool:
        """检查URL是否在允许的域名白名单内

        白名单由两部分组成：
        1. 内置的官方域名（ALLOWED_DOMAINS），不可修改
        2. 用户在设置页面中自定义添加的域名（custom_allowed_domains）
        当用户开启"允许任意域名下载"开关（allow_any_domain_download）时跳过校验。
        """
        from core.config.custom_domain_whitelist import is_url_allowed
        return is_url_allowed(url)

    def _is_path_safe(self, file_path: str, base_dir: str) -> bool:
        """检查文件路径是否安全（防止路径遍历攻击）"""
        try:
            abs_file_path = os.path.realpath(file_path)
            abs_base_dir = os.path.realpath(base_dir)
            if not abs_file_path.startswith(abs_base_dir + os.sep) and abs_file_path != abs_base_dir:
                log('WARNING', f'路径遍历检测: {file_path} 不在允许的目录内')
                return False
            return True
        except Exception as e:
            log('ERROR', f'路径安全检查失败: {e}')
            return False

    def _load_download_dir(self):
        """从设置加载下载目录"""
        try:
            from core.config.settings_manager import get_settings_manager, get_default_download_dir
            settings_mgr = get_settings_manager()
            self._download_dir = settings_mgr.get('download_dir', '')
            if not self._download_dir or not os.path.exists(self._download_dir):
                self._download_dir = get_default_download_dir()
                os.makedirs(self._download_dir, exist_ok=True)
        except Exception:
            self._download_dir = get_default_download_dir()
            os.makedirs(self._download_dir, exist_ok=True)

    def set_download_dir(self, dir_path):
        """设置下载目录"""
        if dir_path and os.path.exists(dir_path):
            self._download_dir = dir_path
        elif dir_path:
            os.makedirs(dir_path, exist_ok=True)
            self._download_dir = dir_path

    def get_download_dir(self):
        """获取下载目录"""
        return self._download_dir or os.path.join(get_project_root(), 'downloads')

    def set_access_token(self, token):
        """设置访问令牌 - 委托给统一 HTTP 客户端"""
        self._http.set_access_token(token)
        self.access_token = self._http.get_access_token()
        self.headers = self._http.get_headers()

    def _load_access_token_from_settings(self):
        """从设置管理器加载并解密 access token"""
        try:
            from core.config.settings_manager import get_settings_manager
            from core.network.token_crypto import decrypt_token
            settings_mgr = get_settings_manager()
            encrypted_token = settings_mgr.get('access_token', '')
            if encrypted_token:
                token = decrypt_token(encrypted_token)
                if token:
                    self.set_access_token(token)
                    log('DEBUG', f'从设置管理器加载 Access Token，长度: {len(token)}')
                    return token
        except Exception as e:
            log('WARNING', f'从设置管理器加载 Access Token 失败: {e}')
        return None

    def set_proxy(self, proxy_config):
        """设置代理 - 委托给统一 HTTP 客户端

        Args:
            proxy_config: 代理配置字典，包含 type, host, port, username, password
                       如果为 None 或 False，则禁用代理
        """
        self._http.set_proxy(proxy_config)

    def add_download_task(self, url, title=None, chapters=None, save_path=None):
        """添加下载任务"""
        log('STEP', f"添加下载任务: {title or '未命名'}")
        if not self._is_url_allowed(url):
            confirm_enabled = True
            try:
                from core.config.settings_manager import get_settings_manager
                confirm_enabled = get_settings_manager().get('confirm_non_whitelist_download', True)
            except Exception:
                pass
            if confirm_enabled:
                from PyQt5.QtWidgets import QMessageBox
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc.lower()
                reply = QMessageBox.warning(None, _('download.security_reminder'), _('download.non_whitelist_warning_template', domain=domain, url=url[:120]), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    log('INFO', f'用户取消了非白名单域名下载: {url[:50]}...')
                    return None
                log('WARNING', f'用户确认继续下载非白名单域名: {domain}')
            else:
                log('ERROR', f'URL不在允许的域名白名单中: {url[:50]}...')
                raise ValueError(_('core.download.downloader.auto_001'))
        with self._lock:
            if len(self.tasks) >= self.max_queue_size:
                log('WARNING', f"{_('core.download.downloader.fstr_001')}{self.max_queue_size}{_('core.download.downloader.fstr_002')}")
                raise RuntimeError(f"{_('core.download.downloader.fstr_001')}{self.max_queue_size}{_('core.download.downloader.fstr_002')}")
        task_id = f'task_{time.time_ns()}'
        if save_path:
            save_dir = os.path.dirname(save_path)
            if save_dir and (not os.path.exists(save_dir)):
                os.makedirs(save_dir, exist_ok=True)
                log('DEBUG', f'创建目录: {save_dir}')
        else:
            settings = self._load_settings()
            save_dir = self.get_download_dir()
            if settings.get('ask_download_dir', True) and (not save_path):
                from PyQt5.QtWidgets import QFileDialog
                default_dir = save_dir or os.path.expanduser('~')
                selected_dir = QFileDialog.getExistingDirectory(None, _('core.downloader.choose_download_location_template', title=title or _('common.unnamed')), default_dir)
                disable_ask = False
                if not selected_dir:
                    log('INFO', f"用户取消了下载任务: {title or '未命名'}")
                    return None
                if disable_ask:
                    settings['ask_download_dir'] = False
                    try:
                        from core.config.settings_manager import get_settings_manager
                        get_settings_manager().set('ask_download_dir', False)
                        log('INFO', '已关闭询问下载位置功能')
                    except Exception as e:
                        log('ERROR', f'保存设置失败: {e}')
                save_dir = selected_dir
            if settings.get('auto_categorize', False):
                from core.download.file_categorizer import CATEGORIZE_BY_SUBJECT
                categorize_rule = settings.get('categorize_rule', CATEGORIZE_BY_SUBJECT)
                save_dir = FileCategorizer.get_categorized_path(base_dir=save_dir, rule=categorize_rule, title=title)
            if not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
                log('DEBUG', f'创建下载目录: {save_dir}')
            filename = self._generate_filename(url, title)
            save_path = os.path.join(save_dir, filename)
        task = {'task_id': task_id, 'url': url, 'save_path': save_path, 'title': title, 'chapters': chapters, 'status': 'pending', 'downloaded_size': 0, 'total_size': 0, 'speed': 0, 'error': None}
        with self._lock:
            self.tasks[task_id] = task
            self.task_list.append(task_id)
        log('SUCCESS', f'任务已添加: {task_id}')
        log('DEBUG', f'保存路径: {save_path}')
        self.task_added.emit(task_id)
        self._task_event.set()
        self._start_worker()
        self._save_tasks()
        return task_id

    def _generate_filename(self, url, title=None):
        """生成文件名 - 使用新的命名规则系统"""
        settings = self._load_settings()
        rule = settings.get('file_naming_rule', 'default')
        include_chapter = settings.get('include_chapter_info', False)
        include_timestamp = settings.get('include_timestamp', False)
        return FileNameGenerator.generate_filename(rule=rule, title=title, chapters=None, url=url, include_chapter=include_chapter, include_timestamp=include_timestamp)

    def _load_settings(self):
        """加载设置 - 使用统一设置管理器"""
        from core.config.settings_manager import get_settings_manager
        return get_settings_manager().get_all()

    def get_task(self, task_id):
        """获取任务"""
        return self.tasks.get(task_id)

    def get_all_tasks(self):
        """获取所有任务"""
        return [self.tasks[tid] for tid in self.task_list if tid in self.tasks]

    def get_active_tasks(self):
        """获取活跃任务"""
        return [task for task in self.get_all_tasks() if task['status'] in ['pending', 'downloading', 'paused']]

    def get_completed_tasks(self):
        """获取完成任务"""
        return [task for task in self.get_all_tasks() if task['status'] in ['completed', 'failed', 'cancelled']]

    def _start_worker(self):
        """启动工作线程（事件驱动，避免 busy-wait）"""
        with self._worker_lock:
            self._task_event.set()
            if not self._is_running:
                self._is_running = True
                self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
                self._worker_thread.start()

    def _worker_loop(self):
        """工作线程主循环 - 事件驱动（仅在有待处理任务时唤醒）"""
        while True:
            self._task_event.wait(timeout=5.0)
            with self._worker_lock:
                self._task_event.clear()
                with self._lock:
                    has_pending = any(
                        self.tasks.get(tid, {}).get('status') == 'pending'
                        for tid in self.task_list
                    )
                if not has_pending:
                    self._is_running = False
                    break
            for task_id in list(self.task_list):
                with self._worker_lock:
                    if not self._is_running:
                        break
                task = self.tasks.get(task_id)
                if task and task['status'] == 'pending':
                    self._download_task(task)
        self.all_tasks_completed.emit()

    def _generate_backup_url(self, url: str) -> str:
        """根据主URL生成备用CDN URL
        
        通过替换CDN域名来生成备用下载链接
        """
        CDN_SERVERS = ['c1', 's-file-1', 'r1-ndr-private']
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            for server in CDN_SERVERS:
                server_domain = f'{server}.ykt.cbern.com.cn'
                if server_domain in domain:
                    for alt_server in CDN_SERVERS:
                        alt_domain = f'{alt_server}.ykt.cbern.com.cn'
                        if alt_domain != server_domain:
                            new_url = url.replace(server_domain, alt_domain, 1)
                            log('DEBUG', f'生成备用CDN URL: {domain} -> {alt_domain}')
                            return new_url
                    break
        except Exception as e:
            log('WARNING', f'生成备用URL失败: {e}')
        return ''

    def _download_with_fallback(self, url: str, save_path: str, headers: dict, progress_fn=None, cancel_event=None) -> tuple:
        """带备用CDN降级的下载函数
        
        先尝试主URL，失败后自动尝试备用CDN
        返回: (success, bytes_downloaded, error_message)
        """
        backup_url = self._generate_backup_url(url)
        urls_to_try = [url]
        if backup_url:
            urls_to_try.append(backup_url)
            log('INFO', '备用CDN已就绪，主链接失败时将自动切换')
        last_error = None
        for attempt, download_url in enumerate(urls_to_try):
            if attempt > 0:
                log('INFO', f'主链接失败，正在切换到备用CDN重试... (第{attempt}次尝试)')
                tmp_path = save_path + '.tmp'
                try:
                    os.remove(tmp_path)
                except FileNotFoundError:
                    pass
                except Exception:
                    pass
            success, bytes_down, err = self._download_single(download_url, save_path, headers, progress_fn, cancel_event)
            if success:
                return (True, bytes_down, None)
            last_error = err
            log('WARNING', f'下载尝试 {attempt + 1}/{len(urls_to_try)} 失败: {err}')
            if cancel_event and cancel_event.is_set():
                return (False, 0, _('core.download.downloader.auto_009'))
        return (False, 0, last_error)

    def _download_single(self, url: str, save_path: str, headers: dict, progress_fn=None, cancel_event=None) -> tuple:
        """执行单次下载，使用临时文件 + 原子重命名，SSL 证书验证失败时自动降级重试。

        返回: (success, bytes_downloaded, error_message)
        """
        tmp_path = save_path + '.tmp'
        start_pos = 0
        try:
            start_pos = os.path.getsize(tmp_path)
        except FileNotFoundError:
            pass
        if start_pos > 0:
            headers = headers.copy()
            headers['Range'] = f'bytes={start_pos}-'
            log('INFO', f'检测到临时文件断点，已从 {format_bytes(start_pos)} 处继续')

        def _fetch(verify: bool):
            nonlocal start_pos
            with self._http.get_stream(url, headers=headers, verify=verify) as response:
                if cancel_event and cancel_event.is_set():
                    return (False, 0, _('core.download.downloader.auto_009'))
                if not response.ok:
                    if response.status_code == 416 and start_pos > 0:
                        try:
                            os.replace(tmp_path, save_path)
                        except Exception:
                            try:
                                os.remove(tmp_path)
                            except Exception:
                                pass
                        return (True, start_pos, None)
                    return (False, 0, f'HTTP {response.status_code}')
                # 断点续传必须要求服务器返回 206 Partial Content；
                # 若返回 200 表示不支持续传并给出完整文件，则改为从头重写，
                # 避免把完整文件以 'ab' 模式追加到已有半截文件尾部造成损坏。
                if start_pos > 0 and response.status_code != 206:
                    log('WARNING', '服务器未返回206，断点续传不可用，将从头重新下载')
                    start_pos = 0
                content_length = int(response.headers.get('Content-Length', 0))
                total_size = start_pos + content_length if start_pos > 0 else content_length
                mode = 'ab' if start_pos > 0 else 'wb'
                bytes_downloaded = start_pos
                last_report_time = time.time()
                with open(tmp_path, mode) as file:
                    for chunk in response.iter_content(chunk_size=32 * 1024):
                        if cancel_event and cancel_event.is_set():
                            return (False, bytes_downloaded, _('core.download.downloader.auto_009'))
                        file.write(chunk)
                        bytes_downloaded += len(chunk)
                        now = time.time()
                        if now - last_report_time >= 0.1 and progress_fn:
                            progress_fn(bytes_downloaded, total_size)
                            last_report_time = now
                os.replace(tmp_path, save_path)
                if progress_fn:
                    progress_fn(bytes_downloaded, total_size)
                return (True, bytes_downloaded, None)

        try:
            return _fetch(self._http.get_ssl_verify())
        except requests.exceptions.SSLError as e:
            log('WARNING', f'SSL 证书验证失败，尝试跳过验证重试: {e}')
            try:
                return _fetch(False)
            except Exception as retry_err:
                log('WARNING', f'跳过验证重试仍失败: {retry_err}')
                return (False, 0, f"{_('core.download.downloader.fstr_004')}{retry_err}")
        except Exception as e:
            return (False, 0, f"{_('core.download.downloader.fstr_004')}{e}")

    def _download_task(self, task):
        """执行单个下载任务 - 集成临时文件保护、CDN降级、断点续传、限速、校验、声音提示、历史记录"""
        task_id = task['task_id']
        log('STEP', f"开始下载: {task.get('title', '未命名')}")
        settings = self._load_settings()
        if not self.access_token:
            self._load_access_token_from_settings()
        if not self.access_token:
            log('ERROR', 'Access Token 未配置，请在设置中填写有效的 Token')
            task['status'] = 'failed'
            task['error'] = _('core.downloader.access_token_missing')
            self.task_failed.emit(task_id, _('core.downloader.access_token_missing'))
            return
        task['status'] = 'downloading'
        task['downloaded_size'] = 0
        task['total_size'] = 0
        cancel_event = threading.Event()
        self._cancel_events[task_id] = cancel_event
        current_state = {'download_url': task['url'], 'save_path': task['save_path'], 'downloaded_size': 0, 'total_size': 0, 'finished': False, 'failed_reason': None}
        with self._state_lock:
            self.download_states[task_id] = current_state
        save_path = task['save_path']
        speed_limit = settings.get('speed_limit', 0)
        speed_limit_bytes = speed_limit * 1024 if speed_limit > 0 else 0
        last_update_time = time.time()
        update_interval = 0.1
        last_download_size = 0
        last_speed_check_time = time.time()

        def progress_callback(bytes_read, total_bytes):
            nonlocal last_update_time, last_download_size, last_speed_check_time
            log('DEBUG', f"[DWN-CRASH][PROGRESS] 入口: bytes_read={bytes_read}, total_bytes={total_bytes}, task={task.get('title', '?')}")
            current_state['downloaded_size'] = bytes_read
            current_state['total_size'] = total_bytes
            task['downloaded_size'] = bytes_read
            task['total_size'] = total_bytes
            current_time = time.time()
            time_diff = current_time - last_speed_check_time
            if time_diff > 0:
                bytes_since_last = bytes_read - last_download_size
                task['speed'] = bytes_since_last / time_diff
                if speed_limit_bytes > 0:
                    current_speed = bytes_since_last / time_diff
                    if current_speed > speed_limit_bytes:
                        sleep_time = bytes_since_last / speed_limit_bytes - time_diff
                        if sleep_time > 0:
                            time.sleep(min(sleep_time, 1.0))
                last_download_size = bytes_read
                last_speed_check_time = current_time
            if current_time - last_update_time >= update_interval:
                last_update_time = current_time
                last_download_size = bytes_read
                last_speed_check_time = current_time
                with self._state_lock:
                    prev_downloaded = self._cached_all_downloaded
                    prev_total = self._cached_all_total
                    self._cached_all_downloaded = prev_downloaded - current_state.get('_prev_downloaded', 0) + bytes_read
                    self._cached_all_total = prev_total - current_state.get('_prev_total', 0) + total_bytes
                    current_state['_prev_downloaded'] = bytes_read
                    current_state['_prev_total'] = total_bytes
                    all_downloaded_size = self._cached_all_downloaded
                    all_total_size = self._cached_all_total
                    downloaded_number = self._cached_finished_count
                    total_number = len(self.download_states)
                log('DEBUG', f'[DWN-CRASH][PROGRESS] 计算: all_downloaded={all_downloaded_size}, all_total={all_total_size}, states_count={total_number}')
                prev_progress = getattr(self, '_last_emitted_progress', -1)
                if all_total_size > 0:
                    download_progress = all_downloaded_size / all_total_size * 100
                    log('DEBUG', f'[DWN-CRASH][PROGRESS] download_progress={download_progress:.2f}%, prev_progress={prev_progress:.2f}%, diff={abs(download_progress - prev_progress):.2f}%')
                    if abs(download_progress - prev_progress) >= 1.0:
                        progress_text = _('core.downloader.progress_template', downloaded_size=format_bytes(all_downloaded_size), total_size=format_bytes(all_total_size), progress_percent=f'{download_progress:.2f}', downloaded_count=downloaded_number, total_count=total_number)
                        log('DEBUG', f'[DWN-CRASH][PROGRESS] 发射 progress_updated 信号: {download_progress:.2f}%')
                        self.progress_updated.emit(download_progress, progress_text)
                        self._last_emitted_progress = download_progress
                else:
                    log('DEBUG', '[DWN-CRASH][PROGRESS] 警告: all_total_size=0, 跳过进度计算')
                log('DEBUG', f"[DWN-CRASH][PROGRESS] 发射 task_updated 信号: {task['task_id']}")
                self.task_updated.emit(task['task_id'])
        success, bytes_downloaded, error = self._download_with_fallback(url=task['url'], save_path=save_path, headers=self.headers.copy(), progress_fn=progress_callback, cancel_event=cancel_event)
        if not success:
            if cancel_event.is_set():
                task['status'] = 'cancelled'
                current_state['finished'] = True
                current_state['failed_reason'] = error
                log('INFO', f"下载已取消: {task.get('title', '未命名')}")
            else:
                task['status'] = 'failed'
                task['error'] = error
                current_state['finished'] = True
                current_state['failed_reason'] = error
                log('ERROR', f"下载失败: {task.get('title', '未命名')} - {error}")
                self.task_failed.emit(task_id, str(error))
            with self._state_lock:
                if task_id in self.download_states:
                    state = self.download_states.pop(task_id)
                    prev_downloaded = state.get('_prev_downloaded', 0)
                    prev_total = state.get('_prev_total', 0)
                    self._cached_all_downloaded = max(0, self._cached_all_downloaded - prev_downloaded)
                    self._cached_all_total = max(0, self._cached_all_total - prev_total)
            if task_id in self._cancel_events:
                del self._cancel_events[task_id]
            return
        task['downloaded_size'] = bytes_downloaded
        task['total_size'] = bytes_downloaded
        current_state['downloaded_size'] = bytes_downloaded
        current_state['total_size'] = bytes_downloaded
        log('SUCCESS', f'文件下载完成 ({format_bytes(bytes_downloaded)})')
        if task.get('chapters'):
            log('STEP', '添加书签中...')
            add_bookmarks(save_path, task['chapters'])
            log('SUCCESS', '书签添加完成')
        auto_verify = settings.get('auto_verify', False)
        retry_on_verify_fail = settings.get('retry_on_verify_fail', False)
        if auto_verify:
            log('STEP', '开始校验文件...')
            is_valid, verify_error = DownloadVerifier.verify_pdf(save_path)
            if not is_valid:
                log('WARNING', f'文件校验失败: {verify_error}')
                if retry_on_verify_fail:
                    log('INFO', '校验失败，自动重试下载...')
                    task['status'] = 'pending'
                    task['error'] = f"{_('core.download.downloader.fstr_003')}{verify_error}"
                    task['downloaded_size'] = 0
                    task['speed'] = 0
                    try:
                        os.remove(save_path)
                    except Exception:
                        pass
                    with self._state_lock:
                        if task_id in self.download_states:
                            self.download_states.pop(task_id)
                            prev_downloaded = current_state.get('_prev_downloaded', 0)
                            prev_total = current_state.get('_prev_total', 0)
                            self._cached_all_downloaded = max(0, self._cached_all_downloaded - prev_downloaded)
                            self._cached_all_total = max(0, self._cached_all_total - prev_total)
                    if task_id in self._cancel_events:
                        cancel_event.clear()
                    self._save_tasks()
                    self._task_event.set()
                    return
                else:
                    task['error'] = f"{_('core.download.downloader.fstr_003')}{verify_error}"
        try:
            download_dir = os.path.dirname(save_path)
            history = DownloadHistory(download_dir)
            content_id = URLFixer.extract_content_id(task['url']) or f'task_{task_id}'
            record = DownloadRecord(resource_id=content_id, title=task.get('title', _('core.download.downloader.auto_006')), filename=os.path.basename(save_path), file_size=bytes_downloaded, save_path=save_path, download_url=task['url'])
            history.add_record(record)
            log('DEBUG', '下载历史记录已保存')
        except Exception as e:
            log('WARNING', f'保存下载历史记录失败: {e}')
        log('DEBUG', f"[DWN-CRASH] 步骤1: 下载成功，bytes_downloaded={bytes_downloaded}, task={task.get('title', '?')}")
        task['status'] = 'completed'
        current_state['finished'] = True
        log('SUCCESS', f"任务完成: {task.get('title', '未命名')}")
        log('DEBUG', f'[DWN-CRASH] 步骤2: 发射 task_completed 信号, task_id={task_id}')
        self.task_completed.emit(task['task_id'])
        log('DEBUG', '[DWN-CRASH] 步骤3: 保存任务到文件')
        self._save_tasks()
        log('DEBUG', '[DWN-CRASH] 步骤4: 准备播放声音信号')
        sound_config = {'sound_enabled': settings.get('sound_enabled', False), 'download_complete_sound': settings.get('download_complete_sound', False)}
        self.play_download_sound_signal.emit(sound_config)
        log('DEBUG', f'[DWN-CRASH] 步骤6: 移除 current_state, states_count={len(self.download_states)}')
        with self._state_lock:
            if task_id in self.download_states:
                self.download_states.pop(task_id)
                prev_downloaded = current_state.get('_prev_downloaded', 0)
                prev_total = current_state.get('_prev_total', 0)
                self._cached_all_downloaded = max(0, self._cached_all_downloaded - prev_downloaded)
                self._cached_all_total = max(0, self._cached_all_total - prev_total)
                self._cached_finished_count += 1
        log('DEBUG', f'[DWN-CRASH] 步骤7: current_state 已移除, cached_downloaded={self._cached_all_downloaded}, cached_total={self._cached_all_total}, cached_count={self._cached_finished_count}')
        if task_id in self._cancel_events:
            del self._cancel_events[task_id]
        log('DEBUG', '[DWN-CRASH] 步骤8: _download_task 函数执行完毕, 未发生崩溃')

    def _show_notification(self, title, message):
        """显示右上角通知"""
        try:
            from gui.widgets import show_notification
            show_notification(title, message)
        except Exception as e:
            log('ERROR', f'显示通知失败: {e}')

    def pause_task(self, task_id):
        """暂停任务 - 将状态设为 paused，保留文件"""
        try:
            with self._lock:
                if task_id not in self.tasks:
                    return
                task = self.tasks[task_id]
                if task['status'] not in ['pending', 'downloading']:
                    return
                task['status'] = 'paused'
                if task_id in self._cancel_events:
                    self._cancel_events[task_id].set()
                    log('INFO', f'已发送暂停信号: {task_id}')
                self._save_tasks()
        except Exception as e:
            log('ERROR', f'暂停任务失败: {e}')
            return
        self.task_updated.emit(task_id)
        log('INFO', f'任务已暂停: {task_id}')

    def cancel_task(self, task_id):
        """取消任务 - 真正中断下载（原子性操作）"""
        try:
            with self._lock:
                if task_id not in self.tasks:
                    return
                task = self.tasks[task_id]
                if task['status'] not in ['pending', 'downloading']:
                    return
                task['status'] = 'cancelled'
                if task_id in self._cancel_events:
                    self._cancel_events[task_id].set()
                    log('INFO', f'已发送取消信号: {task_id}')
                self._save_tasks()
        except Exception as e:
            log('ERROR', f'取消任务失败: {e}')
            return
        self.task_updated.emit(task_id)
        log('INFO', f'任务已取消: {task_id}')

    def remove_task(self, task_id):
        """移除任务"""
        with self._lock:
            if task_id in self.tasks:
                if task_id in self.task_list:
                    self.task_list.remove(task_id)
                del self.tasks[task_id]
        self._save_tasks()

    def clear_all_tasks(self):
        """清空所有任务"""
        with self._lock:
            self.tasks.clear()
            self.task_list.clear()
        with self._state_lock:
            self.download_states.clear()
            self._cached_all_downloaded = 0
            self._cached_all_total = 0
            self._cached_finished_count = 0
            self._last_emitted_progress = -1.0
        self._cancel_events.clear()
        self._task_event.clear()
        self._save_tasks()

    def retry_task(self, task_id):
        """重试任务"""
        with self._lock:
            if task_id not in self.tasks:
                return
            task = self.tasks[task_id]
            if task['status'] in ('downloading', 'pending'):
                return
            task['status'] = 'pending'
            task['downloaded_size'] = 0
            task['error'] = None
        self.task_updated.emit(task_id)
        self._task_event.set()
        self._start_worker()
        self._save_tasks()

    def shutdown(self, timeout: float = 10.0):
        """优雅关闭下载器，停止工作线程并保存任务状态。

        Args:
            timeout: 等待工作线程结束的最大秒数。
        """
        self.app_closing = True
        self._task_event.set()
        with self._worker_lock:
            worker = self._worker_thread
        if worker and worker.is_alive():
            worker.join(timeout=timeout)
            if worker.is_alive():
                log('WARNING', '下载工作线程未在超时内结束')
        self._save_tasks()

    def _save_tasks(self):
        """保存任务到文件"""
        try:
            import json
            tasks_data = []
            for task_id in self.task_list:
                if task_id in self.tasks:
                    task = self.tasks[task_id].copy()
                    tasks_data.append(task)
            with open(self._tasks_file, 'w', encoding='utf-8') as f:
                json.dump(tasks_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log('ERROR', f'保存任务失败: {e}')

    def _load_tasks(self):
        """从文件加载任务"""
        try:
            import json
            if os.path.exists(self._tasks_file):
                with open(self._tasks_file, 'r', encoding='utf-8') as f:
                    tasks_data = json.load(f)
                with self._lock:
                    for task in tasks_data:
                        task_id = task.get('task_id')
                        if task_id:
                            if task.get('status') in ['downloading', 'pending']:
                                task['status'] = 'pending'
                                task['downloaded_size'] = 0
                            self.tasks[task_id] = task
                            self.task_list.append(task_id)
                            self.task_added.emit(task_id)
                log('INFO', f'已加载 {len(tasks_data)} 个任务')
        except Exception as e:
            log('ERROR', f'加载任务失败: {e}')