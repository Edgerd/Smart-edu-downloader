# Tasks

- [ ] Task 1: 扩展默认设置与路径解析
  - [ ] SubTask 1.1: 在 `core/infrastructure/default_settings.py` 的“缓存与日志设置”分组中新增 `log_retention_days`（默认 7）和 `log_cleanup_period`（默认 "每周"）。
  - [ ] SubTask 1.2: （可选）在 `core/infrastructure/path_resolver.py` 中新增 `get_crash_logs_dir()`，统一崩溃日志目录为 `runtime/logs/crashes/`。

- [ ] Task 2: 重写日志模块
  - [ ] SubTask 2.1: 重写 `core/infrastructure/logger.py`，统一级别映射、保持单例与多 Handler 机制，新增 `log_crash_safe()` 用于崩溃时的安全写入。
  - [ ] SubTask 2.2: 重写 `core/infrastructure/log_file_handler.py`，实现按日期命名日志文件、按 `log_retention_days` 自动清理、保留按大小轮转备份。
  - [ ] SubTask 2.3: 修改 `setup_file_logging()` 与 `setup_gui_logging()`，在启动时读取设置并触发清理，记录清理结果。

- [ ] Task 3: 实现崩溃捕获与记录
  - [ ] SubTask 3.1: 创建 `core/infrastructure/crash_handler.py`，实现 `install_crash_handler()` 注册 `sys.excepthook`。
  - [ ] SubTask 3.2: 崩溃时解析 traceback，提取异常类型、消息、出错文件与行号，以追加模式写入 `crash_YYYYMMDD_HHMMSS.log`。
  - [ ] SubTask 3.3: 崩溃处理完成后启动崩溃提示工具，并将崩溃日志路径通过命令行参数传入。
  - [ ] SubTask 3.4: 在 `main.py` 的最早阶段（`if __name__ == '__main__':` 之后、任何 Qt/业务初始化之前）调用 `install_crash_handler()`。

- [ ] Task 4: 实现崩溃提示工具
  - [ ] SubTask 4.1: 创建 `gui/widgets/crash_reporter_dialog.py`，实现中文崩溃提示窗口：显示原因、文件/行号、可展开堆栈、操作按钮。
  - [ ] SubTask 4.2: 创建 `tools/crash_reporter.py` 作为独立子进程入口，接收 `--crash-log` 参数并显示窗口。
  - [ ] SubTask 4.3: 验证崩溃提示工具在非 Qt 主进程环境中也能独立运行。

- [ ] Task 5: 设置界面增加日志选项
  - [ ] SubTask 5.1: 在 `gui/pages/setting_page.py` 的“日志设置”分组中增加“日志保留时间”和“自动清理周期”下拉框。
  - [ ] SubTask 5.2: 将下拉框的值与设置项 `log_retention_days`、`log_cleanup_period` 双向绑定，并在保存设置时写入。

- [ ] Task 6: 版本号与更新日志
  - [ ] SubTask 6.1: 按 0.01 步长递增 `core/infrastructure/version.py` 的小版本号。
  - [ ] SubTask 6.2: 在 `.dev/产品更新信息.md` 中新增一条更新记录，说明日志自动清理、崩溃捕获与中文崩溃提示工具。

- [ ] Task 7: 验证与编译
  - [ ] SubTask 7.1: 运行 `python -m py_compile` 检查所有新增/修改文件无语法错误。
  - [ ] SubTask 7.2: 运行程序，确认启动时日志清理正常、设置项保存与读取正常、崩溃提示工具可正常弹出。

# Task Dependencies
- [Task 3] depends on [Task 2]
- [Task 4] depends on [Task 3]
- [Task 5] depends on [Task 1]
- [Task 6] depends on [Task 2] [Task 3] [Task 4] [Task 5]
- [Task 7] depends on [Task 6]
