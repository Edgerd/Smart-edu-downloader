# -*- coding: utf-8 -*-
"""历史记录清理模块。

提供清除下载历史与搜索历史的功能，供设置页面等 GUI 入口调用。
"""

import os

from core.infrastructure.path_resolver import get_download_history_file, get_cache_dir
from core.infrastructure.logger import log


class HistoryCleaner:
    """历史记录清理器。

    封装下载历史文件与搜索历史文件的删除逻辑，供外部以静态方法形式调用，
    避免在 GUI 层混入文件操作细节。
    """

    @staticmethod
    def clean_all() -> None:
        """清除全部历史记录。

        依次删除下载历史文件与搜索历史文件，删除过程中产生的异常会被
        捕获并记录日志，不会向外抛出。最后统一记录一次清理完成日志。

        Note:
            本方法不包含任何 GUI 交互逻辑，调用方需自行处理用户确认。
        """
        # 清除下载历史记录文件
        history_file = get_download_history_file()
        if os.path.exists(history_file):
            try:
                os.remove(history_file)
                log("INFO", f"下载历史记录文件已删除: {history_file}")
            except OSError as e:
                log("ERROR", f"删除历史记录文件失败: {e}")

        # 清除搜索历史文件
        search_history_file = os.path.join(get_cache_dir(), "search_history.json")
        if os.path.exists(search_history_file):
            try:
                os.remove(search_history_file)
                log("INFO", f"搜索历史文件已删除: {search_history_file}")
            except OSError as e:
                log("ERROR", f"删除搜索历史文件失败: {e}")

        log("INFO", "历史记录已清除")
