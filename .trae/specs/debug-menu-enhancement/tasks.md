# Tasks

- [x] Task 1: 重命名通知测试tab为调试菜单并重构布局
  - [x] 修改tab标题从"🔔 通知测试"为"🔧 调试菜单"
  - [x] 重构_create_notification_tab方法为_create_debug_menu_tab
  - [x] 使用QScrollWidget或QGroupBox组织多个功能区块
  - [x] 保留原有通知测试功能作为第一个区块

- [x] Task 2: 实现日志级别过滤功能
  - [x] 添加日志级别复选框组(INFO/WARNING/ERROR/DEBUG/SUCCESS)
  - [x] 实现日志过滤逻辑
  - [x] 更新日志显示区域根据过滤条件动态刷新

- [x] Task 3: 实现变量监控面板
  - [x] 添加变量输入框和添加按钮
  - [x] 实现变量值获取和显示逻辑
  - [x] 添加定时刷新机制
  - [x] 支持移除监控变量

- [x] Task 4: 实现性能分析工具
  - [x] 添加性能指标显示区域(内存/CPU)
  - [x] 实现性能数据获取(psutil或platform模块)
  - [x] 添加刷新按钮和自动刷新选项

- [x] Task 5: 实现错误捕获展示
  - [x] 添加错误历史列表显示
  - [x] 实现错误捕获机制(可hook sys.excepthook)
  - [x] 显示错误时间、类型、堆栈信息
  - [x] 支持清除错误历史

# Task Dependencies
- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 1]
- [Task 5] depends on [Task 1]
