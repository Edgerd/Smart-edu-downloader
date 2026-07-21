# -*- coding: utf-8 -*-
"""精确分析现有主题预设的 HSL 关系并搜索更优派生参数。"""
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


print("主色/背景色 HSL 精确值：")
for p, b in PAIRS:
    ph, ps, pl = hex_to_hsl(p)
    bh, bs, bl = hex_to_hsl(b)
    print(f"{p} -> {b}  主色 H={ph:6.1f} S={ps:5.1f} L={pl:5.1f}  背景 H={bh:6.1f} S={bs:5.1f} L={bl:5.1f}")
