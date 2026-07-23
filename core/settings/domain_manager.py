# -*- coding: utf-8 -*-
"""域名白名单管理模块"""

from typing import List, Optional


class DomainManager:
    """域名管理器"""

    @staticmethod
    def normalize_domain(domain: str) -> str:
        """规范化域名"""
        if not domain:
            return ""
        d = domain.strip().lower()
        for prefix in ("http://", "https://"):
            if d.startswith(prefix):
                d = d[len(prefix):]
                break
        for sep in ("/", "?", "#"):
            if sep in d:
                d = d.split(sep, 1)[0]
                break
        return d.strip()

    @staticmethod
    def is_valid_domain(domain: str) -> bool:
        """校验域名格式是否合法"""
        if not domain:
            return False
        if "." not in domain:
            return False
        if any(c in domain for c in (" ", "\t", "\n")):
            return False
        return True

    @staticmethod
    def add_domain(domain_input: str, list_widget) -> Optional[str]:
        """添加域名到列表控件"""
        normalized = DomainManager.normalize_domain(domain_input)
        if not DomainManager.is_valid_domain(normalized):
            return None

        # 去重检查
        existing = []
        for i in range(list_widget.count()):
            existing.append(list_widget.item(i).text().strip())

        if normalized in existing:
            return None  # 已存在

        list_widget.addItem(normalized)
        return normalized

    @staticmethod
    def remove_selected(list_widget) -> int:
        """删除列表中选中的域名"""
        selected_items = list_widget.selectedItems()
        count = len(selected_items)
        for item in selected_items:
            row = list_widget.row(item)
            list_widget.takeItem(row)
        return count

    @staticmethod
    def clear_all(list_widget) -> None:
        """清空列表"""
        list_widget.clear()

    @staticmethod
    def refresh_list(list_widget, domains: List[str]) -> None:
        """刷新列表显示"""
        list_widget.clear()
        for d in domains:
            if isinstance(d, str) and d.strip():
                list_widget.addItem(d.strip())