# Material Design 右键菜单控件重写计划

## 目标
重写项目中的右键菜单控件，使其视觉风格严格符合 Google Material Design（白色背景、圆角、阴影、蓝色悬停），并附带一个可直接运行的示例窗口，演示主窗口右键点击时的水波纹反馈。

## 当前状态
- 现有右键菜单控件位于 `gui/widgets/custom_context_menu.py`，使用 Fluent 风格（`apply_menu_style`），圆角 8px、选中填充主题色。
- 项目中已有 `MaterialButton` 和 `RippleEffect` 实现，可作为水波纹参考。
- 需要把菜单改为 Material 风格，并在菜单项/触发方式上满足用户列出的具体规格。

## 计划变更

### 1. 重写 `gui/widgets/custom_context_menu.py`
保持对外静态方法 `setup_for_text_edit` / `setup_for_line_edit` 基本不变，但内部菜单构建与样式全部改为 Material Design：

- 新增私有样式方法：
  - `_apply_material_style(menu)`：设置 QSS，实现：
    - `QMenu`：背景 `#FFFFFF`，圆角 `6px`，内边距 `8px 0px`，无边框或细边框 `#E0E0E0`。
    - `QMenu::item`：上下内边距 `8px`，左右内边距 `24px`，字体 `14px`，颜色 `#202124`，背景透明。
    - `QMenu::item:selected`：背景 `#E8F0FE`，文字 `#1A73E8`。
    - `QMenu::separator`：高度 `1px`，背景 `#E0E0E0`，左右边距 `12px`。
  - `_apply_shadow(menu)`：为 `QMenu` 附加 `QGraphicsDropShadowEffect`，颜色 `rgba(0,0,0,0.2)`，模糊半径 `10`，偏移 `(0,2)`，并注释说明样式表 `box-shadow` 在部分平台无效，因此使用 effect。

- 修改 `_show_text_edit_menu` / `_show_line_edit_menu`：
  - 在创建 `QMenu` 后立即调用 `_apply_material_style` 和 `_apply_shadow`。
  - 菜单项文字保持中文（撤销、重做、剪切、复制、粘贴、删除、全选）。
  - 增加一个“更多操作”子菜单，包含两个子项（例如“复制为纯文本”、“在浏览器中打开”），子菜单同样应用 Material 样式与阴影。

- 可选：提供 `show_context_menu(parent, pos, status_label=None)` 公共静态方法，用于在任意 QWidget 上弹出示例菜单，并统一在 `status_label` 上显示“执行：复制”等提示。

### 2. 新增主窗口右键水波纹示例
在 `gui/widgets/custom_context_menu.py` 的 `__main__` 中编写完整演示：

- 创建 `QMainWindow`，中央放置一个 `QLabel` 或 QWidget，设置 `Qt.CustomContextMenu`。
- 实现 `RippleWidget`（临时浮层）：
  - 在右键点击位置绘制一个从中心扩散的半透明圆，使用 `RippleEffect` 或类似定时器动画。
  - 动画结束后自动关闭。
- `contextMenuEvent` / `customContextMenuRequested` 流程：
  1. 在点击位置显示 `RippleWidget` 并启动水波纹。
  2. 延迟约 100ms 后弹出 `MaterialContextMenu`。
  3. 菜单项触发时更新窗口底部 `QStatusBar` 或 `QLabel` 的文本，例如“执行：复制”。

### 3. 字体与依赖
- 菜单项字体优先使用项目 `gui/fonts.py` 的 `body_font()`；若导入失败则回退到系统默认无衬线字体 `QFont("Microsoft YaHei UI", 10)`。
- 仅依赖 PyQt5 标准组件和现有 `RippleEffect`，不引入第三方库。

## 验收标准
- `python gui/widgets/custom_context_menu.py` 可直接运行，弹出主窗口。
- 在主窗口任意空白区域右键：先看到水波纹扩散，随后弹出白色圆角阴影菜单。
- 菜单包含“复制、粘贴、剪切、全选、更多操作”五项，更多操作内含两个子项。
- 悬停菜单项时背景变 `#E8F0FE`，文字变 `#1A73E8`。
- 点击菜单项后，窗口状态栏显示对应操作提示。
- `python -m py_compile gui/widgets/custom_context_menu.py` 通过。

## 风险与说明
- `QGraphicsDropShadowEffect` 直接加在 `QMenu` 上时，阴影会跟随菜单矩形；若平台对顶层窗口裁剪导致圆角处阴影异常，可通过给菜单加 1px 透明外间距或调整 `setWindowFlags` 兜底。计划优先按用户要求使用 effect 实现。
- 水波纹动画为演示效果，不会污染主程序逻辑；仅作为 `__main__` 入口。
