"""
全局线程池模块

提供线程池复用机制,避免频繁创建和销毁线程带来的性能开销。
适用于 I/O 密集型任务的并发执行。
"""

from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Callable, Optional


# 全局线程池实例
_thread_pool: Optional[ThreadPoolExecutor] = None


def _get_or_create_pool() -> ThreadPoolExecutor:
    """
    内部函数:获取或创建全局线程池实例

     Returns:
        ThreadPoolExecutor: 全局线程池实例
    """
    global _thread_pool
    if _thread_pool is None:
        _thread_pool = ThreadPoolExecutor(
            max_workers=10,
            thread_name_prefix="SmartEduWorker"
        )
    return _thread_pool


def get_thread_pool() -> ThreadPoolExecutor:
    """
    获取全局线程池实例

    如果线程池尚未初始化,则自动创建一个大小为10的线程池。
    该线程池适合 I/O 密集型任务(如网络请求、文件读写等)。

    Returns:
        ThreadPoolExecutor: 配置好的全局线程池实例

    Example:
        >>> pool = get_thread_pool()
        >>> future = pool.submit(some_function, arg1, arg2)
        >>> result = future.result()
    """
    return _get_or_create_pool()


def submit_task(fn: Callable, *args, **kwargs) -> Future:
    """
    向全局线程池提交异步任务

    将任务提交到全局线程池中执行,返回一个 Future 对象用于获取任务结果。

    Args:
        fn: 要执行的函数或可调用对象
        *args: 传递给函数的位置参数
        **kwargs: 传递给函数的关键字参数

    Returns:
        Future: 表示异步执行结果的 Future 对象,可通过 result() 获取返回值

    Example:
        >>> def download_file(url):
        ...     # 下载文件逻辑
        ...     return f"Downloaded: {url}"
        ...
        >>> future = submit_task(download_file, "https://example.com/file.pdf")
        >>> # 执行其他操作...
        >>> result = future.result()  # 阻塞等待结果
        >>> print(result)
        Downloaded: https://example.com/file.pdf

    Note:
        - 如果不需要等待结果,可以忽略返回的 Future 对象
        - 如需处理异常,可使用 future.add_done_callback() 添加回调函数
        - 调用 future.result() 会阻塞当前线程直到任务完成
    """
    pool = get_thread_pool()
    return pool.submit(fn, *args, **kwargs)


def shutdown_pool(wait: bool = True) -> None:
    """
    关闭全局线程池

    在程序退出时调用,确保所有任务完成并释放线程资源。

    Args:
        wait: 是否等待所有待执行的任务完成,默认为 True

    Example:
        >>> # 程序退出前调用
        >>> shutdown_pool()
    """
    global _thread_pool
    if _thread_pool is not None:
        _thread_pool.shutdown(wait=wait)
        _thread_pool = None
