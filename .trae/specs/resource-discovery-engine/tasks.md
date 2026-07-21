# Tasks

- [ ] Task 1: 创建资源数据模型（resource_model.py）
  - [ ] SubTask 1.1: 定义 `DiscoveredResource` 数据类，包含 resource_id、title、resource_type、download_url、teacher_name、lesson_index、lesson_title、file_extension、cover_url 字段
  - [ ] SubTask 1.2: 定义 `PageType` 枚举，包含 tch_material、sync_classroom、quality_course、prepare、lesson 五种类型
  - [ ] SubTask 1.3: 定义 `ResourceTarget` 数据类，用于描述目标资源类型（title、suffix、alias_titles）
  - [ ] SubTask 1.4: 定义 `CourseCatalog` 数据类，用于教材目录浏览（学段、学科、版本、年级、册次）

- [ ] Task 2: 创建页面类型检测器（page_type_detector.py）
  - [ ] SubTask 2.1: 实现 `detect_page_type(url)` 方法，根据 URL 路径识别 5 种页面类型
  - [ ] SubTask 2.2: 实现 `extract_resource_id(url, page_type)` 方法，从 URL 提取 contentId/resourceId/activityId/lessonId
  - [ ] SubTask 2.3: 为每种页面类型编写 URL 匹配规则测试用例

- [ ] Task 3: 创建 API 路由映射模块（api_router.py）
  - [ ] SubTask 3.1: 定义 `API_ENDPOINTS` 字典，映射页面类型到 API 端点模板
  - [ ] SubTask 3.2: 实现 `build_api_url(page_type, resource_id)` 方法
  - [ ] SubTask 3.3: 实现 `get_resource_targets(page_type)` 方法，返回该页面类型下的目标资源类型列表
  - [ ] SubTask 3.4: 定义教材目录 API 端点（tags、data_version、part_100.json 等）

- [ ] Task 4: 创建资源发现引擎（discovery_engine.py）
  - [ ] SubTask 4.1: 实现 `get_access_token()` 方法，从 HTTP 客户端获取 token
  - [ ] SubTask 4.2: 实现 `find_resource_layer(obj, target_titles)` 递归查找方法，遍历 JSON 对象查找匹配 title 的资源层
  - [ ] SubTask 4.3: 实现 `extract_pdf_url(ti_items, token)` 方法，从 ti_items 中提取 PDF 链接并附加 token
  - [ ] SubTask 4.4: 实现 `discover_from_url(url)` 方法，自动识别页面类型并发现所有资源（模式1）
  - [ ] SubTask 4.5: 实现 `discover_from_textbook_id(textbook_id)` 方法，通过教材 ID 获取关联资源（模式2）
  - [ ] SubTask 4.6: 实现 `discover_course_resources(resource_id, page_type)` 方法，发现单个课程的所有资源
  - [ ] SubTask 4.7: 实现 `get_total_lesson_count(resource_id, page_type)` 方法，获取课程总课时数
  - [ ] SubTask 4.8: 实现多课时遍历逻辑，返回完整资源列表

- [ ] Task 5: 创建教材目录浏览器（catalog_browser.py）
  - [ ] SubTask 5.1: 实现 `fetch_tags()` 方法，获取教材分类标签树
  - [ ] SubTask 5.2: 实现 `fetch_textbook_list()` 方法，获取教材列表（复用 ResourceLibrary.fetch_book_list）
  - [ ] SubTask 5.3: 实现 `browse_catalog(catalog)` 方法，根据级联选择浏览教材（模式3）
  - [ ] SubTask 5.4: 实现 `get_textbook_resources(textbook_id)` 方法，获取教材关联的课程资源

- [ ] Task 6: 集成到 ResourceLibrary
  - [ ] SubTask 6.1: 在 `resource_library.py` 中导入资源发现引擎
  - [ ] SubTask 6.2: 新增 `discover_resources(url)` 方法，自动识别页面类型并调用发现引擎
  - [ ] SubTask 6.3: 新增 `discover_from_textbook_id(textbook_id)` 方法
  - [ ] SubTask 6.4: 保持原有 `parse()` 方法兼容性，内部调用发现引擎获取第一个资源

- [ ] Task 7: 增强文件名生成（file_naming.py）
  - [ ] SubTask 7.1: 新增 `generate_smart_filename(title, resource_type, lesson_index=None, total_lessons=1, teacher_name="")` 方法
  - [ ] SubTask 7.2: 实现中文数字转换（1→一，2→二，...）
  - [ ] SubTask 7.3: 实现文件名非法字符清理

- [ ] Task 8: 编写单元测试
  - [ ] SubTask 8.1: 为 `page_type_detector.py` 编写测试用例
  - [ ] SubTask 8.2: 为 `api_router.py` 编写测试用例
  - [ ] SubTask 8.3: 为 `resource_model.py` 编写测试用例
  - [ ] SubTask 8.4: 为 `discovery_engine.py` 的 `find_resource_layer()` 编写测试用例（模拟 JSON 数据）
  - [ ] SubTask 8.5: 为 `file_naming.py` 的智能文件名生成编写测试用例

# Task Dependencies

- [Task 2] depends on [Task 1]
- [Task 3] depends on [Task 1]
- [Task 4] depends on [Task 2, Task 3]
- [Task 5] depends on [Task 3]
- [Task 6] depends on [Task 4, Task 5]
- [Task 7] is independent
- [Task 8] depends on [Task 2, Task 3, Task 4, Task 6, Task 7]
