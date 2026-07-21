# Tasks

- [x] Task 1: 实现智能输入检测与路由逻辑
  - 修改 `_smart_search_and_download` 方法，检测输入是否为 URL 链接
  - URL 链接（`http://`、`https://`、`www.` 开头）走现有下载流程，按钮不拆分
  - 中文关键词走资源库 `search_resources` 搜索流程
  - 搜索后保存结果列表到 `self._search_results`，设置 `self._current_search_index = 0`

- [x] Task 2: 实现按钮动态变换布局
  - 在 `_create_button_area` 中新增三按钮组合（默认隐藏）："就是这个！"、"上一个"、"下一个"
  - "上一个"/"下一个"按钮使用 `IconManager` 加载 `上一个_svg.svg` / `下一个_svg.svg` 图标
  - 搜索完成后调用 `_show_navigation_buttons()` 隐藏"智能检索并下载"、显示三按钮
  - 下载完成后调用 `_reset_search_buttons()` 恢复"智能检索并下载"、隐藏三按钮

- [x] Task 3: 实现搜索结果切换逻辑
  - 实现 `_navigate_next()` 方法：索引 +1，超出末尾则循环到 0
  - 实现 `_navigate_prev()` 方法：索引 -1，超出开头则循环到末尾
  - 实现 `_update_search_display()` 方法：更新封面预览（`cover_widget`）和处理结果（`result_text`）
  - 切换时封面预览区显示当前结果的封面
  - 切换时处理结果区显示当前结果的课本名称

- [x] Task 4: 实现键盘方向键快捷键
  - 在 `HomePage` 中重写 `keyPressEvent`
  - 上键（`Qt.Key_Up`）触发 `_navigate_prev()`
  - 下键（`Qt.Key_Down`）触发 `_navigate_next()`
  - 仅在 `self._search_results` 非空时生效

- [x] Task 5: 实现确认下载逻辑
  - 实现 `_confirm_search_download()` 方法
  - 从 `self._search_results[self._current_search_index]` 获取资源 URL，触发下载
  - 无选中结果时提示"请先选择一个课本"
  - 下载完成后调用 `_reset_search_buttons()` 恢复按钮状态

# Task Dependencies
- Task 2, Task 3 依赖 Task 1（需要搜索结果数据）
- Task 4 依赖 Task 3（需要导航方法）
- Task 5 依赖 Task 2, Task 3（需要按钮和选择逻辑）