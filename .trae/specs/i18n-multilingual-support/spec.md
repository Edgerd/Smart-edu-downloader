# 多语言支持（i18n）改造 Spec

## Why
当前 Smart Edu Downloader 的界面文本（按钮、标签、提示、菜单、状态栏消息等）大量以中文字符串硬编码在 PyQt5 代码中。当需要支持其他语言或统一修改文案时，必须逐文件修改源码，维护成本高且容易遗漏。因此需要引入一套完整的多语言（i18n）架构，将用户可见文本与代码分离，先落地中文语言包，再为后续扩展其他语言打好基础。

## What Changes
- 新增 `i18n/` 目录作为语言包根目录，按 `i18n/<lang>/LC_MESSAGES/messages.json` 或 `i18n/<lang>.json` 组织（优先采用扁平 JSON 便于维护）。
- 新增 `core/i18n/translator.py` 语言加载与查询模块，应用启动时自动扫描 `i18n/` 下所有语言文件并加载到内存。
- 新增 `core/i18n/__init__.py`，对外暴露简洁接口 `_(key, **kwargs)` / `gettext(key, **kwargs)`。
- 新增 `i18n/zh_CN.json` 中文语言包，汇总当前所有面向用户的界面文本。
- 修改 `core/infrastructure/default_settings.py`，新增默认设置项 `language: "zh_CN"`。
- 修改 `main.py`，在 `QApplication` 创建后尽早初始化 translator，确保所有 UI 组件创建时即可取到翻译。
- 修改 `gui/pages/setting_page.py`，在"界面"设置分组中新增"显示语言"选项：下拉框列出已加载语言，选择后保存设置并提示"需要重启应用才能生效"。
- 逐步替换 `gui/pages/`、`gui/widgets/`、`gui/components/`、`core/` 中所有面向用户的硬编码中文文本为 `_("key")` 调用。
- 日志、异常、调试信息中面向开发者的文本可保留中文或英文，不强制翻译；面向用户的提示、通知、弹窗必须翻译。

## Impact
- 受影响功能：主页、资源库、下载页、更多页、设置页、调试面板、标题栏、状态栏、通知、系统托盘、各类弹窗。
-