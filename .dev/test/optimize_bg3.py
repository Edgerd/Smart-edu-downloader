# -*- coding: utf-8 -*-
"""测试若干人工候选算法，找到兼顾默认值的最优解。"""
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


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def evaluate(name, fn):
    total = 0
    print(f"\n{name}:")
    for p, t in PAIRS:
        r = fn(p)
        d = color_distance(r, t)
        total += d
        print(f"  {p} -> {r} (目标 {t}, 距离 {d:.1f})")
    print(f"  total = {total:.2f}")
    return total


# 候选算法
def v1(p):
    h, s, l = hex_to_hsl(p)
    return hsl_to_hex(h, max(8, min(85, s * 0.65 + 10)), 92)


def linear_91(p):
    h, s, l = hex_to_hsl(p)
    return hsl_to_hex(h, clamp(s * 0.78, 6, 95), 91)


def linear_92(p):
    h, s, l = hex_to_hsl(p)
    return hsl_to_hex(h, clamp(s * 0.78, 6, 95), 92)


def piecewise_L(p):
    """亮度根据主色饱和度微调：高饱和更亮，低饱和接近91。"""
    h, s, l = hex_to_hsl(p)
    L = clamp(91 + s * 0.05, 88, 96)
    return hsl_to_hex(h, clamp(s * 0.78, 6, 95), L)


def hue_aware(p):
    """根据色相微调亮度：蓝紫区域略提亮。"""
    h, s, l = hex_to_hsl(p)
    # 蓝紫区域 (h 190-270) 提升亮度
    boost = 0
    if 190 <= h <= 270:
        boost = 3
    L = clamp(91 + boost, 88, 96)
    return hsl_to_hex(h, clamp(s * 0.78, 6, 95), L)


def saturation_adaptive(p):
    """饱和度映射更平缓，高饱和保留更多。"""
    h, s, l = hex_to_hsl(p)
    # 高饱和度区域减少压缩
    ratio = 0.75 + 0.25 * (s / 100)
    return hsl_to_hex(h, clamp(s * ratio, 6, 95), 92)


evaluate("v1 (当前)", v1)
evaluate("linear L=91 S=0.78s", linear_91)
evaluate("linear L=92 S=0.78s", linear_92)
evaluate("piecewise_L", piecewise_L)
evaluate("hue_aware", hue_aware)
evaluate("saturation_adaptive L=92", saturation_adaptive)
