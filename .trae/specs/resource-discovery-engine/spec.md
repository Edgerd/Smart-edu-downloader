# 资源发现引擎 Spec

## Why

当前 SED 只能处理单页面类型的单一 PDF 资源下载，无法像浏览器插件那样自动发现课程中的所有可下载资源（课件、教学设计、学习任务单、课后练习等），也无法识别多课时结构和不同页面类型对应的 API 端点。需要构建一个独立的资源发现引擎，使 SED 具备批量资源发现和多页面适配能力。

## What Changes

* **新增** `core/resource/discovery_engine.py` 资源发现引擎模块

* **新增** `core/resource/page_type_detector.py` 页面类型检测器模块

* **新增** `core/resource/api_router.py` API 路由映射模块

* **新增** `core/resource/resource_model.py` 资源数据模型

* **修改** `core/resource/resource_library.py` 的 `parse()` 方法，集成资源发现引擎

* **修改** `core/download/file_naming.py` 增加智能文件名生成（课时 + 教师名 + 资源类型）

## Impact

* **Affected specs**: 资源解析、下载管理

* **Affected code**:

  * `core/resource/resource_library.py`（集成新引擎）

  * `core/resource/discovery_engine.py`（新增）

  * `core/resource/page_type_detector.py`（新增）

  * `core/resource/api_router.py`（新增）

  * `core/resource/resource_model.py`（新增）

  * `core/download/file_naming.py`（增强文件名生成）

## ADDED Requirements

### Requirement: 页面类型检测

系统 SHALL 能够识别以下 5 种页面类型：

* `tch_material`（教师材料/电子课本）

* `sync_classroom`（同步课堂/课堂活动）

* `quality_course`（精品课程）

* `prepare`（备课页面）

* `lesson`（精品课程课时页）

#### Scenario: 识别同步课堂页面

* **WHEN** 用户输入 URL 包含 `syncClassroom/classActivity`

* **THEN** 系统识别为 `sync_classroom` 类型，并使用对应的 API 端点

#### Scenario: 识别精品课程页面

* **WHEN** 用户输入 URL 包含 `qualityCourse` 或 `yearQualityCourse`

* **THEN** 系统识别为 `quality_course` 类型

### Requirement: API 路由映射

系统 SHALL 为每种页面类型提供对应的 API 端点：

* `tch_material`: `https://s-file-2.ykt.cbern.com.cn/zxx/ndrv2/resources/tch_material/details/{contentId}.json`

* `sync_classroom`: `https://s-file-2.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/resources/details/{resourceId}.json`

* `quality_course`: `https://s-file-2.ykt.cbern.com.cn/zxx/ndrv2/resources/{resourceId}.json`

* `prepare`: `https://s-file-2.ykt.cbern.com.cn/zxx/ndrv2/prepare_sub_type/resources/details/{resourceId}.json`

* `lesson`: `https://s-file-2.ykt.cbern.com.cn/zxx/ndrv2/prepare_lesson/resources/details/{resourceId}.json`

#### Scenario: 构建 API URL

* **WHEN** 页面类型为 `sync_classroom`，resourceId 为 `abc123`

* **THEN** 系统构建 API URL 为 `https://s-file-2.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/resources/details/abc123.json`

### Requirement: 递归资源发现

系统 SHALL 实现递归资源发现算法，能够：

* 遍历 JSON 响应中的 `relations`、`resource_structure.relations` 等多层结构

* 根据 `res_ref` 引用解析具体资源项

* 递归查找 `title` 或 `resource_type_code_name` 匹配目标资源的对象

* 从 `ti_items` 中提取 PDF 下载链接

#### Scenario: 递归查找课件资源

* **WHEN** API 返回的 JSON 包含多层嵌套的 `relations.national_course_resource`

* **THEN** 系统递归遍历所有层级，找到 `title="课件"` 的资源项，并提取 PDF 链接

#### Scenario: 多课时资源发现

* **WHEN** API 返回的 `resource_structure.relations` 包含多个课时

* **THEN** 系统遍历每个课时，分别发现对应的课件、教学设计等资源

### Requirement: 资源数据模型

系统 SHALL 定义统一的资源数据模型，包含：

* `resource_id`: 资源唯一标识

* `title`: 资源标题

* `resource_type`: 资源类型（课件/教学设计/学习任务单/课后练习等）

* `download_url`: 下载链接

* `teacher_name`: 教师姓名

* `lesson_index`: 课时索引（从 0 开始）

* `lesson_title`: 课时标题

* `file_extension`: 文件扩展名

### Requirement: 多页面资源类型适配

系统 SHALL 为不同页面类型提供不同的目标资源类型：

* `sync_classroom`（课堂活动）：课件、教学设计、学习任务单、课后练习

* `quality_course`（精品课程）：课件、教学设计、学习任务单、课后练习

* `lesson`（课时页）：教材、课件、学习任务单、课后练习

* `prepare`（备课页面）：动态识别当前页面的资源类型

#### Scenario: 精品课程资源发现

* **WHEN** 页面类型为 `quality_course`

* **THEN** 系统依次发现课件、教学设计、学习任务单、课后练习四种资源

### Requirement: 智能文件名生成

系统 SHALL 根据以下规则生成文件名：

* 基础格式：`标题 + (-第X课时) + (-教师名) + (-资源类型) + .扩展名`

* 课时信息：仅在多课时课程或当前课时不是第一课时时添加

* 课时数字：使用中文数字（一、二、三、四...）

* 资源类型后缀：课件、教学设计、学习任务单、课后练习等

#### Scenario: 多课时文件名生成

* **WHEN** 课程标题为"初中数学"，课时索引为 2（第三课时），教师名为"张三"，资源类型为"课件"

* **THEN** 生成文件名：`初中数学-第三课时-张三-课件.pdf`

### Requirement: API 内容获取机制

系统 SHALL 复用现有的 HTTP 客户端基础设施获取 API 响应：

- **HTTP 客户端**：使用 `core/network/http_client.py` 的 `HttpClient` 单例
- **认证方式**：通过 `X-ND-AUTH` 请求头传递 Access Token
- **请求方法**：对 API 端点发送 HTTP GET 请求
- **响应解析**：解析 JSON 响应获取资源数据

#### 获取流程

```
用户输入URL → 识别页面类型 → 提取资源ID → 构建API URL → HTTP GET请求 → 解析JSON响应 → 递归提取资源
```

#### 具体示例

**输入URL**：
```
https://basic.smartedu.cn/syncClassroom/classActivity?activityId=abc123-4567-8901
```

**构建API URL**：
```
https://s-file-2.ykt.cbern.com.cn/zxx/ndrv2/national_lesson/resources/details/abc123-4567-8901.json
```

**发送HTTP GET请求**（复用 HttpClient）：
```python
from core.network.http_client import get_http_client
http = get_http_client()
response = http.get(api_url)  # 自动携带 Access Token
data = response.json()
```

**JSON响应结构示例**：
```json
{
  "title": "初中数学-勾股定理",
  "teacher_list": [{"name": "张三"}],
  "resource_structure": {
    "relations": [
      {"title": "第一课时", "res_ref": "[1,2,3]"},
      {"title": "第二课时", "res_ref": "[4,5,6]"}
    ]
  },
  "relations": {
    "national_course_resource": [
      {
        "title": "课件",
        "ti_items": [{
          "ti_file_flag": "pdf",
          "ti_storages": ["https://s-file-1.ykt.cbern.com.cn/.../xxx.pdf"]
        }]
      }
    ]
  }
}
```

**递归提取资源**：
- 遍历 `resource_structure.relations` 获取所有课时
- 根据 `res_ref` 索引定位到具体资源项
- 从 `ti_items` 中提取 PDF 下载链接
- 附加 Access Token 参数到下载 URL

#### Scenario: API 请求携带认证信息

- **WHEN** 资源发现引擎发起 API 请求
- **THEN** HTTP 客户端自动在请求头中添加 `X-ND-AUTH: MAC id="{token}",nonce="0",mac="0"`

#### Scenario: 获取多课时资源列表

- **WHEN** API 返回的 JSON 包含 `resource_structure.relations` 数组（长度为 3）
- **THEN** 系统遍历每个课时，分别调用 API 获取课件、教学设计等资源，最终返回资源列表

### Requirement: 三种资源获取模式

系统 SHALL 支持三种资源获取模式：

#### 模式1: URL 输入 → 自动发现资源
用户输入课程 URL，系统自动识别页面类型并发现所有可下载资源。

#### Scenario: URL 模式成功发现资源
- **WHEN** 用户输入精品课程 URL
- **THEN** 系统自动识别页面类型，调用对应 API，返回该课程下所有课件、教学设计等资源

#### 模式2: 教材 ID → 获取关联课程资源
用户输入教材 ID（UUID），系统获取该教材关联的所有课程资源。

#### Scenario: 教材 ID 模式获取关联资源
- **WHEN** 用户输入教材 ID（如 `5b6f0c2f-eaba-4850-853b-8d99d7c151c0`）
- **THEN** 系统调用 `part_100.json` API 获取资源列表，对每个资源调用 `details/{id}.json` 获取下载链接

#### 模式3: 浏览模式
系统提供类似资源库的浏览界面，支持级联筛选（学段 → 学科 → 版本 → 年级 → 册次），用户可选择并查看教材/课程列表，点击后获取资源详情。

#### Scenario: 浏览模式选择教材
- **WHEN** 用户通过级联下拉菜单选择"初中 → 数学 → 人教版 → 七年级 → 上册"
- **THEN** 系统显示该分类下的所有教材，用户点击某个教材后获取其关联资源

## MODIFIED Requirements

### Requirement: ResourceLibrary.parse()

`ResourceLibrary.parse()` 方法 SHALL 集成资源发现引擎，支持：

* 自动识别页面类型

* 调用对应的 API 端点

* 使用递归算法发现所有可下载资源

* 返回资源列表而非单一资源 URL

**Migration**: 保持原有 `parse()` 方法签名兼容，新增 `discover_resources()` 方法用于批量资源发现

## REMOVED Requirements

无
