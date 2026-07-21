# 欢迎界面修复与优化实施计划

## 1. Summary

本次计划针对 `gui/welcome/` 新手引导欢迎界面及关联组件进行 22 项修复与优化，覆盖布局、样式、交互、错误修复、主题一致性、Material Design 3 按钮统一、赞助页面重构等方面。所有改动限定在欢迎向导内部，主应用其它界面仅做必要的最小兼容（如设置区域描边）。

## 2. Current State Analysis

### 2.1 已确认的现状

* `welcome_page.py` 第 64 行使用了 `QFrame` 但导入列表中缺少 `QFrame`，存在 `NameError`。

* 欢迎页 "Smart edu downloader" 名称位于底部版本行附近，未放在图标正下方，也未使用主题色。

* `base_page.py` 的 `add_centered_content` 采用「控件上下各加 stretch」的居中方式，导致部分页面内容偏中、底部导航按钮紧贴窗口底部，而不是紧跟在文本下方。

* `MaterialCheckBox` 在 `_draw_box` 中为焦点状态绘制了虚线圆角矩形，造成未选中时出现虚线描边。

* `CircleNavButton` 已具备 SVG 颜色替换能力，但普通 `QPushButton`（浏览、打开云平台、复制代码、关闭等）未统一使用 Material Design 3 按钮，也无水波纹。

* `AntiFraudDialog` 当前居中显示，需改为右下角固定位置，并严格按图 1 的黄色警告弹窗样式实现。

* `BasicSettingsPage` 中 `download.svg` 使用 `QPixmap` 原始加载，未按主题色着色；"询问下载位置" 行与图 2 要求不符（需移除图标和描述，开关开启时禁用下载位置输入）。

* `ThemePage` 使用 `QScrollArea` 包裹主题选择器，主题较多时会出现滚动条，与需求 14 冲突。

* `SystemPage` 的快捷方式选项图标带有圆形背景（`background: {accent}15; border-radius: 20px`），需按图 3 去除。

* `FinishPage` 中庆祝图片 `celebration.png` 尺寸固定为 180×180 且可能显示不全，说明文本最大宽度 720 与当前窗口比例不匹配，"轰！嚓-嚓-嚓！推推" 后缺少换行。

* `TokenPage` 的下一步按钮在输入框为空时仍然启用，且没有明确提示引导输入。

* `PrivacyPolicyDialog` 标题为普通 `QLabel`，仅链接文本中的「隐私政策」可点击，需让整个标题文本成为超链接。

* 设置区域 `SettingGroup` 默认边框为 `#E0E8F0`，需要去除。

* 当前赞助弹窗由 `main.py` 的 `check_and_show_tip()` 在启动次数为 1/5/10... 时触发，需要在第一次启动和从「更多」打开新手教程时改为向导内的赞助页面。

* 全局滚动条样式仍为原生，需要统一替换为现代样式并纳入项目记忆。

### 2.2 依赖与约定

* 框架：PyQt5。

* 主题色来源：`core.config.theme_config.primary_color()` / `gui.styles.load_primary_color()`。

* 字体来源：`gui.fonts` 系列（`title_font`、`subtitle_font`、`body_font`、`small_font`）。

* 自定义按钮：`gui/widgets/material_button.py`（`MaterialButton`）已具备 Material Design 3 样式和水波纹。

* 自定义复选框：`gui/components/material_checkbox.py`（`MaterialCheckBox`）。

* 自定义开关：`gui/widgets/switch_button.py`（`SwitchWithLabel`）。

* i18n 源文件：`i18n/zh_CN.json`，修改后需同步到其它语言包。

* 项目记忆：`c:\Users\Administrator\.trae-cn\memory\projects\-e-hello-web-Smart-edu-downloader\project_memory.md` 中已有滚动条、按钮等样式约定，本次需追加滚动条现代样式约定。

## 3. Proposed Changes

### 3.1 错误修复与导入

#### 文件：`gui/welcome/pages/welcome_page.py`

* **What**：在顶部 `PyQt5.QtWidgets` 导入列表中增加 `QFrame`。

* **Why**：`_LanguageSelectorDialog._init_ui` 第 64 行使用了 `QFrame()`，但当前导入未包含，导致 `NameError`。

* **How**：将 `QFrame` 加入 `from PyQt5.QtWidgets import (...)` 元组。

### 3.2 欢迎页布局与主题色

#### 文件：`gui/welcome/pages/welcome_page.py`

* **What**：将 "Smart edu downloader" 应用名称从底部版本行附近移动到程序图标正下方，颜色设为主题色。

* **Why**：需求 1 要求视觉层次清晰，名称位于图标正下方并跟随主题色。

* **How**：

  1. 在 `_create_content` 中图标 `logo_label` 下方新增 `app_name_label`，文本取自 `_("welcome_onboarding.welcome.app_name")`，颜色使用 `self._accent_color`，字体使用 `title_font()` 或 `large_font()`。
  2. 调整 `logo_layout` 间距，使名称紧贴图标下方。
  3. 底部版本行保留，但不再承担展示应用名称的职责。
  4. `set_accent_color` 中同步更新 `app_name_label` 的颜色。

### 3.3 反诈通知弹窗位置与样式

#### 文件：`gui/welcome/pages/anti_fraud_dialog.py`

* **What**：将弹窗固定显示在父窗口右下角，并按图 1 调整内部排版。

* **Why**：需求 3 要求弹窗位置固定右下角，样式严格参照图 1。

* **How**：

  1. 在 `showEvent` 或 `_init_ui` 中计算位置：`parent_rect = parent.rect(); move(parent.mapToGlobal(QPoint(parent_rect.width() - self.width() - margin, parent_rect.height() - self.height() - margin)))`。
  2. 保持黄色背景 `#FFF4CE`、边框 `#F9D99A`、圆角 8px、左侧警示图标、正文、右上角关闭按钮的整体结构。
  3. 调整 `card_layout` 为 `QVBoxLayout` 或保持 `QHBoxLayout` 但增加文本与图标的间距，确保与图 1 一致。
  4. 关闭按钮改为更醒目的 Material 风格文本按钮或保持 "×"，但尺寸和悬停效果需统一。

### 3.4 复选框虚线描边去除

#### 文件：`gui/components/material_checkbox.py`

* **What**：移除未选中及选中状态下复选框内部的虚线焦点环。

* **Why**：需求 4/16 要求彻底去除虚线描边，保持视觉一致性。

* **How**：

  1. 删除/注释 `_draw_box` 中「焦点指示器」段落（第 388-398 行）。
  2. 若需保留键盘焦点可访问性，可改为绘制与边框同色的实线细环或完全移除；按需求直接移除。

### 3.5 标题与内容整体垂直居中

#### 文件：`gui/welcome/pages/base_page.py`

* **What**：使标题、副标题、内容区作为一个整体在窗口中垂直居中，底部导航按钮紧跟内容下方。

* **Why**：需求 5 要求标题、副标题及界面元素整体与窗口居中对齐。

* **How**：

  1. 改造 `_init_ui`：用一个 `QVBoxLayout` 包裹 `title_label`、`subtitle_label`、`content_layout`，并给该包裹布局设置 `setAlignment(Qt.AlignCenter)` 或上下 stretch。
  2. 内容区 `content_layout` 不再使用 `addStretch(1)`，避免内容被推向中间但导航按钮被压到最底部。
  3. 修改 `add_centered_content` 为 `add_content`，不再添加上下 stretch，仅将控件按顶部对齐加入 `content_layout`。
  4. 各子页面 `_create_content` 中调用新的 `add_content`。
  5. 导航按钮 `nav_layout` 放在内容区下方，与内容保持固定间距。

### 3.6 下一步按钮紧跟文本下方

#### 文件：`gui/welcome/pages/base_page.py` 及各子页面

* **What**：让「下一步/完成」等导航按钮位于页面内容文本下方，而不是窗口最底部。

* **Why**：需求 6 要求按钮在界面中文本下面，而不是窗口下面。

* **How**：

  1. 在 `base_page.py` 中调整 `nav_layout` 的位置，使其直接位于 `content_layout` 下方，二者间距固定（如 24px）。
  2. 移除 `nav_layout` 上方的额外 stretch。
  3. 确保所有子页面通过 `set_nav_buttons` 设置按钮后，按钮出现在内容正下方。

### 3.7 移除所有文本与控件描边

#### 文件：`gui/welcome/pages/*.py`、`gui/components/material_checkbox.py`、`gui/components/circle_nav_button.py` 等

* **What**：移除界面中所有文本、输入框、按钮、卡片等控件的多余描边/边框。

* **Why**：需求 7/16 要求界面元素无任何多余边框。

* **How**：

  1. `material_checkbox.py`：移除焦点虚线环（同 3.4）。
  2. `circle_nav_button.py`：确认 `setStyleSheet('background: transparent; border: none;')` 已生效；绘制时不再绘制额外边框。
  3. 各页面卡片 `QFrame` 的 `border: 1px solid #E0E0E0` 若与图 2/图 3 冲突，则移除或仅在需要时保留。
  4. `basic_settings_page.py` / `token_page.py` 的输入框 focus 边框保留主题色边框，但非 focus 状态的 `#E0E8F0` 边框按需求决定是否保留（图 2 显示输入框有边框，但主题色 focus 时加深，因此保留输入框边框但统一颜色）。
  5. 文本标签默认无边框，检查是否有硬编码 `border` 样式并移除。

### 3.8 下载图标主题色动态变化

#### 文件：`gui/welcome/pages/basic_settings_page.py`

* **What**：`resources\images\welcome\download.svg` 颜色跟随主题色。

* **Why**：需求 8 要求文件保存位置图标颜色动态变化。

* **How**：

  1. 复用 `circle_nav_button.py` 中的 `_replace_svg_fill` 逻辑，或调用 `core.ui.icon_manager.IconManager.load_colored_pixmap`。
  2. 推荐新增一个独立工具函数（如 `gui/utils/svg_utils.py` 或页面内私有方法）读取 SVG、替换 fill/stroke 为主题色并返回 `QPixmap`。
  3. 在 `set_accent_color` 中重新渲染图标。

### 3.9 询问下载位置开关行为

#### 文件：`gui/welcome/pages/basic_settings_page.py`

* **What**：询问下载位置区域不显示图标和描述文本；开关开启时禁用下载位置输入框。

* **Why**：需求 9 要求界面与图 2 一致。

* **How**：

  1. 移除「每次下载前询问下载位置」行的 `switch_icon`（问号圆形图标）和 `switch_desc` 描述标签，仅保留标题和开关。
  2. 连接开关 `stateChanged`/`toggled` 信号到 `_on_ask_switch_changed`。
  3. 当开关开启时，设置 `dir_input.setEnabled(False)` 并降低透明度/置灰；关闭时恢复启用。
  4. 同步更新 `browse_btn` 的启用状态。

### 3.10/3.11 Material Design 3 按钮统一

#### 文件：`gui/welcome/pages/basic_settings_page.py`、`token_page.py`、`privacy_policy_dialog.py`、`welcome_page.py`、`anti_fraud_dialog.py` 等

* **What**：将向导内所有 `QPushButton` 替换为 `MaterialButton`（填充/描边/文字变体），并统一主题色与水波纹。

* **Why**：需求 10/11 要求下一步按钮及所有按钮具备 Material Design 3 样式和水波纹。

* **How**：

  1. `basic_settings_page.py` 的 `browse_btn` 使用 `MaterialButton`，`VARIANT_FILLED`，主题色背景。
  2. `token_page.py` 的 `open_cloud_btn` 使用 `VARIANT_FILLED`，`copy_code_btn` 使用 `VARIANT_OUTLINED`。
  3. `privacy_policy_dialog.py` 的关闭按钮使用 `MaterialButton` `VARIANT_TEXT` 或 `VARIANT_FILLED`。
  4. `welcome_page.py` 的数据迁移、语言设置链接按钮若视觉上为文字链接可保持 `QPushButton` 但样式需清理；或改用 `MaterialButton` `VARIANT_TEXT`。
  5. `CircleNavButton`（上一步/下一步/完成对钩）本身已自绘圆形，需补充水波纹效果：在 `circle_nav_button.py` 中集成 `RippleEffect`，点击时从点击位置触发水波纹。
  6. 所有 `MaterialButton` 通过 `setAccentColor(self._accent_color)` 同步主题色。

### 3.12 Access Token 输入验证

#### 文件：`gui/welcome/pages/token_page.py`

* **What**：输入框为空时禁用下一步按钮，并显示提示信息。

* **Why**：需求 12 要求未输入时禁用下一步并明确提示。

* **How**：

  1. 在 `_create_content` 中创建 `tip_label`，初始文本为 `_("welcome_onboarding.access_token.empty_tip")`（需新增 i18n 键），颜色为红色或主题色提示。
  2. 连接 `token_input.textChanged` 到 `_on_token_changed`。
  3. `_on_token_changed` 中检查文本是否为空，更新 `next_btn.setEnabled(bool(text.strip()))` 和 `tip_label` 文本/可见性。
  4. 若已有初始值（非首次运行），初始化时同步一次状态。

### 3.13 滚动条现代样式

#### 文件：全局样式入口（如 `gui/styles.py` 或 `main.py` 中 QApplication 设置）

* **What**：将应用所有滚动条替换为现代样式（8px 圆角、灰色滑块、悬停变深、无箭头）。

* **Why**：需求 13 要求现代滚动条并纳入项目记忆。

* **How**：

  1. 在全局样式字符串中追加 `QScrollBar::vertical`/`QScrollBar::horizontal` 样式，宽度 8px、圆角 4px、背景透明、滑块 `#C0C8D0`、悬停 `#A0A8B0`、无上下箭头。
  2. 通过 `QApplication.instance().setStyleSheet(...)` 或统一入口注入。
  3. 更新 `project_memory.md` 滚动条相关约定。

### 3.14 主题选择界面无滚动条

#### 文件：`gui/welcome/pages/theme_page.py`、`gui/components/theme_selector.py`

* **What**：颜色选择界面一次性完整显示所有主题选项，不允许出现滚动条。

* **Why**：需求 14 要求所有主题可见。

* **How**：

  1. 移除 `ThemePage` 中的 `QScrollArea`，直接将 `theme_selector` 添加到 `content_layout`。
  2. 在 `ThemeSelector` 中调整预设网格列数或卡片尺寸，使整体高度在 600px 窗口内完整显示。
  3. 若自定义主题区域过高，可折叠或调整布局；优先保证预设主题完整可见。
  4. 禁用 `theme_selector` 自身的滚动条（如有）。

### 3.15 去除图标圆形背景

#### 文件：`gui/welcome/pages/system_page.py`

* **What**：删除快捷方式选项图标外的圆形背景。

* **Why**：需求 15 要求按图 3 去除圆形背景。

* **How**：

  1. 在 `_create_option_row` 中移除 `icon_label.setStyleSheet(...)` 的 `background` 和 `border-radius`。
  2. 保持图标本身按主题色着色（SVG 替换 fill），图标尺寸保持 24×24。

### 3.16 描边问题统一修复

同 3.7，额外关注：

* `QLineEdit` 非 focus 状态边框统一为 `#E0E8F0` 或按图 2 保留。

* 卡片边框按需移除。

* `MaterialCheckBox` 无边框阴影外的虚线。

### 3.17 完成页图片完整展示

#### 文件：`gui/welcome/pages/finish_page.py`

* **What**：修复 `celebration.png` 显示不全问题。

* **Why**：需求 17 要求图片完整展示。

* **How**：

  1. 将图片加载从 `QPixmap.scaled(IMAGE_SIZE, IMAGE_SIZE, ...)` 改为按图片原始比例缩放，最大宽度/高度不超过可用区域。
  2. `image_label.setScaledContents(False)` 保持比例，避免拉伸截断。
  3. 在 `resizeEvent` 中根据当前尺寸重新缩放，确保窗口大小变化时图片仍然完整。

### 3.18 设置区域描边去除

#### 文件：`gui/pages/settings/components/setting_group.py`

* **What**：去除 `SettingGroup` 的 `#E0E8F0` 边框。

* **Why**：需求 18 要求去除设置区域描边。

* **How**：

  1. 将 `DEFAULT_STYLE` 中 `border: 1px solid #E0E8F0;` 移除，或改为 `border: none;`。
  2. 若需要视觉分隔，可改用阴影或背景色差异，不使用描边。

### 3.19 赞助弹窗改为赞助页面

#### 新增文件：`gui/welcome/pages/sponsor_page.py`

#### 修改文件：`gui/welcome/wizard.py`、`main.py`、`gui/pages/more_page.py`（或打开新手教程的入口）

* **What**：将第一次启动和「更多」新手教程中的赞助弹窗改为向导内的独立赞助页面，作为最后一页。

* **Why**：需求 19 要求赞助是页面不是弹窗，且位于欢迎向导最后一页。

* **How**：

  1. 新增 `SponsorPage(BaseWelcomePage)`：

     * 标题/副标题（如 "支持作者"）。

     * 展示赞赏码图片（复用 `gui/widgets/donation_dialog.py` 中的图片加载逻辑）。

     * 提供「进入主界面」按钮（`MaterialButton` 或 `CircleNavButton`）。
  2. 在 `wizard.py` 中：

     * 增加 `PAGE_SPONSOR` 常量。

     * `_pages` 列表顺序调整为 `[..., PAGE_FINISH, PAGE_SPONSOR]`。

     * `finish()` 逻辑由「完成页对钩直接 accept」改为「赞助页进入主界面按钮 accept」。

     * 完成页的 `finish_btn`（对钩）改为 `next_btn`，点击进入赞助页；赞助页提供最终完成按钮。

     * 当从「更多」打开新手教程时，无论是否首次启动，都显示赞助页作为最后一页。
  3. 在 `main.py` 中：

     * 首次启动时不再调用 `check_and_show_tip()` 的弹窗逻辑。

     * 非首次启动且启动次数为 5/10... 时仍显示赞助弹窗（保持现有逻辑）。
  4. 在打开新手教程的入口（如 `more_page.py`）中，启动向导时标记为非首次运行模式，但仍走到赞助页。

### 3.20 多选框点击文本联动

#### 文件：`gui/components/material_checkbox.py`、`gui/welcome/pages/license_page.py`、`system_page.py`

* **What**：点击复选框旁边的文本也能切换复选框状态。

* **Why**：需求 20 要求点击文本与点击复选框效果相同。

* **How**：

  1. 对于 `license_page.py` 的隐私政策同意行：将 `agree_label` 的 `mousePressEvent` 连接到 `agree_checkbox.setChecked(not agree_checkbox.isChecked())`。
  2. 对于 `system_page.py` 的快捷方式选项行：将标题和描述标签的 `mousePressEvent` 连接到对应 `MaterialCheckBox` 的切换。
  3. 可选增强：在 `MaterialCheckBox` 中支持 `setText` 并在组件内部绘制文本，使文本点击天然属于组件；但当前 `license_page.py` 和 `system_page.py` 都是外部 `QLabel + MaterialCheckBox` 组合，优先在外部处理。

### 3.21 隐私政策标题整体超链接

#### 文件：`gui/welcome/pages/privacy_policy_dialog.py`

* **What**：将隐私政策对话框中的整个标题 "Smart edu downloader 隐私政策" 转换为可点击超链接。

* **Why**：需求 21 要求整个标题文本可点击。

* **How**：

  1. 将标题 `QLabel` 改为 `QTextBrowser` 或保持 `QLabel` 但设置 `setTextFormat(Qt.RichText)`、`setOpenExternalLinks(True)`。
  2. 文本设置为富文本：`<a href="https://.../privacy_policy.html" style="color: #212121; text-decoration: none;">Smart edu downloader 隐私政策</a>`（链接地址使用项目 docs 或占位链接）。
  3. 标题保持可点击但不破坏原有样式。

### 3.22 完成页文本宽度与换行

#### 文件：`gui/welcome/pages/finish_page.py`、`i18n/zh_CN.json`

* **What**：增加完成页说明文本可显示区域宽度，并在 "轰！嚓-嚓-嚓！推推" 后添加换行。

* **Why**：需求 22 要求文本显示完整且格式正确。

* **How**：

  1. `desc_label.setMaximumWidth` 从 720 调整为合适值（如 520-560，或根据窗口宽度动态计算）。
  2. 在 `_build_description_text` 中，在删除线文本后插入 `<br>` 或 `<br/>`，使其与后续描述文本分行显示。
  3. 同步检查并更新 i18n 中 `welcome_onboarding.completion.strikethrough_text` 或直接在代码中拼接换行。

## 4. Assumptions & Decisions

1. **范围限定**：按钮样式与居中仅作用于欢迎向导 9 个页面（含新增赞助页），主应用其它界面不做大规模重构。
2. **赞助页面来源**：复用现有 `gui/widgets/donation_dialog.py` 中的赞赏码图片路径与展示逻辑，保持图片尺寸和排版风格。
3. **滚动条样式**：全局注入 `QScrollBar` 样式，影响主应用所有滚动条，这是需求 13 明确要求的。
4. **主题色同步**：所有新引入的 `MaterialButton`、`CircleNavButton`、SVG 图标都在 `set_accent_color` 中同步刷新。
5. **按钮水波纹**：

   * `MaterialButton` 已内置水波纹，直接使用。

   * `CircleNavButton` 需新增水波纹绘制，使用项目现有 `gui/widgets/ripple_effect.py` 或自绘 Ripple。
6. **i18n 新增键**：

   * `welcome_onboarding.access_token.empty_tip`

   * `welcome_onboarding.sponsor.title`

   * `welcome_onboarding.sponsor.subtitle`

   * `welcome_onboarding.sponsor.finish_tip`

   * 其他现有文案如有调整同步更新。
7. **反诈弹窗**：保持居中模糊背景改为仅右下角固定；关闭按钮样式与向导按钮统一。
8. **输入框边框**：按图 2 保留输入框边框，但非 focus 颜色统一，不视为需求 7/16 中的「多余描边」。

## 5. Verification Steps

1. **语法检查**：`python -m py_compile main.py gui/welcome/wizard.py gui/welcome/pages/*.py gui/components/material_checkbox.py gui/components/circle_nav_button.py gui/widgets/material_button.py gui/pages/settings/components/setting_group.py`。
2. **导入检查**：运行 `.dev/test/test_imports.py`。
3. **i18n 验证**：运行 `.dev/test/verify_i18n.py`，确保新增键已同步到所有语言包。
4. **静态扫描**：运行 `.dev/test/scan_bugs.py`，人工甄别合理的中文硬编码和 fallback。
5. **启动验证**：

   * 删除/修改 `runtime/settings/settings.json` 的 `first_run` 为触发欢迎向导，启动 `python main.py`。

   * 检查欢迎页名称在图标下方且为主题色。

   * 检查许可页反诈弹窗位于右下角且样式正确。

   * 检查复选框无虚线描边。

   * 检查各页面内容整体居中，下一步按钮在内容下方。

   * 检查基本设置页图标为主题色，询问开关开启时下载位置禁用。

   * 检查 Access Token 页空输入时下一步禁用并提示。

   * 检查主题页无滚动条且所有主题可见。

   * 检查系统页图标无圆形背景。

   * 检查完成页图片完整、文本换行正确。

   * 检查赞助页作为最后一页出现。
6. **交互验证**：

   * 点击隐私政策文本可打开对话框。

   * 点击复选框旁文本可切换复选框。

   * 按钮点击有水波纹。

   * 切换语言后所有文本刷新。

