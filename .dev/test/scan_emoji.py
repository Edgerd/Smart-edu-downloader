# -*- coding: utf-8 -*-
"""扫描设置/调试菜单代码中的 emoji 字符。"""
import os
import re
import sys

sys.path.insert(0, r"e:\hello\web\Smart-edu-downloader")

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F9FF"  # 杂项符号和象形文字
    "\U0001FA00-\U0001FA6F"  # 扩展象形文字
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000027BF"  # 杂项符号
    "\U0001F100-\U0001F1FF"  # 信封符号
    "\U0001F200-\U0001F251"  # 带圈补充
    "\U0001F004\U0001F0CF"   # 麻将/扑克
    "\U00002B50\U00002B55"   # 星形/圆圈
    "]+",
    flags=re.UNICODE,
)

TARGET_DIRS = [
    r"e:\hello\web\Smart-edu-downloader\gui\pages\settings",
    r"e:\hello\web\Smart-edu-downloader\gui\components\debug",
]


def main():
    found = []
    for target_dir in TARGET_DIRS:
        for root, _dirs, files in os.walk(target_dir):
            for filename in files:
                if not filename.endswith(".py"):
                    continue
                path = os.path.join(root, filename)
                with open(path, "r", encoding="utf-8") as f:
                    for lineno, line in enumerate(f, start=1):
                        match = EMOJI_PATTERN.search(line)
                        if match:
                            found.append((path, lineno, match.group(), line.strip()))

    if not found:
        print("未在设置/调试菜单代码中发现 emoji。")
        return

    print(f"发现 {len(found)} 处 emoji：")
    for path, lineno, emoji, text in found:
        rel = os.path.relpath(path, r"e:\hello\web\Smart-edu-downloader")
        print(f"  {rel}:{lineno}: {emoji!r} -> {text!r}")


if __name__ == "__main__":
    main()
