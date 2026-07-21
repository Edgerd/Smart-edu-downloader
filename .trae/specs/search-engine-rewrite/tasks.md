# Tasks

- [x] Task 1: 创建 `core/resource/search_cache.py` — 搜索缓存模块
  - [x] 1.1 实现 `SearchCache` 类：LRU 策略，最大 50 条，过期时间 5 分钟
  - [x] 1.2 实现 `get(keyword) -> Optional[List[Dict]]` 方法
  - [x] 1.3 实现 `put(keyword, results)` 方法
  - [x] 1.4 实现 `clear()` 和 `invalidate(keyword)` 方法
  - [x] 1.5 使用 `OrderedDict` 实现 LRU 淘汰

- [x] Task 2: 创建 `core/resource/search_index.py` — 倒排索引模块
  - [x] 2.1 实现 `SearchIndex` 类：构建和维护倒排索引
  - [x] 2.2 实现 `build_index(resources)` — 对标题、学科、年级、版本分词并建立倒排映射
  - [x] 2.3 实现 `query(keyword) -> List[str]` — O(1) 查询匹配的资源 ID 列表
  - [x] 2.4 实现 `update_index(resource)` — 增量更新单个资源索引
  - [x] 2.5 实现中文分词逻辑（字符级 bigram）

- [x] Task 3: 创建 `core/resource/search_filter.py` — 搜索过滤器模块
  - [x] 3.1 实现 `SearchFilter` 基类（抽象）
  - [x] 3.2 实现 `SubjectFilter` — 按学科过滤
  - [x] 3.3 实现 `GradeFilter` — 按年级过滤
  - [x] 3.4 实现 `PublisherFilter` — 按版本过滤
  - [x] 3.5 实现 `FilterFactory` — 工厂模式创建过滤器
  - [x] 3.6 实现 `CompositeFilter` — 组合多个过滤器（AND 逻辑）

- [x] Task 4: 创建 `core/resource/search_suggester.py` — 搜索建议模块
  - [x] 4.1 实现 `SearchSuggester` 类
  - [x] 4.2 实现 `get_suggestions(partial_keyword, limit)` — 基于标题的建议
  - [x] 4.3 实现历史联想：优先从搜索历史中匹配
  - [x] 4.4 实现语义扩展：将"初中"关联到"七年级/八年级/九年级"
  - [x] 4.5 实现热门关键词推荐

- [x] Task 5: 完全重写 `core/resource/search_engine.py` — 搜索引擎主类
  - [x] 5.1 实现 `SearchEngine` 单例类
  - [x] 5.2 集成 `SearchIndex`、`SearchCache`、`SearchFilter`、`SearchSuggester`
  - [x] 5.3 实现 `search(keyword)` — 完整搜索流程（缓存→索引查询→评分→过滤→排序）
  - [x] 5.4 实现 `get_suggestions(partial)` — 委托给 SearchSuggester
  - [x] 5.5 实现 `set_search_mode(mode)` — 完美/大致匹配模式切换
  - [x] 5.6 实现 `SearchHistoryManager` — 保留搜索历史功能
  - [x] 5.7 实现智能关键词修复（缩写展开、版本识别）
  - [x] 5.8 实现评分算法（标题+100、学科+80、年级+60、版本+60、多字段匹配+50）
  - [x] 5.9 实现通配符搜索（`*`、`?`）
  - [x] 5.10 实现模糊匹配（编辑距离 ≤ 2）
  - [x] 5.11 实现搜索统计（耗时、结果数）

- [x] Task 6: 适配 `core/resource/resource_library.py` 搜索接口
  - [x] 6.1 更新 `search_resources()` 方法，适配新 SearchEngine 接口
  - [x] 6.2 更新 `get_search_suggestions()` 方法
  - [x] 6.3 更新 `get_hot_keywords()` 方法
  - [x] 6.4 更新 `get_search_history()` / `clear_search_history()` 方法
  - [x] 6.5 新增 `search_resources_with_stats()` 和 `get_search_engine()` 方法

- [x] Task 7: 重构 `gui/pages/resource_page.py` 搜索 UI
  - [x] 7.1 添加搜索模式切换按钮（完美匹配/大致匹配）
  - [x] 7.2 添加搜索建议下拉列表（实时显示、键盘导航、点击选择）
  - [x] 7.3 添加搜索统计显示（耗时、结果数）
  - [x] 7.4 添加空结果智能建议（"您是不是想搜：xxx"）
  - [x] 7.5 添加热门搜索展示区域
  - [x] 7.6 添加搜索纠错提示

- [x] Task 8: 创建 `tests/test_search_engine.py` — 单元测试
  - [x] 8.1 测试 `SearchCache` 缓存命中/过期/LRU 淘汰
  - [x] 8.2 测试 `SearchIndex` 构建和查询
  - [x] 8.3 测试 `SearchFilter` 单个和组合过滤
  - [x] 8.4 测试 `SearchSuggester` 建议生成
  - [x] 8.5 测试 `SearchEngine` 完整搜索流程
  - [x] 8.6 测试完美匹配/大致匹配模式
  - [x] 8.7 测试关键词修复（缩写展开）
  - [x] 8.8 测试通配符和模糊搜索
  - [x] 8.9 测试搜索历史记录
  - [x] 8.10 33 个测试用例全部通过

- [x] Task 9: 版本号更新和更新日志
  - [x] 9.1 更新 `core/version.py` 版本号 5.6.13 Beta 8 → Beta 9
  - [x] 9.2 更新 `.dev/产品更新信息.md` 添加变更记录