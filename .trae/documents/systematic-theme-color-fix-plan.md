# 系统性修复主题颜色切换问题实施计划

## 摘要

本计划旨在修复 Smart eduDownloader 中主题色切换时多处 UI 元素颜色/字体未正确同步的问题。核心思路是：

1. **统一主题色来源**：所有控件默认颜色统一使用 `load_primary_color()`，禁止硬编码 `#2078DA`、`#007AFF`、`#1A82E2` 等蓝色；主题切换时通过 `update_theme_colors(primary, background)` 接口主动刷新。
2. **补齐刷新接口**：为缺少 `update_theme_colors` 的页面/子控件补全实现，并确保父容器在主题变化时递归通知子标签页。
3. **修复背景继承**：调试面板等内容区通过透明背景或显式同步背景色，避免 `#FFFFFF` 残留。
4. **统一字体**：在公共样式函数中为 `QTableWidget`、`QTreeWidget`、`QComboBox`、`QMenu` 等控件显式声明鸿蒙字体。
5. **SVG 图标动态着色**：扩展 `IconManager` 颜色替换规则并支持缓存清理，确保主题切换后图标重新渲染。

---

## 当前状态分析

### 已完成的修复（来自前序会话）

- `gui/widgets/ios_download_item.py`：已将硬编码 `#007AFF` 改为 `load_primary_color()`，并新增 `update_theme_colors`。
- `gui/widgets/download_status_indicator.py`：已将下载中颜色改为 `load_primary_color()`，并新增 `update_theme_colors`。
- `gui/styles.py`：已为 `get_fluent_table_style`、`get_fluent_tree_style`、`get_fluent_menu_style`、`get_fluent_rounded_menu_style`、`get_resource_page_combobox_style` 添加鸿蒙字体声明。

### 仍存在的问题

| 问题类别 | 具体表现 | 影响文件 |
|---|---|---|
| 硬编码主题色 | `MaterialMenu` / `MaterialMenuItem` 默认 `accent_color="#2078DA"` | `gui/widgets/material_menu.py` |
| 硬编码主题色 | `CustomContextMenu` 加载失败 fallback 返回 `#2078DA` | `gui/widgets/custom_context_menu.py` |
| 硬编码主题色 | `DonationDialog` 加载失败 fallback 返回 `#2078DA` | `gui/widgets/donation_dialog.py` |
| 硬编码主题色 | `CrashReporterDialog` 在模块导入时一次性读取主题色，切换后不更新 | `gui/widgets/crash_reporter_dialog.py` |
| SVG 颜色规则不全 | `IconManager._FILL_REGEX` 只替换 `white/#ffffff/#fff/#1A82E2`，未包含 `#2078DA/#007AFF` 等，且缓存不会随主题切换清理 | `core/ui/icon_manager.py` |
| 垂直标签按钮 | `MaterialTabButton` 默认水波纹色 `#7AB8F5`，SVG 替换规则不足 | `gui/widgets/vertical_tab_widget.py` |
| Material 按钮 | `MaterialButton` 默认水波纹色 `#7AB8F5` | `gui/widgets/material_button.py` |
| 导航栏按钮 | `NavButton` 默认水波纹色 `#7AB8F5`；`NavBar` 缺少 `update_theme_colors`，主题切换后图标/文字颜色不刷新 | `gui/components/nav_bar.py` |
| 调试面板背景 | `DebugPanel.update_theme_colors` 未更新 `stacked_widget` 背景样式；`LogTab` 无 `update_theme_colors`；部分子控件内部使用 `background: white` | `gui/debug_panel.py`、`gui/components/debug/log_tab.py`、`gui/components/debug/debug_tools_tab.py` 等 |
| 设置子标签页 | `BaseSettingTab` 只有 `set_accent_color`，缺少标准 `update_theme_colors`；部分子标签页内部按钮/输入框未注册或刷新 | `gui/pages/settings/base_tab.py`、各 `tabs/*.py` |
| 字体不一致 | 部分 `QComboBox`、`QMenu`、`QTableWidget` 样式仍缺失 `font-family`；调试面板小标题、设置页下拉框前文字未强制使用鸿蒙字体 | `gui/styles.py`、各页面 |

---

## 修复任务

### 任务 1：修复硬编码主题色控件

#### 1.1 `gui/widgets/material_menu.py`

- 将 `MaterialMenuItem.__init__` 的默认参数 `accent_color: str = "#2078DA"` 改为 `accent_color: str = None`，在方法内使用 `load_primary_color()` 兜底。
- 将 `MaterialMenu.__init__` 的默认参数 `accent_color: str = "#2078DA"` 改为 `accent_color: str = None`，在方法内使用 `load_primary_color()` 兜底。
- 确保 `setAccentColor` 递归更新子菜单时，子菜单也使用新的主题色。

#### 1.2 `gui/widgets/custom_context_menu.py`

- 将 fallback 颜色 `"#2078DA"` 改为调用 `load_primary_color()`，保持与主程序主题一致。

#### 1.3 `gui/widgets/donation_dialog.py`

- 将 fallback 颜色 `"#2078DA"` 改为调用 `load_primary_color()`。
- 为 `DonationDialog` 新增 `update_theme_colors(primary, background)` 方法，刷新关闭按钮主题色（对话框若已在显示中）。

#### 1.4 `gui/widgets/crash_reporter_dialog.py`

- 删除模块级常量 `ACCENT_COLOR = _load_primary_color()`，避免导入时固定。
- 在 `CrashReporterDialog.__init__` 中动态读取 `load_primary_color()`，用于按钮和样式。
- 新增 `update_theme_colors(primary, background)` 方法，刷新所有使用主题色的按钮/标签样式（若对话框已在显示中）。

---

### 任务 2：统一 SVG 图标着色与缓存

#### 2.1 `core/ui/icon_manager.py`

- 扩展 `_FILL_REGEX` 匹配规则，增加 `#2078DA`、`#007AFF`、`#1277DD` 等项目中实际使用的蓝色占位符。
- 新增 `clear_pixmap_cache()` 方法（或扩展 `clear_cache`），支持只清理按颜色缓存的 pixmap，避免主题切换后仍命中旧颜色缓存。
- 在 `SettingsHandler.apply_theme_colors` 中调用 `icon_manager.clear_cache()`，确保切换主题后 SVG 重新着色。

#### 2.2 `gui/widgets/vertical_tab_widget.py`

- 在 `MaterialTabButton._load_icon` 中补充 SVG 颜色替换规则，与 `IconManager` 规则对齐（替换 `#1A82E2`、`#2078DA`、`#007AFF`、`#1277DD` 等为主题色）。
- 将 `MaterialTabButton._ripple_color` 初始值从 `#7AB8F5` 改为基于 `load_primary_color()` 的淡化色（使用 `ripple_tint`）。

---

### 任务 3：统一 Material 按钮与导航栏水波纹颜色

#### 3.1 `gui/widgets/material_button.py`

- 将 `MaterialButton._ripple_color` 初始值 `#7AB8F5` 改为基于 `load_primary_color()` 的淡化色。
- 在 `setAccentColor` 中同步更新 `_ripple_color`，确保切换主题后水波纹颜色正确。

#### 3.2 `gui/components/nav_bar.py`

- 将 `NavButton._ripple_color` 初始值 `#7AB8F5` 改为基于 `_active_color` 的淡化色。
- 在 `set_active_color` 中同步更新水波纹颜色。
- 为 `NavBar` 新增 `update_theme_colors(primary, background)` 方法：
  - 更新 `_accent_color`。
  - 重新加载所有导航按钮的 SVG 图标（使用新的主题色）。
  - 更新按钮文字颜色：激活状态为 `#FFFFFF`，未激活状态为 `#FFFFFF`（导航栏背景为主题色，文字始终白色）。
  - 调用 `set_active_button` 刷新当前按钮高亮。
- 在 `SettingsHandler._notify_theme_color_changed` 循环中，`NavBar` 会被自动通知。

---

### 任务 4：修复调试面板背景色与主题同步

#### 4.1 `gui/debug_panel.py`

- 在 `update_theme_colors` 中显式更新 `self.nav_bar.stacked_widget` 的背景样式，避免内容区残留旧背景色或变白。
- 同步刷新 `minimize_btn` 等使用语义灰的按钮（保持灰色，但需确保不影响主题色按钮）。

#### 4.2 `gui/components/debug/log_tab.py`

- 新增 `update_theme_colors(primary, background)` 方法：
  - 刷新 `export_btn` 主题色（`clear_btn` 保持红色语义色）。
  - 刷新日志级别复选框颜色（保持语义色，仅确保不硬编码主题蓝）。
  - 刷新日志文本区域背景/边框颜色（保持深色主题，仅同步边框强调色）。

#### 4.3 `gui/components/debug/console_tab.py`

- 在已有的 `update_theme_colors` 中补充刷新 `console_input` 的焦点边框色和 `execute_btn` 主题色。

#### 4.4 `gui/components/debug/debug_tools_tab.py`

- 在已有的 `update_theme_colors` 中补充刷新 `var_monitor_list`、`error_list` 等内部 `background: white` 的控件，改为 `background: {background}` 或保持卡片式白底但同步边框色。
- 确保 `QGroupBox` 标题颜色随主题色更新（当前已通过 `DebugPanel._get_panel_style` 全局设置，但需验证子标签页未覆盖）。

#### 4.5 `gui/components/debug/info_tab.py` / `lab_tab.py`

- 验证现有 `update_theme_colors` 已正确同步背景与标题色；补充刷新依赖版本标签颜色（保持语义绿/红，但避免硬编码蓝）。

---

### 任务 5：统一设置子标签页主题刷新接口

#### 5.1 `gui/pages/settings/base_tab.py`

- 新增标准 `update_theme_colors(primary: str, background: str)` 方法，内部调用 `set_accent_color(primary)` 并刷新 `_get_input_style` 等依赖主题色的样式。
- 保留 `set_accent_color` 作为兼容接口。

#### 5.2 各设置子标签页

- `basic_tab.py`、`download_tab.py`、`interface_tab.py`、`advanced_tab.py`、`privacy_tab.py`：
  - 确保所有使用主题色的按钮已通过 `register_accent_button` 注册，或在 `update_theme_colors` 中显式刷新。
  - 将 `interface_tab.py` 中硬编码的 `#2078DA` 默认值改为 `load_primary_color()`（如自定义主题 base 默认值）。
  - 将下拉框、输入框等样式统一使用 `BaseSettingTab._get_input_style`，确保焦点色随主题变化。

#### 5.3 `gui/pages/setting_page.py`

- 在 `update_theme_colors` 中确保所有子标签页都被递归通知；优先调用 `update_theme_colors`，不存在时回退到 `set_accent_color`。

---

### 任务 6：修复主页/资源页/下载页/更多页剩余问题

#### 6.1 `gui/pages/home_page.py`

- 检查 `update_theme_colors` 是否刷新了 `url_input`（`AnimatedGradientBorderEdit`）的焦点边框色；若该控件支持 `setAccentColor` 则调用。
- 检查封面控件 `cover_widget` 的占位图标及预览区域背景色是否已随主题更新（`CoverWidget.update_theme_colors` 已存在，验证其是否正确处理占位图标）。
- 确保历史记录标签页 `tab_widget` 样式中未硬编码蓝色。

#### 6.2 `gui/pages/resource_page.py`

- 在 `update_theme_colors` 中补充刷新所有 `WheelComboBox` 的样式（使用 `get_resource_page_combobox_style(primary)`）。
- 检查课本预览占位图标：若使用 `IconManager.load_title_svg` 或 `load_colored_pixmap`，需确保颜色参数为 `primary`。
- 检查预览区域背景色是否硬编码为白色，应继承内容区背景或显式同步。

#### 6.3 `gui/pages/download_page.py`

- 验证 `update_theme_colors` 已刷新下载表格、统计标签、操作按钮；检查是否有遗漏的蓝色按钮。

#### 6.4 `gui/pages/more_page.py`

- 验证 `update_theme_colors` 已刷新标题、分组标题、表格样式；检查历史记录表格表头字体是否已使用鸿蒙字体。

---

### 任务 7：统一字体样式

#### 7.1 `gui/styles.py`

- 为 `get_fluent_table_style` 的 `QTableWidget::item` 补充 `font-family: "{get_harmonyos_family()}"`。
- 为 `get_fluent_tree_style` 的 `QTreeWidget::item` 补充 `font-family`。
- 为 `get_fluent_menu_style` / `get_fluent_rounded_menu_style` 的 `QMenu` 和 `QMenu::item` 补充 `font-family`。
- 为 `get_resource_page_combobox_style` 的 `QComboBox` 和 `QComboBox QAbstractItemView::item` 补充 `font-family`。

#### 7.2 各页面

- 设置页下拉框前的 `QLabel` 已使用 `body_font()`，无需额外修改，但需确认未通过 `setStyleSheet` 覆盖字体。
- 调试面板小标题（`QGroupBox::title`）已在 `DebugPanel._get_panel_style` 中声明 `font-family`。
- 表格表头通过 `get_fluent_table_style` 统一声明字体。

---

### 任务 8：更新版本号与产品更新日志

#### 8.1 `core/infrastructure/version.py`

- 当前 `VERSION = "5.6.16 Beta 9"`，与 `.dev/产品更新信息.md` 中已记录的 Beta 10 不一致。
- 本任务属于正式功能修复集合，按规范升级到 `5.6.16 Beta 10`（与现有更新日志对齐；若后续发现 Beta 10 已存在其他记录，则升级为 Beta 11，需以实际文件为准）。

#### 8.2 `.dev/产品更新信息.md`

- 在 `5.6.16 Beta 10`（或新 Beta 11）条目中添加：
  - 修复主题色切换时 SVG 图标、导航栏高亮文字、调试面板标题/导航栏、主页表格标签页、Material 按钮、资源页预览占位图标等未更新的问题。
  - 统一所有蓝色按钮为跟随当前主题色。
  - 修复调试面板内容区背景色变白的问题。
  - 统一设置页下拉框前文字、调试面板小标题、表格表头字体为鸿蒙字体。
- 更新日期使用 `2026-07-11`。

---

## 验证步骤

1. **静态语法检查**
   - 运行 `python -m py_compile` 对所有修改过的 Python 文件进行编译，确保无语法错误。
   - 运行 `python -c "from gui.main_window import MainWindow"` 验证导入无异常。

2. **主题切换功能测试**
   - 启动程序，分别切换到不同主题预设（极客蓝、铁杆粉、活跃橙、秋议金、自定义颜色）。
   - 检查主页、资源库、下载、设置、更多页面：
     - 标题 SVG 图标颜色是否随主题变化。
     - Material 按钮颜色是否随主题变化。
     - 表格选中/表头样式是否正确。
   - 打开调试面板（F12），检查：
     - 标题颜色、导航栏背景、内容区背景是否随主题变化。
     - 日志、控制台、信息、工具、实验室各标签页背景是否为内容区背景色而非 `#FFFFFF`。

3. **边界场景测试**
   - 程序启动瞬间切换主题：确认无颜色残留。
   - 连续多次切换主题：确认所有控件颜色保持一致，无缓存导致的旧颜色。
   - 重启程序后：确认上次主题色正确加载并应用。

4. **字体一致性检查**
   - 检查设置页下拉框前文字、调试面板分组标题、各页面表格表头是否使用鸿蒙字体（可通过截图或设置系统无鸿蒙字体时观察 fallback 差异）。

---

## 假设与决策

- **语义色保留**：红色（危险/删除）、绿色（成功/添加）、灰色（取消/次要操作）等语义色按钮保持原色，不强制跟随主题色；仅将原来使用蓝色（`#2078DA`、`#007AFF`、`#1A82E2`）的按钮/元素改为主题色。
- **SVG 缓存**：主题切换时清空 `IconManager` 的 pixmap 缓存，确保重新渲染；svg 文本缓存可保留。
- **调试面板日志区域**：日志文本区域保持深色背景（便于阅读），仅同步边框/强调色。
- **崩溃提示对话框**：由于通常在程序崩溃后显示，动态读取主题色即可，不要求运行时响应主题切换（但仍实现 `update_theme_colors` 以保持一致性）。
- **版本号**：按项目规范，本次修复集合属于预发布版本迭代，仅递增预发布标识（Beta 9 → Beta 10），不升级主/小版本号。
