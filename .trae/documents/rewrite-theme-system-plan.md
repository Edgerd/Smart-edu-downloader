# 主题色系统重写计划

## 1. Summary

将当前独立的 `theme_color`（标题栏/导航栏）与 `accent_color`（按钮/高亮/标题文字）合并为单一主题配置。设置界面不再暴露两个颜色选择器，改为展示「主题名 + 主题色 + 背景色」的预设列表，并支持「自定义」主题的 HSL/不透明度/渐变开关调节。

## 2. Current State Analysis

- `core/config/theme_config.py`：已创建，内置 9 种预设 + 自定义，提供 `get_theme_config`、`primary_color`、`background_color`、`title_bar_gradient`、`build_custom_config` 等接口。
- `core/infrastructure/default_settings.py`：`theme_color` 已改为字典，`accent_color` 已删除。
- `gui/styles.py`：已新增 `load_theme_color`、`load_primary_color`、`load_background_color`；保留 `load_accent_color()` 作为兼容别名。
- `gui/managers/settings_handler.py`：`apply_theme_colors` 已支持渐变、不透明度、内容区背景色。
- `gui/main_window.py`：`_apply_styles` 和 `_toggle_theme` 已使用新的主题配置字典。
- `gui/pages/settings/tabs/interface_tab.py`：已重写为主题预设卡片网格 + 自定义调节区域，但 `_slider_layout` 方法存在 bug。
- `core/config/settings_manager.py`：**尚未** 在 `_load()` 中调用旧设置迁移。
- `gui/pages/setting_page.py`：**尚未** 适配新主题配置，仍保留 `accent_color` 相关逻辑。
- 全局约有 30+ 处仍直接调用 `load_accent_color()` 或引用 `self._accent_color`。
- i18n 语言包：**尚未** 添加新的主题相关键。

## 3. Proposed Changes

### 3.1 修复 `gui/pages/settings/tabs/interface_tab.py`

- 修复 `_slider_layout(self, slider, value_label)`：当前实现无法正确拿到标签文本，应改为接收 `label` 参数，返回包含 `label`、`slider`、`value_label` 的水平布局。
- 同步修改 `_create_custom_theme_section` 中的调用，传入对应的 `QLabel`。
- 主题卡片选中边框颜色从硬编码 `#2078DA` 改为使用 `primary_color(self._theme_config)`，避免子组件硬编码主题色。

### 3.2 修改 `gui/pages/setting_page.py`

- 删除实例变量 `_accent_color`，保留 `_theme_config`（已在 interface_tab 中维护）。
- 修改 `_build_callbacks`：
  - 删除 `"choose_theme_color"`、 `"choose_accent_color"`。
  - 新增 `"theme_preset_selected"` → `_on_theme_preset_selected(config)`。
  - 新增 `"custom_theme_changed"` → `_on_custom_theme_changed(config)`。
- 新增 `_on_theme_preset_selected(config)`：
  - 更新 `self._theme_config`。
  - 立即应用主题到主窗口（调用 `self.settings_handler.apply_theme_colors`）。
- 新增 `_on_custom_theme_changed(config)`：
  - 更新 `self._theme_config`。
  - 立即应用主题到主窗口。
- 修改 `_collect_settings`：删除 `self.settings["accent_color"]`，只写入 `self.settings["theme_color"] = self._theme_config`。
- 修改 `_refresh_all_tabs`：
  - 头部标题颜色改为 `primary_color(self._theme_config)`。
  - `tab_widget.setAccentColor` 同样改为主色。
  - 删除对 `set_accent_color` 的调用（保留接口兼容性，但颜色来源改为主色）。
- 修改 `_create_header` 和 `_create_save_buttons`：颜色来源改为主色。
- 删除 `_choose_theme_color`、`_choose_accent_color` 方法。
- 删除/修改 `_update_color_button` 中的 `load_accent_color()` 调用。

### 3.3 兼容旧设置：`core/config/settings_manager.py`

- 在 `_load()` 中读取 `saved` 后、赋值给 `self._settings` 前，调用 `theme_config.migrate_old_theme_settings(saved)`。
- 迁移后若设置有变更，自动保存一次。

### 3.4 全局替换 `accent_color`/`load_accent_color`

对以下文件进行最小化替换，改为 `load_primary_color()` 或 `primary_color(get_theme_config(settings))`：

- `gui/components/nav_bar.py`
- `gui/widgets/system_tray.py`
- `gui/widgets/material_button.py`
- `gui/widgets/switch_button.py`
- `gui/widgets/custom_context_menu.py`
- `gui/widgets/material_menu.py`
- `gui/widgets/donation_dialog.py`
- `gui/widgets/crash_reporter_dialog.py`
- `gui/widgets/notification_widget.py`
- `gui/widgets/ios_progress_bar.py`
- `gui/widgets/ios_download_item.py`
- `gui/widgets/page_header.py`
- `gui/widgets/cover_widget.py`
- `gui/widgets/download_dir_dialog.py`
- `gui/pages/home_page.py`
- `gui/pages/download_page.py`
- `gui/pages/resource_page.py`
- `gui/pages/more_page.py`
- `gui/pages/about_dialog.py`
- `gui/debug_panel.py`
- `gui/components/debug/**/*.py`

替换策略：
- `from gui.styles import load_accent_color` → `load_primary_color`。
- `self._accent_color = load_accent_color()` → `self._accent_color = load_primary_color()`（变量名可保留，减少diff）。
- `settings.get("accent_color", ...)` → `primary_color(get_theme_config(settings))`。

保留 `gui/styles.py` 中的 `load_accent_color()` 作为兼容别名，避免未在计划内顾及的调用点崩溃。

### 3.5 更新 i18n 多语言包

在 `i18n/zh_CN.json`、`i18n/en_US.json`、`i18n/ja_JP.json`、`i18n/lzh_CN.json`、`i18n/emo_JI.json` 中新增：

```json
{
  "settings.interface.theme_settings": "🎨 主题设置",
  "settings.interface.theme_preset": "主题预设",
  "settings.interface.custom_theme": "自定义主题",
  "settings.interface.hue": "色调",
  "settings.interface.saturation": "饱和度",
  "settings.interface.lightness": "亮度",
  "settings.interface.opacity": "不透明度",
  "settings.interface.use_gradient": "标题栏渐变",
  "settings.interface.preview": "标题栏预览",
  "theme.preset.xuansuhei": "玄素黑",
  "theme.preset.tieganfen": "铁杆粉",
  "theme.preset.shenmizi": "神秘紫",
  "theme.preset.ouhuangcai": "欧皇彩",
  "theme.preset.qiuyijin": "秋议金",
  "theme.preset.huoyuecheng": "活跃橙",
  "theme.preset.tiaopiaohong": "跳票红",
  "theme.preset.jikelan": "极客蓝",
  "theme.preset.xingkonglan": "星空蓝",
  "theme.preset.custom": "自定义"
}
```

保留旧的 `settings.common.select_theme_color` / `select_accent_color` 键作为兼容（其他代码可能仍引用，待后续清理）。

### 3.6 版本与更新日志

- 当前版本为 `5.6.16 Beta 8`，本次为正式功能重写，计划发布为 `5.6.17`（按 0.01 步长升级小版本号）。
- 更新 `.dev/产品更新信息.md`，记录：主题色与强调色合并、9 种内置主题预设、自定义主题 HSL/不透明度/渐变支持、旧设置自动迁移。
- 更新 `core/infrastructure/version.py` 中的版本号。

## 4. Migration Strategy

1. 首次启动时，`settings_manager._load()` 检测 `theme_color` 类型。
2. 若是字符串，按如下规则映射：
   - `#2078DA`、`#1277DD`、`#1A82E2` → 极客蓝
   - `#2ECC71` → 活跃橙
   - 其他 → 自定义 preset，base 为该字符串，background 自动派生
3. 删除 `accent_color` 键。
4. 保存迁移后的设置文件。

## 5. Verification Steps

1. 运行 `python -m compileall -q .` 全项目编译通过。
2. 运行 `python .dev/test/test_imports.py` 所有模块导入正常。
3. 启动程序，进入设置 → 界面，确认：
   - 显示 10 个主题预设卡片。
   - 点击不同预设，标题栏/导航栏/内容区背景实时变化。
   - 选择「欧皇彩」时标题栏呈现 #7349C2 → #BB3E68 渐变。
   - 选择「自定义」时显示 HSL/不透明度/渐变开关，拖动滑块实时预览。
   - 保存设置后重启，主题保持。
4. 旧设置文件测试：手动构造包含 `"theme_color": "#2078DA"` 和 `"accent_color": "#2078DA"` 的 `settings.json`，启动后确认自动迁移为新格式且界面正常。
5. 主界面主题切换快捷键/按钮循环切换 9 个内置预设。

## 6. Assumptions & Decisions

- **只保留 `theme_color` 一个设置项**：`accent_color` 完全删除，所有强调色统一使用主题配置的 `primary`。
- **背景色自动派生**：自定义主题下背景色由 `primary` 自动亮化生成，用户不直接选择背景色。
- **自定义调节维度**：色相(0-360) + 饱和度(0-100) + 亮度(0-100) + 不透明度(0-255) + 渐变开关。
- **渐变支持**：每个预设可独立配置 `gradient`，普通预设为 `None`；自定义预设默认无渐变，用户可开启。
- **欧皇彩特殊处理**：`primary` 用于按钮/标题文字，`gradient` 仅用于标题栏/导航栏背景。
- **兼容别名保留**：`gui/styles.py` 中的 `load_accent_color()` 保留，避免一次性全局崩溃；新代码使用 `load_primary_color()`。
