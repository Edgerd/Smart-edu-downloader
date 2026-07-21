# Tasks
- [x] Task 1: 创建日志文件处理器模块 `core/log_file_handler.py`
  - [x] SubTask 1.1: 实现 `FileLogHandler` 类，继承自 `LogHandler`
  - [x] SubTask 1.2: 实现日志格式化为 `[时间戳] [级别] [模块] 具体信息` 格式
  - [x] SubTask 1.3: 实现日志目录 `logs/` 自动创建逻辑
  - [x] SubTask 1.4: 实现日志写入文件功能，使用 UTF-8 编码
- [x] Task 2: 实现日志轮转机制
  - [x] SubTask 2.1: 使用 `RotatingFileHandler` 实现单文件5MB上限
  - [x] SubTask 2.2: 配置最多保留10个备份文件
  - [x] SubTask 2.3: 备份文件由 RotatingFileHandler 自动管理（数字后缀）
- [x] Task 3: 实现日志清理策略
  - [x] SubTask 3.1: 实现扫描 `logs/` 目录功能
  - [x] SubTask 3.2: 实现删除修改时间超过7天的日志文件逻辑
  - [x] SubTask 3.3: 在程序启动时自动调用清理函数
- [x] Task 4: 集成到现有日志系统
  - [x] SubTask 4.1: 在 `core/logger.py` 的 `setup_gui_logging()` 中同时初始化文件日志
  - [x] SubTask 4.2: 确保文件日志异常不影响主程序（try-except 保护）
- [x] Task 5: 验证与测试
  - [x] SubTask 5.1: 语法编译验证通过
  - [x] SubTask 5.2: 日志格式符合规范
  - [x] SubTask 5.3: 轮转机制已实现（RotatingFileHandler）
  - [x] SubTask 5.4: 清理策略已实现（clean_old_logs）

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1, Task 2, Task 3]
- [Task 5] depends on [Task 4]
