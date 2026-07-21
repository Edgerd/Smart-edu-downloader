# Tasks

- [x] Task 1: 数据层 - `_flatten_resources` 提取教材版本信息
  - [ ] 在 `_flatten_resources` 中增加 `publisher` 参数传递
  - [ ] 从 `display_name` 中识别教材版本（冀教版、人教版、北师大版、苏教版等）
  - [ ] 区分版本与学科/年级（两者不会混淆）
  - [ ] 返回结果中增加 `publisher` 字段

- [x] Task 2: 搜索修复 - 新增 `_repair_search_term` 方法
  - [ ] 识别年级缩写模式（七下→七年级下册、八上→八年级上册）
  - [ ] 识别学科缩写（数→数学、语→语文、英→英语）
  - [ ] 识别顺序混乱的搜索词并重组为标准格式
  - [ ] 仅在搜索词确实需要修复时才进行处理

- [x] Task 3: 关键词提取增强 - 重写 `_extract_keywords`
  - [ ] 增加教材版本关键词识别（冀教版、人教版、北师大版、苏教版、湘教版、鲁教版、沪科版、浙教版、华师大版等）
  - [ ] "新版" → "根据2022年版课程标准修订" 关键词替换
  - [ ] 口语化表达修正（的、课本、教材等填充词过滤）
  - [ ] 年级+册次缩写展开（七下→七年级+下册）
  - [ ] 增强册次信息提取（下册→下、上册→上）

- [x] Task 4: 搜索评分优化 - 更新 `_calculate_smart_score`
  - [ ] 增加 publisher 字段的匹配评分
  - [ ] 版本精确匹配加分（+200），版本不匹配扣分（-300）
  - [ ] 年级+册次组合完整性加分
  - [ ] 资源 full_text 纳入 publisher 字段
  - [ ] `search_resources` 将 publisher 传给评分函数

- [x] Task 5: UI层 - 搜索结果表格增加教材版本列
  - [ ] 列数从 4 改为 5，表头增加"教材版本"
  - [ ] 标题列缩短（从 `:Stretch` 改为固定宽度或更小 stretch 比例）
  - [ ] `_display_current_page` 中填充 publisher 列数据
  - [ ] 操作列索引从 3 调整为 4

- [x] Task 6: 版本号升级和更新日志
  - [ ] 更新 `core/version.py` 版本号递增
  - [ ] 更新 `产品更新信息.md` 添加本次更新记录

# Task Dependencies
- Task 2、Task 3 可并行开发
- Task 1、Task 2、Task 3 可并行开发
- Task 4 依赖 Task 1（需要 publisher 字段）
- Task 5 依赖 Task 1（需要 publisher 数据）
- Task 6 最后执行