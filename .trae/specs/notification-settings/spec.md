# 通知设置增强与赞赏码路径修复 Spec

## Why
当前通知弹窗位置硬编码为右上角、时长不可配置、大小固定，且下载完成音效使用系统默认蜂鸣声而非自定义音效。用户需要更灵活的通知控制。同时赞赏码图片路径已变更导致无法显示。

## What Changes
- 设置页面新增"通知设置"分组（位于"界面"标签页最下方）
- 通知位置：支持左上/右上/左下/右下四种选择
- 通知时长：1-60秒可调，支持"不消失"开关，开关开启时隐藏时长控件
- 通知大小：支持小/中/大三种尺寸
- 下载完成音效：使用 `resources/mp3/success.mp3`，替代系统默认 `winsound.MessageBeep`
- 修复赞赏码图片路径：`resources/赞赏码 请杯奶茶吧.png` → `resources/images/donation_qr.png`

## Impact
- Affected specs: 无
- Affected code: `gui/pages/setting_page.py`, `gui/widgets/notification_widget.py`, `core/sound_player.py`, `gui/widgets/donation_dialog.py`, `core/settings_manager.py`

## ADDED Requirements

### Requirement: 通知位置设置
系统 SHALL 支持用户在设置中配置通知弹窗的显示位置（左上/右上/左下/右下），默认右上。

#### Scenario: 用户选择通知位置为左下
- **WHEN** 用户在设置中将通知位置设为"左下"
- **THEN** 后续所有通知弹窗出现在屏幕左下角

### Requirement: 通知时长设置
系统 SHALL 支持用户在设置中配置通知显示时长（1-60秒），并提供"不自动消失"开关。

#### Scenario: 用户设置通知时长为5秒
- **WHEN** 用户在设置中将通知时长设为5秒
- **THEN** 通知显示5秒后自动消失

#### Scenario: 用户开启"不自动消失"
- **WHEN** 用户开启"不自动消失"开关
- **THEN** 时长滑块隐藏，通知显示后不会自动消失，需手动点击关闭

### Requirement: 通知大小设置
系统 SHALL 支持用户在设置中配置通知弹窗的大小（小/中/大），默认中。

#### Scenario: 用户选择通知大小为"大"
- **WHEN** 用户在设置中将通知大小设为"大"
- **THEN** 后续通知弹窗使用更大的尺寸显示

### Requirement: 下载完成音效使用自定义MP3
系统 SHALL 在下载完成时播放 `resources/mp3/success.mp3` 作为提示音。

#### Scenario: 下载任务完成
- **WHEN** 下载任务完成且用户开启了下载完成音效
- **THEN** 系统播放 `resources/mp3/success.mp3`

## MODIFIED Requirements

### Requirement: 赞赏码对话框图片路径
**Migration**: 原路径 `resources/赞赏码 请杯奶茶吧.png` 已废弃，改为 `resources/images/donation_qr.png`。

#### Scenario: 显示赞赏码对话框
- **WHEN** 用户触发赞赏码显示
- **THEN** 对话框加载 `resources/images/donation_qr.png` 显示赞赏码图片