# Tasks

- [x] Task 1: 建立多语言核心模块
  - [x] SubTask 1.1: 创建 `core/i18n/__init__.py`，导出一个全局可访问的翻译函数 `_()` 或 `tr()`
  - [x] SubTask 1.2: 创建 `core/i18n/translator.py`，实现 `Translator` 类，支持扫描 `i18n/` 目录、加载 JSON 语言文件、键查找、缺省回退
  - [x] SubTask 1.3: 创建项目根目录 `i18n/zh_CN.json` 初始文件，包含通用键（如应用名、确定、取消等）
  - [x] SubTask 1.4: 实现 `get_available_languages()` 返回已加载语言列表，供设置界面使用

- [x] Task 2: 提取界面中文文本到语言包
  - [x] SubTask 2.1: 扫描 `gui/pages/*.py`，列出所有硬编码中文展示文本
  - [x] SubTask 2.2: 扫描 `gui/widgets/*.py`、`gui/components/**/*.py`，列出所有硬编码中文展示文本
  - [x] SubTask 2.3: 扫描 `core/` 中面向用户的文本（日志、通知、异常提示等），列出需国际化的中文
  - [x] SubTask 2.4: 将上述文本整理成结构化键值对，写入 `i18n/zh_CN.json`

- [x] Task 3: 替换 `gui/pages/` 中的硬编码中文
  - [x] SubTask 3.1: 替换 `home_page.py` 中所有界面文本为翻译调用
  - [x] SubTask 3.2: 替换 `resource_page.py` 中所有界面文本为翻译调用
  - [x] SubTask 3.3: 替换 `download_page.py` 中所有界面文本为翻译调用
  - [x] SubTask 3.4: 替换 `more_page.py` 中所有界面文本为翻译调用
  - [x] SubTask 3.5: 替换 `setting_page.py` 中所有界面文本为翻译调用

- [x] Task 4: 替换 `gui/widgets/` 和 `gui/components/` 中的硬编码中文
  - [x] SubTask 4.1: 替换通用控件（按钮、菜单、对话框等）中的中文文本
  - [x] SubTask 4.2: 替换调试面板组件中的中文文本
  - [x] SubTask 4.3: 替换状态栏、导航栏、标题栏等全局组件中的中文文本

- [x] Task 5: 替换 `core/` 中的硬编码中文
  - [x] SubTask 5.1: 替换下载、搜索、缓存模块中面向用户的通知/提示文本
  - [x] SubTask 5.2: 替换设置相关模块（collector、saver、export 等）中的用户可见文本

- [x] Task 6: 设置界面添加语言选择功能
  - [x] SubTask 6.1: 在 `core/infrastructure/default_settings.py` 的界面设置区新增 `"language": "zh_CN"`
  - [x] SubTask 6.2: 在 `gui/pages/setting_page.py` 的"界面"分类下新增语言选择行（下拉框 + 重启提示标签）
  - [x] SubTask 6.3: 在 `gui/managers/settings_handler.py` 中处理 `language` 设置的读取与保存

- [x] Task 7: 启动流程集成翻译器
  - [x] SubTask 7.1: 在 `main.py` 中，于 `MainWindow` 创建前初始化 `core.i18n` 并加载配置语言
  - [x] SubTask 7.2: 确保所有页面和控件在导入时即可使用 `_()` 函数

- [x] Task 8: 验证与测试
  - [x] SubTask 8.1: 运行 `python -m py_compile` 检查所有修改文件无语法错误
  - [x] SubTask 8.2: 启动应用，确认界面文本正常显示且没有中文硬编码遗漏
  - [x] SubTask 8.3: 在设置界面切换语言（当前只有 zh_CN），验证保存后重启提示正确出现

# Task Dependencies

- Task 2 depends on Task 1
- Task 3 depends on Task 2
- Task 4 depends on Task 2
- Task 5 depends on Task 2
- Task 6 depends on Task 1
- Task 7 depends on Task 1 and Task 6
- Task 8 depends on Task 3, Task 4, Task 5, Task 6, Task 7
