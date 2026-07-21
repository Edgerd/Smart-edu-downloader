# 修复新手引导向导（Welcome Wizard）多项缺陷

## 1. 摘要

本次计划针对 `gui/welcome` 新手引导向导在近期测试中暴露的 10 类问题进行集中修复，涵盖窗口拖拽抖动、内容不居中、反诈提示框内容、文本/图标/按钮视觉异常、图片显示不全、弹窗黑底以及运行时 `UnboundLocalError` 等。所有修改严格遵循项目现有 PyQt5 规范、一功能一文件、PEP 8/PEP 257 以及 i18n 键管理要求。

## 2. 现状分析

通过对以下核心文件的代码审查，确认问题根因：

- `gui/welcome/wizard.py`
- `gui/welcome/pages/base_page.py`
- `gui/welcome/pages/welcome_page.py`
- `gui/welcome/pages/license_page.py`
- `gui/welcome/pages/anti_fraud_dialog.py`
- `gui/welcome/pages/privacy_policy_dialog.py`
- `gui/welcome/pages/tutorial_page.py`
- `gui/welcome/pages/finish_page.py`
- `gui/welcome/pages/basic_settings_page.py`
- `gui/welcome/pages/theme_page.py`
- `gui/welcome/pages/system_page.py`
- `gui/welcome/pages/token_page.py`
- `gui/components/circle_nav_button.py`
- `gui/components/material_checkbox.py`
- `i18n/zh_CN.json`

主要问题归类：

| 问题 | 根因 |
|------|------|
| 拖动窗口高度抽搐 | 页面切换动画使用 `QGraphicsOpacityEffect`，堆叠容器尺寸未固定；页面内容高度不一致导致布局重协商。 |
| 内容不居中/与示例图不符 | `BaseWelcomePage.content_layout` 本身带 `stretch=1`，`add_centered_content` 又额外插入上下 stretch，双重居中造成内容偏下、顶部留白过大；隐藏标题仍占布局空间。 |
| 反诈提示框内容与要求不符 | `i18n/zh_CN.json` 的 `anti_fraud_content` 不含 `{link}` 占位符，代码中 `replace("{link}", ...)` 失效；弹窗未使用标题（符合要求），但正文未插入 B站超链接。 |
| 文本出现圆角描边 | `MaterialCheckBox` 绘制了虚线焦点环；部分 `QPushButton`/`QFrame` 样式表携带 `border-radius` 与 `border`，在透明背景或特效叠加时边缘产生描边感。 |
| SVG 图标白色无法显示 | 部分 SVG 仅通过 `stroke` 或根标签无显式 `fill` 定义颜色；`_replace_svg_fill` 对大小写/无 fill 场景覆盖不足。 |
| 按钮未选中时出现虚线描边 | `MaterialCheckBox` 焦点环为虚线；`CircleNavButton` 虽已 `NoFocus`，但部分平台默认焦点矩形仍可能闪现。 |
| 示例图片显示不全 | `TutorialPage._scale_image` 使用固定最大尺寸 760×360，未根据内容区实际可用高度计算，导致图片被截断或压缩后显示区域不足。 |
| 完成页内容显示不全/文案错误 | `QVBoxLayout` 未导入会导致运行时错误；描述文案出现 `ClassIsland` 且 `strikethrough_text` 为无意义占位符；`setMaximumWidth(720)` 在特定字体下仍可能截断。 |
| 语言设置弹窗黑底 | `_LanguageSelectorDialog` 与 `PrivacyPolicyDialog` 使用 `WA_TranslucentBackground` 且外层布局保留 12px 透明边距，在 Windows 部分环境下透明区域显示黑色。 |
| `UnboundLocalError` | `welcome_page.py` 历史版本中 `QFileDialog.getOpenFileName` 返回值解包变量名为 `_`，与 `core.i18n._()` 冲突；当前代码已改为 `_selected_filter`，但需确保调用链无遗漏。 |

## 3. 修改方案

### 3.1 `gui/welcome/wizard.py`

**修改内容：**

1. 为 `self.stack` 设置固定尺寸策略，避免页面切换时因子页面 `sizeHint` 不同导致窗口高度重协商：
   ```python
   self.stack.setFixedSize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
   ```
2. 动画期间禁用页面重新布局：在 `_fade_out`/`_fade_in` 开始时对当前页面调用 `setUpdatesEnabled(False)`，动画结束后再恢复。
3. 确保 `self.setWindowFlags` 包含 `Qt.MSWindowsFixedSizeDialogHint`（已存在），防止用户调整窗口大小。
4. 在 `_on_theme_changed` 中确认所有页面主题色同步刷新（当前已遍历，无需额外改动）。

### 3.2 `gui/welcome/pages/base_page.py`

**修改内容：**

1. 将 `content_layout` 的 stretch 因子从 `1` 改为 `0`，让内容高度由子控件决定，而不是被布局拉伸。
2. 调整 `add_centered_content`：仅在内容区上下各插入一次 `addStretch(1)`，并移除 `content_layout` 本身的 stretch，避免双重居中。
3. 对不需要标题/副标题的页面（`TutorialPage`、`FinishPage`），在 `_init_ui` 中根据子类返回的隐藏标签不占用空间；或在子类中调用 `self.title_label.hide(); self.title_label.setFixedHeight(0)` 彻底消除占位。
4. 保持标题/副标题的默认居中对齐，供需要标题的页面复用。

### 3.3 `gui/welcome/pages/welcome_page.py`

**修改内容：**

1. 将 `_on_confirm` 中的局部导入 `from core.config.settings_manager import set_setting` 提到文件顶部，与 `get_settings_manager` 统一导入。
2. 修复 `_LanguageSelectorDialog` 黑底：
   - 将外层 `layout.setContentsMargins(12, 12, 12, 12)` 改为 `0`，让白色卡片填满整个弹窗。
   - 保留卡片圆角与边框。
   - 确保 `card` 的 `minimumSize` 等于弹窗尺寸，消除透明边缘。
3. 确认 `_on_import_config` 的返回值解包变量为 `_selected_filter`，避免与 `_()` 函数名冲突。

### 3.4 `gui/welcome/pages/license_page.py`

**修改内容：**

1. 移除第 89 行 `self.agree_label.mousePressEvent = lambda _evt: self._on_privacy_link_clicked()`，仅保留 `linkActivated.connect()`，恢复 QLabel 链接默认交互。
2. 调整复选框垂直位置：将 `content_widget` 不再通过 `add_centered_content` 居中，而是直接 `self.content_layout.addWidget(content_widget, 0, Qt.AlignCenter)`，使其位于标题下方合理位置。
3. 保持 `showEvent` 触发的反诈弹窗逻辑不变。

### 3.5 `gui/welcome/pages/anti_fraud_dialog.py`

**修改内容：**

1. 保持无标题设计（符合要求）。
2. 修改 `_build_content_text`，不再依赖 `anti_fraud_content` 中的 `{link}` 占位符，而是将 B站超链接按用户指定格式拼接在正文末尾：
   ```python
   content = _("welcome_onboarding.license.anti_fraud_content")
   link_text = _("welcome_onboarding.license.bilibili_link")
   link_html = (
       f'<a href="https://space.bilibili.com/3537111380658360" '
       f'style="color: {self._accent_color}; text-decoration: none;">'
       f'{link_text}</a>'
   )
   return f"{content}{link_html}。"
   ```
3. 弹窗尺寸从固定 540×220 调整为自适应内容高度，避免正文被截断。
4. 将外层 `layout.setContentsMargins(16, 16, 16, 16)` 改为 `0`，并给 `QDialog` 自身设置与卡片一致的 `#FFF4CE` 背景，消除透明黑边。

### 3.6 `gui/welcome/pages/privacy_policy_dialog.py`

**修改内容：**

1. 修复黑底：
   - 将外层 `layout.setContentsMargins(12, 12, 12, 12)` 改为 `0`。
   - 给 `QDialog` 自身设置背景色 `background: #FFFFFF;`。
2. 关闭按钮背景色改为使用主题色 `self._accent_color`，而不是硬编码 `#2078DA`。
3. 保持无边框、支持拖拽。

### 3.7 `gui/welcome/pages/tutorial_page.py`

**修改内容：**

1. 补充缺失的导入：
   ```python
   from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
   ```
2. 重构 `_scale_image`，根据 `self.image_label` 的实际可用尺寸动态计算缩放上限：
   ```python
   available_width = self.width() - 80   # 左右边距 40+40
   available_height = max(200, self.height() - 180)  # 预留导航、说明文字空间
   scaled = self._raw_pixmap.scaled(
       available_width,
       available_height,
       Qt.KeepAspectRatio,
       Qt.SmoothTransformation,
   )
   ```
3. 给 `image_label` 设置 `setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)` 与 `setMinimumSize`，确保图片区域始终可见。
4. 隐藏标题/副标题时彻底释放其占位，避免挤压图片区域。

### 3.8 `gui/welcome/pages/finish_page.py`

**修改内容：**

1. 补充缺失的导入：
   ```python
   from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
   ```
2. 修正完成页文案：
   - 将 i18n 键 `welcome_onboarding.completion.strikethrough_text` 的值改为用户指定文本 `"轰！嚓-嚓-嚓！推推"`（已符合，保留）。
   - 将 `description` 改为：
     ```
     应用的基本设置已完成，感谢您选用 Smart edu downloader。点击对号以结束设置向导。后续可点击【更多】重新打开新手引导。
     ```
3. 设置 `desc_label.setTextFormat(Qt.RichText)`，确保删除线与 HTML 链接正常渲染。
4. 将 `desc_label.setMaximumWidth(720)` 保留，若仍截断则增加 `setMinimumHeight` 或调整行高；必要时改用 `QTextBrowser` 只读展示富文本。

### 3.9 `gui/components/circle_nav_button.py`

**修改内容：**

1. 保持 `setFocusPolicy(Qt.NoFocus)`，避免按钮获得焦点后出现虚线框。
2. 增强 SVG 颜色替换：
   - 对 `fill`/`stroke` 属性匹配增加大小写兼容（`fill=`/`FILL=`）。
   - 若 SVG 根标签无 fill 且无 stroke，注入默认 `fill` 后，对内部所有路径的 `fill`/`stroke` 统一替换。
   - 对只含 `style="fill:#fff"` 等内联样式的路径做正则替换。
3. 确保渲染后的 `QPixmap` 在按钮重绘时正确居中。

### 3.10 `gui/components/material_checkbox.py`

**修改内容：**

1. 移除 `_draw_box` 末尾的虚线焦点环绘制代码（第 388–398 行），解决“未选中按钮出现虚线描边”问题。
2. 如需保留键盘可访问性，可改为在获得焦点时绘制 1px 实线主题色圆角矩形，但默认不显示；本次按用户要求直接移除虚线焦点环。

### 3.11 `gui/welcome/pages/basic_settings_page.py`

**修改内容：**

1. 将 `self.add_centered_content(card, Qt.AlignCenter)` 改为 `self.content_layout.addWidget(card, 0, Qt.AlignCenter)`，使设置卡片紧贴标题下方，减少不必要的垂直居中留白。
2. 保持卡片内布局不变。

### 3.12 `gui/welcome/pages/theme_page.py`、`system_page.py`、`token_page.py`

**修改内容：**

1. 统一内容定位策略：
   - `theme_page.py`、`token_page.py` 标题/副标题保持左对齐，内容卡片/滚动区改为顶部对齐。
   - `system_page.py` 标题/副标题保持居中，卡片改为顶部对齐。
2. 将 `add_centered_content(...)` 改为 `self.content_layout.addWidget(..., 0, Qt.AlignTop)`，或新增 `add_top_content` helper。
3. 确保 `theme_page.py` 的 `QScrollArea` 在内容较少时不显示多余滚动条。

### 3.13 `i18n/zh_CN.json`

**修改内容：**

1. 修改 `welcome_onboarding.completion.description`：
   ```json
   "description": "应用的基本设置已完成，感谢您选用 Smart edu downloader。点击对号以结束设置向导。后续可点击【更多】重新打开新手引导。"
   ```
2. 修改 `welcome_onboarding.license.anti_fraud_content`，在末尾增加可替换链接位置：
   ```json
   "anti_fraud_content": "Smart edu downloader 是免费的软件，官方没有提供任何形式的付费支持服务，源作者B站首页地址在{link}。如果您通过有偿协助等付费方式取得本应用，在遇到问题时请在与卖家约定的服务框架下，优先向卖家求助。如果卖家没有提供您预期的服务，请退款或通过其它形式积极维护您的合法权益。"
   ```
3. 同步更新 `bilibili_link` 为 `https://space.bilibili.com/3537111380658360` 的显示文本（保持 `"访问B站主页"` 或按需求显示为超链接文本）。
4. 更新后同步到其他语言包（`en_US.json`、`ja_JP.json`、`emo_JI.json`、`lzh_CN.json`、`zh_TW.json`、`gt_CN.json`），至少保持键结构与 `zh_CN.json` 一致；翻译可先用英文/原文占位，后续人工校对。

### 3.14 版本号与更新日志

**修改内容：**

1. 当前版本为 `5.6.16 Beta 11`。本次为同一预发布版本下的缺陷集中修复，按规范**不升级**预发布标识，维持 `5.6.16 Beta 11`。
2. 在 `.dev/产品更新信息.md` 的 `5.6.16 Beta 11` 条目下追加修复记录：
   - 修复欢迎向导窗口拖动时高度抽搐
   - 修复各引导页内容不居中/顶部留白过大
   - 修复反诈提示框文案与超链接显示
   - 修复文本/按钮异常描边与焦点环
   - 修复白色 SVG 图标在主题色按钮上不可见
   - 修复教程页与完成页图片/内容显示不全
   - 修复语言设置与隐私政策弹窗黑底
   - 修复欢迎页 `UnboundLocalError`

## 4. 假设与决策

1. **窗口拖动抽搐**：假设用户通过系统标题栏拖动窗口。当前窗口已使用 `Qt.MSWindowsFixedSizeDialogHint` 禁止调整大小，抽搐主要由页面切换动画期间的布局重协商引起。通过固定 `QStackedWidget` 尺寸、动画期间禁用更新即可解决。不引入无边框客户区拖拽，避免与现有 `QDialog` 模态行为冲突。
2. **反诈提示框**：严格按用户要求不显示标题，正文内容使用用户提供的原文，B站链接以富文本超链接形式嵌入，链接文本显示为“访问B站主页”或按需求隐藏括号内容。
3. **文本圆角描边**：判定为 `MaterialCheckBox` 虚线焦点环及部分容器 `border-radius` 在透明/特效场景下的视觉残留。通过移除焦点环、消除透明边距、清理冗余边框解决。
4. **内容居中**：将“居中”理解为“在窗口可视区域内合理居中，不贴顶不贴底”，而不是“绝对几何中心”。因此减少双重 stretch，使内容位于标题下方、导航按钮上方。
5. **版本号**：本次为预发布版本内的缺陷修复，不升级版本号。

## 5. 验证步骤

1. **静态语法检查**
   ```powershell
   python -m py_compile gui/welcome/wizard.py
   python -m py_compile gui/welcome/pages/base_page.py
   python -m py_compile gui/welcome/pages/welcome_page.py
   python -m py_compile gui/welcome/pages/license_page.py
   python -m py_compile gui/welcome/pages/anti_fraud_dialog.py
   python -m py_compile gui/welcome/pages/privacy_policy_dialog.py
   python -m py_compile gui/welcome/pages/tutorial_page.py
   python -m py_compile gui/welcome/pages/finish_page.py
   python -m py_compile gui/welcome/pages/basic_settings_page.py
   python -m py_compile gui/welcome/pages/theme_page.py
   python -m py_compile gui/welcome/pages/system_page.py
   python -m py_compile gui/welcome/pages/token_page.py
   python -m py_compile gui/components/circle_nav_button.py
   python -m py_compile gui/components/material_checkbox.py
   ```
2. **导入验证**
   ```powershell
   python -c "from gui.welcome.wizard import WelcomeWizard; print('OK')"
   python -c "from gui.welcome.pages.tutorial_page import TutorialPage; print('OK')"
   python -c "from gui.welcome.pages.finish_page import FinishPage; print('OK')"
   ```
3. **i18n 一致性检查**
   ```powershell
   python .dev/test/verify_i18n.py
   ```
4. **运行时快速验证**（可选，需完整环境）：
   - 启动程序进入首次引导，逐页切换检查是否抖动。
   - 检查反诈提示框无标题、内容正确、B站链接可点击。
   - 检查语言设置弹窗、隐私政策弹窗无黑底。
   - 检查教程页图片完整显示、完成页文案正确。
   - 检查复选框/导航按钮无虚线描边，白色 SVG 图标可见。

## 6. 任务清单

- [ ] 修复 `wizard.py` 窗口抖动与堆叠容器尺寸。
- [ ] 重构 `base_page.py` 内容居中逻辑。
- [ ] 修复 `welcome_page.py` 导入与语言弹窗黑底。
- [ ] 修复 `license_page.py` 链接事件与布局。
- [ ] 修复 `anti_fraud_dialog.py` 内容与黑底。
- [ ] 修复 `privacy_policy_dialog.py` 黑底与硬编码颜色。
- [ ] 修复 `tutorial_page.py` 导入与图片缩放。
- [ ] 修复 `finish_page.py` 导入与文案。
- [ ] 修复 `circle_nav_button.py` SVG 颜色替换。
- [ ] 修复 `material_checkbox.py` 虚线焦点环。
- [ ] 调整 `basic_settings_page.py`/`theme_page.py`/`system_page.py`/`token_page.py` 内容定位。
- [ ] 更新 `i18n/zh_CN.json` 完成页与反诈文案。
- [ ] 同步其他语言包键结构。
- [ ] 更新 `.dev/产品更新信息.md`。
- [ ] 运行 py_compile、import 与 i18n 验证。
