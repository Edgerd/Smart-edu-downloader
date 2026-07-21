* [x] gui/styles.py 已创建且包含 darken_color()、get_button_style() 函数
* [x] 4 个页面（home/resource/download/more）已删除本地重复样式函数并导入 gui/styles.py
* [x] downloader.py 进度回调速度计算已修复（B1），时间窗口对齐
* [x] downloader.py 校验失败重试已改为重新入队（B2），不再递归
* [x] downloader.py 文件保存已使用 os.replace（B6）
* [x] downloader.py TOCTOU 竞态已简化为 try/except（B7）
* [x] downloader.py worker_loop 退出信号已修复（B5）
* [x] more_page.py _open_log 已支持 Windows/macOS/Linux 跨平台（B3）
* [x] resource_page.py _load_accent_color 已使用 SettingsManager（B4）
* [x] 4 个页面已删除重复的 sys.path.insert，由 main.py 统一处理
* [x] home_page.py import re、import pyperclip 已移至文件头部
* [x] resource_page.py import json 已移至文件头部
* [x] home_page.py 未使用的 import threading 已验证实际使用，保留
* [x] core/token_crypto.py 已创建且包含加密/解密/迁移函数
* [x] downloader.py 不再直接导入 GUI 层模块（Core → GUI 依赖已解除）
* [x] setting_page.py 使用 core.token_crypto 替代本地加解密逻辑
* [x] gui/pages/__init__.py、gui/managers/__init__.py、gui/components/__init__.py、gui/widgets/__init__.py 已添加模块 docstring
* [x] main.py 已补充 example_download/example_resource_search/example_cache_management/example_settings/example_http_client 示例方法
* [x] Token 加密方案已从 XOR 升级为 Fernet，旧格式自动迁移
* [x] proxy_password 使用统一加密方案
* [x] 未使用代码已清理（冗余 animation_manager.py、_debug_manager 等）
* [x] version.py 和 产品更新信息.md 已同步更新
* [x] 所有修改文件通过 py_compile 语法检查，退出码 0，无报错
