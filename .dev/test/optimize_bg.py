# -*- coding: utf-8 -*-
"""网格搜索更优的背景色派生算法参数。"""
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


def total_distance(fn):
    return sum(color_distance(fn(p), t) for p, t in PAIRS)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


best = (float('inf'), None, None)

# 搜索亮度固定值
for L in range(86, 97):
    # 搜索饱和度线性缩放 a*S + b
    for a in [x / 100 for x in range(60, 105, 1)]:
        for b in range(-15, 16):
            def make_fn(L, a, b):
                return lambda p: hsl_to_hex(
                    hex_to_hsl(p)[0],
                    clamp(a * hex_to_hsl(p)[1] + b, 6, 95),
                    L
                )
            d = total_distance(make_fn(L, a, b))
            if d < best[0]:
                best = (d, f"L={L}, S={a}*s+{b}", make_fn(L, a, b))

print(f"线性最优: {best[1]}, total={best[0]:.2f}")
print("各预设结果：")
for p, t in PAIRS:
    r = best[2](p)
    print(f"  {p} -> {r} (目标 {t}, 距离 {color_distance(r, t):.1f})")

# 搜索非线性：S = s * (base + curve * s/100)
best2 = (float('inf'), None, None)
for L in range(86, 97):
    for base in [x / 100 for x in range(50, 90, 1)]:
        for curve in [x / 100 for x in range(0, 60, 1)]:
            def make_fn2(L, base, curve):
                return lambda p: hsl_to_hex(
                    hex_to_hsl(p)[0],
                    clamp(hex_to_hsl(p)[1] * (base + curve * hex_to_hsl(p)[1] / 100), 6, 95),
                    L
                )
            d = total_distance(make_fn2(L, base, curve))
            if d < best2[0]:
                best2 = (d, f"L={L}, S=s*({base:.2f}+{curve:.2f}*s/100)", make_fn2(L, base, curve))

print(f"\n非线性最优: {best2[1]}, total={best2[0]:.2f}")
for p, t in PAIRS:
    r = best2[2](p)
    print(f"  {p} -> {r} (目标 {t}, 距离 {color_distance(r, t):.1f})")
