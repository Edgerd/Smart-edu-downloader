# 设置页面拆分重构 Spec

## Why

`gui/pages/setting_page.py` 当前长达 1748 行，混杂了 UI 创建代码、样式代码、GUI 交互代码和功能实现代码（历史清除、UI 刷新、自动保存信号连接等）。这导致页面文件难以维护、职责不清。需要将功能实现代码下沉到 `core/settings/` 子模块，使页面只保留 GUI 相关代码。

## What Changes

- 新增 `core/settings/history_cleaner.py`：历史记录清除功能（下载历史 + 搜索历史文件删除）
- 新增 `core/settings/ui_refresher.py`：UI 刷新器，从 settings 字典反向更新所有 GUI 控件（与 SettingsCollector 对称）
- 新增 `core/settings/auto_save_connector.py`：自动保存信号连接器，统一连接所有控件的变更信号到延迟保存回调
- 修改 `core/settings/__init__.py`：导出三个新模块
- 修改 `gui/pages/setting_page.py`：
  - 删除 `_clear_history` 方法体，改为调用 `HistoryCleaner.clean_all()`
  - 删除 `_refresh_ui` 方法体，改为调用 `SettingsRefresher.refresh_from(page)`
  - 删除 `_connect_auto_save_signals` 方法体，改为调用 `AutoSaveConnector.connect(page, callback)`
  - 保留所有 UI 创建、样式、GUI 交互（文件对话框、颜色选择、Token 高亮动画）代码
  - 保留已有的薄包装方法（委托给 TokenManager/SettingsSaver/SettingsExporter/DomainManager）

## Impact

- Affected code:
  - `gui/pages/setting_page.py`（主要重构对象，预计减少约 300 行）
  - `core/settings/__init__.py`（新增导出）
  - 新增 3 个文件：`core/settings/history_cleaner.py`、`core/settings/ui_refresher.py`、`core/settings/auto_save_connector.py`
- 不涉及外部 API 变更，SettingPage 对外行为完全不变
- 不修改已有的 collector/saver/export/domain_manager/token_manager 模块

## ADDED Requirements

### Requirement: 历史记录清除模块

系统应在 `core/settings/history_cleaner.py` 提供 `HistoryCleaner.clean_all()` 静态方法，负责删除下载历史文件和搜索历史文件，并记录日志。

#### Scenario: 清除历史成功
- **WHEN** 调用 `HistoryCleaner.clean_all()`
- **THEN** 删除 `get_download_history_file()` 返回的文件（若存在）
- **AND** 删除 `get_cache_dir()/search_history.json` 文件（若存在）
- **AND** 每次删除操作记录 INFO 日志，失败记录 ERROR 日志

### Requirement: UI 刷新器模块

系统应在 `core/settings/ui_refresher.py` 提供 `SettingsRefresher.refresh_from(page)` 静态方法，从 `page.settings` 字典更新所有 GUI 控件值，与 `SettingsCollector` 的收集逻辑对称。

#### Scenario: 刷新所有控件
- **WHEN** 调用 `SettingsRefresher.refresh_from(page)`
- **THEN** 基础设置、剪贴板、下载、界面、颜色、高级、搜索、隐私、通知、域名白名单所有控件均从 settings 字典读取对应键值更新
- **AND** Token 输入框显示解密后的明文
- **AND** 通知"不自动消失"开关为 True 时隐藏时长控件

### Requirement: 自动保存信号连接器模块

系统应在 `core/settings/auto_save_connector.py` 提供 `AutoSaveConnector.connect(page, schedule_save_callback)` 静态方法，将页面所有开关、下拉框、输入框、数值控件的变更信号连接到延迟保存回调。

#### Scenario: 连接所有控件信号
- **WHEN** 调用 `AutoSaveConnector.connect(page, schedule_save_callback)`
- **THEN** 所有 SwitchWithLabel 控件连接 toggled 信号
- **AND** 所有 QComboBox 控件连接 currentTextChanged 信号
- **AND** 所有 QLineEdit 控件连接 textChanged 信号
- **AND** 所有 QSpinBox/QSlider 控件连接 valueChanged 信号
- **AND** 信号触发时调用 `schedule_save_callback`

## MODIFIED Requirements

### Requirement: 设置页面职责

`SettingPage` 类仅保留 GUI 相关代码：UI 创建、样式定义、GUI 交互（文件对话框、颜色选择、Token 高亮动画）、以及对 `core/settings` 子模块的薄包装调用。功能实现代码（历史清除、UI 刷新、自动保存信号连接）委托给 core 子模块。
