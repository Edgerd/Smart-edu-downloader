# Tasks

* [x] Task 1: 创建 gui/styles.py 公共样式工具模块

  * [x] SubTask 1.1: 从 4 个页面提取 _darken_color 函数

  * [x] SubTask 1.2: 从 4 个页面提取 _get_button_style 函数

  * [x] SubTask 1.3: 从页面提取 _load_accent_color 到 styles.py 快捷方法

  * [x] SubTask 1.4: 4 个页面更新导入和调用指向 gui/styles.py

  * [x] SubTask 1.5: 从 4 个页面中删除本地重复的样式函数定义

* [x] Task 2: 修复 downloader.py 核心 Bug

  * [x] SubTask 2.1: 修复 B1 - 进度回调速度计算时间窗口错乱

  * [x] SubTask 2.2: 修复 B2 - 校验失败递归改为重新入队

  * [x] SubTask 2.3: 修复 B6 - os.remove+os.rename 替换为 os.replace

  * [x] SubTask 2.4: 修复 B7 - TOCTOU 竞态简化为 try/except

  * [x] SubTask 2.5: 修复 B5 - worker_loop 退出信号发射

  * [x] SubTask 2.6: 修复 B8 - 设置页面 lambda 闭包安全

* [x] Task 3: 修复 more_page.py 跨平台兼容

  * [x] SubTask 3.1: 修复 B3 - _open_log 使用 platform 检测跨平台打开文件

* [x] Task 4: 修复 resource_page.py 设置读取统一

  * [x] SubTask 4.1: 修复 B4 - _load_accent_color 使用 SettingsManager

  * [x] SubTask 4.2: 删除直接读取 settings.json 的代码

* [x] Task 5: 修复 PEP 8 合规问题

  * [x] SubTask 5.1: 删除 4 个页面中重复的 sys.path.insert

  * [x] SubTask 5.2: 修复 home_page.py 中 import re 移至文件头部

  * [x] SubTask 5.3: 修复 resource_page.py 中 import json 移至文件头部

  * [x] SubTask 5.4: 修复 home_page.py 中 import pyperclip 移至文件头部

  * [x] SubTask 5.5: 删除 home_page.py 中未使用的 import threading（经验证实际被使用，保留）

* [x] Task 6: 解除 Core → GUI 依赖（架构解耦）

  * [x] SubTask 6.1: 创建 core/token_crypto.py Token 加解密模块

  * [x] SubTask 6.2: 将 setting_page.py 中的 Token 加解密逻辑移至 core/token_crypto.py

  * [x] SubTask 6.3: downloader.py 改为导入 core.token_crypto 而非 gui.pages.setting_page

  * [x] SubTask 6.4: setting_page.py 改为导入 core.token_crypto 复用

* [x] Task 7: 补充模块级 docstring

  * [x] SubTask 7.1: gui/pages/__init__.py 添加模块 docstring

  * [x] SubTask 7.2: gui/managers/__init__.py 添加模块 docstring

  * [x] SubTask 7.3: gui/components/__init__.py 添加模块 docstring

  * [x] SubTask 7.4: gui/widgets/__init__.py 添加模块 docstring

* [x] Task 8: 补充 main.py 示例方法

  * [x] SubTask 8.1: 添加 example_download() 示例

  * [x] SubTask 8.2: 添加 example_resource_search() 示例

  * [x] SubTask 8.3: 添加 example_cache_management() 示例

  * [x] SubTask 8.4: 添加 example_settings() 示例

  * [x] SubTask 8.5: 添加 example_http_client() 示例

* [x] Task 9: Token 加密升级（安全修复 S1/S2）

  * [x] SubTask 9.1: 在 core/token_crypto.py 实现基于 Fernet 的加密方案

  * [x] SubTask 9.2: 添加自动迁移函数，检测旧 XOR 格式并转换

  * [x] SubTask 9.3: setting_page.py 更新为使用新加密模块

  * [x] SubTask 9.4: proxy_password 使用统一加密方案

* [x] Task 10: 清理未使用代码

  * [x] SubTask 10.1: 检查 gui/widgets/animation_manager.py 与 gui/managers/animation_manager.py 重复情况

  * [x] SubTask 10.2: 删除 main.py 中未使用的 _debug_manager

  * [x] SubTask 10.3: 统一 settings_manager 路径常量，消除 settings.json 硬编码

* [x] Task 11: 更新产品更新信息.md 和 version.py

  * [x] SubTask 11.1: 更新 version.py 版本号

  * [x] SubTask 11.2: 在 产品更新信息.md 中添加本轮修复记录

# Task Dependencies

* Task 1 先于 Task 4（Task 4 的 _load_accent_color 修复依赖 Task 1 的样式模块）

* Task 6 与 Task 9 相互依赖（Token 加密模块是两者的共同基础）

* Task 2 可独立执行

* Task 3 可独立执行

* Task 5 可独立执行

* Task 7 可独立执行

* Task 8 可独立执行

* Task 10 可独立执行

* Task 11 必须在所有任务完成后执行
