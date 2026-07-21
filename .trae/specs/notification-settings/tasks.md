# Tasks

* [x] Task 1: 在 `core/settings_manager.py` 中新增通知相关默认设置项

  * 新增 `notification_position`（默认 `"右上"`）

  * 新增 `notification_duration`（默认 `5`，范围 1-60 秒）

  * 新增 `notification_never_hide`（默认 `False`）

  * 新增 `notification_size`（默认 `"中"`）

* [x] Task 2: 在 `gui/pages/setting_page.py` 的"界面"标签页最下方新增"🔔 通知设置"分组

  * 通知位置：下拉框（左上/右上/左下/右下）

  * 通知时长：滑块（1-60秒）+ 数字显示

  * "不自动消失"开关：开启时隐藏时长滑块，下方设置上移

  * 通知大小：下拉框（小/中/大）

  * 在 `_collect_settings` 中收集新设置项

  * 在 `_refresh_ui` 中刷新新设置项

* [x] Task 3: 修改 `gui/widgets/notification_widget.py`，使通知支持位置、大小、时长配置

  * `show_notification()` 从 `SettingsManager` 读取位置/大小/时长，动态计算屏幕坐标

  * 位置映射：左上=(20,20), 右上=(screen_w-w-20,20), 左下=(20,screen_h-h-20), 右下=(screen_w-w-20,screen_h-h-20)

  * 大小映射：小=280px, 中=320px, 大=400px

  * 时长：`never_hide=True` 时 `duration=0` 不自动关闭

* [x] Task 4: 修改 `core/sound_player.py`，下载完成音效改用 `resources/mp3/success.mp3`

  * `play_completion_sound()` 优先使用 `success.mp3` 播放

  * 若 `success.mp3` 不存在则回退到系统默认蜂鸣声

  * 增加设置自定义音效支持

* [x] Task 5: 修复 `gui/widgets/donation_dialog.py` 赞赏码图片路径

  * 将 `resources/赞赏码 请杯奶茶吧.png` 改为 `resources/images/donation_qr.png`

* [x] Task 6: 在F12调试界面增加调试标签页 先支持显示测试通知 调试功能后续完善

* [x] task 7  暂不更新版本号 

  * 更新 `产品更新信息.md` 添加变更日志