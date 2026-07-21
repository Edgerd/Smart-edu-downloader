# Checklist

- [x] `core/i18n/translator.py` 实现 Translator 类，支持扫描、加载、查找、回退
- [x] `core/i18n/__init__.py` 导出 `_()` / `tr()` 翻译函数
- [x] 项目根目录 `i18n/` 存在且包含 `zh_CN.json`
- [x] `i18n/zh_CN.json` 包含所有界面展示文本的键值对
- [x] `core/infrastructure/default_settings.py` 中新增 `"language": "zh_CN"` 默认设置
- [x] `main.py` 在创建 MainWindow 前初始化翻译器并加载配置语言
- [x] `gui/pages/setting_page.py` 的"界面"分类中存在语言选择下拉框
- [x] 语言选择变更后显示"重启生效"提示
- [x] `gui/managers/settings_handler.py` 正确读取和保存 `language` 设置
- [x] `gui/pages/` 中所有页面不再包含硬编码中文展示文本
- [x] `gui/widgets/` 和 `gui/components/` 中所有用户可见文本通过翻译接口获取
- [x] `core/` 中面向用户的通知、提示、异常文本通过翻译接口获取
- [x] 应用能正常启动，界面中文显示无异常
- [x] `python -m py_compile` 检查所有修改文件无语法错误

## 验证结果摘要

| 验证项 | 状态 | 备注 |
|--------|------|------|
| 中文 UI 文本扫描 | 通过 | `gui/` 与 `core/` 中已无硬编码中文 UI 文本 |
| 翻译键补充 | 通过 | 已补充 `nav`、`core.tooltips`、`widgets.download_item`、`core.url` 及 `common.unknown` 等键 |
| 语法检查 | 通过 | 全部修改文件通过 `py_compile`，`zh_CN.json` 通过 `json.load` |
| main.py 启动流程 | 通过 | 在 MainWindow 前完成 `set_language` 调用 |
| 设置界面语言模块 | 通过 | 下拉框、重启提示、保存逻辑完整 |
| 最小启动测试 | 通过 | MainWindow 实例化成功并正常退出 |

## 补充修复记录

- `gui/pages/more_page.py`：历史记录标签页刷新时改用 `tab_type` 属性识别类型，移除对中文标签文本的依赖。
- `core/ui/icon_manager.py`：`NAV_ICONS` 的导航名称与提示文本全部改用翻译键。
- `core/ui/status_bar.py`：悬停提示字典与 `update_all_tooltips` 中的中文提示全部改用 `core.tooltips.*` 键。
- `gui/main_window.py`：剪贴板 URL 检测通知改用 `notifications.clipboard_url_detected_*` 键。
- `gui/widgets/ios_download_item.py`：操作按钮提示与未知状态文本改用翻译键。
- `core/url/url_modifier.py`：URL 校验提示、空历史提示及请求错误提示改用翻译键。
- `i18n/zh_CN.json`：新增上述模块所需的全部翻译键。
