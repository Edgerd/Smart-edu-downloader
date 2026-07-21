# 教材封面展示 Spec

## Why

当前主页和资源库页面在解析教材资源后，仅展示文字信息（标题、学科、年级等），缺少直观的封面图片展示。用户需要通过文字来判断教材，体验不够直观。资源列表 JSON 中每本书都包含 `preview` 字段（含 Slide1~SlideN 的图片 URL），其中 Slide1 就是教材封面。

## What Changes

- 主页右上角区域新增教材封面展示框
- 资源库右上角区域新增教材封面展示框
- 新增封面下载与缓存逻辑（从 Slide1 下载，缓存到 runtime/temp/）
- 资源解析完成后自动提取 Slide1 并触发封面下载与显示
- 无封面时显示占位符（如书籍图标或默认图片）

## Impact

- **Affected code**:
  - `gui/pages/home_page.py` — 右上角封面展示框
  - `gui/pages/resource_page.py` — 右上角封面展示框
  - `core/cover_cache.py` — 新增封面下载与缓存模块
  - `gui/widgets/cover_widget.py` — 新增封面显示控件
  - `core/cache_manager.py` — 新增封面缓存路径定义
  - `core/version.py` — 递增版本号
  - `docs/产品更新信息.md` — 添加更新日志

## ADDED Requirements

### Requirement: 封面缓存模块

系统 SHALL 提供 `core/cover_cache.py` 模块，负责封面的下载、缓存、读取。

- 缓存目录：`runtime/temp/covers/`
- 缓存键：使用教材 contentId（从资源数据中获取）
- 缓存格式：`.jpg` 或 `.png`（保持原始格式）
- 缓存过期策略：7 天自动清理过期封面文件
- 线程安全：支持多线程并发下载不同封面

#### Scenario: 下载封面并缓存

- **WHEN** 资源解析完成后传入教材 contentId
- **THEN** 从 Slide1 URL 下载封面图片，保存到 `runtime/temp/covers/{contentId}.jpg`

#### Scenario: 读取已缓存的封面

- **WHEN** 封面已存在且未过期
- **THEN** 直接返回本地文件路径，不发起网络请求

#### Scenario: 下载失败回退

- **WHEN** 网络请求失败或 Slide1 URL 无效
- **THEN** 返回 None，UI 显示占位符

### Requirement: 封面显示控件

系统 SHALL 提供 `gui/widgets/cover_widget.py` 封面显示控件，用于在主页和资源库展示封面。

- 支持加载本地图片文件和占位符
- 支持圆角边框（4px）
- 固定尺寸：宽 160px，高 220px（可配置）
- 加载中显示加载动画（如旋转指示器或占位文字）
- 图片保持原始比例，居中裁剪填充

#### Scenario: 成功加载封面

- **GIVEN** 封面图片已下载
- **WHEN** 控件加载该图片
- **THEN** 显示封面，带圆角边框

#### Scenario: 加载失败显示占位符

- **WHEN** 封面下载失败或图片不存在
- **THEN** 显示默认占位符（如书籍图标 + "封面" 文字）

### Requirement: 主页封面展示

主页 SHALL 在右上角区域（标题下方或侧边）显示当前选中教材的封面。

- 封面框与现有标题/按钮布局协调
- 资源解析完成后自动更新封面
- 切换教材时封面同步更新
- 无封面时显示占位符

#### Scenario: 解析完成后显示封面

- **WHEN** 用户输入 URL 并解析完成
- **THEN** 右上角显示该教材的封面图片

#### Scenario: 无封面时显示占位符

- **WHEN** 教材无 Slide1 或下载失败
- **THEN** 显示占位符，不影响其他功能

### Requirement: 资源库封面展示

资源库 SHALL 在右上角区域显示当前选中/搜索结果中第一个教材的封面。

- 与主页风格一致
- 搜索结果更新时封面同步更新
- 可切换显示搜索结果中的任意教材封面（点击列表项触发）

#### Scenario: 搜索后显示封面

- **WHEN** 用户执行搜索，搜索结果列表更新
- **THEN** 封面框显示搜索结果中第一个教材的封面

#### Scenario: 点击切换封面

- **WHEN** 用户点击搜索结果列表中的某一项
- **THEN** 封面框切换显示该教材的封面

### Requirement: 封面缓存清理

系统 SHALL 在启动时清理过期的封面缓存文件。

- 过期时间：7 天
- 清理范围：`runtime/temp/covers/` 目录下的过期文件
- 清理过程不应阻塞主线程

#### Scenario: 启动时自动清理

- **WHEN** 程序启动
- **THEN** 扫描封面缓存目录，删除超过 7 天的文件
