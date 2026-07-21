# 多样式标题栏功能 Spec

## Why
当前主窗口采用标题栏与导航栏上下分离的布局，占用较高垂直空间，且标题文本和字体样式固定。为提升界面紧凑度和个性化，需要新增一种将标题、导航、窗口控制按钮合并到同一行的精简样式，并开放标题文本与字体样式的自定义能力。

## What Changes
- 新增统一的标题栏组件 `gui/components/unified_title_bar.py`，支持“大号”与“精简”两种布局模式。
- 在默认设置中新增 `title_bar_style`（`large`/`compact`）、`custom_title_text`、`title_font_styles` 三个设置项。
- 修改 `gui/main_window.py`，使其根据 `title_bar_style` 动态创建大号分离式布局或精简合并式布局，并支持运行时切换。
- 在调试面板的“实验室”标签页 `gui/components/debug/lab_tab.py` 增加标题栏样式切换开关/下拉框，以及标题自定义入口。
- 更新 `resources/i18n/zh_CN.json` 等语言包，新增标题栏相关的翻译键。
- 按预发布版本规则升级 `core/infrastructure/version.py` 与 `.dev/产品更新信息.md`：当前为 `5.6.17 Beta 10`，升级为 `5.6.17 Beta 11`。

## Impact
- Affected specs: 主窗口布局、调试实验室、设置持久化、国际化。
- Affected code:
  - `gui/components/unified_title_bar.py`（新增）
  - `gui/main_window.py`
  - `gui/components/debug/lab_tab.py`
  - `core/infrastructure/default_settings.py`
  - `resources/i18n/zh_CN.json`、`resources/i18n/en_US.json`、`resources/i18n/zh_TW.json`
  - `version.py`
  - `.dev/产品更新信息.md`

## ADDED Requirements

### Requirement: 统一标题栏组件
The system SHALL 提供一个 `UnifiedTitleBar` 组件，能够根据模式在“大号”与“精简”两种视觉风格间切换。

#### Scenario: 大号模式
- **WHEN** `UnifiedTitleBar` 被设置为 `large` 模式
- **THEN** 其外观与行为应与现有的 `TitleBar` + `NavBar` 上下组合保持一致：标题栏高度 50px，显示完整标题 `SED - Smart-edu-downloader`，导航栏位于标题栏下方，高度 55px，导航按钮尺寸、字体、图标大小与当前一致。

#### Scenario: 精简模式
- **WHEN** `UnifiedTitleBar` 被设置为 `compact` 模式
- **THEN** 标题、五个导航按钮、最小化/最大化/关闭按钮在同一水平行排列；标题在左，导航按钮居中，窗口控制按钮在右；整体高度降低到约 40px；标题显示 `SED`；字体、图标、按钮大小均按比例缩小。

### Requirement: 标题自定义
The system SHALL 允许用户自定义标题栏显示的文本，并可单独设置标题字体的粗体、斜体样式。

#### Scenario: 默认标题
- **WHEN** 用户未自定义标题
- **THEN** 大号模式显示 `SED - Smart-edu-downloader`，精简模式显示 `SED`。

#### Scenario: 自定义标题与字体样式
- **WHEN** 用户在实验室设置中修改标题文本并勾选粗体/斜体
- **THEN** 标题栏立即应用新的文本和字体样式，并在重启后保持。

### Requirement: 设置持久化
The system SHALL 将标题栏样式、自定义标题文本、字体样式持久化到 `settings.json`。

#### Scenario: 设置保存
- **WHEN** 用户在实验室中切换样式或修改标题
- **THEN** 设置管理器在 1 秒延迟后自动保存，程序重启后恢复上次选择。

## MODIFIED Requirements

### Requirement: 主窗口布局
原 `MainWindow._create_ui()` 固定创建 `TitleBar` 与 `NavBar` 两个组件。
修改后：
- `MainWindow` 根据 `title_bar_style` 决定创建大号分离组件或精简统一组件。
- 切换设置时，`MainWindow` 能够销毁旧组件、创建新组件并保留当前页面、主题、最大化状态。
- 精简模式下，导航按钮点击仍通过 `NavigationManager` 切换页面；窗口控制按钮事件保持原有行为。

## REMOVED Requirements

### Requirement: 固定标题栏与导航栏分离布局
**Reason**: 需要支持用户切换为更紧凑的合并布局。
**Migration**: 默认保持大号分离布局，新增精简合并布局作为可选项；不删除现有 `TitleBar` 与 `NavBar` 文件，仅让主窗口按需引用。
