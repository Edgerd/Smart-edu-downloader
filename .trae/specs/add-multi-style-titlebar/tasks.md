# Tasks

- [x] Task 1: 新增统一标题栏组件 `gui/components/unified_title_bar.py`
  - [x] SubTask 1.1: 实现 `UnifiedTitleBar` 类，支持 `large` 与 `compact` 两种模式
  - [x] SubTask 1.2: 大号模式复刻现有 `TitleBar` + `NavBar` 的视觉效果与信号
  - [x] SubTask 1.3: 精简模式实现标题（左）、五个导航按钮（中）、控制按钮（右）单行布局
  - [x] SubTask 1.4: 精简模式下缩小字体、图标、按钮尺寸与组件高度
  - [x] SubTask 1.5: 支持自定义标题文本与粗体/斜体字体样式

- [x] Task 2: 新增标题栏相关默认设置项
  - [x] SubTask 2.1: 在 `core/infrastructure/default_settings.py` 中添加 `title_bar_style`（默认 `large`）
  - [x] SubTask 2.2: 添加 `custom_title_text`（默认空字符串，空时按模式显示默认标题）
  - [x] SubTask 2.3: 添加 `title_font_styles`（列表，支持 `bold`、`italic`，默认空列表）

- [x] Task 3: 修改 `gui/main_window.py` 支持动态切换标题栏样式
  - [x] SubTask 3.1: 读取 `title_bar_style` 并决定创建大号或精简标题栏
  - [x] SubTask 3.2: 提供 `set_title_bar_style(style)` 方法，支持运行时切换并重建布局
  - [x] SubTask 3.3: 确保切换后当前页面、导航状态、主题色、最大化/圆角状态保持一致
  - [x] SubTask 3.4: 监听 `title_bar_style`、`custom_title_text`、`title_font_styles` 设置变更并热更新

- [x] Task 4: 在调试面板实验室中增加标题栏设置控件
  - [x] SubTask 4.1: 在 `gui/components/debug/lab_tab.py` 添加“标题栏样式”选择器（大号 / 精简）
  - [x] SubTask 4.2: 添加自定义标题输入框
  - [x] SubTask 4.3: 添加粗体、斜体复选框
  - [x] SubTask 4.4: 变更时调用主窗口接口并保存设置

- [x] Task 5: 更新国际化语言包
  - [x] SubTask 5.1: 在 `resources/i18n/zh_CN.json` 新增标题栏相关键
  - [x] SubTask 5.2: 同步更新 `resources/i18n/en_US.json`
  - [x] SubTask 5.3: 同步更新 `resources/i18n/zh_TW.json`

- [x] Task 6: 更新版本号与产品更新信息
  - [x] SubTask 6.1: 将 `core/infrastructure/version.py` 从 `5.6.17 Beta 10` 升级到 `5.6.17 Beta 11`
  - [x] SubTask 6.2: 在 `.dev/产品更新信息.md` 新增本次更新记录

- [x] Task 7: 运行验证
  - [x] SubTask 7.1: 执行 `python -m py_compile` 检查关键文件无语法错误
  - [x] SubTask 7.2: 运行程序，检查大号模式与精简模式显示正常
  - [x] SubTask 7.3: 检查标题自定义、粗体/斜体、样式切换功能正常

# Task Dependencies
- Task 3 depends on Task 1、Task 2
- Task 4 depends on Task 3
- Task 5 depends on Task 4
- Task 6 depends on Task 5
- Task 7 depends on Task 6
