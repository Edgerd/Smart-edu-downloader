"""
路径解析器模块

集中管理所有运行时数据文件的绝对路径，避免各模块重复计算。
所有运行时产生的缓存、日志、设置和临时文件均存放于系统临时目录下的
Smart-edu-downloader 子目录中，避免污染项目目录或被打包进代码仓库。
"""
import os
import sys
import tempfile

# 教材下载目录默认名称（保持中文，不参与翻译）
TEXTBOOK_DOWNLOAD_DIR_NAME = '教材下载'

# 应用运行时根目录名称，位于系统临时目录下
_RUNTIME_ROOT_NAME = 'Smart-edu-downloader'


def _calculate_project_root() -> str:
    """
    计算项目根目录路径

    始终基于 __file__ 的绝对路径向上查找，确保无论从哪里运行程序，
    都能正确定位到项目根目录。

    Returns:
        str: 项目根目录的绝对路径
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    current_file = os.path.realpath(__file__)
    file_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
    if os.path.isdir(os.path.join(file_root, 'core')) or os.path.isdir(os.path.join(file_root, 'gui')):
        return file_root
    return file_root
_PROJECT_ROOT = _calculate_project_root()


def get_project_root() -> str:
    """获取项目根目录"""
    return _PROJECT_ROOT


def _ensure_dir(path: str) -> None:
    """确保目录存在"""
    os.makedirs(path, exist_ok=True)


def get_runtime_root() -> str:
    """获取运行时根目录路径。

    使用系统临时目录（os.TempDir() 或 /tmp）作为根目录，
    并在此下创建应用专属子目录，避免与其他应用冲突。

    Returns:
        str: 运行时根目录的绝对路径
    """
    runtime_root = os.path.join(tempfile.gettempdir(), _RUNTIME_ROOT_NAME)
    _ensure_dir(runtime_root)
    return runtime_root


def get_settings_dir() -> str:
    """获取设置目录路径"""
    settings_dir = os.path.join(get_runtime_root(), 'settings')
    _ensure_dir(settings_dir)
    return settings_dir


def get_settings_file() -> str:
    """获取设置文件路径"""
    return os.path.join(get_settings_dir(), 'settings.json')


def get_cache_dir() -> str:
    """获取缓存目录路径"""
    cache_dir = os.path.join(get_runtime_root(), 'cache')
    _ensure_dir(cache_dir)
    return cache_dir

def get_search_history_file() -> str:
    """获取搜索历史文件路径"""
    return os.path.join(get_cache_dir(), 'search_history.json')

def get_url_history_file() -> str:
    """获取URL历史文件路径"""
    return os.path.join(get_cache_dir(), 'url_history.json')

def get_download_tasks_file() -> str:
    """获取下载任务文件路径"""
    return os.path.join(get_cache_dir(), 'download_tasks.json')

def get_resource_list_file() -> str:
    """获取资源列表缓存文件路径"""
    return os.path.join(get_cache_dir(), 'resource_list.json')

def get_cache_meta_file() -> str:
    """获取缓存元数据文件路径"""
    return os.path.join(get_cache_dir(), 'cache_meta.json')

def get_download_history_file() -> str:
    """获取下载历史文件路径"""
    return os.path.join(get_cache_dir(), 'download_history.json')

def get_logs_dir() -> str:
    """获取日志目录路径"""
    logs_dir = os.path.join(get_runtime_root(), 'logs')
    _ensure_dir(logs_dir)
    return logs_dir


def get_crash_logs_dir() -> str:
    """获取崩溃日志目录路径"""
    crash_logs_dir = os.path.join(get_logs_dir(), 'crashes')
    _ensure_dir(crash_logs_dir)
    return crash_logs_dir


def get_temp_dir() -> str:
    """获取临时目录路径"""
    temp_dir = os.path.join(get_runtime_root(), 'temp')
    _ensure_dir(temp_dir)
    return temp_dir


def migrate_wrong_runtime_location() -> None:
    """
    迁移错误位置的 runtime 目录：将项目目录上一级或项目根目录的 runtime/ 迁移到系统临时目录。

    当程序工作目录不正确时（例如从 E:\\hello 运行而非 E:\\hello\\Smart-edu-downloader），
    runtime 数据可能被错误地保存到项目目录附近。此函数检测并迁移这些数据到系统临时目录。
    """
    runtime_root = get_runtime_root()
    for relative_path in (os.path.join(_PROJECT_ROOT, '..', 'runtime'), os.path.join(_PROJECT_ROOT, 'runtime')):
        old_runtime = os.path.normpath(relative_path)
        if not os.path.isdir(old_runtime):
            continue
        if os.path.normpath(old_runtime) == os.path.normpath(runtime_root):
            continue
        try:
            import shutil
            _merge_directories(old_runtime, runtime_root)
            shutil.rmtree(old_runtime)
        except Exception:
            pass


def migrate_old_settings() -> None:
    """
    迁移旧设置文件：根目录 settings.json → 系统临时目录/settings/settings.json
    仅在旧文件存在且新文件不存在时执行迁移。
    """
    old_file = os.path.join(_PROJECT_ROOT, 'settings.json')
    new_file = get_settings_file()
    if os.path.exists(old_file) and (not os.path.exists(new_file)):
        try:
            import shutil
            shutil.copy2(old_file, new_file)
            os.remove(old_file)
        except Exception:
            pass


def migrate_old_runtime() -> None:
    """
    迁移旧 runtime 目录：core/runtime/ 或项目根目录 runtime/ → 系统临时目录。
    仅在旧目录存在时执行迁移。
    """
    runtime_root = get_runtime_root()
    for old_runtime in (os.path.join(_PROJECT_ROOT, 'core', 'runtime'), os.path.join(_PROJECT_ROOT, 'runtime')):
        if os.path.exists(old_runtime):
            try:
                import shutil
                _merge_directories(old_runtime, runtime_root)
                shutil.rmtree(old_runtime)
            except Exception:
                pass


def migrate_old_download_history() -> None:
    """
    迁移旧下载历史文件：下载目录/download_history.json → 系统临时目录/cache/download_history.json
    优先从用户下载目录迁移。
    """
    new_file = get_download_history_file()
    if os.path.exists(new_file):
        return
    try:
        from core.infrastructure.platform_utils import get_system_downloads_dir
        default_dl = os.path.join(get_system_downloads_dir(), TEXTBOOK_DOWNLOAD_DIR_NAME)
        old_file = os.path.join(default_dl, 'download_history.json')
        if os.path.exists(old_file):
            import shutil
            shutil.copy2(old_file, new_file)
            os.remove(old_file)
    except Exception:
        pass


def migrate_all_old_data() -> None:
    """集中执行所有旧数据迁移，应在应用启动早期调用一次"""
    migrate_wrong_runtime_location()
    migrate_old_settings()
    migrate_old_runtime()
    migrate_old_download_history()

def _merge_directories(src: str, dst: str) -> None:
    """合并两个目录，src 中的文件/子目录合并到 dst 中"""
    import shutil
    _ensure_dir(dst)
    for item in os.listdir(src):
        src_item = os.path.join(src, item)
        dst_item = os.path.join(dst, item)
        if os.path.isdir(src_item):
            if not os.path.exists(dst_item):
                shutil.copytree(src_item, dst_item)
            else:
                _merge_directories(src_item, dst_item)
        elif not os.path.exists(dst_item):
            shutil.copy2(src_item, dst_item)