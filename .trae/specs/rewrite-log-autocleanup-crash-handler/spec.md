# 日志自动清理与崩溃记录重写 Spec

## Why
当前日志模块（`core/infrastructure/logger.py`、`log_file_handler.py`）只实现了基础的多目标输出和固定 7 天的文件清理，存在以下问题：
1. 日志保留天数写死在代码里，无法关联程序设置。
2. 未捕获未处理异常，程序崩溃时无法自动记录崩溃原因与代码位置。
3. 崩溃时没有中文提示界面，用户不知道发生了什么。
4. 日志文件路径、崩溃日志路径、崩溃报告 UI 之间没有统一规范。

## What Changes
- 新增设置项 `log_retention_days`（默认 7 天）和 `log_cleanup_period`（默认 "每周"），日志清理与设置绑定。
- 重写 `core/infrastructure/logger.py`，统一日志级别映射、增加崩溃安全写入能力。
- 重写 `core/infrastructure/log_file_handler.py`，支持按设置天数/周期自动清理、按日期分片、崩溃日志独立文件。
- 新增 `core/infrastructure/crash_handler.py`，注册 `sys.excepthook`，在崩溃时记录完整 traceback 并启动崩溃提示工具。
- 新增 `gui/crash_reporter.py`（或独立可执行入口 `tools/crash_reporter.py`），中文界面展示崩溃原因、文件位置、堆栈摘要，并提供“打开日志目录”“复制错误信息”“重新启动”按钮。
- 在 `main.py` 最早期安装崩溃钩子，确保 `main.py` 自身异常也能被捕获。
- 在 `setting_page.py` 的“日志设置”分组中增加“日志保留时间”和“自动清理周期”选项。
- 同步更新 `core/infrastructure/default_settings.py`、版本号与更新日志。

## Impact
- 受影响模块：日志记录、设置管理、设置界面、主程序入口。
- 新增文件：
  - `core/infrastructure/crash_handler.py`
  - `gui/widgets/crash_reporter_dialog.py`
  - `tools/crash_reporter.py`（独立子进程入口）
- 修改文件：
  - `core/infrastructure/logger.py`
  - `core/infrastructure/log_file_handler.py`
  - `core/infrastructure/default_settings.py`
  - `core/infrastructure/path_resolver.py`（可选：新增崩溃日志目录）
  - `gui/pages/setting_page.py`
  - `main.py`
  - `core/infrastructure/version.py`
  - `.dev/产品更新信息.md`

## ADDED Requirements

### Requirement: 日志保留设置
The system SHALL 提供 `log_retention_days` 与 `log_cleanup_period` 设置项，默认值分别为 `7` 和 `"每周"`。

#### Scenario: 设置生效
- **WHEN** 用户修改日志保留天数或清理周期
- **THEN** 下次启动或定时清理时按新设置执行，过期日志文件被删除。

### Requirement: 设置驱动的日志清理
The system SHALL 在应用启动时读取 `log_retention_days` 与 `log_cleanup_period`，清理 `runtime/logs/` 中修改时间超过保留天数的文件。

#### Scenario: 正常启动
- **WHEN** 应用启动并初始化日志
- **THEN** 日志模块根据设置天数删除旧日志，并写入一条 `INFO` 记录本次清理结果。

### Requirement: 崩溃异常捕获
The system SHALL 在 `main.py` 最早可执行阶段安装全局异常钩子，捕获所有未处理异常（包括 `main.py` 自身抛出的异常）。

#### Scenario: 任意线程未处理异常
- **WHEN** 程序在主线程或 Qt 事件循环中发生未处理异常
- **THEN** 崩溃处理器将异常类型、消息、完整 traceback 写入崩溃日志，并启动崩溃提示工具。

### Requirement: 崩溃原因中文提示
The system SHALL 在崩溃时启动一个独立的中文提示窗口，显示：
- 崩溃简短原因（异常类型 + 消息）。
- 出错的文件路径与行号。
- 可展开的堆栈摘要。
- 操作按钮：打开日志目录、复制错误信息、重新启动程序、关闭。

#### Scenario: 用户查看崩溃信息
- **WHEN** 崩溃提示工具启动
- **THEN** 窗口置顶且可正常交互，崩溃日志路径为 `runtime/logs/crash_YYYYMMDD_HHMMSS.log`。

### Requirement: 日志文件安全写入
The system SHALL 在崩溃处理过程中使用仅追加模式写入崩溃日志，避免依赖已损坏的日志处理器对象；写入失败时不得再次抛异常导致进程强制终止。

## MODIFIED Requirements

### Requirement: 现有文件日志处理器
现有 `FileLogHandler` 仅支持固定 7 天清理和 RotatingFileHandler。修改后：
- 支持按日期命名的主日志文件（`app_YYYYMMDD.log`）。
- 清理逻辑读取 `log_retention_days`。
- 保留 RotatingFileHandler 按大小的备份机制。

### Requirement: 设置界面日志分组
“日志设置”分组在原有“日志级别”“调试模式”基础上，增加：
- “日志保留时间”下拉框：`1天 / 3天 / 7天 / 14天 / 30天 / 永久`。
- “自动清理周期”下拉框：`每次启动 / 每天 / 每周 / 每月`。

## REMOVED Requirements

### Requirement: 固定 7 天日志清理
**Reason**：保留天数应来自设置，不应硬编码。
**Migration**：`clean_old_logs()` 的默认 `days` 参数改为读取 `SettingsManager` 中的 `log_retention_days`，调用方显式传入天数。
