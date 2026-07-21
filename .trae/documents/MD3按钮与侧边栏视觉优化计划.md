# MD3 按钮与侧边栏视觉优化计划

## 1. Summary（概述）

本次任务针对当前项目中 MD3 风格按钮与侧边栏导航存在的视觉与交互问题进行统一优化，核心目标：

1. 将设置界面（`setting_page.py`）中所有普通 `QPushButton` 替换为 `MaterialButton`，统一高度、圆角与水波纹动效。
2. 将设置侧边栏（`VerticalTabWidget`）标签按钮改为“左侧贴边、右侧圆角”的 Chrome 设置风格胶囊形，并添加水波纹与悬浮阴影。
3. 创建独立颜色计算模块，实现“主题色淡化”水波纹算法：深色主题变浅、浅色主题略微加深。
4. 修复按钮阴影在水波纹动画期间时隐时现的 Bug，将阴影统一改为只在鼠标悬浮时显示，并推广到主程序所有按钮。

## 2. Current State Analysis（现状分析）

| 文件 | 当前问题 |
|------|----------|
| `gui/widgets/material_button.py` | ① 默认高度 40px，但图标按钮/FAB 已固定；② 水波纹颜色基于背景亮度简单选择黑白，未按主题色淡化；③ 阴影在 `pressed` 时关闭、有水波纹时 `update()` 重绘导致阴影效果抖动/时隐时现；④ 普通 `MaterialButton` 默认 elevation 为 0，只有 hover 才有阴影，但 pressed 逻辑仍会影响阴影开关。 |
| `gui/pages/setting_page.py` | ① 保存/导入/导出/重置按钮高度仅 28–30px，且使用 `QPushButton + 样式表`，无水波纹；② 浏览/添加/删除/清空/颜色选择等按钮同样为普通 `QPushButton`；③ `_get_button_style` 圆角当前为 20px，用户反馈过大。 |
| `gui/widgets/vertical_tab_widget.py` | ① 标签按钮为普通 `QPushButton`，样式表圆角 12px，整体在侧边栏内部留边距，未延伸至边缘；② 无自定义绘制，无水波纹；③ 主题色硬编码为 `#2078DA`，无法跟随主题切换。 |
| 颜色计算 | 颜色工具分散在 `material_button.py`、`setting_page.py`、`home_page.py`、`styles.py` 中，没有统一模块，算法也不一致（有的按 RGB 减法，有的按比例混合）。 |

## 3. Proposed Changes（具体改动）

### 3.1 新增颜色计算模块 `gui/utils/color_utils.py`

**What/How：**
- 创建 `gui/utils/__init__.py` 与 `gui/utils/color_utils.py`。
- 提供统一函数：
  - `hex_to_rgb(hex_color) -> Tuple[int, int, int]`
  - `rgb_to_hex(r, g, b) -> str`
  - `lighten(hex_color, percent) -> str`：按比例向白色混合。
  - `darken(hex_color, percent) -> str`：按比例向黑色混合。
  - `mix(color1, color2, weight) -> str`：两色线性混合。
  - `ripple_tint(base_color, mode="auto", lighten_percent=18, darken_percent=12) -> str`：根据主题色亮度返回淡化色。当 `base_color` 为深色时返回 `lighten(base_color, lighten_percent)`；当为浅色时返回 `darken(base_color, darken_percent)`；亮度阈值取 128。
- 所有函数标注类型提示、docstring，异常处理时返回原色。

**Why：**
- 集中管理颜色算法，避免 UI 文件中重复实现；满足用户“创建一个专门的颜色计算模块”的要求；为后续主题系统扩展提供基础。

### 3.2 重构 `gui/widgets/material_button.py`

**What/How：**
1. **水波纹颜色**：移除内嵌 `_lighten/_darken/_mix/_ripple_color_for`，改为从 `gui.utils.color_utils` 导入 `ripple_tint` 与 `mix`。`_update_style()` 中根据变体传入合适的 base_color：
   - `filled` → `accent_color`
   - `tonal` → `container_color`
   - `outlined/text/elevated` → `accent_color`
   使用 `ripple_tint(base_color)` 得到淡化主题色。
2. **按钮高度**：保留 `setFixedHeight` 接口；将普通 `MaterialButton` 默认高度从 40 调整为用户可接受的 36（设置页的小按钮可显式设为 32，主按钮设为 36/40）。
3. **阴影逻辑**：
   - 默认 `_elevation = 0`；`_hover_elevation` 保持 2（filled/tonal/elevated）或 0（outlined/text）。
   - `_update_shadow()` 中移除 `pressed` 分支对阴影的关闭；仅当 `hovered` 时启用 `_hover_elevation`，否则启用 `_elevation`。`disabled` 时关闭。
   - 修复 `mousePressEvent/mouseReleaseEvent` 中 `_pressed` 变化时不必触发 `_update_shadow()`，避免水波纹重绘与阴影刷新冲突。
   - 去除 `QGraphicsDropShadowEffect` 在水波纹动画 `update()` 期间的频繁开关，改为只在 `enterEvent/leaveEvent/setEnabled` 中更新阴影。
4. **图标模式文字绘制**：已支持 `_icon_mode`，保持无水平 padding；普通按钮字号按高度自适应（≥40→14，≥32→12，<32→10）。
5. **MaterialIconButton/FAB**：默认圆角保持 12/16，阴影跟随 `_base_button`；父按钮透传 `setEnabled`。

**Why：**
- 消除阴影与水波纹动画冲突的闪烁；让水波纹颜色真正体现主题色淡化效果；让按钮默认更紧凑。

### 3.3 重构 `gui/widgets/vertical_tab_widget.py`

**What/How：**
1. 将标签按钮改为自定义 `MaterialTabButton`（继承 `QPushButton` 自绘制，或直接使用 `MaterialButton` 并调整形状）。
   - 采用 `QPainterPath` 绘制左直角、右圆角的胶囊形状（`border-top-left-radius: 0, border-bottom-left-radius: 0, border-top-right-radius: 20, border-bottom-right-radius: 20`）。
   - 按钮布局占满侧边栏宽度，左右不留 margin；右侧留出小间隙避免与内容区重叠。
   - 高度统一 40px。
2. **水波纹**：复用 `gui.utils.color_utils.ripple_tint` 计算当前背景色的淡化波纹色。
3. **阴影**：只在悬浮时添加轻微右侧阴影（`QGraphicsDropShadowEffect`，offset_x=2, blur=6, alpha=30）。
4. **主题色跟随**：对外暴露 `setAccentColor(color)` 方法；`SettingPage` 初始化后调用一次，将当前 `accent_color` 传入。
5. 保留未选中/选中/悬浮/按下状态：
   - 未选中：透明背景，`#666666` 文字，悬浮时背景为 `mix(white, accent_color, 0.08)`。
   - 选中：背景 `accent_color`，白色文字。
   - 按下：背景加深/变浅（根据亮度）。
   - 水波纹：基于当前背景色淡化。

**Why：**
- 实现用户截图所示的 Chrome 设置侧边栏选中效果；让侧边栏按钮也有 Material 水波纹与悬浮阴影。

### 3.4 重构 `gui/pages/setting_page.py`

**What/How：**
1. **统一按钮组件**：将所有 `QPushButton("浏览...")`、`QPushButton("添加")`、`QPushButton("删除")`、`QPushButton("清空")`、`QPushButton("浏览")`、`QPushButton("🌐 打开云平台获取 Token")`、`QPushButton("📋 一键复制代码")`、`QPushButton("🗑️ 清除浏览历史")`、`QPushButton("📥 导入配置")`、`QPushButton("📤 导出配置")`、`QPushButton("🔄 恢复默认")`、`QPushButton("💾 保存设置")` 替换为 `MaterialButton`。
2. **高度调整**：
   - 保存按钮：36px（主按钮）。
   - 导入/导出/重置：32px。
   - 浏览/添加/删除/清空：28–32px 根据空间调整。
   - 隐私页“打开云平台”等：36px。
3. **颜色与变体映射**：
   - 主按钮/保存/打开云平台：`MaterialButton.VARIANT_FILLED`，`accent_color`。
   - 导入/导出/浏览/添加/复制代码：`MaterialButton.VARIANT_TONAL` 或 `VARIANT_OUTLINED`，传入对应强调色。
   - 删除/清空/恢复默认：红色强调色，`VARIANT_OUTLINED` 或 `VARIANT_FILLED`。
4. **颜色选择按钮**：保留 `QPushButton` 作为颜色预览方块（无需水波纹），但降低尺寸至 28×28 并微调样式。
5. **移除/替换 `_get_button_style` / `_get_primary_button_style`**：删除旧的样式表生成方法；改用 `MaterialButton` 直接设置。
6. **导入调整**：从 `gui.widgets.material_button` 导入 `MaterialButton`；从 `gui.utils.color_utils` 导入需要的颜色函数，替换内嵌 `_lighten_color/_darken_color`。
7. **侧边栏主题同步**：在 `_init_ui()` 最后调用 `self.tab_widget.setAccentColor(self._accent_color)`。

**Why：**
- 设置界面按钮获得统一 MD3 外观、水波纹与悬浮阴影；降低高度避免臃肿。

### 3.5 更新 `gui/styles.py`

**What/How：**
1. 将 `create_styled_button` 内部使用的颜色工具替换为 `gui.utils.color_utils`。
2. 将 `darken_color` 标记为弃用或删除，统一使用 `color_utils.darken`。
3. 保留 `load_accent_color()` 作为主题色统一入口。

**Why：**
- 避免项目中存在两套颜色算法，确保所有 UI 组件颜色一致。

### 3.6 验证与清理

**What/How：**
- 对修改后的文件运行 `python -m py_compile` 语法检查。
- 运行 `python main.py` 或 `python -m gui.widgets.material_button` 验证：
  - 设置页按钮有水波纹、悬浮阴影。
  - 侧边栏按钮为左方右圆、贴边、有水波纹。
  - 水波纹颜色为主题色淡化，深色按钮变浅、浅色按钮变深。
  - 点击按钮时阴影稳定，不随水波纹闪烁。
- 删除 `material_button.py` 和 `setting_page.py` 中内嵌的 `_lighten/_darken/_mix/_ripple_color_for/_lighten_color/_darken_color` 等冗余私有方法。

## 4. Assumptions & Decisions（假设与决策）

1. **按钮高度**：设置页主按钮统一 36px，辅助按钮 32px，小操作按钮 28–32px。若用户希望更矮，可在实现时进一步下调。
2. **侧边栏形状**：采用“左侧 0 圆角、右侧 20px 圆角”的胶囊形，并延伸至侧边栏左边缘，与 Chrome 设置截图一致。
3. **阴影策略**：默认不显示阴影，仅在悬浮时显示；disabled 状态无阴影。所有 `MaterialButton` 及其变体统一遵循此策略。
4. **颜色模块位置**：放在 `gui/utils/color_utils.py`，因为当前项目没有 `utils` 包，且颜色计算主要服务于 UI 层。后续若核心层也需要可迁移到 `core/utils`。
5. **普通 `QPushButton` 处理**：`nav_bar.py`、`title_bar.py` 中的导航/控制按钮保持原样（它们已有统一样式且非 MD3 按钮）。若用户后续要求也可替换，本次不纳入范围。

## 5. Verification Steps（验证步骤）

1. `python -m py_compile gui/utils/color_utils.py gui/widgets/material_button.py gui/widgets/vertical_tab_widget.py gui/pages/setting_page.py gui/styles.py` 无报错。
2. `python -m gui.widgets.material_button` 演示窗口中点击各变体按钮，水波纹颜色为淡化主题色，阴影在悬浮时出现，点击期间不闪烁。
3. `python main.py` 启动后进入设置页：
   - 左侧标签按钮左直右圆、贴边、悬浮/点击有水波纹。
   - 底部保存/导入/导出/重置按钮高度统一，点击有水波纹与悬浮阴影。
   - 各分组内浏览/添加/删除等按钮同样有水波纹。
4. 切换不同主题色（若支持）后侧边栏与按钮颜色同步变化。
