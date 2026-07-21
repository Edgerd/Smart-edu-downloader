# 资源库搜索引擎完全重写 Spec

## Why

当前 `core/resource/search_engine.py` 存在评分算法复杂、代码难以维护、智能修复效果有限、搜索建议仅基于标题匹配、大规模资源列表搜索效率低等问题。需要对搜索功能进行完全重写，实现一个架构清晰、性能优异、用户体验良好的搜索系统。

## What Changes

- **BREAKING** 完全重写 `core/resource/search_engine.py`，拆分为多模块架构
- 新增 `core/resource/search_index.py` — 倒排索引模块
- 新增 `core/resource/search_filter.py` — 搜索过滤器模块
- 新增 `core/resource/search_cache.py` — 搜索结果缓存模块
- 新增 `core/resource/search_suggester.py` — 搜索建议模块
- 重构 `core/resource/resource_library.py` 中搜索相关接口
- 重构 `gui/pages/resource_page.py` 中搜索 UI 交互
- 新增 `tests/test_search_engine.py` 单元测试

## Impact

- Affected specs: 替代 `search-algorithm-optimization`、`search-version-enhancement`（已合并其功能）
- Affected code:
  - `core/resource/search_engine.py` — 完全重写（主搜索引擎）
  - `core/resource/search_index.py` — 新增（倒排索引）
  - `core/resource/search_filter.py` — 新增（过滤器）
  - `core/resource/search_cache.py` — 新增（缓存）
  - `core/resource/search_suggester.py` — 新增（搜索建议）
  - `core/resource/resource_library.py` — 接口适配
  - `gui/pages/resource_page.py` — UI 交互适配
  - `tests/test_search_engine.py` — 新增单元测试

## ADDED Requirements

### Requirement: 模块化搜索架构
系统 SHALL 将搜索功能拆分为独立模块，遵循单一职责原则。

- `SearchEngine` — 搜索引擎主类，协调各子模块完成搜索流程
- `SearchIndex` — 倒排索引管理，构建和查询资源索引
- `SearchFilter` — 搜索过滤器，按学科/年级/版本筛选结果
- `SearchCache` — 搜索结果缓存，LRU 策略避免重复计算
- `SearchSuggester` — 搜索建议生成，基于历史、标题和语义

#### Scenario: 搜索引擎协调各模块
- **WHEN** 用户执行搜索
- **THEN** SearchEngine 先检查 SearchCache，未命中则调用 SearchIndex 查询，再通过 SearchFilter 过滤，最终返回结果

### Requirement: 倒排索引
系统 SHALL 构建倒排索引以加速搜索，支持 O(1) 关键词查找。

#### Scenario: 构建索引
- **GIVEN** 10000+ 个资源
- **WHEN** 调用 `build_index(resources)`
- **THEN** 索引构建完成，包含标题、学科、年级、版本字段的分词-资源映射

#### Scenario: 索引查询
- **GIVEN** 已构建的索引
- **WHEN** 查询关键词"数学"
- **THEN** 返回所有包含"数学"的资源 ID 列表，耗时 < 10ms

### Requirement: 多维度智能匹配
系统 SHALL 支持对资源标题、学科、年级、版本信息的多维度匹配。

#### Scenario: 标题匹配
- **WHEN** 搜索关键词命中资源标题
- **THEN** 该资源获得最高优先级权重

#### Scenario: 学科匹配
- **WHEN** 搜索关键词包含学科名（如"数学"）
- **THEN** 仅返回该学科的资源，其他学科被过滤

### Requirement: 完美/大致匹配模式切换
系统 SHALL 提供两种搜索模式，用户可切换。

#### Scenario: 完美匹配
- **WHEN** 搜索模式为"完美匹配"且搜索"冀教版 数学 八年级 下册"
- **THEN** 仅返回同时满足版本、学科、年级、册次全部条件的资源

#### Scenario: 大致匹配
- **WHEN** 搜索模式为"大致匹配"且搜索"数学"
- **THEN** 返回所有与"数学"相关的资源，按匹配度排序

### Requirement: 智能关键词修复
系统 SHALL 自动展开缩写和修复乱序关键词。

#### Scenario: 年级缩写展开
- **WHEN** 用户输入"七下"
- **THEN** 自动转换为"七年级 下册"进行搜索

#### Scenario: 学科缩写展开
- **WHEN** 用户输入"数"
- **THEN** 自动转换为"数学"进行搜索

### Requirement: 搜索历史记录
系统 SHALL 完整记录用户的搜索关键词、搜索时间和返回结果数量。

#### Scenario: 记录搜索
- **WHEN** 用户执行搜索
- **THEN** 关键词、时间戳、结果数量被持久化保存

#### Scenario: 获取历史
- **WHEN** 用户查看搜索历史
- **THEN** 返回按时间倒序排列的历史记录列表

### Requirement: 搜索建议
系统 SHALL 在用户输入过程中实时推荐相关关键词。

#### Scenario: 实时建议
- **WHEN** 用户输入"七年"
- **THEN** 显示包含"七年级"、"七年级上册"、"七年级下册"等建议

#### Scenario: 历史联想
- **WHEN** 用户输入已搜索过的关键词前缀
- **THEN** 优先显示历史搜索记录中的匹配项

### Requirement: 语义搜索
系统 SHALL 基于关键词的语义相似度进行资源匹配。

#### Scenario: 语义相似匹配
- **WHEN** 用户搜索"初中数学"
- **THEN** 返回包含"七年级数学"、"八年级数学"、"九年级数学"的资源

### Requirement: 模糊搜索
系统 SHALL 支持通配符（`*`、`?`）和模糊匹配功能。

#### Scenario: 通配符搜索
- **WHEN** 用户搜索"人教*数学"
- **THEN** 返回所有版本为"人教版"且学科为"数学"的资源

#### Scenario: 模糊匹配
- **WHEN** 用户搜索"树学"（拼写错误）
- **THEN** 返回"数学"相关的资源，并提示"您是不是想搜：数学"

### Requirement: 搜索过滤
系统 SHALL 实现按学科、年级、版本进行多维度筛选。

#### Scenario: 组合筛选
- **WHEN** 用户筛选"学科=数学"且"年级=八年级"
- **THEN** 仅返回满足两个条件的资源

### Requirement: 热门搜索
系统 SHALL 展示热门关键词排行榜。

#### Scenario: 热门关键词
- **WHEN** 用户打开搜索页面
- **THEN** 显示搜索次数最多的前 10 个关键词

### Requirement: 搜索结果缓存
系统 SHALL 设计并实现 LRU 缓存机制，避免重复搜索计算。

#### Scenario: 缓存命中
- **WHEN** 用户再次搜索相同关键词（5分钟内）
- **THEN** 直接返回缓存结果，耗时 < 5ms

#### Scenario: 缓存过期
- **WHEN** 缓存超过 5 分钟
- **THEN** 缓存项被视为过期，重新执行搜索

### Requirement: 异步搜索
系统 SHALL 支持后台搜索处理，不阻塞 UI。

#### Scenario: 异步搜索
- **WHEN** 用户点击搜索按钮
- **THEN** 搜索在后台线程执行，UI 显示加载状态，完成后通过信号更新结果

### Requirement: 搜索统计
系统 SHALL 实时显示搜索耗时和结果数量。

#### Scenario: 显示统计
- **WHEN** 搜索完成
- **THEN** 界面显示"搜索耗时 45ms，找到 23 个结果"

### Requirement: 搜索纠错
系统 SHALL 实现自动纠正拼写错误的功能。

#### Scenario: 拼写纠错
- **WHEN** 用户搜索"语数"（意图为"语文"或"数学"）
- **THEN** 系统尝试纠正并提供建议

### Requirement: 设计模式应用
系统 SHALL 应用以下设计模式：

- **策略模式**：支持多种搜索算法（精确匹配、模糊匹配、语义匹配）灵活切换
- **单例模式**：确保搜索引擎全局唯一实例
- **工厂模式**：创建不同类型的过滤器实例

### Requirement: 代码质量
系统 SHALL 满足以下代码质量标准：

- 严格遵循 PEP 8 编码规范
- 全面使用类型提示（Type Hints）
- 编写完整的 docstring 文档（PEP 257）
- 实现全面的异常捕获和日志记录
- 单元测试覆盖率达到 80% 以上

### Requirement: 性能指标
系统 SHALL 满足以下性能要求：

- 单关键词搜索耗时 < 100ms
- 支持 10000+ 资源的快速搜索
- 索引构建时间 < 500ms
- 内存占用控制在合理范围

## MODIFIED Requirements

### Requirement: resource_library.py 搜索接口
`ResourceLibrary.search_resources()` 和 `get_search_suggestions()` 方法 SHALL 适配新的搜索引擎架构，保持对外接口兼容。

## REMOVED Requirements

无。所有现有功能将被新架构覆盖。