# Tasks

- [x] Task 1: 创建历史记录清除模块 `core/settings/history_cleaner.py`
  - [x] SubTask 1.1: 实现 `HistoryCleaner.clean_all()` 静态方法，删除下载历史文件和搜索历史文件，记录日志
- [x] Task 2: 创建 UI 刷新器模块 `core/settings/ui_refresher.py`
  - [x] SubTask 2.1: 实现 `SettingsRefresher.refresh_from(page)` 静态方法，从 settings 字典更新所有 GUI 控件（基础/剪贴板/下载/界面/颜色/高级/搜索/隐私/通知/域名白名单）
  - [x] SubTask 2.2: Token 输入框显示解密明文，通知"不自动消失"时隐藏时长控件
- [x] Task 3: 创建自动保存信号连接器模块 `core/settings/auto_save_connector.py`
  - [x] SubTask 3.1: 实现 `AutoSaveConnector.connect(page, schedule_save_callback)` 静态方法，连接所有开关/下拉框/输入框/数值控件信号
- [x] Task 4: 更新 `core/settings/__init__.py` 导出三个新模块
- [x] Task 5: 重构 `gui/pages/setting_page.py`
  - [x] SubTask 5.1: 导入三个新模块
  - [x] SubTask 5.2: `_clear_history` 改为调用 `HistoryCleaner.clean_all()`，保留确认对话框
  - [x] SubTask 5.3: `_refresh_ui` 改为调用 `SettingsRefresher.refresh_from(self)`
  - [x] SubTask 5.4: `_connect_auto_save_signals` 改为调用 `AutoSaveConnector.connect(self, lambda: self._auto_save_timer.start(2000))`
  - [x] SubTask 5.5: 删除原方法体中已迁移的代码
- [x] Task 6: 验证代码正确性
  - [x] SubTask 6.1: `python -m py_compile` 编译所有修改文件
  - [x] SubTask 6.2: 确认 setting_page.py 行数显著减少（1748 → 1545）

# Task Dependencies

- Task 5 依赖 Task 1、Task 2、Task 3、Task 4
- Task 6 依赖 Task 5
- Task 1、Task 2、Task 3 可并行
