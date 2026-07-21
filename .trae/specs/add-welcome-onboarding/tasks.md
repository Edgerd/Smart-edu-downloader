# 新手引导实现任务列表

- [x] Task 1: 创建公共组件
  - [x] SubTask 1.1: 创建 `gui/components/material_checkbox.py`，实现 Material Design 3 复选框（含涟漪、填充、对勾路径动画）。
  - [x] SubTask 1.2: 创建 `gui/components/circle_nav_button.py`，实现圆形导航按钮（上一步/下一步/对号），支持禁用状态、悬浮提示、SVG 图标。
  - [x] SubTask 1.3: 创建 `docs/privacy_policy.md` 空占位文件。

- [x] Task 2: 创建引导页面
  - [x] SubTask 2.1: 创建 `gui/welcome/wizard.py` 主窗口框架，管理 9 页堆叠、淡入淡出动画、底部导航、设置持久化。
  - [x] SubTask 2.2: 创建 `gui/welcome/pages/welcome_page.py` 欢迎页（图标、名称、箭头、数据迁移、语言设置）。
  - [x] SubTask 2.3: 创建 `gui/welcome/pages/license_page.py` 许可条款页（隐私政策、MD3 复选框、反诈弹窗）。
  - [x] SubTask 2.4: 创建 `gui/welcome/pages/basic_settings_page.py` 基本设置页（下载目录、询问位置开关）。
  - [x] SubTask 2.5: 创建 `gui/welcome/pages/token_page.py` Access Token 页（输入框、打开平台、复制代码、教程文本）。
  - [x] SubTask 2.6: 创建 `gui/welcome/pages/theme_page.py` 主题设置页（复用 `InterfaceSettingTab` 主题区）。
  - [x] SubTask 2.7: 创建 `gui/welcome/pages/system_page.py` 系统快捷方式页（桌面/开始菜单复选框）。
  - [x] SubTask 2.8: 创建 `gui/welcome/pages/tutorial_page.py` 教程页 1 和 2（图片 + 文本）。
  - [x] SubTask 2.9: 创建 `gui/welcome/pages/finish_page.py` 完成页（celebration 图片、删除线文本、对号按钮）。

- [x] Task 3: 集成启动流程
  - [x] SubTask 3.1: 修改 `main.py`，在首次启动时显示 `WelcomeWizard` 模态窗口，完成后再创建主窗口。
  - [x] SubTask 3.2: 确保 `first_run` 标志在向导完成后正确写入设置。

- [x] Task 4: 添加更多页面入口
  - [x] SubTask 4.1: 修改 `gui/pages/more_page.py`，在实用工具区添加「新手教程」按钮。
  - [x] SubTask 4.2: 点击按钮时打开 `WelcomeWizard`（非首次运行模式，不修改 `first_run`）。

- [x] Task 5: 多语言支持
  - [x] SubTask 5.1: 在 `i18n/zh_CN.json` 中添加新手引导相关翻译键。
  - [x] SubTask 5.2: 同步新增键到 `i18n/en_US.json`、`i18n/ja_JP.json`、`i18n/lzh_CN.json`、`i18n/zh_TW.json`、`i18n/emo_JI.json`（初始值可用英文或复制 zh_CN，后续本地化）。

- [x] Task 6: 验证与收尾
  - [x] SubTask 6.1: 使用 `py_compile` 校验新增/修改的 Python 文件语法。
  - [x] SubTask 6.2: 运行 `python -c "import main"` 确认无导入错误。
  - [x] SubTask 6.3: 验证首次启动时向导弹出，后续启动不再弹出。
  - [x] SubTask 6.4: 验证「更多」页面按钮可重新打开向导。
  - [x] SubTask 6.5: 更新 `core/infrastructure/version.py`（Beta 10 → Beta 11）和 `.dev/产品更新信息.md`。

# Task Dependencies

- Task 2 依赖 Task 1（页面使用公共组件）。
- Task 3 依赖 Task 2（需要向导主窗口）。
- Task 4 依赖 Task 2（需要向导主窗口）。
- Task 5 可与其他任务并行，但在 Task 6 的导入测试前完成。
