# 程序启动新手引导 Spec

## Why

新用户首次启动 Smart eduDownloader 时，需要经过简洁的引导流程完成语言、下载目录、Access Token、主题、系统快捷方式等基础配置，并了解基本使用方法，以降低上手门槛。

## What Changes

- 新增 `WelcomeWizard` 窗口模块，在程序首次启动时于主窗口之前弹出。
- 实现 9 屏引导流程：欢迎、许可条款、基本设置、Access Token、主题设置、系统快捷方式、教程 1、教程 2、完成。
- 新增独立的 `MaterialCheckBox` 自定义复选框组件，符合 Material Design 3 规范。
- 新增圆形导航按钮组件（上一步/下一步/对号完成），支持悬浮提示。
- 在 `more_page` 的实用工具区添加「新手教程」按钮，可重新打开引导。
- 新增/更新相关 i18n 翻译键。
- 创建空的隐私政策占位文件 `docs/privacy_policy.md`。

## Impact

- Affected specs: 启动流程、设置系统、多语言支持、UI 组件库。
- Affected code:
  - `main.py`（启动流程）
  - `gui/welcome/wizard.py`（新增）
  - `gui/welcome/pages/*.py`（新增，9 个屏幕）
  - `gui/components/material_checkbox.py`（新增）
  - `gui/components/circle_nav_button.py`（新增）
  - `gui/pages/more_page.py`（添加按钮）
  - `core/config/settings_manager.py`（`first_run` 标志）
  - `i18n/zh_CN.json` 等语言包
  - `docs/privacy_policy.md`（新增占位）

## ADDED Requirements

### Requirement: 首次启动检测

The system SHALL detect whether the application is launched for the first time using the `first_run` setting (default `False`).

#### Scenario: First launch
- **WHEN** the application starts and `first_run` is `False`
- **THEN** the `WelcomeWizard` is shown modally before the main window appears.
- **AND** after the wizard finishes, `first_run` is set to `True` and the main window is shown.

#### Scenario: Subsequent launch
- **WHEN** the application starts and `first_run` is `True`
- **THEN** the main window is shown directly without the wizard.

### Requirement: 欢迎屏幕

The system SHALL display a welcome screen as the first page of the wizard.

#### Scenario: Welcome page displayed
- **WHEN** the wizard opens
- **THEN** the wizard window uses a light grayish-white background (`#F5F5F5` or the default theme background color) and has a fixed size of approximately 860×600 px.
- **AND** the window title bar shows the application name and a close button.
- **AND** the screen shows the application icon (`resources/logo/logo_48x48.ico`, 96×96 px) and application name "Smart edu downloader" centered vertically.
- **AND** a circular theme-color next arrow button (diameter 48 dp) is placed below the application name; the arrow icon uses `resources/images/welcome/arrow_r.svg` rendered in white.
- **AND** the bottom of the screen shows the version number and two text buttons: 「数据迁移」 and 「语言设置」 in the theme accent color.
- **AND** clicking 「数据迁移」 opens a file dialog and imports the selected settings file using `SettingsExporter.import_config()`.
- **AND** clicking 「语言设置」 opens a language selection popup/combo.
- **AND** clicking the arrow transitions to the license screen with a 250 ms fade-in/fade-out animation.

### Requirement: 许可条款屏幕

The system SHALL display a license/terms screen with a Material Design 3 checkbox.

#### Scenario: License page displayed
- **WHEN** the user navigates to the license page
- **THEN** the screen shows a centered bold title 「同意许可条款」 and a centered subtitle 「要继续使用 Smart edu downloader，您必须阅读并同意以下许可条款。».
- **AND** below the subtitle is a `MaterialCheckBox` labeled 「我已阅读并同意《Smart edu downloader 隐私政策》」，where 「隐私政策」 is a clickable blue hyperlink.
- **AND** a yellow `#FFF4CE` rounded rectangle notification (radius 8 px, padding 12 px, shadow 1 dp) appears at the bottom-right corner with the anti-fraud message and a clickable Bilibili link.
- **AND** the notification has a close button (×) on the top-right; the user can dismiss it.
- **AND** the notification icon area is a `#9D5D00` circle (diameter 24 dp) displaying `resources/images/welcome/bang.svg` (white exclamation mark) on the left side of the message.
- **AND** the checkbox uses a custom `MaterialCheckBox` component, not the native Qt checkbox; its checkmark uses `resources/images/welcome/tick.svg` rendered in white.
- **AND** the next arrow (`resources/images/welcome/arrow_r.svg`) is grayed out (`#BBBBBB`) and disabled until the checkbox is checked.
- **AND** hovering over the arrow (enabled or disabled) shows a tooltip 「下一步」.
- **AND** only the privacy policy is shown (no open-source license).
- **AND** clicking the privacy policy link opens a modal dialog window displaying `docs/privacy_policy.md` (placeholder content for now).

### Requirement: 隐私政策窗口

The system SHALL display the privacy policy in a separate modal dialog when the user clicks the privacy policy link.

#### Scenario: Privacy policy dialog
- **WHEN** the user clicks the 「隐私政策」 hyperlink on the license page
- **THEN** a modal dialog opens with the title 「Smart edu downloader 隐私政策」.
- **AND** the dialog shows the content of `docs/privacy_policy.md` rendered as rich text / Markdown.
- **AND** the dialog displays an effective date line at the top.
- **AND** the dialog has a 「关闭」 button at the bottom-right to dismiss it.
- **AND** the dialog is scrollable if the content exceeds the available height.

### Requirement: Material Design 3 复选框

The system SHALL provide a custom checkbox component matching Material Design 3 specifications.

#### Scenario: Unchecked state
- **WHEN** the checkbox is unchecked
- **THEN** it displays a 24dp rounded square with a thin light gray border.

#### Scenario: Checked state
- **WHEN** the user clicks the checkbox
- **THEN** a ripple effect spreads outward from the touch point.
- **AND** a blue fill spreads outward from the center.
- **AND** a white checkmark (`resources/images/welcome/tick.svg`) is drawn with a path animation appearing stroke-by-stroke.
- **AND** the animation uses `FastOutSlowIn` easing.
- **AND** the checkbox has a subtle 1dp shadow with layered depth.

### Requirement: 基本设置屏幕

The system SHALL allow the user to configure the download directory and ask-before-download option.

#### Scenario: Basic settings page
- **WHEN** the user reaches the basic settings page
- **THEN** the screen shows a centered bold title 「基本」 and a centered subtitle 「配置 Smart edu downloader 的基本设置」.
- **AND** it shows a card-style panel with two rows:
  - Row 1: `resources/images/welcome/download.svg` icon (as-is), label 「文件保存位置」, description text, input field, and a browse button on the right.
  - Row 2: a switch labeled 「每次下载前询问下载位置」 with description text.
- **AND** a circular theme-color next arrow button (`resources/images/welcome/arrow_r.svg`, diameter 48 dp) is centered at the bottom.

### Requirement: Access Token 配置屏幕

The system SHALL guide the user through configuring the Access Token.

#### Scenario: Token page
- **WHEN** the user reaches the token page
- **THEN** the screen shows a bold title 「Access Token」 and subtitle 「配置下载所必须的用户 Token 令牌」 aligned to the left.
- **AND** it shows an input field labeled 「Access Token」 with a Paste button or direct paste support.
- **AND** it shows two buttons: 「打开云平台获取 token」 and 「一键复制代码」.
- **AND** it displays the 5-step configuration tutorial text in a numbered list.
- **AND** clicking 「打开云平台获取 token」 opens `https://www.zxx.edu.cn/` (or the configured cloud platform URL) in the default browser.
- **AND** clicking 「一键复制代码」 copies the JavaScript snippet `copy(localStorage.getItem('access_token'))` to the clipboard and shows a confirmation tooltip.
- **AND** circular previous (`resources/images/welcome/arrow_l.svg`, white on white/light gray background) and next (`resources/images/welcome/arrow_r.svg`, white on theme-color background) arrow buttons are present at the bottom.

### Requirement: 主题设置屏幕

The system SHALL allow the user to configure the application theme.

#### Scenario: Theme page
- **WHEN** the user reaches the theme page
- **THEN** the screen shows a bold title 「颜色配置」 and subtitle 「配置 Smart edu downloader 的主题外观」 aligned to the left.
- **AND** it reuses the existing theme preset grid and custom sliders from `InterfaceSettingTab`.
- **AND** circular previous (`resources/images/welcome/arrow_l.svg`) and next (`resources/images/welcome/arrow_r.svg`) arrow buttons are present at the bottom.

### Requirement: 系统快捷方式屏幕

The system SHALL allow the user to configure desktop and start-menu shortcuts.

#### Scenario: System page
- **WHEN** the user reaches the system page
- **THEN** the screen shows a centered bold title 「系统」 and a centered subtitle 「配置 Smart edu downloader 的系统集成功能，这些功能可以优化您使用本软件的体验」.
- **AND** it shows a list of `MaterialCheckBox` items, each with an icon, a primary label, and a secondary description:
  - 「创建桌面快捷方式」 with description 「在桌面上添加软件快捷方式。」
  - 「创建开始菜单快捷方式」 with description 「在开始菜单中添加软件快捷方式。」
- **AND** circular previous (`resources/images/welcome/arrow_l.svg`, white/light background) and next (`resources/images/welcome/arrow_r.svg`, theme-color background) arrow buttons are centered at the bottom.

### Requirement: 教程屏幕

The system SHALL show two tutorial screens explaining how to use the application.

#### Scenario: Tutorial 1
- **WHEN** the user reaches tutorial 1
- **THEN** the screen shows `resources/images/welcome/Teach/1.png` (a screenshot of the home page) centered at the top, scaled to fit within the wizard width with preserved aspect ratio.
- **AND** below the image it shows the text 「课本教材可在【主页】搜索并下载。」.
- **AND** circular previous (`resources/images/welcome/arrow_l.svg`) and next (`resources/images/welcome/arrow_r.svg`) arrow buttons are present at the bottom.

#### Scenario: Tutorial 2
- **WHEN** the user reaches tutorial 2
- **THEN** the screen shows `resources/images/welcome/Teach/2.png` (a screenshot of the resource library page) centered at the top, scaled to fit within the wizard width with preserved aspect ratio.
- **AND** below the image it shows the text 「无法搜索的教材可点击【资源】在资源库界面寻找。」.
- **AND** circular previous (`resources/images/welcome/arrow_l.svg`) and next (`resources/images/welcome/arrow_r.svg`) arrow buttons are present at the bottom.

### Requirement: 完成屏幕

The system SHALL display a completion screen at the end of the wizard.

#### Scenario: Completion page
- **WHEN** the user reaches the final page
- **THEN** the screen shows `resources/images/welcome/Teach/help/celebration.png` centered, scaled to approximately 180×180 px (or its natural size if smaller).
- **AND** below the image it shows a centered bold title 「完成」.
- **AND** below the title it shows the centered text with 「轰！嚓-嚓-嚓！推推」 rendered with a strikethrough line through it, followed by 「应用的基本设置已完成，感谢您选用 ClassIsland。点击对号以结束设置向导。后续可点击【更多】重过新手引导。」.
- **AND** circular previous arrow (`resources/images/welcome/arrow_l.svg`, white/light background) and circular checkmark completion button (`resources/images/welcome/true.svg`, white on theme-color background, diameter 48 dp) are centered at the bottom.
- **AND** clicking the checkmark closes the wizard with an accept result and opens the main window.

### Requirement: 更多页面入口

The system SHALL provide a way to reopen the wizard from the more page.

#### Scenario: Reopen wizard
- **WHEN** the user navigates to the more page
- **THEN** a 「新手教程」 button is visible in the utility tools section.
- **AND** clicking the button opens the `WelcomeWizard` again.

## MODIFIED Requirements

### Requirement: 启动流程

The application SHALL show the welcome wizard before the main window only on the first launch.

- **WHEN** `main()` is called
- **THEN** settings are loaded and `is_first_run` is evaluated.
- **AND** if `is_first_run` is true, the `WelcomeWizard` is executed modally.
- **AND** only after the wizard is accepted does the main window initialize and show.

## REMOVED Requirements

无。
