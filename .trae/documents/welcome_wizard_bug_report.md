# 新手引导（Welcome Wizard）Bug 检测报告

> 检测范围：`gui/welcome/` 目录下所有页面、`gui/components/circle_nav_button.py`、
> `gui/components/material_checkbox.py`、`gui/components/theme_selector.py`、
> `main.py` 启动流程、相关 i18n 键与崩溃日志。
> 检测日期：2026-07-11

---

## 1. 检测结论摘要

新手引导目前已可正常启动（历史启动崩溃已修复），但在**设置持久化、主题实时同步、布局居中、文案与功能完整性**等方面仍存在一批问题。其中 **设置键名错误导致"下载前询问位置"失效**、**Access Token 明文保存导致后续无法加载**、**系统快捷方式设置只保存不执行** 属于高优先级功能缺陷，需要优先修复。

---

## 2. 历史崩溃问题（已修复，需回归验证）

| 崩溃现象 | 文件/位置 | 根因 | 当前状态 |
|---------|----------|------|---------|
| `UnboundLocalError: cannot access local variable '_'` | `welcome_page.py:211` | `QFileDialog.getOpenFileName` 返回值用 `_` 接收，覆盖了 `core.i18n._` 翻译函数 | 已改为 `_selected_filter`，崩溃修复 |
| `AttributeError: 'super' object has no attribute 'title_label'` | `license_page.py:47` | 在基类尚未初始化 `title_label` 前调用 `super().title_label.font()` | 已删除该调用，崩溃修复 |
| `AttributeError: 'NoneType' object has no attribute 'get'` | `theme_selector.py:392` | `_theme_config.get("custom", {}).get("base", ...)` 中 `custom` 为 `None` | 已改为 `(self._theme_config.get("custom") or {}).get("base", ...)`，崩溃修复 |

**验证建议**：启动程序（临时将 `first_run` 设为 `false`）确认不再出现上述崩溃。

---

## 3. 严重功能性 Bug

### 3.1 `ask_before_download` 设置键名错误，开关不生效

- **位置**：`gui/welcome/wizard.py:124`、`gui/welcome/pages/basic_settings_page.py`
- **问题**：向导保存的键名为 `ask_before_download`。
- **实际程序使用的键名**：`ask_download_dir`（见 `core/infrastructure/default_settings.py:84`、`core/download/downloader.py:242`、`gui/pages/settings/tabs/download_tab.py`）。
- **影响**：用户在基本设置页切换的"每次下载前询问下载位置"开关不会生效，下载时仍按 `ask_download_dir` 的旧值处理。
- **修复建议**：将向导保存键统一改为 `ask_download_dir`，或全项目统一为 `ask_before_download`（推荐与现有设置页保持一致，使用 `ask_download_dir`）。

### 3.2 Access Token 以明文保存，主程序加载逻辑期望密文

- **位置**：`gui/welcome/wizard.py:127`
- **问题**：`settings["access_token"] = token_page.get_access_token()` 直接写入用户输入的明文。
- **主程序加载逻辑**：`main.py:load_access_token()` 对非空 token 调用 `decrypt_token()` 解密。
- **影响**：首次启动时用户在向导填写的 Access Token 保存为明文，下次启动 `decrypt_token` 大概率失败，导致 token 被当作空值处理，需要重新设置。
- **修复建议**：保存前调用 `core.network.token_crypto.encrypt_token()` 加密。

### 3.3 系统快捷方式设置只保存设置，不执行创建

- **位置**：`gui/welcome/pages/system_page.py`、`gui/welcome/wizard.py:132-133`
- **问题**：`SystemPage` 仅返回 `create_desktop_shortcut` 与 `create_start_menu_shortcut` 两个布尔值，`wizard.finish()` 直接 `settings.update(...)` 存入配置文件。
- **缺失**：项目中没有任何地方消费这两个键（搜索整个项目无相关调用）。
- **默认值**：`default_settings.py` 中也没有这两个键的默认值。
- **影响**：用户勾选"创建桌面快捷方式"后，实际不会创建任何快捷方式，造成功能欺诈。
- **修复建议**：在 `wizard.finish()` 或独立模块中，根据这两个 bool 调用 Windows Shell/Win32 API 实际创建快捷方式；并在 `default_settings.py` 中补充默认值 `False`。

### 3.4 语言切换后向导界面不会实时刷新

- **位置**：`gui/welcome/pages/welcome_page.py:275-279`、`gui/welcome/wizard.py`
- **问题**：`_LanguageSelectorDialog` 确认后调用 `set_language(code)` 并发射 `language_changed` 信号，但 `WelcomeWizard` 未连接该信号，也没有调用任何页面刷新文本的方法。
- **影响**：用户在欢迎页切换语言后，当前打开的向导仍显示旧语言文本，必须关闭并重新打开才能生效。
- **修复建议**：在 `wizard._connect_buttons()` 中连接 `welcome_page.language_changed` 信号，触发所有页面重新设置 `_()` 文本。

### 3.5 从"更多"页重新打开向导时未加载当前用户设置

- **位置**：`gui/welcome/pages/theme_page.py:63`、`gui/welcome/pages/basic_settings_page.py:114`
- **问题**：
  - `ThemePage` 初始主题固定为 `config_from_preset_key("jingdianlan")`，不从当前设置读取。
  - `BasicSettingsPage` 的下载目录固定使用 `get_default_download_dir()`，不从当前 `download_dir` 设置读取。
- **影响**：非首次运行时点击"更多"→"新手教程"，用户看到的是默认配置而非自己当前的配置，修改后容易误覆盖。
- **修复建议**：初始化时从 `get_settings_manager().get_all()` 读取当前 `theme_color` 与 `download_dir` 作为默认值。

### 3.6 导入配置后向导状态未刷新

- **位置**：`gui/welcome/pages/welcome_page.py:247-274`
- **问题**：数据迁移导入配置后，仅调用 `settings_manager.update(settings)`，向导已创建的页面（主题色、下载目录等）仍保持旧状态。
- **影响**：导入配置后用户继续操作向导，看到的主题色、目录等仍是导入前的值，视觉上与实际设置不一致。
- **修复建议**：导入成功后调用 `wizard._apply_theme_colors()` 并刷新各页面默认值，或提示用户重启向导。

---

## 4. 视觉与布局 Bug

### 4.1 多个页面内容未垂直居中

- **位置**：`basic_settings_page.py:175`、`token_page.py:154`、`system_page.py:85`、`tutorial_page.py:80/88`、`finish_page.py:75/82`
- **问题**：这些页面使用 `content_layout.insertWidget(1, ...)` 将卡片/图片插入到内容区，但 `BaseWelcomePage.content_layout` 初始没有上下 `stretch`，导致内容偏上，视觉上不居中。
- **已正确处理的页面**：`welcome_page.py` 使用了 `add_centered_content()`（内部自动添加 stretch）。
- **修复建议**：上述页面改用 `add_centered_content()`，或手动 `addStretch(1)` / `insertStretch(0, 1)`。

### 4.2 教程页图片只按宽度缩放，可能超出显示区域

- **位置**：`gui/welcome/pages/tutorial_page.py:107-114`
- **问题**：`_scale_image()` 仅使用 `scaledToWidth(self.MAX_IMAGE_WIDTH, ...)`，未限制高度。
- **影响**：若 `Teach/1.png` 或 `Teach/2.png` 是长图，高度会超出内容区，导致图片底部被裁剪或挤压导航按钮。
- **修复建议**：同时约束最大高度，例如：
  ```python
  max_height = max(200, self.content_layout.geometry().height() - 120)
  scaled = self._raw_pixmap.scaled(
      self.MAX_IMAGE_WIDTH, max_height,
      Qt.KeepAspectRatio, Qt.SmoothTransformation
  )
  ```

### 4.3 反诈通知的对齐参数在垂直布局中不生效

- **位置**：`gui/welcome/pages/license_page.py:96`
- **问题**：`self.content_layout.insertWidget(2, self.notice, alignment=Qt.AlignRight | Qt.AlignTop)`。
- **问题分析**：`QVBoxLayout::insertWidget` 的 `alignment` 参数在垂直布局中对单个 widget 的水平对齐有效，但 `Qt.AlignTop` 在此上下文中无效，且由于内容区缺少 stretch，通知不会"沉底"。
- **影响**：反诈通知位置可能与设计预期不符。
- **修复建议**：将通知放入独立的右下角容器，或改用 `QHBoxLayout` + `addStretch()` 控制水平位置。

### 4.4 基本设置页与系统设置页的图标占位符为空

- **位置**：
  - `basic_settings_page.py:152-154`：`switch_icon = QLabel()` 只设置了 `fixedSize`，无图标、无背景。
  - `system_page.py:122-130`：`icon_label` 只设置了圆形背景色，无图标。
- **影响**：列表左侧出现 32×32 或 40×40 的空白区域，视觉不完整。
- **修复建议**：补充对应 SVG 图标（如 `download.svg` 复用、系统页新增 `desktop.svg` / `start-menu.svg`），或移除空白占位并调整布局。

### 4.5 完成页文案包含错误应用名"ClassIsland"

- **位置**：`i18n/zh_CN.json:1073`
- **问题**：`"description": "...感谢您选用 ClassIsland。点击对号以结束设置向导。"`
- **影响**：文案与当前应用 `Smart edu downloader` 不符，显得草率。
- **修复建议**：改为"感谢您选用 Smart edu downloader"。同步检查其他语言包。

### 4.6 多处控件颜色/样式未跟随主题色变化

#### 4.6.1 隐私政策对话框关闭按钮颜色硬编码
- **位置**：`privacy_policy_dialog.py:99`
- **问题**：`background: #2078DA;` 为固定蓝色，切换主题后仍显示蓝色。

#### 4.6.2 多个主要按钮 hover 颜色硬编码
- **位置**：
  - `basic_settings_page.py:141`
  - `token_page.py:120`
  - `welcome_page.py:101`
- **问题**：hover 颜色固定为 `#1A65C7`，不跟随当前主题色。

#### 4.6.3 主题变化后子页面控件不刷新
- **位置**：`basic_settings_page.py`、`token_page.py`、`license_page.py`、`finish_page.py`、`tutorial_page.py`
- **问题**：这些页面要么没有重写 `set_accent_color()`，要么只更新了部分按钮。在主题页选择新主题后：
  - 输入框 focus 边框颜色仍为旧主题色；
  - 主要按钮背景色仍为旧主题色；
  - 隐私政策链接颜色仍为旧主题色；
  - `prev_btn` 在 `ThemePage`/`FinishPage` 中未更新；
  - `TutorialPage` 的导航按钮完全未更新。
- **修复建议**：所有页面重写 `set_accent_color()`，统一刷新依赖主题色的控件样式；或基类提供统一刷新接口。

### 4.7 `FinishPage` 与 `TutorialPage` 富文本字体可能不受 `setFont` 控制

- **位置**：`finish_page.py:78-81`
- **问题**：`desc_label` 使用 `_build_description_text()` 返回 HTML，随后调用 `setFont(body_font())` 与 `setWordWrap(True)`。QLabel 在显示富文本时，`setFont` 对 `<span>` 内的文本通常不生效，且 `wordWrap` 对块级 HTML 行为与纯文本不同。
- **影响**：删除线文本与后续说明可能字号不一致或换行异常。
- **修复建议**：用 CSS 在 HTML 字符串中指定字体，或拆分为两个 QLabel 分别管理。

---

## 5. 交互与体验 Bug

### 5.1 用户关闭向导即退出整个程序

- **位置**：`main.py:180-184`
- **问题**：`if wizard.exec_() != QDialog.Accepted: sys.exit(0)`。
- **影响**：首次启动时用户点击向导右上角关闭按钮（或按 Esc），程序直接退出而不是进入主界面。部分用户可能只是想稍后配置。
- **修复建议**：根据产品策略决定。若必须完成设置，应弹出提示；若允许跳过，则进入主界面但下次启动仍弹向导。

### 5.2 `CircleNavButton` 鼠标拖出按钮外释放仍会触发导航

- **位置**：`gui/components/circle_nav_button.py:203-208`
- **问题**：`mouseReleaseEvent` 未判断释放位置是否在按钮矩形内。
- **影响**：用户按下按钮后划出按钮再释放，仍会触发页面切换，与常规按钮行为不符。
- **修复建议**：在 `mouseReleaseEvent` 中检查 `self.rect().contains(event.pos())`。

### 5.3 `MaterialCheckBox` 键盘事件可能重复处理

- **位置**：`gui/components/material_checkbox.py:290-297`
- **问题**：空格/回车切换选中后调用 `event.accept()`，随后仍执行 `super().keyPressEvent(event)`。
- **影响**：在某些焦点策略下可能导致一次按键触发两次切换。
- **修复建议**：`event.accept()` 后增加 `return`，不再调用父类处理。

### 5.4 复制 JS 代码提示仅依赖 Tooltip，提示不明显

- **位置**：`gui/welcome/pages/token_page.py:187-195`
- **问题**：复制成功后仅在按钮上设置 2 秒 tooltip，如果用户鼠标未悬停在按钮上则看不到提示。
- **修复建议**：增加更明显的视觉反馈，例如按钮文字临时变为"已复制"，或显示轻量通知。

### 5.5 教程页导航按钮 tooltip 硬编码使用 tutorial_1

- **位置**：`gui/welcome/pages/tutorial_page.py:90-91`
- **问题**：无论当前是第 1 页还是第 2 页，都读取 `welcome_onboarding.tutorial_1.previous_tip` / `next_tip`。
- **影响**：当前 i18n 中两页提示相同，无实际错误，但属于语义硬编码，后续维护易出错。
- **修复建议**：使用 `f"welcome_onboarding.tutorial_{self.tutorial_index}.previous_tip"` 动态读取。

### 5.6 完成页未校验必填项即可结束向导

- **位置**：`gui/welcome/wizard.py:118-139`
- **问题**：`finish()` 直接收集并保存所有设置，未检查：
  - 用户是否已同意隐私政策（虽然 LicensePage 已禁用 next_btn，但通过其他路径仍可到达完成页）；
  - Access Token 是否为空（可能用户跳过了配置）。
- **影响**：可能产生不完整或非法的首次配置。
- **修复建议**：在 `finish()` 中增加必要的校验与提示。

---

## 6. 代码质量与规范问题

### 6.1 未使用的导入

- **位置**：`gui/welcome/pages/welcome_page.py:23`
- **问题**：`from PyQt5.QtWidgets import ... QGraphicsDropShadowEffect` 已导入但未使用。
- **修复建议**：删除。

### 6.2 无意义的 f-string

- **位置**：`gui/welcome/pages/base_page.py:55`
- **问题**：`title.setStyleSheet(f"color: #212121;")` 中 f-string 无变量。
- **修复建议**：改为普通字符串 `"color: #212121;"`。

### 6.3 i18n 存在重复键

- **位置**：`i18n/zh_CN.json:1077-1079`
- **问题**：`more_page.tutorial_button` 与 `more_page.button_text` 都是"新手教程"。
- **修复建议**：合并为一个键，例如统一使用 `more_page.button_text`。

### 6.4 隐私政策 Markdown 文件内容为空

- **位置**：`docs/privacy_policy.md`
- **问题**：文件仅包含标题与"生效日期：待填写"，没有实质内容。
- **影响**：用户点击隐私政策链接后看到空文档，不符合合规要求。
- **修复建议**：补充隐私政策正文。

### 6.5 `wizard.finish()` 缺少异常保护

- **位置**：`gui/welcome/wizard.py:118-139`
- **问题**：若某个页面的 `get_*()` 方法抛出异常，整个 `finish()` 会失败，设置部分保存或全部不保存。
- **修复建议**：增加 `try...except` 捕获并记录日志，必要时提示用户。

### 6.6 从"更多"页修改主题后，主窗口不会实时刷新

- **位置**：`gui/pages/more_page.py:491-494`
- **问题**：打开向导修改主题并完成后，仅保存设置，未通知 `MainWindow` 重新应用主题。
- **影响**：用户需要重启程序才能看到新主题。
- **修复建议**：向导关闭后调用主窗口主题刷新方法，或监听 `settings_manager.setting_changed` 信号。

---

## 7. 修复优先级建议

### P0（必须立即修复）
1. `ask_before_download` 键名错误，改为 `ask_download_dir`。
2. Access Token 保存前调用 `encrypt_token()` 加密。
3. 系统快捷方式设置需要实际执行创建逻辑，或暂时移除该页/选项（避免功能欺诈）。

### P1（严重影响体验）
4. 语言切换后实时刷新向导文本。
5. 从"更多"页打开时加载当前用户设置（主题、下载目录）。
6. 修复多个页面内容垂直不居中问题。
7. 完成页文案"ClassIsland"改为正确应用名。
8. 隐私政策 Markdown 补充内容。

### P2（视觉与细节优化）
9. 统一主题色变化时所有子控件的样式刷新。
10. 教程页图片同时约束宽高。
11. 基本设置页/系统设置页补充图标或移除空白占位。
12. 修复按钮 hover 颜色硬编码问题。
13. `CircleNavButton` 鼠标释放位置校验。
14. `MaterialCheckBox` 键盘事件重复处理。

### P3（规范与可维护性）
15. 清理未使用导入、无意义 f-string、i18n 重复键。
16. `wizard.finish()` 增加异常保护。
17. 完善崩溃日志回归验证。

---

## 8. 验证建议

1. 临时将 `runtime/settings/settings.json` 中的 `first_run` 设为 `false`，启动程序，确认向导能正常弹出且不再崩溃。
2. 在基本设置页关闭"每次下载前询问下载位置"，完成向导后检查 `settings.json` 中的 `ask_download_dir` 是否被正确写入。
3. 在 Access Token 页输入任意字符串，完成向导后检查 `settings.json` 中的 `access_token` 是否为加密格式（以 `gAAAAA` 或 `xor:` 开头）。
4. 勾选"创建桌面快捷方式"，完成向导后检查桌面是否实际生成快捷方式。
5. 切换语言后，确认向导内所有页面文本立即刷新。
6. 从"更多"页打开新手教程，确认显示的是当前用户的主题色与下载目录。
7. 在主题页切换不同预设/自定义颜色，确认向导背景、按钮、输入框 focus 色同步变化。
8. 检查教程页图片是否完整显示、无裁剪。
9. 检查完成页"轰！嚓-嚓-嚓！推推"删除线样式与后续文本是否正确换行。
10. 检查隐私政策弹窗内容是否完整、关闭按钮颜色是否跟随主题色。

---

*报告结束*
