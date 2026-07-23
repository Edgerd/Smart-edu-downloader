# -*- coding: utf-8 -*-
"""下载历史记录模块"""

import os
import json
from datetime import datetime
from typing import List, Optional

from core.infrastructure.logger import log
from core.infrastructure.path_resolver import get_download_history_file


class DownloadRecord:
    """单条下载记录"""

    def __init__(self, resource_id: str, title: str, filename: str,
                 file_size: int, save_path: str, download_url: str = ""):
        self.resource_id = resource_id
        self.title = title
        self.filename = filename
        self.file_size = file_size
        self.save_path = save_path
        self.download_url = download_url
        self.downloaded_at = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "resource_id": self.resource_id,
            "title": self.title,
            "filename": self.filename,
            "file_size": self.file_size,
            "save_path": self.save_path,
            "download_url": self.download_url,
            "downloaded_at": self.downloaded_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DownloadRecord":
        record = cls(
            resource_id=data.get("resource_id", ""),
            title=data.get("title", ""),
            filename=data.get("filename", ""),
            file_size=data.get("file_size", 0),
            save_path=data.get("save_path", ""),
            download_url=data.get("download_url", ""),
        )
        record.downloaded_at = data.get("downloaded_at", "")
        return record


class DownloadHistory:
    """下载历史管理器"""

    def __init__(self, history_dir: str = None):
        self.history_path = get_download_history_file()
        self.records: List[DownloadRecord] = []
        self._load()

    def _load(self):
        """从文件加载历史记录"""
        if not os.path.exists(self.history_path):
            log("DEBUG", "下载历史文件不存在，创建新记录")
            self.records = []
            return

        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.records = [DownloadRecord.from_dict(r) for r in data.get("records", [])]
            log("DEBUG", f"已加载 {len(self.records)} 条下载历史记录")
        except Exception as e:
            log("WARNING", f"加载下载历史记录失败: {e}")
            self.records = []

    def _save(self):
        """保存历史记录到文件"""
        try:
            os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
            data = {
                "records": [r.to_dict() for r in self.records],
                "total_count": len(self.records),
                "updated_at": datetime.now().isoformat(),
            }
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            log("DEBUG", "下载历史记录已保存")
        except Exception as e:
            log("WARNING", f"保存下载历史记录失败: {e}")

    def add_record(self, record: DownloadRecord):
        """添加下载记录"""
        # 检查是否已存在相同资源ID
        for i, existing in enumerate(self.records):
            if existing.resource_id == record.resource_id:
                # 更新已有记录
                self.records[i] = record
                log("DEBUG", f"更新下载记录: {record.title}")
                self._save()
                return

        self.records.append(record)
        log("DEBUG", f"添加下载记录: {record.title}")
        self._save()

    def is_downloaded(self, resource_id: str) -> bool:
        """检查资源是否已下载（记录存在且文件仍存在）"""
        for record in self.records:
            if record.resource_id == resource_id:
                if os.path.exists(record.save_path):
                    return True
                else:
                    # 记录存在但文件已不存在，移除记录
                    log("DEBUG", f"资源记录存在但文件已删除: {record.title}")
                    self.records.remove(record)
                    self._save()
                    return False
        return False

    def get_record(self, resource_id: str) -> Optional[DownloadRecord]:
        """获取指定资源的下载记录"""
        for record in self.records:
            if record.resource_id == resource_id:
                return record
        return None

    def get_all_records(self) -> List[DownloadRecord]:
        """获取所有下载记录"""
        return list(self.records)

    def remove_record(self, resource_id: str):
        """移除指定资源的下载记录"""
        self.records = [r for r in self.records if r.resource_id != resource_id]
        self._save()

    def get_downloaded_count(self) -> int:
        """获取已下载资源数量"""
        return len(self.records)

    def get_total_size(self) -> int:
        """获取已下载资源总大小（字节）"""
        return sum(r.file_size for r in self.records)
