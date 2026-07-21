# -*- coding: utf-8 -*-
"""分析现有主题预设的主色与背景色关系，辅助重写派生算法。"""
import sys
import os
import colorsys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.chdir(project_root)


def hex_to_rgb(hex_color):
    c = hex_color.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r, g, b):
    return f"#{r:02X}{g:02X}{b:02X}"


def hex_to_hsl(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    h, l, s = colorsys.rgb_to_hls(r / 255.0, g / 255.0, b / 255.0)
    return (h * 360, s * 100, l * 100)


def hsl_to_hex(h, s, l):
    h = max(0, min(360, h)) / 360.0
    s = max(0, min(100, s)) / 100.0
    l = max(0, min(100, l)) / 100.0
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return rgb_to_hex(int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))


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


def color_distance(c1, c2):
    r1, g1, b1 = hex_to_rgb(c1)
    r2, g2, b2 = hex_to_rgb(c2)
    return ((r1 - r2) ** 2 + (g1 - g2) ** 2 + (b1 - b2) ** 2) ** 0.5


def derive_bg_avg(primary):
    """使用平均 ΔL 和 ΔS。"""
    h, s, l = hex_to_hsl(primary)
    new_l = min(96, l + 47)
    new_s = max(8, s - 10)
    return hsl_to_hex(h, new_s, new_l)


def derive_bg_weighted(primary):
    """根据主色亮度加权 ΔL。"""
    h, s, l = hex_to_hsl(primary)
    # 暗色需要更多提亮
    delta_l = 50 + (50 - l) * 0.4
    new_l = min(96, l + delta_l)
    new_s = max(8, min(85, s * 0.78 - 8))
    return hsl_to_hex(h, new_s, new_l)


def derive_bg_smooth(primary):
    """平滑公式：饱和度缩放，亮度提升到固定区域。"""
    h, s, l = hex_to_hsl(primary)
    # 目标亮度：主色越暗，背景越亮；但上限在 94 左右
    new_l = min(95, l + (95 - l) * 0.85)
    # 饱和度缩放并加偏移
    new_s = max(6, min(85, s * 0.72 - 5))
    return hsl_to_hex(h, new_s, new_l)


def derive_bg_v1(primary):
    """之前的最佳候选。"""
    h, s, l = hex_to_hsl(primary)
    new_l = 92
    new_s = max(8, min(85, s * 0.65 + 10))
    return hsl_to_hex(h, new_s, new_l)


CANDIDATES = [
    ("avg", derive_bg_avg),
    ("weighted", derive_bg_weighted),
    ("smooth", derive_bg_smooth),
    ("v1", derive_bg_v1),
]


print("候选算法与目标背景色对比（距离越小越好）:")
header = f"{'primary':10} {'target':10}"
for name, _ in CANDIDATES:
    header += f" {name:10}"
print(header)
print("-" * len(header))

total_dist = {name: 0 for name, _ in CANDIDATES}
for primary, bg in PAIRS:
    line = f"{primary:10} {bg:10}"
    for name, fn in CANDIDATES:
        result = fn(primary)
        dist = color_distance(result, bg)
        total_dist[name] += dist
        line += f" {result:10}"
    print(line)

print("-" * len(header))
print(f"{'total':21}", end="")
for name, _ in CANDIDATES:
    print(f" {total_dist[name]:10.2f}", end="")
print()
