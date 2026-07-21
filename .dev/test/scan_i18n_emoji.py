# -*- coding: utf-8 -*-
"""扫描语言包中设置/调试相关键的 emoji。"""
import os
import re
import json
import sys

sys.path.insert(0, r"e:\hello\web\Smart-edu-downloader")

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F100-\U0001F1FF"
    "\U0001F200-\U0001F251"
    "\U0001F004\U0001F0CF"
    "\U00002B50\U00002B55"
    "]+",
    flags=re.UNICODE,
)

I18N_DIR = r"e:\hello\web\Smart-edu-downloader\resources\i18n"

# 关注 settings / debug 相关键
INTERESTING_PREFIXES = ("settings.", "debug.", "common.success", "common.error",
                        "common.tip", "common.confirm", "common.add",
                        "common.delete", "common.clear")


def scan_file(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    found = []
    for key, value in data.items():
        if not key.startswith(INTERESTING_PREFIXES):
            continue
        if not isinstance(value, str):
            continue
        match = EMOJI_PATTERN.search(value)
        if match:
            found.append((key, value, match.group()))
    return found


def main():
    for filename in sorted(os.listdir(I18N_DIR)):
        if not filename.endswith(".json"):
            continue
        path = os.path.join(I18N_DIR, filename)
        found = scan_file(path)
        if not found:
            continue
        print(f"\n{filename}:")
        for key, value, emoji in found:
            print(f"  {key}: {value!r} (emoji: {emoji!r})")


if __name__ == "__main__":
    main()
