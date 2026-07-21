# Checklist

## 代码实现检查
- [ ] resource_model.py 包含 DiscoveredResource 数据类，所有字段类型正确
- [ ] resource_model.py 包含 PageType 枚举，定义 5 种页面类型
- [ ] resource_model.py 包含 ResourceTarget 数据类
- [ ] page_type_detector.py 实现 detect_page_type() 方法，能识别 5 种页面类型
- [ ] page_type_detector.py 实现 extract_resource_id() 方法，能从 URL 提取资源 ID
- [ ] api_router.py 定义 API_ENDPOINTS 映射表
- [ ] api_router.py 实现 build_api_url() 方法
- [ ] api_router.py 实现 get_resource_targets() 方法
- [ ] discovery_engine.py 实现 find_resource_layer() 递归查找方法
- [ ] discovery_engine.py 实现 extract_pdf_url() 方法
- [ ] discovery_engine.py 实现 get_activity_resource() 方法
- [ ] discovery_engine.py 实现 get_total_lesson_count() 方法
- [ ] discovery_engine.py 实现 discover_all_resources() 方法
- [ ] resource_library.py 新增 discover_resources() 方法
- [ ] resource_library.py 保持原有 parse() 方法兼容
- [ ] file_naming.py 新增 generate_smart_filename() 方法
- [ ] file_naming.py 实现中文数字转换

## 功能验证检查
- [ ] 页面类型检测器能正确识别 syncClassroom/classActivity URL
- [ ] 页面类型检测器能正确识别 qualityCourse URL
- [ ] 页面类型检测器能正确识别 prepare/detail URL
- [ ] 页面类型检测器能正确识别 jpk.smartedu.cn lesson URL
- [ ] 页面类型检测器能正确识别 tchMaterial URL
- [ ] API 路由能为每种页面类型构建正确的 API URL
- [ ] 递归查找能找到多层嵌套 JSON 中的目标资源
- [ ] 资源发现能遍历所有课时并发现对应资源
- [ ] 智能文件名能正确添加课时信息（多课时场景）
- [ ] 智能文件名能正确添加教师名
- [ ] 智能文件名能正确添加资源类型后缀
- [ ] 单课时课程文件名不包含课时信息

## 单元测试检查
- [ ] page_type_detector 测试用例全部通过
- [ ] api_router 测试用例全部通过
- [ ] resource_model 测试用例全部通过
- [ ] discovery_engine.find_resource_layer 测试用例全部通过
- [ ] file_naming 测试用例全部通过

## 代码规范检查
- [ ] 所有新增文件遵循 PEP 8 规范
- [ ] 所有类、方法、模块包含 docstring（PEP 257）
- [ ] 新增文件均放置在 core/resource/ 目录下
- [ ] 核心层不依赖 GUI 层
- [ ] 无硬编码颜色值、路径等配置项
