# 日志文件存储功能规范

## Why
当前日志系统仅输出到GUI调试面板和控制台，缺少持久化存储能力，导致程序重启后无法追溯历史日志，不利于问题排查和运行状态回溯。

## What Changes
- 新增 `FileLogHandler` 日志处理器，将日志写入文件
- 实现日志轮转机制（RotatingFileHandler），防止单文件过大
- 实现7天自动清理策略，定期删除过期日志
- 日志格式统一为：`[时间戳] [级别] [模块] 具体信息`
- 支持中英文混合输出（UTF-8编码）

## Impact
- 受影响模块：`core/logger.py` - 新增文件日志处理器
- 新增目录：`logs/` - 存储日志文件
- 不影响现有GUI和Console日志输出

## ADDED Requirements

### Requirement: 日志文件存储
系统 SHALL 将日志写入文件，支持持久化存储。

#### Scenario: 程序启动时初始化文件日志
- **WHEN** 程序启动并调用日志初始化
- **THEN** 自动创建 `logs/` 目录并开始写入日志文件

### Requirement: 日志格式
系统 SHALL 使用统一格式记录日志：`[YYYY-MM-DD HH:MM:SS] [级别] [模块] 具体信息`

#### Scenario: 记录一条INFO日志
- **WHEN** 调用 `info("下载完成", module="Downloader")`
- **THEN** 日志文件内容为：`[2026-06-06 10:30:00] [INFO] [Downloader] 下载完成`

### Requirement: 日志轮转
系统 SHALL 实现日志轮转机制，单个日志文件不超过5MB，最多保留10个备份文件。

#### Scenario: 日志文件达到大小上限
- **WHEN** 当前日志文件大小达到5MB
- **THEN** 自动轮转到新文件，旧文件重命名为 `log_20260606_103000.txt` 格式

### Requirement: 日志清理
系统 SHALL 自动清理超过7天的历史日志文件。

#### Scenario: 启动时清理过期日志
- **WHEN** 程序启动并初始化日志系统
- **THEN** 扫描 `logs/` 目录，删除修改时间超过7天的日志文件

### Requirement: 日志系统可靠性
系统 SHALL 确保日志功能异常不影响主程序运行。

#### Scenario: 磁盘空间不足或权限问题
- **WHEN** 日志写入失败
- **THEN** 静默降级（停止文件日志），主程序继续正常运行
