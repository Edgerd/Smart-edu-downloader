# iOSProgressBar 组件问题修复计划

## 概述
修复 `gui/widgets/ios_progress_bar.py` 中发现的 7 个问题，涉及代码质量、潜在崩溃风险和 API 完整性。

## 当前状态分析
- 文件：`e:\hello\Smart-edu-downloader\gui\widgets\ios_progress_bar.py`
- 组件：`iOSProgressBar` 继承自 `QWidget`，自定义绘制实现 iOS 风格进度条
- 使用者：`download_page.py` (总进度条), `ios_download_item.py` (下载项进度条)

## 修复清单

### 修复 1：文字颜色硬编码 → 使用 `_text_color` 属性
**文件**: `ios_progress_bar.py`
**行**: 129, 142
**问题**: `setTextColor()` 方法无效，文字颜色被硬编码为 `#1C1C1E` 和 `#FFFFFF`
**修复**: 将第 129 行改为使用 `self._text_color`（深色文字），新增一个 `_overlay_text_color` 属性用于填充区域的白色文字，并提供 `setOverlayTextColor()` 方法

### 修复 2：动画定时器未在 reset() 中停止
**文件**: `ios_progress_bar.py`
**行**: 250-255
**问题**: `reset()` 方法没有停止 `_animation_timer`，组件销毁后可能崩溃
**修复**: 在 `reset()` 开头添加 `self._animation_timer.stop()`

### 修复 3：高亮区域越界风险
**文件**: `ios_progress_bar.py`
**行**: 114-117
**问题**: 当 `fill_width < 2` 时，`fill_width - 2` 为负数，创建非法路径
**修复**: 添加条件判断 `if fill_width > 4:` 才绘制高亮区域

### 修复 4：enterEvent / leaveEvent 未调用父类
**文件**: `ios_progress_bar.py`
**行**: 158-166
**问题**: 缺少 `super().enterEvent(event)` / `super().leaveEvent(event)`
**修复**: 在方法末尾添加 `super().enterEvent(event)` / `super().leaveEvent(event)`

### 修复 5：清理冗余变量 `_bar_height`
**文件**: `ios_progress_bar.py`
**行**: 49, 198-202
**问题**: `_bar_height` 定义但从未用于绘制逻辑
**修复**: 删除 `_bar_height` 属性定义，`setBarHeight()` 方法保留但只操作 `setFixedHeight()` 和 `update()`

### 修复 6：`_animated_value` 可能超出范围
**文件**: `ios_progress_bar.py`
**行**: 270
**问题**: 浮点累加可能导致 `_animated_value` 略微超过 `_value`
**修复**: 在 `_animate_progress` 中确保 `_animated_value` 不超过 `_value`：
```python
self._animated_value += diff * self._animation_speed
# 防止过冲
if diff > 0:
    self._animated_value = min(self._animated_value, self._value)
else:
    self._animated_value = max(self._animated_value, self._value)
```

### 修复 7：添加 `valueChanged` 信号
**文件**: `ios_progress_bar.py`
**行**: 25 (信号定义区), 168-172 (setValue 方法)
**问题**: 缺少标准 `QProgressBar` 的 `valueChanged(int)` 信号
**修复**: 
1. 添加 `valueChanged = pyqtSignal(int)`
2. 在 `setValue()` 中进度实际变化后发射信号

## 验证
- 运行应用检查进度条显示是否正常
- 检查文字颜色是否可通过 API 设置
- 确认动画不再越界
