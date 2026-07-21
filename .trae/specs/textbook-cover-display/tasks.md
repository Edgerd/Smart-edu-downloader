# 教材封面展示 Tasks

## Tasks

- [x] Task 1: 创建封面缓存模块 `core/cover_cache.py`
  - [x] 定义封面缓存目录路径 `runtime/temp/covers/`
  - [x] 实现 `_ensure_cover_dir()` 创建缓存目录
  - [x] 实现 `download_cover(cover_url, content_id)` 下载封面并保存到本地
  - [x] 实现 `get_cover_path(content_id)` 获取已缓存的封面路径
  - [x] 实现 `clear_expired_covers(days=7)` 清理过期封面缓存
  - [x] 所有文件操作使用绝对路径
  - [x] 下载失败时返回 None，不抛异常

- [x] Task 2: 创建封面显示控件 `gui/widgets/cover_widget.py`
  - [x] 创建 `CoverWidget` 类，继承 `QFrame`
  - [x] 固定尺寸 160x220，圆角 4px
  - [x] 实现 `load_cover(file_path)` 加载本地图片
  - [x] 实现 `load_cover_from_url(url, content_id)` 异步下载并显示
  - [x] 加载失败时显示占位符（书籍图标 + "封面" 文字）
  - [x] 加载中显示加载动画
  - [x] 图片保持比例居中显示

- [x] Task 3: 集成封面展示到主页 `home_page.py`
  - [x] 在主页右上角区域（标题下方）添加 `CoverWidget`
  - [x] 资源解析完成后，从解析结果中提取 Slide1 URL 和 contentId
  - [x] 调用 `CoverWidget.load_cover_from_url()` 触发封面下载和显示
  - [x] 无封面时显示占位符

- [x] Task 4: 集成封面展示到资源库 `resource_page.py`
  - [x] 在资源库右上角区域添加 `CoverWidget`
  - [x] 搜索结果更新时，提取第一个结果的 Slide1 和 contentId
  - [x] 调用 `CoverWidget.load_cover_from_url()` 显示封面
  - [x] 用户点击搜索结果列表项时，切换显示对应教材封面
  - [x] 无封面时显示占位符

- [x] Task 5: 启动时清理过期封面缓存
  - [x] 在 `main.py` 的 `delayed_init()` 方法中调用 `clear_expired_covers()`
  - [x] 异步执行，不阻塞启动

- [x] Task 6: 更新版本号和更新日志
  - [x] 递增 `core/infrastructure/version.py` 版本号（5.6.13 Beta 4 → 5.6.13 Beta 5）
  - [x] 在 `产品更新信息.md` 添加封面展示功能说明

# Task Dependencies

- Task 2 依赖 Task 1（封面控件需要缓存模块）
- Task 3 依赖 Task 2（主页集成需要封面控件）
- Task 4 依赖 Task 2（资源库集成需要封面控件）
- Task 5 依赖 Task 1（清理缓存需要缓存模块）
