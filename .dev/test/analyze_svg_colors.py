# -*- coding: utf-8 -*-
"""分析 SVG 图标中使用的所有 fill 颜色。"""
import os
import re

root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

for folder in ["resources/images/titles", "resources/images/nav"]:
    print(f"\n{folder}:")
    path = os.path.join(root, folder)
    for name in sorted(os.listdir(path)):
        if not name.endswith(".svg"):
            continue
        with open(os.path.join(path, name), "r", encoding="utf-8") as f:
            content = f.read()
        fills = re.findall(r'fill="([^"]+)"', content)
        unique = sorted(set(fills))
        print(f"  {name}: {unique}")
