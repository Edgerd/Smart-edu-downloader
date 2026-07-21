# 修复通知位置显示异常 Spec

## Why
通知弹窗在左下和右下位置显示异常，原因是 `show_notification()` 方法在 `show()` 之前就调用 `self.height()` 获取高度，此时窗口未布局完成，高度为0或不正确，导致 Y 轴坐标计算错误，通知显示在屏幕侧边中间而非预期角落。

## What Changes
- 修改 `gui/widgets/notification_widget.py` 的 `show_notification()` 方法
- 调整顺序：先 `show()` 让窗口布局计算完成，再获取实际高度并计算位置，最后 `move()` 到正确坐标
- 确保所有四个位置（左上/右上/左下/右下）都能正确显示在屏幕角落，且在任务栏上方

## Impact
- Affected specs: notification-settings（已完成，本 spec 修复其遗留的位置计算 bug）
- Affected code: `gui/widgets/notification_widget.py` 的 `show_notification()` 方法

## MODIFIED Requirements

### Requirement: 通知位置计算
通知弹窗 SHALL 在显示后获取实际尺寸，再计算屏幕坐标，确保四个角落位置都正确显示。

#### Scenario: 左下位置显示
- **WHEN** 通知位置设置为"左下"
- **THEN** 通知显示在屏幕左下角，任务栏上方，与屏幕边缘保持 20px 间距

#### Scenario: 右下位置显示
- **WHEN** 通知位置设置为"右下"  
- **THEN** 通知显示在屏幕右下角，任务栏上方，与屏幕边缘保持 20px 间距

#### Scenario: 左上位置显示
- **WHEN** 通知位置设置为"左上"
- **THEN** 通知显示在屏幕左上角，与屏幕边缘保持 20px 间距

#### Scenario: 右上位置显示
- **WHEN** 通知位置设置为"右上"
- **THEN** 通知显示在屏幕右上角，与屏幕边缘保持 20px 间距
