# 多语言支持改造 Spec

## Why

当前 Smart Edu Downloader 的界面文本以硬编码中文为主，无法支持后续国际化扩展，也不利于统一维护。本改造将建立完整的多语言架构，使所有界面展示文本通过语言包获取，为后续扩展其他语言打下基础。

## What Changes

- 新增 `core/i18n/` 多语言核心模块，提供语言加载、翻译查找、默认回退等能力。
- 新增项目根目录 `i18n/` 文件夹，按 `i18n/<locale>.json` 组织语言文件。
- 当前阶段仅提供 `zh_CN.json` 中文语言包，包含所有界面展示文本。
- 所有界面代码（`gui/` 及 `core/` 中面向用户的文本）禁止直接出现中文，统一通过 `_()` 或 `tr()` 接口获取。
- 在 `core/infrastructure/default_settings.py` 中新增 `language` 设置项，默认值为 `"zh_CN"`。
- 在设置界面的"界面"分类下新增"语言选择"功能模块，支持下拉选择已加载语言；变更后提示用户重启应用生效。
- 应用启动时自动扫描 `i18n/` 目录，加载所有有效的语言文件；若当前语言文件缺失则回退到 `zh_CN`。

## Impact

- 新增能力：运行时多语言文本解析、语言包热扫描、设置界面语言切换。
- 影响代码：
  - `core/i18n/translator.py`（新增）
  - `core/i18n/__init__.py`（新增）
  - `core/infrastructure/default_settings.py`（新增 `language` 默认值）
  - `main.py`（启动时初始化翻译器并加载语言包）
  - `gui/pages/setting_page.py`（新增语言选择模块）
  - `gui/managers/settings_handler.py`（保存语言设置）
  - `gui/` 及 `core/` 中所有含硬编码中文展示文本的文件（替换为翻译调用）
- 影响产物：新增 `i18n/zh_CN.json` 文件，成为应用正常运行依赖。

## ADDED Requirements

### Requirement: 多语言核心模块

The system SHALL provide a centralized internationalization module under `core/i18n/`.

#### Scenario: 加载语言文件
- **WHEN** the application starts
- **THEN** it scans the `i18n/` directory at the project root
- **AND** loads every valid `<locale>.json` file into memory
- **AND** falls back to `zh_CN` if the configured language file is missing or invalid

#### Scenario: 翻译接口
- **WHEN** any module calls `_("key")` or `tr("key")`
- **THEN** the system returns the text defined in the currently loaded language file
- **AND** if the key is missing, returns the key itself as a fallback

### Requirement: 中文语言包

The system SHALL provide a complete Chinese language pack at `i18n/zh_CN.json`.

#### Scenario: 覆盖所有界面文本
- **WHEN** the application runs in Chinese
- **THEN** every user-facing text previously hard-coded in Chinese MUST be resolved from `i18n/zh_CN.json`

### Requirement: 设置项存储当前语言

The system SHALL store the selected display language in settings.

#### Scenario: 保存语言偏好
- **WHEN** the user selects a language in the settings page
- **THEN** the value is persisted to `settings.json` under the key `language`
- **AND** the change only takes effect after the application is restarted

### Requirement: 设置界面语言选择模块

The system SHALL provide a language selector in the settings UI under the "Interface" section.

#### Scenario: 展示可用语言
- **WHEN** the user opens the interface settings
- **THEN** a dropdown lists all languages loaded from `i18n/`
- **AND** the currently configured language is pre-selected

#### Scenario: 变更后提示重启
- **WHEN** the user changes the language selection
- **THEN** a label or notification indicates that a restart is required to apply the change

## MODIFIED Requirements

### Requirement: 启动流程

The application startup sequence is modified to initialize the translator before any UI text is rendered.

- **GIVEN** the application is starting
- **WHEN** `main()` runs
- **THEN** it loads settings, determines `language`, initializes `core.i18n`, and loads the matching language pack before creating `MainWindow`

### Requirement: 界面代码无硬编码中文

All modules under `gui/` and any `core/` modules that produce user-facing text MUST use the translation interface.

- **GIVEN** a string that appears in the UI
- **THEN** it MUST NOT be written as a Chinese literal in Python code
- **AND** it MUST be referenced via a translation key

## REMOVED Requirements

无移除的功能。本改造为纯增量改造，不影响现有业务逻辑。
