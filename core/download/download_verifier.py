"""下载校验模块"""
from core.i18n import _
import os
import hashlib
from core.infrastructure.logger import log

class DownloadVerifier:
    """下载文件校验器"""

    @staticmethod
    def verify_file(file_path, expected_size=None, expected_hash=None, hash_algorithm='md5'):
        """校验下载文件"""
        try:
            if not os.path.exists(file_path):
                return (False, _('core.download.download_verifier.auto_004'))
            if expected_size is not None and expected_size > 0:
                actual_size = os.path.getsize(file_path)
                if actual_size != expected_size:
                    error_msg = f"{_('core.download.download_verifier.fstr_004')}{expected_size}{_('core.download.download_verifier.fstr_002')}{actual_size}{_('core.download.download_verifier.fstr_001')}"
                    log('WARNING', error_msg)
                    return (False, error_msg)
            if expected_hash:
                actual_hash = DownloadVerifier._calculate_hash(file_path, hash_algorithm)
                if actual_hash != expected_hash.lower():
                    error_msg = f"{_('core.download.download_verifier.fstr_003')}{expected_hash}{_('core.download.download_verifier.fstr_007')}{actual_hash}"
                    log('WARNING', error_msg)
                    return (False, error_msg)
            if os.path.getsize(file_path) == 0:
                return (False, _('core.download.download_verifier.auto_005'))
            try:
                with open(file_path, 'rb') as f:
                    f.read(1024)
            except Exception as e:
                return (False, f"{_('core.download.download_verifier.fstr_005')}{e}")
            log('INFO', f'文件校验通过: {file_path}')
            return (True, None)
        except Exception as e:
            log('ERROR', f'文件校验失败: {e}')
            return (False, f"{_('core.download.download_verifier.fstr_006')}{e}")

    @staticmethod
    def _calculate_hash(file_path, algorithm='md5'):
        """计算文件哈希值"""
        try:
            if algorithm == 'md5':
                hasher = hashlib.md5()
            elif algorithm == 'sha1':
                hasher = hashlib.sha1()
            elif algorithm == 'sha256':
                hasher = hashlib.sha256()
            else:
                hasher = hashlib.md5()
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(8192)
                    if not chunk:
                        break
                    hasher.update(chunk)
            return hasher.hexdigest()
        except Exception as e:
            log('ERROR', f'计算文件哈希失败: {e}')
            return ''

    @staticmethod
    def verify_pdf(file_path):
        """专门校验PDF文件"""
        try:
            is_valid, error = DownloadVerifier.verify_file(file_path)
            if not is_valid:
                return (False, error)
            with open(file_path, 'rb') as f:
                header = f.read(5)
                if header != b'%PDF-':
                    return (False, _('core.download.download_verifier.auto_003'))
            file_size = os.path.getsize(file_path)
            if file_size > 100:
                with open(file_path, 'rb') as f:
                    f.seek(-20, os.SEEK_END)
                    tail = f.read(20)
                    if b'%%EOF' not in tail:
                        log('WARNING', f'PDF文件可能不完整（缺少%%EOF标记）: {file_path}')
            log('INFO', f'PDF文件校验通过: {file_path}')
            return (True, None)
        except Exception as e:
            log('ERROR', f'PDF文件校验失败: {e}')
            return (False, f"{_('core.download.download_verifier.fstr_006')}{e}")