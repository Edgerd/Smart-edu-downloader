# Checklist

* [x] `settings_manager.py` 包含 `notification_position`、`notification_duration`、`notification_never_hide`、`notification_size` 默认值

* [x] 设置页面"界面"标签页最下方显示"🔔 通知设置"分组，包含位置下拉框、时长滑块、不消失开关、大小下拉框

* [x] 开启"不自动消失"开关时，时长滑块隐藏，下方设置上移

* [x] 关闭"不自动消失"开关时，时长滑块重新显示

* [x] 保存设置后通知位置/大小/时长正确写入 `settings.json`

* [x] 通知弹窗根据设置的位置出现在屏幕对应角落

* [x] 通知弹窗宽度根据设置的大小（小/中/大）正确变化

* [x] 通知时长=0（不消失）时，通知不会自动关闭

* [x] 通知时长>0 时，通知在指定秒数后自动消失

* [x] 下载完成音效播放 `resources/mp3/success.mp3`

* [x] 支持下载自定义音效

* [x] `success.mp3` 不存在时回退到系统默认蜂鸣声

* [x] 赞赏码对话框加载 `resources/images/donation_qr.png` 显示图片

* [x] `产品更新信息.md` 包含本次变更日志

* [x] 在F12调试界面增加调试标签页 先支持显示测试通知

* [x] 所有文件 `py_compile` 通过