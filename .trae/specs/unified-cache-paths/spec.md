# 统一缓存与设置路径规范

## Why

项目中存在多个位置的 settings.json 和 runtime 文件夹，导致缓存数据分散、配置不一致，且部分模块使用相对路径而非项目根目录的绝对路径。

当前问题：
- `settings.json` 同时存在于项目根目录和 `core/` 下，数据可能不同步
- `runtime/` 同时存在于项目根目录和 `core/` 下，日志和缓存文件分散
- `more_page.py` 使用裸文件名 `"search_history.json"`，依赖当前工作目录
- `setting_page.py` 使用裸文件名 `"settings.json"`，依赖当前工作目录
- `download_history.py` 使用裸文件名 `"download_history.json"`，依赖传入目录
- 多个模块各自计算项目根目录路径，缺乏统一入口

## What Changes

- **新增** `core/infrastructure/path_resolver.py` 模块，集中管理所有数据文件路径
- **MODIFIED** `more_page.py`：搜索历史路径改用 path_resolver
- **MODIFIED** `setting_page.py`：settings_file 路径改用 path_resolver
- **MODIFIED** `download_history.py`：下载历史路径改用 path_resolver
- **MODIFIED** `core/cache/clipboard_monitor.py`：日志输出改用 `log` 函数
- **DELETED** `core/settings.json`（重复文件）
- **DELETED** `core/runtime/` 目录（重复目录）

## Impact

- Affected specs: 路径解析、缓存管理、设置管理
- Affected code: 所有使用 `runtime/` 或 `settings.json` 的模块

## ADDED Requirements

### Requirement: 统一路径解析器

系统 SHALL 提供 `core/infrastructure/path_resolver.py` 模块，集中管理所有数据文件路径，包括：
- 项目根目录（通过 `__file__` 向上追溯得到）
- 设置文件路径：`runtime/settings/settings.json`
- 缓存目录：`runtime/cache/`
- 日志目录：`runtime/logs/`
- 临时目录：`runtime/temp/`
- 下载历史文件：`runtime/cache/download_history.json`
- 搜索历史文件：`runtime/cache/search_history.json`
- URL历史文件：`runtime/cache/url_history.json`
- 下载任务文件：`runtime/cache/download_tasks.json`
- 资源列表缓存：`runtime/cache/resource_list.json`
- 缓存元数据：`runtime/cache/cache_meta.json`

#### Scenario: 获取路径
- **WHEN** 任何模块需要访问数据文件路径
- **THEN** 通过 path_resolver 提供的函数获取绝对路径

### Requirement: 目录自动创建

所有路径解析函数 SHALL 在返回路径前确保对应目录已存在（`os.makedirs(..., exist_ok=True)`）。

## MODIFIED Requirements

### Requirement: SettingsManager 设置路径

设置文件 SHALL 存储在 `runtime/settings/settings.json`，不再使用项目根目录下的 `settings.json`。

**Migration**: 启动时自动检测旧路径（根目录 `settings.json`），若存在则迁移到 `runtime/settings/settings.json`，并删除旧文件。

### Requirement: more_page.py 搜索历史路径

搜索历史 SHALL 通过 path_resolver 获取路径，不再使用裸文件名。

### Requirement: download_history.py 下载历史路径

下载历史文件 SHALL 存储在 `runtime/cache/download_history.json`，不再依赖用户下载目录。

### Requirement: 日志路径

日志目录 SHALL 保持 `runtime/logs/`，由 log_file_handler.py 管理。

### Requirement: 缓存路径

所有缓存文件 SHALL 存储在 `runtime/cache/` 目录下，由 cache_manager.py 管理。

## REMOVED Requirements

### Requirement: core/settings.json

**Reason**: 重复文件，与根目录 settings.json 数据不一致
**Migration**: 启动时自动迁移到 runtime/settings/settings.json

### Requirement: core/runtime/ 目录

**Reason**: 与根目录 runtime/ 重复
**Migration**: 启动时迁移文件到根目录 runtime/，然后删除 core/runtime/
