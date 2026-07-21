# -*- coding: utf-8 -*-
"""检查资源列表中书籍字段，确认是否包含封面 URL。"""
import sys
import os
import json

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.chdir(project_root)

from core.config.settings_manager import get_settings_manager

mgr = get_settings_manager()
cache_dir = mgr.get_cache_dir() if hasattr(mgr, 'get_cache_dir') else os.path.join(project_root, 'runtime', 'cache')
resource_file = os.path.join(cache_dir, 'resource_list.json')

if not os.path.exists(resource_file):
    print(f"资源列表不存在: {resource_file}")
    sys.exit(0)

with open(resource_file, 'r', encoding='utf-8') as f:
    data = json.load(f)


def find_books(node, depth=0):
    if isinstance(node, dict):
        if 'id' in node and ('title' in node or 'name' in node):
            yield node
        for v in node.values():
            yield from find_books(v, depth + 1)
    elif isinstance(node, list):
        for item in node:
            yield from find_books(item, depth + 1)


books = list(find_books(data))[:5]
print(f"找到 {len(books)} 本样例书籍:")
for b in books:
    print(json.dumps(b, ensure_ascii=False, indent=2)[:800])
    print("---")
