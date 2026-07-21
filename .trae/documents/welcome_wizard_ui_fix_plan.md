# 欢迎界面修复与优化计划

## 摘要

本计划针对 Smart edu downloader 新手引导欢迎界面的 22 项 UI/UX 问题进行系统性修复与优化。核心工作集中在 `gui/welcome/` 目录，少量涉及 `main.py` 与全局样式配置。修复原则：保持 PyQt5 兼容、复用现有主题系统、遵循项目「一功能一文件」与 PEP 8/PEP 257 规范、不破坏既有功能。

---

## 当前状态分析

### 已完成的底层修复（本次计划的基础）

- `wizard.py` 的 `finish()` 已正确保存 `ask_download_dir`、加密 Access Token、调用 `create_shortcuts()`。
- 语言包 `welcome_onboarding.common` 与 `welcome_onboarding.more_page.tutorial_button` 已补齐。
- `InterfaceSettingTab` 的 `_create_slider` 缺失问题已修复。

### 仍然存在的界面问题

| 区域 | 问题 |
|------|------|
| `welcome_page.py` | 程序名未置于图标正下方、颜色非主题色；`_LanguageSelectorDialog` 使用 `QFrame` 但未导入；无边框弹窗存在黑底风险 |
| `license_page.py` | 标题/内容整体未垂直居中；复选框焦点虚线环；隐私政策链接点击区域仅限文本；反诈弹窗位置未固定右下角 |
| `basic_settings_page.py` | 下载图标未随主题色变化；询问开关行包含图标和描述；开关开启时未禁用下载目录输入框 |
| `token_page.py` | 未输入 Token 时下一步仍可点击；缺少明确提示 |
| `theme_page.py` | 主题选择器放在 `QScrollArea` 内，预设过多时会出现滚动条 |
| `system_page.py` | 选项图标带圆形背景 |
| `finish_page.py` | 庆祝图片显示不全；说明文本宽度不足；删除线文本后缺少换行 |
| `material_checkbox.py` | 未选中状态出现虚线焦点环；点击文本不会切换选中状态 |
| `CircleNavButton` / `QPushButton` | 欢迎向导内部按钮未统一使用 MD3 水波纹效果 |
| 全局滚动条 | 样式为原生样式，未统一为现代样式 |
| `setting_group.py` / `base_tab.py` | 设置卡片使用 `#E0E8F0` 描边 |
| `main.py` | 首次启动时在 `delayed_init()` 中弹出赞助弹窗；需求要求改为向导内独立页面 |

---

## 修复方案

### 1. 欢迎首页文字与布局（需求 1）

**文件**：`gui/welcome/pages/welcome_page.py`

**修改**：
- 在 `_create_content()` 中，将程序图标 `logo_label` 与程序名 `name_label` 放入同一个垂直布局，程序名置于图标正下方。
- `name_label` 文本颜色使用主题色 `self._accent_color`。
- 版本号、数据迁移、语言设置链接保持底部水平布局。

**参考代码位置**：`welcome_page.py:150-200` 附近。

---

### 2. NameError：未导入 QFrame（需求 2）

**文件**：`gui/welcome/pages/welcome_page.py`

**修改**：
- 在顶部 `PyQt5.QtWidgets` 导入列表中补充 `QFrame`。
- 同步检查 `welcome_page.py` 其他未导入类型、`tutorial_page.py`、`finish_page.py` 等是否存在类似问题。

---

### 3. 许可条款弹窗位置与样式（需求 3）

**文件**：`gui/welcome/pages/anti_fraud_dialog.py`

**修改**：
- 弹窗固定显示在父窗口右下角：在 `showEvent` 或创建后通过 `move(parent.mapToGlobal(QPoint(parent.width()-self.width()-margin, parent.height()-self.height()-margin)))` 定位。
- 严格参照图 1 效果：黄色背景 `#FFF4CE`、圆角卡片、左侧警示圆点图标、正文段落、右上角关闭按钮。
- 已有实现基本符合，重点调整位置计算与卡片内边距。

---

### 4. 复选框未选中状态虚线描边（需求 4）

**文件**：`gui/components/material_checkbox.py`

**修改**：
- 在 `_draw_box()` 中移除或默认禁用焦点指示器虚线环绘制逻辑（行 388-398）。
- 保留键盘可访问性：可改为仅在键盘聚焦时显示极淡实心描边，或完全移除。
- 同步移除 `CircleNavButton` 等组件的焦点环。

---

### 5. 标题与内容垂直居中（需求 5）

**文件**：`gui/welcome/pages/base_page.py`、各子页面

**修改**：
- 仅针对欢迎向导 9 页。
- 改造 `BaseWelcomePage`：标题、副标题、内容区、导航按钮作为一个整体在窗口内垂直居中。
- 废弃或调整 `add_centered_content()` 的「上下各 addStretch(1)」策略，避免内容与标题之间出现过大空隙。
- 子页面改为顶部添加 spacer、内容紧凑排列、底部 spacer，实现整体居中。

---

### 6. 下一步按钮位于文本下方（需求 6）

**文件**：`gui/welcome/pages/base_page.py`、各子页面

**修改**：
- 将 `nav_layout` 从页面最底部提升到内容卡片正下方。
- 确保按钮与上方文本/卡片的间距固定，不随窗口高度变化被拉伸到底部。

---

### 7. 移除文本与控件描边（需求 7、16）

**文件**：欢迎向导各页面、自定义组件

**修改**：
- 移除所有 `QLabel` 样式表中不必要的 `border` 属性。
- `MaterialCheckBox` 移除焦点虚线环。
- `CircleNavButton` 确认无描边。
- `base_tab.py`、各页面的 `QLineEdit` focus 边框保留（属于交互状态），其他装饰性描边去除。

---

### 8. 下载图标随主题色变化（需求 8）

**文件**：`gui/welcome/pages/basic_settings_page.py`

**修改**：
- 读取 `resources/images/welcome/download.svg`，使用 `QSvgRenderer` 或复用 `CircleNavButton._replace_svg_fill()` 逻辑，将 SVG 颜色替换为主题色后渲染为 `QPixmap`。
- 封装一个私有方法 `_load_themable_svg(icon_path, size, color)`，避免重复代码。

---

### 9. 下载位置设置界面简化（需求 9）

**文件**：`gui/welcome/pages/basic_settings_page.py`

**修改**：
- 删除「每次下载前询问下载位置」行的问号图标与描述文本，仅保留标题和开关。
- 当 `ask_switch` 开启时，禁用 `dir_input` 与 `browse_btn`；关闭时恢复启用。
- 连接 `ask_switch` 的 `toggled` 信号到 `_on_ask_changed()`。

---

### 10/11. 按钮 MD3 水波纹效果（需求 10、11）

**文件**：`gui/welcome/pages/` 下各页面

**修改**：
- 范围限定在欢迎向导内部按钮。
- 将页面内的 `QPushButton`（浏览、打开云平台、复制代码等）替换为 `MaterialButton`，设置对应 variant 与主题色。
- `CircleNavButton` 已自定义绘制，补充水波纹效果：在点击位置启动 `RippleEffect`，在 `paintEvent` 中绘制。
- 统一按钮高度、圆角、悬浮阴影，确保视觉一致。

---

### 12. Access Token 输入验证（需求 12）

**文件**：`gui/welcome/pages/token_page.py`

**修改**：
- 初始化时 `next_btn.setEnabled(False)`。
- 连接 `token_input.textChanged` 到 `_on_token_changed()`：
  - 空文本时禁用下一步，显示提示信息（如输入框下方红色小字或在输入框 placeholder 中提示）。
  - 有文本时启用下一步。
- 添加 `QLabel token_tip_label` 用于显示提示。

---

### 13. 现代滚动条样式（需求 13）

**文件**：全局样式入口（如 `gui/styles.py` 或 `MainWindow._apply_styles()`）

**修改**：
- 在全局样式表中注入 `QScrollBar` 现代样式：宽/高 8px、圆角 4px、滑块 `#C0C8D0`、悬停 `#A0A8B0`、隐藏箭头、轨道透明。
- 更新项目记忆：滚动条样式已纳入统一主题管理。

---

### 14. 主题选择界面无滚动条（需求 14）

**文件**：`gui/welcome/pages/theme_page.py`、`gui/components/theme_selector.py`

**修改**：
- 移除 `ThemePage` 中对 `QScrollArea` 的使用，直接将 `theme_selector` 添加到内容布局。
- 调整 `ThemeSelector` 预设网格为固定行数或缩放卡片尺寸，确保在 860×600 窗口内一次性显示所有主题选项而不出现滚动条。
- 保留 `ThemeSelector` 在设置页中的滚动区能力（通过参数控制）。

---

### 15. 删除图标圆形背景（需求 15）

**文件**：`gui/welcome/pages/system_page.py`

**修改**：
- 移除 `_create_option_row()` 中 `icon_label` 的 `background` 与 `border-radius` 样式，使图标直接显示在白色卡片背景上。
- 同步检查 `basic_settings_page.py` 中是否存在类似圆形背景。

---

### 17. 完成界面图片显示不全（需求 17）

**文件**：`gui/welcome/pages/finish_page.py`

**修改**：
- 调整 `IMAGE_SIZE` 或根据内容区可用高度动态计算图片尺寸。
- 使用 `Qt.KeepAspectRatio` 缩放并确保完整显示，不被标题/文本/按钮挤压。
- 可适当增大内容区与图片间距。

---

### 18. 设置区域描边去除（需求 18）

**文件**：`gui/pages/settings/components/setting_group.py`、`gui/pages/settings/base_tab.py`

**修改**：
- 将 `SettingGroup.DEFAULT_STYLE` 中 `border: 1px solid #E0E8F0;` 移除或改为透明。
- 检查 `base_tab.py` 中输入框默认边框是否需要保留；保留 focus 主题色边框，去除装饰性浅灰描边。

---

### 19. 赞助弹窗改为向导内页面（需求 19）

**文件**：`gui/welcome/wizard.py`、`main.py`、新增 `gui/welcome/pages/donation_page.py`

**修改**：
- 新增 `DonationPage(BaseWelcomePage)`：复用现有 `DonationDialog` 中的图片与文案，作为独立页面。
- 在 `wizard.py` 中：
  - 增加 `PAGE_DONATION` 常量，页面顺序调整为完成页之后。
  - 首次启动时：完成页的对钩按钮直接结束向导（不进入赞助页）。
  - 非