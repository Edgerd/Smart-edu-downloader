# -*- coding: utf-8 -*-
"""
自定义异常模块
"""
from core.i18n import _
class SmartEduDownloaderError(Exception):
    """基础异常类"""
    def __init__(self, message: str = _("core.exceptions.unknown_error")):
        self.message = message
        super().__init__(self.message)


class NetworkError(SmartEduDownloaderError):
    """网络相关错误"""


class RequestError(NetworkError):
    """请求错误"""


class ConnectionError(NetworkError):
    """连接错误"""


class RequestTimeoutError(NetworkError):
    """超时错误"""


class URLValidationError(SmartEduDownloaderError):
    """URL验证错误"""


class URLError(SmartEduDownloaderError):
    """URL格式错误"""


class FileError(SmartEduDownloaderError):
    """文件相关错误"""


class FileWriteError(FileError):
    """文件写入错误"""


class FileReadError(FileError):
    """文件读取错误"""


class FileRenameError(FileError):
    """文件重命名错误"""


class DownloadError(SmartEduDownloaderError):
    """下载相关错误"""


class DownloadTimeoutError(DownloadError):
    """下载超时错误"""


class DownloadFailedError(DownloadError):
    """下载失败错误"""


class TaskError(SmartEduDownloaderError):
    """任务相关错误"""


class ValidationError(SmartEduDownloaderError):
    """验证错误"""


class ConfigError(SmartEduDownloaderError):
    """配置错误"""


class ResourceError(SmartEduDownloaderError):
    """资源相关错误"""
