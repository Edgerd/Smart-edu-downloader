# 统一主题色下拉菜单实现与替换计划

## 1. 摘要

核心控件 `ThemeComboBox` 与样式函数 `get_theme_combobox_style` 已实现。本计划完成剩余集成与清理工作：将所有界面中的下拉框统一到 `ThemeComboBox` 视觉体系，确保边框/箭头随主题色热重载，并同步更新版本号与更新日志。

## 2. 现状分析

- `gui/widgets/theme_combobox.py` 已实现 `ThemeComboBox(QComboBox)`，支持动态主题色、运行时 SVG 着色、无边框阴影弹出窗。
- `gui/styles.py::get_theme_combobox_style(...)` 已按参考图规范生成 QSS。
- `gui/widgets/custom_controls.py` 中 `NoWheelComboBox` / `WheelComboBox` 已改为继承 `ThemeComboBox`。
- `gui/widgets/__init__.py` 已导出 `ThemeComboBox`。
- 仍存在的旧逻辑：
  - `gui/pages/resource_page.py` 在创建时和 `update_theme_colors` 中仍为 `WheelComboBox` 手动设置 `get_resource_page_combobox_style`。
  - `gui/debug_panel.py` 全局注入 `get_resource_page_combobox_style`。
  - `gui/pages/settings/base_tab.py` 未在 `update_theme_colors` 中刷新 `ThemeComboBox`。
  - `gui/components/debug/tools/log_file_manager.py` 直接使用原生 `QComboBox`。
  - `gui/styles.py::get_resource_page_combobox_style` 在替换后不再被代码引用。

## 3. 变更方案

### 3.1 资源页下拉框样式与热重载

文件：`gui/pages/resource_page.py`

- 移除 `from gui.styles import ... get_resource_page_combobox_style` 导入（仅保留 `load_primary_color`）。
- 在 `_create_browser_area` 中删除为级联 `WheelComboBox` 调用 `combo.setStyleSheet(get_resource_page_combobox_style(...))` 的代码。
- 在 `_create_search_area` 中删除为三个筛选 `WheelComboBox` 调用 `setStyleSheet(get_resource_page_combobox_style(...))` 的代码。
- 修改 `update_theme_colors`：
  - 删除 `combo_style = get_resource_page_combobox_style(primary)` 及后续 `setStyleSheet(combo_style)` 调用。
  - 改为遍历 `self.filter_subject_combo`、`self.filter_grade_combo`、`self.filter_publisher_combo` 及 `self.combo_boxes`，逐个调用 `combo.update_theme_colors(primary, background)`。

### 3.2 调试面板移除旧样式注入

文件：`gui/debug_panel.py`

- 从 `from .styles import (...)` 中移除 `get_resource_page_combobox_style`。
- 在 `_get_panel_style` 的返回字符串中删除 `{get_resource_page_combobox_style(self._accent_color)}` 行。
- 子标签页中的 `NoWheelComboBox` 会自行管理样式，无需面板注入。

### 3.3 设置标签页基类支持 ThemeComboBox 热重载

文件：`gui/pages/settings/base_tab.py`

- 在 `BaseSettingTab.update_theme_colors` 中追加：
  ```python
  from gui.widgets import ThemeComboBox
  for combo in self.findChildren(ThemeComboBox):
      if hasattr(combo, "update_theme_colors"):
          combo.update_theme_colors(primary, background)
  ```
- 各设置标签页（`interface_tab.py`、`download_tab.py`、`advanced_tab.py`、`privacy_tab.py`）无需修改控件类型，因为已使用 `NoWheelComboBox`。

### 3.4 日志文件管理器替换原生 QComboBox

文件：`gui/components/debug/tools/log_file_manager.py`

- 将 `from PyQt5.QtWidgets import (..., QComboBox, QMessageBox)` 中的 `QComboBox` 移除。
- 在文件顶部添加 `from gui.widgets import ThemeComboBox`。
- 将 `self.level_combo = QComboBox()` 改为 `self.level_combo = ThemeComboBox(enable_wheel=False)`。
- 删除随后对 `self.level_combo.setFont(body_font())` 的调用（`ThemeComboBox` 构造函数已设置）。

### 3.5 清理旧样式函数与冗余导入

文件：`gui/styles.py`

- 在确认 `get_resource_page_combobox_style` 无代码引用后，删除该函数及其鸿蒙字体相关引用，保持文件整洁。

文件：`gui/widgets/custom_controls.py`

- 移除 `from PyQt5.QtWidgets import QSpinBox, QComboBox, QLineEdit, QApplication` 中不再使用的 `QComboBox`。
- 移除 `from gui.styles import load_primary_color` 和 `from gui.utils.color_utils import lighten` 中仅被已删除旧 `NoWheelComboBox` 使用的部分（保留 `NoWheelSpinBox` 所需引用，避免误删）。

### 3.6 版本号与更新日志

文件：`core/infrastructure/version.py`

- 当前版本为 `5.6.17 Beta 12`，本次为预发布迭代，按规范递增预发布标识：
  - `VERSION = "5.6.17 Beta 13"`
  - `VERSION_INFO = (5, 6, 17, 'Beta', 13)`

文件：`.dev/产品更新信息.md`

- 在 `## 5.6.17 Beta 13` 下新增条目：
  - 新增功能：统一主题色下拉菜单控件，替换所有原生/旧版下拉框；边框与箭头图标随主题色变化，展开列表与标题栏形成连续矩形边框。
  - 影响范围：资源页、设置页各标签页、欢迎页、F12 调试面板及其子工具。

## 4. 假设与决策

- **主题色来源**：箭头颜色跟随项目动态主题色 `load_primary_color()`，而非固定 `#2B8FD9`，以满足“方便后续主题切换”。
- **字体**：下拉框 QSS 中显式使用 `"Microsoft YaHei" 12px`，与参考图一致。
- **hover/选中背景**：使用 `#E8F4FD`，未选中项背景使用 `#FFFFFF`。
- **弹出窗无边框阴影**：通过 `Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint` + `Qt.WA_TranslucentBackground` 实现。
- **连续边框**：通过 `QComboBox:on` 移除底部圆角、`QAbstractItemView` 移除顶部圆角与顶部边框实现。
- **替换范围**：所有下拉框，包括原生 `QComboBox`、旧 `NoWheelComboBox`/`WheelComboBox` 间接实例，统一走 `ThemeComboBox` 样式体系。
- **版本策略**：当前处于预发布阶段，仅递增 Beta 标识。

## 5. 验证步骤

1. 对以下文件运行 `python -m py_compile`，确认无语法错误：
   - `gui/widgets/theme_combobox.py`
   - `gui/widgets/custom_controls.py`
   - `gui/widgets/__init__.py`
   - `gui/styles.py`
   - `gui/pages/resource_page.py`
   - `gui/pages/settings/base_tab.py`
   - `gui/components/debug/tools/log_file_manager.py`
   - `gui/debug_panel.py`
   - `core/infrastructure/version.py`
2. 启动应用，检查以下位置下拉菜单：
   - 资源页搜索筛选（学科、年级、版本）及级联浏览下拉框。
   - 设置页 → 界面、下载、高级、隐私标签页。
   - 欢迎页语言选择。
   - F12 调试面板 → 日志文件管理器、实验室标签页。
3. 验证展开时标题栏与列表边框连续、无顶部双线、无系统阴影。
4. 验证箭头在闭合/展开状态切换正确，颜色与当前主题色一致。
5. 在设置中切换主题色，验证所有下拉框边框、箭头颜色自动刷新。
6. 检查 `%TEMP%/Smart-edu-downloader/temp/combobox_icons/` 下按不同主题色生成对应 SVG 临时文件。
