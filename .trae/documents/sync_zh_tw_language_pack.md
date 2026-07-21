# 同步 zh_TW.json 语言包计划

## 摘要

以 `i18n/zh_CN.json` 为基准，整理 `i18n/zh_TW.json`：
1. 删除所有与教材/搜索/日志/分类相关的翻译项（这些已从其他语言包中移除，不应再存在于语言包中）。
2. 补齐 `zh_TW.json` 中相对 `zh_CN.json` 缺少的键。
3. 删除 `zh_TW.json` 中相对 `zh_CN.json` 多出的非必要键。
4. 验证 JSON 语法与程序可正常加载。

## 当前状态分析

- `zh_CN.json` 是当前最完整、最规范的简体中文语言包，已去除教材相关翻译项。
- `zh_TW.json` 是繁体中文语言包，结构大致与 `zh_CN.json` 相同，但存在两类问题：
  - **残留教材相关键**：
    - `common.auto_*`（学科、年级、版本名称）
    - `core.url.url_modifier.auto_* / fstr_*`
    - `core.resource.search_filter.auto_*`
    - `core.resource.search_index.auto_* / fstr_*`
    - `core.resource.search_suggester.auto_* / key_* / fstr_*`
    - `core.resource.search_engine.auto_* / fstr_* / key_*`
    - `core.resource.resource_parser.auto_* / fstr_*`
    - `core.resource.resource_fetcher.auto_* / fstr_*`
    - `core.resource.resource_library.auto_*`
    - `core.resource.resource_processor.auto_*`
    - `core.resource.textbook_info.auto_* / fstr_*`
    - `core.infrastructure.logger.auto_* / fstr_* / key_*`
    - `core.infrastructure.crash_handler.auto_*`
    - `core.infrastructure.path_resolver.auto_*`
    - `core.download.downloader.auto_* / fstr_*`（其中 `auto_005` 为教材分类规则）
    - `core.download.file_categorizer.auto_*`
    - `core.download.download_verifier.auto_* / fstr_*`
    - `core.search.approximate_match_default`
    - `core.config.textbook_download_dir`
  - **结构差异**：可能缺少 `zh_CN.json` 中新增的键，或存在 `zh_CN.json` 中已删除的多余键。

## 计划变更

### 步骤 1：编写并运行同步脚本

在 `.dev/test/` 下创建临时脚本 `sync_zh_tw.py`（执行后可选择删除）：

- 加载 `i18n/zh_CN.json` 和 `i18n/zh_TW.json`。
- 定义教材相关键的匹配规则（正则或前缀集合）。
- 遍历 `zh_TW.json`，删除所有匹配教材相关规则的键。
- 递归对比两文件键结构：
  - 对于 `zh_CN.json` 中有而 `zh_TW.json` 中无的键，从 `zh_CN.json` 复制值到 `zh_TW.json`（作为初始值，后续可人工校对繁体翻译）。
  - 对于 `zh_TW.json` 中有而 `zh_CN.json` 中无的键，直接删除（已去除教材相关项后剩余的孤立键）。
- 保持 JSON 中键的原始顺序与 `zh_CN.json` 一致。
- 将结果写回 `i18n/zh_TW.json`，使用 `ensure_ascii=False, indent=4` 保证可读性。

### 步骤 2：人工校对关键繁体翻译

脚本同步后，重点检查以下繁体表达是否符合台湾地区习惯：
- `common.ok`：確定
- `common.cancel`：取消
- `common.save`：儲存
- `settings.tabs.interface`：介面
- `settings.advanced.enable_debug_mode`：啟用偵錯模式
- 其他已有翻译保持不变，仅对脚本从 `zh_CN.json` 复制过来的新增键进行繁体化。

### 步骤 3：验证

- 使用 `json.load` 验证 `zh_TW.json` 语法正确。
- 运行 `python -c "from core.i18n import set_language, _; set_language('zh_TW'); print(_('app.name'))"` 确认翻译器可正常加载。
- 运行搜索回归测试 `python .dev/test/test_search_service.py` 与 `python .dev/test/verify_multilingual_search.py`，确认切换语言不影响搜索功能。

### 步骤 4：版本号与更新日志

- 当前版本为 `5.6.16 Beta 8`（预发布版本），如本次同步作为独立迭代，递增预发布标识为 `5.6.16 Beta 9`。
- 在 `.dev/产品更新信息.md` 中添加 Beta 9 记录，说明繁体中文语言包同步与教材相关翻译项清理。

## 假设与决策

- 以 `zh_CN.json` 为唯一基准，因为其他语言包（`en_US`、`ja_JP`、`lzh_CN`、`emo_JI`）也已按相同规范清理过教材相关项。
- 教材相关翻译项全部删除，不保留在 `zh_TW.json` 中，与之前对其他语言包的处理保持一致。
- 新增键的初始值先使用 `zh_CN.json` 中的简体中文，再由人工校对为繁体中文，避免程序运行时因键缺失而回退显示键名。

## 验证步骤

1. `python -m py_compile .dev/test/sync_zh_tw.py`
2. `python .dev/test/sync_zh_tw.py`
3. `python -m json.tool i18n/zh_TW.json > /dev/null`
4. `python -c "from core.i18n import set_language, _; set_language('zh_TW'); print(_('app.name'))"`
5. `python .dev/test/test_search_service.py`
6. `python .dev/test/verify_multilingual_search.py`
7. 更新 `core/infrastructure/version.py` 与 `.dev/产品更新信息.md`
