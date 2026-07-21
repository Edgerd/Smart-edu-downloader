# 调试面板标签页卡片式布局重构计划

## 1. 概述

将调试面板（DebugPanel）中的 **信息**、**调试工具**、**实验室** 三个标签页改为设置界面同款的白色背景圆角卡片式布局；**日志**、**控制台** 两个标签页在保持现有深色终端风格的基础上增加圆角边框。

## 2. 当前状态分析

### 2.1 调试面板全局样式

- 文件：`gui/debug_panel.py`
- 已为 `#debugPanel QGroupBox` 设置全局样式：白色背景、1px 实线边框、`border-radius: 8px`
- 已加载主题色 `self._accent_color = load_accent_color()`，但尚未用于 `QGroupBox::title`

### 2.2 信息标签页（InfoTab）

- 文件：`gui/components/debug/info_tab.py`
- 使用 `QGroupBox` 分组（系统信息 / 应用信息 / 依赖信息）
- 每个 `QGroupBox` 通过 `setStyleSheet(self._group_box_style())` 设置了自定义样式，覆盖了全局 `QGroupBox` 样式
- `QScrollArea` 已透明，但 `scroll_content` 未显式透明，可能透出默认灰色背景

### 2.3 调试工具标签页（DebugToolsTab）

- 文件：`gui/components/debug/debug_tools_tab.py`
- 同样使用 `QGroupBox` 分组，并通过 `setStyleSheet(self._group_box_style())` 覆盖全局样式
- 新增工具区块（网络诊断、缓存管理、日志管理、快捷操作）已用 `QGroupBox` 包装
- `QScrollArea` 已透明，但 `scroll_content` 未显式透明

### 2.4 实验室标签页（LabTab）

- 文件：`gui/components/debug/lab_tab.py`
- 当前仅有一个居中的占位 `QLabel`，无卡片容器

### 2.5 日志标签页（LogTab）

- 文件：`gui/components/debug/log_tab.py`
- `QTextEdit` 背景为 `#1E1E1E`，`border: none`，无圆角

### 2.6 控制台标签页（ConsoleTab）

- 文件：`gui/components/debug/console_tab.py`
- `QTextEdit` 背景为 `#0C0C0C`，`border: none`，无圆角
- `QLineEdit` 已有 `border-radius: 4px`

## 3. 拟议改动

### 3.1 统一调试面板全局 QGroupBox 卡片样式

**文件**：`gui/debug_panel.py`

- 在 `_get_panel_style()` 中为 `#debugPanel QGroupBox::title` 增加动态主题色样式
- 保持 `#debugPanel QGroupBox` 的白色背景、圆角、边框样式
- 示例：
  ```python
  #debugPanel QGroupBox {{
      background-color: #FFFFFF;
      border: 1px solid #E0E8F0;
      border-radius: 8px;
      margin-top: 10px;
      padding-top: 10px;
  }}
  #debugPanel QGroupBox::title {{
      color: {self._accent_color};
      font-weight: bold;
      subcontrol-origin: margin;
      padding: 0 5px;
  }}
  ```

### 3.2 信息标签页卡片化

**文件**：`gui/components/debug/info_tab.py`

- 删除 `_group_box_style()` 方法，或将其简化为不再覆盖背景/边框/圆角
- 让 `QGroupBox` 完全继承 `gui/debug_panel.py` 中的全局卡片样式
- 设置 `scroll_content.setStyleSheet("background: transparent;")`，透出父窗口 `#E8F4FD`
- 调整 `scroll_layout` 的 `ContentsMargins` 为 `15` 左右，与设置页卡片间距一致

### 3.3 调试工具标签页卡片化

**文件**：`gui/components/debug/debug_tools_tab.py`

- 删除 `_group_box_style()` 方法中的背景/边框/圆角定义，保留标题相关样式或完全移除
- 让 `QGroupBox` 继承全局卡片样式
- 设置 `scroll_content.setStyleSheet("background: transparent;")`
- 调整 `scroll_layout` 的 `ContentsMargins` 为 `15` 左右
- 内部已有白色背景的 `QListWidget`、`QLineEdit` 等控件保持不变

### 3.4 实验室标签页卡片化

**文件**：`gui/components/debug/lab_tab.py`

- 使用 `QGroupBox("实验室")` 作为卡片容器
- 将占位 `QLabel("实验性功能开发中...")` 放入 `QGroupBox` 中
- 设置 `QGroupBox` 继承全局卡片样式（不设置额外样式表）
- 设置 LabTab 自身背景透明，使父窗口 `#E8F4FD` 透出

### 3.5 日志标签页增加圆角

**文件**：`gui/components/debug/log_tab.py`

- 修改 `log_text`（`QTextEdit`）的样式表：
  ```python
  QTextEdit {
      background: #1E1E1E;
      color: #D4D4D4;
      border: 1px solid #3D3D3D;
      border-radius: 8px;
      padding: 8px;
  }
  ```
- 保持深色背景与文字颜色不变

### 3.6 控制台标签页增加圆角

**文件**：`gui/components/debug/console_tab.py`

- 修改 `console_output`（`QTextEdit`）的样式表，增加 `border-radius: 8px` 与边框
- 将 `console_input`（`QLineEdit`）的 `border-radius` 从 `4px` 调整为 `8px`
- 保持深色背景与文字颜色不变

## 4. 假设与决策

- **主题色传递**：通过 `gui/debug_panel.py` 中已加载的 `self._accent_color` 在全局样式表中设置 `QGroupBox::title` 颜色，子组件无需再接收主题色参数。
- **卡片容器**：统一使用 `QGroupBox` 作为卡片容器，与当前 InfoTab / DebugToolsTab 结构保持一致，避免引入新的 `QFrame` 增加复杂度。
- **日志/控制台背景**：根据用户确认，日志和控制台保持现有深色终端风格，仅增加圆角边框。
- **滚动区域背景**：将 `scroll_content` 设为透明，使调试面板父窗口的 `#E8F4FD` 作为内容区背景，与设置页一致。

## 5. 验证步骤

1. 运行 `python -m py_compile gui/debug_panel.py gui/components/debug/info_tab.py gui/components/debug/debug_tools_tab.py gui/components/debug/lab_tab.py gui/components/debug/log_tab.py gui/components/debug/console_tab.py` 检查语法。
2. 启动调试面板（F12），切换到各标签页，确认：
   - 信息、调试工具、实验室页面为白色圆角卡片，标题颜色为主题色
   - 日志、控制台页面的深色文本区域有圆角边框
   - 页面整体背景为 `#E8F4FD`，无灰色/白色杂边
3. 切换主题色后重新打开调试面板，确认卡片标题颜色跟随主题色变化。
