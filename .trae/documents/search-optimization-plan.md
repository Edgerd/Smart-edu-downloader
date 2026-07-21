# 搜索算法优化计划

## 摘要

优化搜索引擎算法，提升搜索精准度，删除热门搜索功能，增加"新版/新教材"别名映射。

## 当前状态分析

### 问题1：学科过滤不彻底

* 当前"大致匹配"模式下，搜索"人教版语文八年级下册"会返回所有相关资源，包括其他学科

* 学科过滤逻辑仅在 `_strict_filter`（完美匹配模式）中实现

* 需要在"大致匹配"模式下也执行学科过滤

### 问题2：热门搜索功能

* `resource_page.py` 中包含热门搜索相关代码（UI、加载、回调）

* 需要完全删除该功能

### 问题3：新版/新教材别名

* 当前 `PUBLISHER_ALIASES` 仅包含统编版/部编版→人教版的映射

* 需要增加"新版"、"新教材"→"2022年版课程标准修订"的映射

## 修改方案

### 修改1：学科自动过滤（search\_engine.py）

**文件**：`core/resource/search_engine.py`

**位置**：`search()` 方法，步骤6和步骤7之间

**修改内容**：
在评分排序后、完美匹配过滤前，增加学科过滤逻辑：

```python
# 6.5 学科自动过滤（无论哪种模式）
if search_subject:
    scored = self._filter_by_subject(keywords, scored)
```

**新增方法**：`_filter_by_subject(keywords, scored)`

* 检测搜索关键词中的学科

* 过滤掉学科不匹配的结果

* 仅当检测到学科关键词时执行

### 修改2：删除热门搜索功能（resource\_page.py）

**文件**：`gui/pages/resource_page.py`

**删除内容**：

1. 属性初始化（第60-61行）：`_hot_keywords`、`_hot_keywords_loaded`
2. 页面显示时的加载逻辑（第238-240行）
3. UI创建（第416-442行）：热门搜索标签区域
4. 加载方法（第1316-1335行）：`_load_hot_keywords()`
5. UI更新方法（第1340-1370行）：`_update_hot_keywords_ui()`
6. 点击回调（第1372-1373行）：`_on_hot_keyword_clicked()`

### 修改3：新版/新教材别名映射（search\_engine.py）

**文件**：`core/resource/search_engine.py`

**位置**：`PUBLISHER_ALIASES` 常量（第231-238行）

**修改内容**：

```python
PUBLISHER_ALIASES: Dict[str, str] = {
    '统编版': '人教版',
    '统编': '人教版',
    '部编版': '人教版',
    '部编': '人教版',
    '人教版': '人教版',
    '新版': '2022年版课程标准修订',
    '新教材': '2022年版课程标准修订',
}
```

**注意**：`PUBLISHER_ALIASES` 的用途是版本别名映射，但"新版/新教材"实际上是指"2022年版课程标准修订"的课本。需要在 `_repair_search_term` 方法中特殊处理这些别名，将其转换为搜索关键词的一部分。

**修改** **`_repair_search_term`** **方法**：
在提取版本信息后，检查是否有"新版"或"新教材"关键词，如果有，将其转换为"2022年版课程标准修订"并添加到搜索词中。

### 修改4：删除搜索结果缓存

**原因**：搜索结果缓存可能导致数据不一致，且占用额外内存，删除后每次搜索都获取最新数据。

**文件**：`core/resource/search_cache.py`
- 删除整个文件

**文件**：`core/resource/search_engine.py`

**删除内容**：
1. 删除 `from core.resource.search_cache import SearchCache` 导入
2. 删除 `self._cache = SearchCache()` 初始化
3. 删除 `search()` 方法中的缓存检查逻辑（步骤1）
4. 删除 `search()` 方法中的缓存写入逻辑（步骤11）
5. 删除 `invalidate_cache()` 方法
6. 删除 `cache` 属性

**文件**：`core/resource/resource_library.py`
- 检查是否有调用 `invalidate_cache()` 的代码，如有则删除

## 验证步骤

1. 运行单元测试：`python .dev/tests/test_search_engine.py`
2. 启动程序验证无报错：`python main.py`
3. 测试搜索"人教版语文八年级下册"，确认结果仅包含语文相关资源
4. 测试搜索"新版数学"，确认能匹配到包含"2022年版课程标准修订"的课本

