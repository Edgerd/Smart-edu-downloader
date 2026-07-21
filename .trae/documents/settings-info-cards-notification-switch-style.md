# 设置页与实验菜单信息卡片化、右下角信息提示及开关样式切换实施计划

## 一、Summary

在已搭建好的基础设施之上，继续完成设置页与实验菜单的信息卡片化改造；将设置页内所有文本输入框统一替换为 qfluentwidgets `LineEdit`；新增程序窗口右下角非阻塞信息提示组件；去除设置相关代码中的 emoji；在实验菜单增加“开关样式”切换功能（Fluent 风格 / iOS 风格），默认保持程序现有内建 iOS 风格开关。

## 二、Current State Analysis

### 2.1 已完成的基础工作

- **右下角信息提示**：`gui/widgets/bottom_right_info_bar.py` 已创建，封装 qfluentwidgets `InfoBar`，支持 `success/warning/error/info` 四种类型，默认停靠父窗口右下角；`gui/main_window.py` 已新增 `show_info_toast()` 接口；`gui/widgets/__init__.py` 已导出。
- **分组卡片化**：`gui/pages/settings/components/setting_group.py` 已改为继承 `qfluentwidgets.CardWidget`，保留 `add_widget/add_layout/update_accent_color` 接口。
- **开关双风格**：`gui/widgets/switch_button.py` 已支持全局 `switch_button_style` 配置，新增 `get_switch_button_style()`、`refresh_all_switch_buttons()` 与 `SwitchWithLabel.setStyle()`；iOS 风格为默认。
- **默认配置键**：`core/infrastructure/default_settings.py` 已新增 `"switch_button_style": "ios"` 与 `"scrollbar_follow_theme": False`。
- **基类清理**：`gui/pages/settings/base_tab.py` 已移除 `QLineEdit` 样式逻辑，`update_theme_colors()` 刷新 `SwitchWithLabel`，并新增 `_create_card_group()` 便捷方法。
- **自定义辅助卡片**：`gui/pages/settings/components/` 下已创建 `SwitchWithLabelSettingCard`、`ComboBoxCard`、`RangeCard`、`LineEditCard`、`PushCard`，均继承 `qfluentwidgets.SettingCard`，分别内嵌项目内建 `SwitchWithLabel`、`NoWheelComboBox`、`NoWheelSpinBox`、`qfluentwidgets.LineEdit`、`MaterialButton`。
- **设置标签页卡片化进度**：
  - `basic_tab.py`：已完成 `SettingCardGroup` + `SwitchWithLabelSettingCard`。
  - `interface_tab.py`：已完成卡片化，`ComboBoxCard` / `RangeCard` / `SwitchWithLabelSettingCard` / `LineEditCard` / `PushCard` 已应用。
  - `download_tab.py`：大部分已完成卡片化；**域名白名单区块仍使用旧式 `SettingGroup` + 自定义控件**，需补齐为卡片形式。

### 2.2 待完成工作

- **高级设置标签页卡片化**：`gui/pages/settings/tabs/advanced_tab.py` 仍使用 `SettingGroup` + `SwitchWithLabel/NoWheelComboBox/NoWheelSpinBox/LineEdit` 平铺，需要改为 `SettingCardGroup` + 自定义辅助卡片。
- **隐私设置标签页卡片化**：`gui/pages/settings/tabs/privacy_tab.py` 仍使用 `SettingGroup` 平铺 + 行内按钮/输入框，需要改为卡片形式。
- **实验菜单改造**：`gui/components/debug/lab_tab.py` 仍使用 `QGroupBox`/`QLineEdit`/`QCheckBox`，需改为卡片化布局，并新增“开关样式”切换入口。
- **i18n 更新**：`resources/i18n/zh_CN.json` 需补充实验菜单新增键及卡片相关文案，并去除 `settings.*` 分组标题中的 emoji；其他语言包同步更新。
- **版本与日志**：版本号从 `5.6.17 Beta 13` 递增为 `5.6.17 Beta 14`，并在 `.dev/产品更新信息.md` 中记录。
- **验证**：启动程序检查设置页、实验菜单、右下角提示、开关样式切换是否正常。

## 三、Assumptions & Decisions

1. **信息提示位置**：在程序窗口右下角显示内部信息提示（非屏幕级通知），采用 qfluentwidgets `InfoBar`，停靠在主窗口/设置窗口右下角。
2. **信息卡片范围**：设置页与实验菜单的“选项分组”统一改为卡片式展示；简单开关/下拉/范围/按钮项使用 `SettingCardGroup` + 自定义辅助卡片；复杂区块（如域名白名单列表、Token 说明代码块、主题选择器）仍用 `SettingGroup(CardWidget)` 包裹，内部保留原有复杂布局。
3. **开关卡片策略**：为满足“默认使用程序内建 iOS 风格”且能一键切换为 Fluent，开关项统一使用自定义 `SwitchWithLabelSettingCard`，内部复用现有 `SwitchWithLabel`。
4. **下拉/范围/按钮/输入卡片策略**：统一使用已创建的自定义辅助卡片 `ComboBoxCard`、`RangeCard`、`PushCard`、`LineEditCard`，以保留项目内建 `NoWheelComboBox`、`NoWheelSpinBox` 等行为，同时获得 Fluent 卡片外观。
5. **开关样式切换范围**：全局生效。实验菜单中的切换会改变设置键 `switch_button_style`，所有 `SwitchWithLabel`（含自定义开关卡片内）根据该键自动渲染为 Fluent 或 iOS 风格。
6. **文本输入框**：设置页所有 `QLineEdit` 统一替换为 `qfluentwidgets.LineEdit`，保留密码框、占位符、右键菜单等行为。
7. **图标来源**：设置卡片图标统一使用 qfluentwidgets `FluentIcon`（FIF），不再使用 emoji；分组标题同步去除 emoji。
8. **版本号**：本次涉及多个界面重构与新增功能，按预发布规则递增预发布标识为 `5.6.17 Beta 14`。

## 四、Proposed Changes

### 4.1 高级设置标签页 `gui/pages/settings/tabs/advanced_tab.py`

全部改为 `SettingCardGroup` + 辅助卡片，分组标题去除 emoji。

- **代理设置**：
  - “启用代理”使用 `SwitchWithLabelSettingCard`。
  - 代理类型使用 `ComboBoxCard`（http / https / socks4 / socks5）。
  - 地址 / 端口 / 用户名 / 密码输入框使用 `LineEditCard`；密码框保持 `EchoMode.Password`。
- **缓存设置**：
  - 启用缓存：使用 `SwitchWithLabelSettingCard`。
  - 缓存大小限制、缓存清理周期：使用 `ComboBoxCard`。
- **API 设置**：
  - API 请求超时、API 重试次数：使用 `RangeCard`。
- **日志设置**：
  - 日志级别、日志保留时间、自动清理周期：使用 `ComboBoxCard`。
  - 启用调试模式：使用 `SwitchWithLabelSettingCard`。
- **搜索设置**：
  - 搜索模式：使用 `ComboBoxCard`。
  - 启用搜索建议、智能关键词修复：使用 `SwitchWithLabelSettingCard`。
  - 搜索结果最大数量：使用 `RangeCard`。
- **配置管理**：
  - 自动导出配置：使用 `SwitchWithLabelSettingCard`。
  - 导出间隔：使用 `ComboBoxCard`。

### 4.2 隐私与安全标签页 `gui/pages/settings/tabs/privacy_tab.py`

- **Access Token**：
  - 外层 `SettingGroup(CardWidget)` 包裹。
  - Token 输入框使用 `LineEditCard`，密码模式保留。
  - “打开云平台”与“复制 JS 代码”按钮改为 `PushCard`。
  - “自动保存 Token”使用 `SwitchWithLabelSettingCard`。
  - Token 帮助文本与 JS 代码块保持现有 QLabel 展示。
- **历史记录**：
  - “清除浏览历史”使用 `PushCard`。
  - 历史记录保留时间使用 `ComboBoxCard`。
  - 自动清除历史使用 `SwitchWithLabelSettingCard`。
- **安全设置**：
  - 网络请求隐私保护、安全下载模式：使用 `SwitchWithLabelSettingCard`。

### 4.3 下载设置标签页白名单区块补全 `gui/pages/settings/tabs/download_tab.py`

- 域名白名单分组改为 `SettingCardGroup` + 辅助卡片：
  - “允许下载任意域名资源”使用 `SwitchWithLabelSettingCard`。
  - “白名单外下载时弹窗确认”使用 `SwitchWithLabelSettingCard`。
- 自定义域名列表保持 `QListWidget` + `LineEdit` + 按钮的复杂布局，外层用 `SettingGroup(CardWidget)` 包裹。

### 4.4 实验菜单卡片化 + 开关样式切换 `gui/components/debug/lab_tab.py`

- 移除 `QGroupBox`，改用 `SettingGroup`（CardWidget）作为外层分组。
- **系统主题色功能区**：使用 `PushCard` 触发读取并应用系统主题色，颜色预览与色值保持 QLabel 展示。
- **标题栏实验功能区**：
  - 标题栏样式下拉改为 `ComboBoxCard`。
  - 自定义标题输入框替换为 `qfluentwidgets.LineEdit`，保持 `editingFinished` 连接。
  - 粗体/斜体复选框改为 `qfluentwidgets.CheckBox`，保持 `stateChanged` 连接。
- **滚动条跟随主题色**：使用 `SwitchWithLabelSettingCard`。
- **新增“开关样式实验”分组**：
  - 使用 `ComboBoxCard` 选择 Fluent / iOS。
  - 切换时写入 `switch_button_style` 设置并调用 `refresh_all_switch_buttons()`。
  - 通过 `BottomRightInfoBar` 或状态标签提示用户已切换。

### 4.5 i18n 更新

**文件**：`resources/i18n/zh_CN.json`

新增/更新键：
- 实验菜单新增键：
  - `debug.lab.switch_style_group`：开关样式实验
  - `debug.lab.switch_style_label`：开关按钮样式
  - `debug.lab.switch_style_fluent`：Fluent 风格
  - `debug.lab.switch_style_ios`：iOS 风格
  - `debug.lab.switch_style_applied`：已切换为 {...} 开关样式
- 去除 `settings.basic`、`settings.download`、`settings.interface`、`settings.advanced`、`settings.privacy` 中分组标题的 emoji（如 💰、📋、🌐、🖼️、🔔、🛡️ 等）。
- 各 SettingCard 的 `content` 描述文案（如需要）。

其他语言包同步更新英文键值（缺失时可先用中文占位）。

### 4.6 版本与更新日志

**文件**：`core/infrastructure/version.py`

- 更新为 `VERSION = "5.6.17 Beta 14"`，`VERSION_INFO = (5, 6, 17, 'Beta', 14)`。

**文件**：`.dev/产品更新信息.md`

在顶部新增 `5.6.17 Beta 14` 章节：
- 新增功能：程序窗口右下角信息提示；实验菜单开关样式切换（Fluent / iOS）；设置页与实验菜单信息卡片化展示。
- 优化改进：设置页文本输入框统一使用 qfluentwidgets LineEdit；去除设置相关代码 emoji。

## 五、Implementation Order

1. **高级设置卡片化**：重构 `gui/pages/settings/tabs/advanced_tab.py`。
2. **隐私设置卡片化**：重构 `gui/pages/settings/tabs/privacy_tab.py`。
3. **下载设置白名单补全**：将 `download_tab.py` 域名白名单区块改为卡片形式。
4. **实验菜单改造**：重构 `gui/components/debug/lab_tab.py`，新增开关样式切换入口。
5. **i18n 更新**：补充中文及英文键值，去除设置相关 emoji。
6. **版本与日志**：更新 `version.py` 与 `.dev/产品更新信息.md`。
7. **验证**：启动主程序，检查设置页、实验菜单、右下角提示、开关样式切换是否正常。

## 六、Verification Steps

1. 启动程序，进入设置页，确认各标签页选项以卡片形式展示，无 emoji。
2. 检查所有文本输入框（下载目录、代理地址、Token、通知音效、实验菜单自定义标题等）为 Fluent 风格 `LineEdit`，焦点边框随主题色变化。
3. 进入 F12 调试面板的“实验”标签页，确认系统主题色、标题栏、滚动条、开关样式等选项为卡片形式。
4. 在实验菜单切换“开关样式”为 Fluent，返回设置页确认开关外观变为 Fluent；切换回 iOS 恢复内建风格。
5. 触发一个右下角信息提示（例如在下载完成或设置保存后），确认提示出现在程序窗口右下角，可自动消失/手动关闭，多提示可堆叠。
6. 检查日志无异常，主题色切换后卡片、输入框、开关颜色同步更新。
7. 确认版本号与更新日志已更新为 `5.6.17 Beta 14`。
