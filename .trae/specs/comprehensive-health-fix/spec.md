# Smart-edu-downloader 全面修复 Spec

## Why

体检报告发现 8 个 Bug、4 项性能冗余、5 项代码质量问题、10 项架构缺陷和 6 项安全风险。修复这些问题将显著提升软件稳定性、性能、可维护性和安全性。

## What Changes

* 修复 8 个 Bug（高/中/低严重度）

* 提取 4 处重复样式函数到公共工具模块

* 解除 Core 层对 GUI 层的依赖

* 强化 Token 加密安全性

* 统一 sys.path 处理

* 清理未使用代码和冗余导入

* 补充 main.py 示例方法

* 补充模块级 docstring

## Impact

* 受影响模块: downloader.py, more\_page.py, resource\_page.py, home\_page.py, setting\_page.py, main.py, fonts.py, settings\_manager.py, 以及 4 个页面文件

* 受影响规范: Token 存储格式变更（需要迁移旧数据）

## ADDED Requirements

### Requirement: 公共样式工具模块

系统 SHALL 提供 gui/styles.py 模块，统一管理按钮样式、颜色加深、强调色加载等公共样式函数。

#### Scenario: 页面调用公共样式函数

* **WHEN** 页面需要按钮样式或颜色加深

* **THEN** 调用 gui/styles.py 中的统一函数，而非本地重复实现

### Requirement: Token 安全加密

系统 SHALL 使用 cryptography.fernet 替代 XOR+Base64 加密方案。

#### Scenario: 用户升级后首次读取旧 Token

* **WHEN** 系统检测到旧版 XOR 加密格式的 Token

* **THEN** 自动迁移至新加密格式并保存

### Requirement: Core 与 GUI 解耦

Core 层 SHALL 不直接导入 GUI 层的任何模块。

#### Scenario: downloader 需要 Token 加解密

* **WHEN** downloader 需要解密 Token

* **THEN** 使用 core 层的独立加解密模块，而非导入 setting\_page

## MODIFIED Requirements

### Requirement: 下载进度回调

修改 downloader.py 的 progress\_callback 实现：

1. 修复速度计算时间窗口错乱（B1）
2. 校验失败重试改为重新入队而非递归（B2）
3. 使用 os.replace 替代 os.remove+os.rename（B6）
4. 简化 TOCTOU 竞态处理（B7）
5. 修复 worker\_loop 退出信号发射（B5）

### Requirement: 跨平台兼容

修改 more\_page.py 的 \_open\_log 方法，使用 platform 检测选择对应的文件打开命令。

### Requirement: 设置读取统一

修改 resource\_page.py 的 \_load\_accent\_color，通过 SettingsManager 获取强调色，而非直接读取文件。

### Requirement: 页面 sys.path 统一

删除 4 个页面中的重复 sys.path.insert，由 main.py 统一处理。

## REMOVED Requirements

### Requirement: XOR Token 加密

**Reason**: 安全性极低，密钥硬编码在源码中
**Migration**: 自动迁移脚本在首次启动时检测并转换旧格式

### Requirement: 页面内重复样式函数

**Reason**: \_darken\_color 和 \_get\_button\_style 在 4 个页面中重复实现
**Migration**: 统一提取至 gui/styles.py，页面调用新模块

### Requirement: 函数内局部 import

**Reason**: 违反 PEP 8，应在文件头部导入
**Migration**: 移至文件头部导入区

### Requirement: 未使用的导入和变量

**Reason**: 保持代码整洁，删除 home\_page.py 中的 import threading 等
**Migration**: 直接删除

<br />

SOLO Agent

思考过程

我来对 Smart-edu-downloader 项目进行全面体检。首先需要了解项目结构和代码

Search Agent 探索项目结构

Smart-edu-downloader

在工作区搜索 '\*\*/\*.py'

在工作区搜索 '\*\*/version.py'

在工作区搜索 '\*\*/\*.md'

在工作区搜索 '**/resources/**'

在工作区搜索 '**/.trae/**'

在工作区搜索 '\*\*/.\*'

### Relevant Code Snippets

1. e:/hello/Smart-edu-downloader/core/version.py:L1-L10
   — 包含版本信息，是项目的核心配置文件之一。
2. e:/hello/Smart-edu-downloader/README.md:L1-L20
   — 项目的主要介绍文档，包含基本使用说明。
3. e:/hello/Smart-edu-downloader/.trae/rules/规范1.md:L1-L10
   — 配置文件，说明项目规范。
4. e:/hello/Smart-edu-downloader/resources/svg\_library/许可证.txt:L1-L10
   — 资源目录中的许可证文件。
5. e:/hello/Smart-edu-downloader/main.py:L1-L10
   — 程序入口点文件。
6. e:/hello/Smart-edu-downloader/requirements.txt:L1-L10
   — 项目依赖包列表文件。
7. e:/hello/Smart-edu-downloader/产品更新信息.md:L1-L10
   — 产品更新记录文档。
8. e:/hello/Smart-edu-downloader/core/ init .py:L1-L5
   — 核心模块的初始化文件。
9. e:/hello/Smart-edu-downloader/gui/ init .py:L1-L5
   — GUI模块初始化文件。
10. e:/hello/Smart-edu-downloader/gui/pages/home\_page.py:L1-L10
    — 主页页面逻辑文件。

### 项目文件树结构

现在我需要读取所有核心代码文件进行分析。先从关键模块开始。

main.py

core\version.py

产品更新信息.md

requirements.txt

feature\_custom\_download.py

core\_*init*\_.py

Thought

core\downloader.py

core\settings\_manager.py

core\http\_client.py

core\logger.py

core\cache\_manager.py

core\resource\_library.py

Thought

gui\_*init*\_.py

gui\pages\download\_page.py

gui\pages\home\_page.py

gui\pages\setting\_page.py

gui\pages\resource\_page.py

gui\pages\more\_page.py

Thought

在工作区搜索 '\*\*/fonts.py'

在工作区搜索 '\*\*/main\_window\.py'

在工作区搜索 '\*\*/debug\_panel.py'

Thought

gui\fonts.py

gui\main\_window\.py

core\exceptions.py

core\settings\_manager.py

core\download\_history.py

Thought

core\url\_modifier.py

core\download\_verifier.py

core\file\_categorizer.py

core\file\_naming.py

core\sound\_player.py

core\textbook\_info.py

压缩

Thought

0/8 已完成

全面读取项目中未检查的源代码文件

Bug 扫描 - 按严重程度列出所有 Bug

性能瓶颈分析

代码质量检查（PEP8/PEP257/字体规范/一功能一文件）

架构问题分析（耦合/依赖/硬编码/未使用代码）

安全风险评估

规范合规检查（version.py + 产品更新信息.md）

输出完整体检报告

Thought

在工作区搜索 '\*\*/\*.py'

在工作区搜索 '\*\*/\*.md'

Thought

我先批量读取项目中尚未检查的源代码文件

main.py

core\version.py

产品更新信息.md

core\http\_client.py

core\logger.py

core\cache\_manager.py

core\exceptions.py

core\download\_history.py

Thought

core\url\_modifier.py

core\download\_verifier.py

core\file\_categorizer.py

core\file\_naming.py

core\sound\_player.py

core\textbook\_info.py

core\status\_bar.py

core\docs.py

Thought

gui\main\_window\.py

gui\pages\home\_page.py

gui\pages\setting\_page.py

gui\pages\resource\_page.py

Thought

gui\pages\download\_page.py

gui\pages\more\_page.py

core\downloader.py

Thought

Now let me read the remaining GUI and utility files

core\resource\_library.py

core\settings\_manager.py

core\_*init*\_.py

gui\_*init*\_.py

gui\widgets\hover\_tooltip\_mixin.py

feature\_custom\_download.py

version\_update.py

压缩

Thought

继续全面体检。我先并行读取尚未检查的关键文件。

main.py

core\version.py

产品更新信息.md

gui\main\_window\.py

gui\pages\home\_page.py

gui\pages\resource\_page.py

gui\pages\setting\_page.py

gui\pages\more\_page.py

Thought

core\downloader.py

core\settings\_manager.py

core\resource\_library.py

core\http\_client.py

core\cache\_manager.py

core\logger.py

feature\_custom\_download.py

gui\fonts.py

Thought

core\downloader.py

core\_*init*\_.py

gui\_*init*\_.py

requirements.txt

在工作区搜索 '\*.py'

Thought

core\downloader.py

在工作区搜索 '\*\*/\*.py'

在工作区搜索 '\*.py'

Thought

core\downloader.py

gui\widgets\hover\_tooltip\_mixin.py

core\thread\_pool.py

Thought

core\downloader.py

gui\pages\download\_page.py

Thought

现在我有了足够的信息，来输出完整的体检报告。

# Smart-edu-downloader 全面体检报告

## 一、Bug 扫描

### 【高严重度】 B1 - downloader.py 进度回调中速度计算时间窗口错乱

* 位置 : downloader.py
* 问题 : last\_speed\_check\_time 在 progress\_callback 内更新（第 654 行），但速度计算用的 time\_diff 在 639 行基于 last\_speed\_check\_time ，而 last\_speed\_check\_time 只在进度上报时（每 0.1s）更新一次。如果外部调用 progress\_callback 频率低于 0.1s，速度值会被放大；如果频率高于 0.1s， last\_download\_size 会跳变导致速度不准。
* 复现条件 : 网络波动导致回调间隔不均匀时速度显示异常。
* 修复代码 : B2 - downloader.py 校验失败递归调用导致潜在栈溢出
* 位置 : downloader.py
* 问题 : self.\_download\_task(task) 在校验失败重试时递归调用自身。虽然每次重试前设置了 task\["status"] = "pending" ，但如果在递归调用中再次校验失败会形成深度递归。此外 \_cancel\_events 在递归前被 del 掉，递归内又创建新的 cancel\_event，但外部无法控制。
* 复现条件 : 设置 auto\_verify=True + retry\_on\_verify\_fail=True + 文件持续校验失败。
* 修复代码 : 改为重新入队而非递归： B3 - more\_page.py os.startfile() 非跨平台
* 位置 : more\_page.py
* 问题 : os.startfile() 是 Windows 专有 API，macOS/Linux 上会抛出 AttributeError 崩溃。
* 复现条件 : macOS/Linux 上点击"查看日志"按钮。
* 修复代码 :

### 【中严重度】 B4 - resource\_page.py \_load\_accent\_color 绕过 SettingsManager 直接读文件

* 位置 : resource\_page.py
* 问题 : 直接 open("settings.json") 相对路径读取，依赖当前工作目录，启动位置不同时读不到。同时绕过了 SettingsManager 的统一管理和加密处理。
* 复现条件 : 从不同目录启动程序或 settings.json 路径不一致。
* 修复代码 : B5 - downloader.py \_worker\_loop 退出时不再触发 all\_tasks\_completed
* 位置 : downloader.py
* 问题 : self.all\_tasks\_completed.emit() 在 \_is\_running = False 之后发射，但此时线程即将退出，信号可能无法被主线程的事件循环正确接收。应使用 pyqtSignal 的跨线程发射（PyQt5 自动处理队列连接），但在某些 Qt 版本中可能丢失。
* 修复代码 : 在设置 \_is\_running = False 后通过 QMetaObject.invokeMethod 或延迟发射： B6 - downloader.py \_download\_single 中 os.remove + os.rename 非原子
* 位置 : downloader.py
* 问题 : os.remove(save\_path) 成功后、 os.rename(tmp\_path, save\_path) 前若崩溃，原文件丢失且新文件未就位。Windows 上 os.rename 在目标存在时会失败。
* 修复代码 : 使用 os.replace （跨平台原子替换）：

### 【低严重度】 B7 - downloader.py \_download\_with\_fallback TOCTOU 竞态

* 位置 : downloader.py
* 问题 : os.path.exists(tmp\_path) + os.remove(tmp\_path) 之间存在 TOCTOU 窗口。
* 修复代码 : B8 - setting\_page.py highlight\_token\_input 中 lambda 捕获 original\_style 不安全
* 位置 : setting\_page.py
* 问题 : QTimer.singleShot(2000, lambda: self.\_restore\_token\_input\_style(original\_style)) 中 original\_style 是局部变量，定时器触发时 SettingPage 可能已销毁。
* 修复代码 : 已有 \_restore\_token\_input\_style 中的可见性检查，可接受。但建议保存为实例属性以更安全。

## 二、性能瓶颈

### 【严重 - 已优化】

问题 位置 优化前 优化后 下载表格全量重建 download\_page.py setRowCount(0)+insertRow O(n) 每 500ms 增量更新 + 状态缓存跳过 工作线程 busy-wait downloader.py time.sleep(0.1) 轮询 threading.Event.wait(5) 进度 O(n) 遍历 downloader.py 每次回调遍历所有 download\_states O(1) 缓存增量更新 资源搜索递归遍历 resource\_library.py 每次搜索递归全部资源树 扁平化缓存 \_flat\_resources\_cache

### 【中等 - 待优化】 P1 - \_darken\_color 重复实现 4 处

* 位置 : home\_page.py , resource\_page.py , setting\_page.py , more\_page.py
* 影响 : 代码冗余，修改时需要同步 4 处
* 修复 : 提取到 gui/utils.py 或 gui/fonts.py P2 - \_get\_button\_style 重复实现 4 处
* 位置 : home\_page.py, resource\_page.py, setting\_page.py, more\_page.py
* 同上 : 提取为公共工具函数 P3 - \_load\_accent\_color 在每个页面中重复加载
* 影响 : 每个页面初始化时各读一次设置
* 修复 : 由 SettingsManager 提供 get\_accent\_color() 快捷方法，利用热缓存 P4 - \_connect\_auto\_save\_signals 中大量信号连接
* 位置 : setting\_page.py
* 影响 : 初始化时连接 40+ 个控件信号，每次控件变化触发 2 秒防抖定时器
* 优化 : 使用事件过滤器统一监听，避免逐个连接

## 三、代码质量

### PEP 8 合规

问题 位置 说明 sys.path.insert 滥用 home\_page.py L26-L28, resource\_page.py L24-L26, download\_page.py L20-L22, more\_page.py L21-L23 4 个页面重复手动修改 sys.path，应由包管理 import re 在函数内部 home\_page.py L825 应在文件头部导入 import json 在函数内部 resource\_page.py L77 同上 import pyperclip 在函数内部 home\_page.py L464 同上且 pyperclip 未在 requirements.txt import threading 未使用 home\_page.py L7 已改用 thread\_pool

### PEP 257 合规

问题 位置 缺少模块级 docstring gui/pages/**init**.py , gui/managers/**init**.py , gui/components/**init**.py , gui/widgets/**init**.py \_on\_combo\_changed 等回调缺少 docstring resource\_page.py L598

### 一功能一文件检查

* downloader.py 中包含 format\_bytes 、 add\_bookmarks 、 Downloader 三类代码， format\_bytes 和 add\_bookmarks 应抽离到各自模块
* 通过

### main.py 示例方法

* 仅有 example\_allow\_custom\_domain\_download() 一个示例
* 缺少 : example\_download() , example\_resource\_search() , example\_cache\_management() , example\_settings() , example\_http\_client()

### 字体规范

* 全项目 ：所有 UI 元素均使用 gui/fonts.py 中的字体函数（ title\_font() , body\_font() , bold\_font() 等），符合 HarmonyOS 规范
* monospace\_font() 使用 Pixel 字体，符合规范
* 通过

## 四、架构问题

### 模块耦合

问题 严重度 说明 feature\_custom\_download.py 导入 core.downloader.Downloader 仅取 ALLOWED\_DOMAINS 中 应定义在独立 constants 模块或由 Downloader 导出 home\_page.py 直接调用 self.main\_window.\_switch\_page(2) 中 硬编码索引 2，应通过 navigation\_manager resource\_page.py \_perform\_add\_download 硬编码 download\_page\_index = 2 中 resource\_page.py#L794 downloader.py 导入 gui.pages.setting\_page.SettingPage 高 Core 层不应依赖 GUI 层 downloader.py 导入 gui.pages.setting\_page.SettingsModel 高 同上，建议 Token 加解密移至 core 层

### 循环依赖风险

* core/**init**.py 使用 **getattr** 延迟导入避免了循环依赖，设计合理
* gui/**init**.py 直接 from .main\_window import MainWindow ，但在 main\_window 导入 pages 时会有间接依赖

### 硬编码

项 位置 建议 download\_page\_index = 2 resource\_page.py L794 使用 PageManager 的页面名称映射 \_TOKEN\_KEY = "SED\_TOKEN\_KEY\_2024" setting\_page.py L39 使用环境变量或运行时生成 "settings.json" 字符串 setting\_page.py 多处 使用 SettingsManager 的路径常量 主题颜色 "#1A82E2" main\_window\.py L264 使用 SettingsManager 读取 Cookie 域名白名单 downloader.py L113-L119 应集中到配置模块

### 测试覆盖

* 项目无任何测试文件 （无 tests/ 目录，无 test\_\*.py ，无 pytest 配置）
* 建议 : 至少覆盖核心模块（downloader, resource\_library, settings\_manager, http\_client）

### 未使用代码

文件/代码 说明 gui/widgets/animation\_manager.py 与 gui/managers/animation\_manager.py 重复，widgets 版本可能已废弃 setting\_page.py SettingsModel.get\_default\_settings() 中 "privacy\_protection" 和 "safe\_download\_mode" 设置了开关但未在任何业务逻辑中生效 main.py \_debug\_manager 全局变量 设置后未实际使用 main.py 中 sys.path.insert(0, ...) 在页面文件中 应在入口文件中统一处理 downloader.py format\_bytes 函数 仅在 downloader.py 内部使用但定义为模块级函数

## 五、安全风险

### 【高风险】 S1 - Token 使用 XOR + Base64 "加密"存储

* 位置 : setting\_page.py
* 风险 : XOR 密钥 SED\_TOKEN\_KEY\_2024 硬编码在源码中，通过逆向可轻易解密所有用户的 Access Token。Token 可被用于访问智慧教育平台的任意资源。
* 修复方案 : S2 - 代理密码以明文存储
* 位置 : setting\_page.py
* 风险 : settings.json 中 proxy\_password 明文存储
* 修复 : 使用与 Token 相同的加密方案

### 【中风险】 S3 - settings.json 无完整性校验

* 位置 : settings\_manager.py
* 风险 : 只有 JSON 格式校验，无签名/哈希校验。被篡改后直接加载
* 修复 : 写入时附加 HMAC 签名，读取时验证 S4 - os.startfile 路径由相对路径构造
* 位置 : more\_page.py
* 风险 : log\_file = "url\_modifier.log" 是相对路径，若被符号链接重定向可能执行恶意文件
* 修复 : 使用绝对路径并验证文件类型

### 【低风险】 S5 - 下载路径遍历已防护但可加强

* 位置 : downloader.py
* 状态 : 已有 \_is\_path\_safe 检查，但仅在部分路径使用
* 建议 : 在所有保存路径前统一调用 S6 - HTTP 请求无 SSL 证书校验配置
* 位置 : http\_client.py
* 风险 : requests.Session 默认启用 SSL 验证，但没有提供关闭选项供测试环境
* 建议 : 添加 verify\_ssl 设置项

## 六、规范合规

### 版本号

### 产品更新信息.md 同步情况

检查项 结果 最新版本号 5.6.12 Beta 4 ✓ 与 version.py 一致 最新更新日期 2026-06-06 ✓ 更新内容完整 ✓ 包含新增功能、修复错误、影响范围 格式规范 ✓ 使用 Markdown 表格和列表

### 版本号格式合规

* 格式 主版本号.小版本号 预发布标识 → 5.6.12 Beta 4 ✓
* 预发布版本仅递增预发布标识（Beta 3 → Beta 4）✓

### 更新日志合规

* 每次代码更新同步编写 ✓
* 包含日期、版本号、更新类型、变更描述、影响范围 ✓

## 总结统计

类别 高 中 低 合计 Bug 3 3 2 8 性能 0 4 0 4 代码质量 0 0 5 5 架构 2 4 4 10 安全 2 2 2 6 规范合规 0 0 1 1

建议优先处理 : B1（速度计算修复）、B2（递归替换为重新入队）、B3（跨平台兼容）、S1（Token 加密升级）、架构耦合（Core → GUI 方向依赖）。
