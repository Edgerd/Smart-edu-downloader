# 资源库搜索功能增强 - 教材版本支持

## Why
当前资源库搜索不显示教材版本（如冀教版、人教版），用户无法在搜索结果中区分同一学科不同版本的教材，也无法使用版本信息进行精确搜索。搜索关键词提取不够智能，无法处理口语化或缩写形式的输入。

## What Changes
- 搜索结果表格新增"教材版本"列（标题列缩短以适配）
- `_flatten_resources` 提取并传递教材版本信息
- `_extract_keywords` 增加教材版本关键词提取（如"冀教版"、"人教版"）
- 新增 `_repair_search_term` 方法，修复缩写/乱序的搜索词
- `_calculate_smart_score` 增加教材版本匹配评分
- 多个搜索逻辑优化（年级册次组合、版本符号识别等）

## Impact
- Affected specs: 无（全新功能）
- Affected code:
  - `gui/pages/resource_page.py` - 表格UI列定义、`_display_current_page`
  - `core/resource_library.py` - `_flatten_resources`、`_extract_keywords`、`_calculate_smart_score`、新增 `_repair_search_term`
  - `产品更新信息.md` - 添加更新日志
  - `core/version.py` - 递增版本号

## ADDED Requirements

### Requirement: 搜索结果表格显示教材版本列
系统 SHALL 在搜索结果表格的"标题"和"学科"列之间插入"教材版本"列，列数从 4 列变为 5 列。标题列宽度缩短约 40% 以容纳新列。

#### Scenario: 搜索结果显示版本信息
- **GIVEN** 用户搜索了数学相关资源
- **WHEN** 搜索结果中包含冀教版和人教版的教材
- **THEN** 表格的"教材版本"列分别显示"冀教版"、"人教版"等版本名称

#### Scenario: 资源无版本信息
- **WHEN** 某个搜索结果的教材版本无法确定
- **THEN** "教材版本"列显示空字符串

### Requirement: 教材版本信息提取
系统 SHALL 在 `_flatten_resources` 方法中从资源层级路径中提取教材版本（publisher）信息。

#### Scenario: 从 display_name 提取版本
- **GIVEN** 资源层级路径中包含 display_name 为"冀教版"的节点
- **WHEN** 扁平化该层级下的资源
- **THEN** 该资源的 publisher 字段为"冀教版"

#### Scenario: 版本和学科同级时正确区分
- **GIVEN** 资源层级路径中同时有"数学"和"人教版"的 display_name
- **WHEN** 扁平化该层级下的资源
- **THEN** subject 为"数学"，publisher 为"人教版"，两者不混淆

### Requirement: 教材版本关键词提取
系统 SHALL 在 `_extract_keywords` 方法中识别并提取教材版本关键词。

#### Scenario: 搜索"冀教版 数学 八年级 下册"
- **WHEN** 用户输入"冀教版 数学 八年级 下册"
- **THEN** 提取的关键词包含"冀教版"、"数学"、"八年级"、"下册"

#### Scenario: 搜索"人教版的语文课本六年级的上册新版"
- **WHEN** 用户输入"人教版的语文课本六年级的上册新版的"
- **THEN** 提取的关键词包含"人教版"、"语文"、"六年级"、"上册"、"根据2022年版课程标准修订"（新版→此关键词）

### Requirement: 搜索词智能修复
系统 SHALL 提供 `_repair_search_term` 方法，将缩写或乱序的搜索词修复为规范形式。

#### Scenario: 修复"七下冀教版数"
- **WHEN** 用户输入"七下冀教版数"
- **THEN** 修复为"七年级 下册 冀教版 数学"

#### Scenario: 修复"八上人教版语"
- **WHEN** 用户输入"八上人教版语"
- **THEN** 修复为"八年级 上册 人教版 语文"

#### Scenario: 无需修复的规范输入
- **WHEN** 用户输入"冀教版 数学 八年级 下册"
- **THEN** 搜索词不变，直接使用

### Requirement: 搜索评分纳入教材版本
系统 SHALL 在 `_calculate_smart_score` 中增加教材版本匹配评分。

#### Scenario: 版本精确匹配加分
- **GIVEN** 搜索关键词包含"冀教版"
- **WHEN** 资源的 publisher 字段匹配"冀教版"
- **THEN** 匹配分数 +200

#### Scenario: 版本不匹配扣分
- **GIVEN** 搜索关键词包含"冀教版"
- **WHEN** 资源的 publisher 字段不包含"冀教版"但包含其他已知版本
- **THEN** 匹配分数 -300

### Requirement: 搜索逻辑优化
系统 SHALL 对搜索逻辑进行多项优化。

#### Scenario: 年级+册次组合匹配
- **GIVEN** 搜索关键词同时包含年级和册次（如"八年级"和"下册"）
- **WHEN** 资源标题同时包含年级和册次
- **THEN** 额外加分（组合完整性加分）

#### Scenario: 版本符号识别
- **GIVEN** 搜索词包含版本标识如"2024版"、"新课标"等
- **WHEN** 提取关键词
- **THEN** 这些标识被正确识别并用于匹配