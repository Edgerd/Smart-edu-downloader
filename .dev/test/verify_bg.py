# -*- coding: utf-8 -*-
"""验证 theme_config._derive_background 新算法效果。"""
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.chdir(project_root)

from core.config.theme_config import _derive_background

PAIRS = [
    ("#1277DD", "#E8F4FD"),
    ("#282A30", "#E6E7EA"),
    ("#E9849D", "#F5DDE2"),
    ("#8B37A6", "#EDDDF1"),
    ("#8F36A1", "#EDDDF0"),
    ("#B49C26", "#F0ECD1"),
    ("#D46A1E", "#F5E6D8"),
    ("#C12F22", "#F6E0DE"),
    ("#2E45B7", "#E0E3F4"),
    ("#2B4BAD", "#DEE4F4"),
]


def hex_to_rgb(hex_color):
    c = hex_color.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def color_distance(c1, c2):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5


total = 0
print("新算法派生结果与目标对比：")
for primary, target in PAIRS:
    result = _derive_background(primary)
    dist = color_distance(result, target)
    total += dist
    print(f"  {primary} -> {result} (目标 {target}, 距离 {dist:.1f})")
print(f"总距离: {total:.2f}")
