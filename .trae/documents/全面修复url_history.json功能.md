# URL History 功能修复计划

## 当前状态分析

### 涉及文件
- `core/url_modifier.py` — URLModifier 类，负责 URL 修改和历史记录管理
- `gui/pages/home_page.py` — 主页，创建独立 URLModifier 实例并显示历史表格
- `gui/pages/more_page.py` — 更多页面，创建独立 URLModifier 实例并显示历史表格

### 核心问题

1. **多实例数据不同步**：`home_page.py` 和 `more_page.py` 各自实例化 `URLModifier()`，导致两个独立的内存历史列表。一个页面写入的改动另一个页面不会立即看到。

2. **缺少单例模式**：项目中其他模块（如 `settings_manager.py`、`downloader.py`）都使用单例模式，但 `URLModifier` 没有。

3. **无线程安全**：历史记录的读写没有使用锁，多线程场景下可能导致数据竞争或文件损坏。

4. **每次修改都写盘**：`_add_to_history()` 每次调用都会执行磁盘写入，效率低且增加冲突风险。

5. **相对路径风险**：`history_file = 'url_history.json'` 使用相对路径，可能因工作目录变化导致读写位置不一致。

6. **无去重机制**：相同 URL 可以被重复添加到历史记录中。

7. **显示数量不一致**：home_page 显示 8 条，more_page 显示 10 条。

## 修复方案

### 1. URLModifier 改造为单例模式

**文件**: `core/url_modifier.py`

- 添加类级 `_instance` 变量和 `__new__` 方法实现单例
- 添加 `threading.Lock` 保护历史记录的并发读写
- 将 `history_file` 改为基于项目根目录的绝对路径
- 添加去重逻辑：添加 URL 前检查是否已存在（按 URL 字符串匹配），若存在则更新时间戳并移到最前，而不是重复添加
- 添加 `_reload_history()` 方法用于从文件重新加载最新数据

```python
class URLModifier:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### 2. 绝对路径处理

**文件**: `core/url_modifier.py`

- 使用 `os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` 获取项目根目录
- 拼接 `url_history.json` 绝对路径

### 3. 线程安全的读写操作

**文件**: `core/url_modifier.py`

- `_load_history()`: 加读锁
- `_save_history()`: 加写锁
- `_add_to_history()`: 加锁保护，并在保存前执行去重

### 4. 去重逻辑

**文件**: `core/url_modifier.py`

- `_add_to_history()` 中：
  - 检查 `url` 是否已存在于 `self.history`
  - 若存在，删除旧条目，更新时间戳后插入到最前面
  - 若不存在，正常插入
  - 保持最多 100 条记录

### 5. 统一显示数量

**文件**: `gui/pages/home_page.py` 和 `gui/pages/more_page.py`

- 统一使用常量 `MAX_HISTORY_DISPLAY = 10`
- 两个页面的历史表格都显示最近 10 条

### 6. 跨页面刷新同步

**文件**: `gui/pages/home_page.py` 和 `gui/pages/more_page.py`

- 由于单例共享同一内存数据，新增 URL 时另一页面已可读取到最新数据
- 在 `home_page.py` 的 `_process_url()`、`_open_in_browser()` 成功回调中，刷新历史表格
- 在 `more_page.py` 页面 `showEvent` 时刷新历史表格

## 假设与决策

- 不引入数据库或外部存储，继续使用 JSON 文件
- 不改动 `search_history.json` 等其他历史记录功能，仅修复 `url_history.json`
- 保持现有 UI 结构和交互风格不变

## 验证步骤

1. 启动程序，在主页输入 URL 并处理
2. 检查 `url_history.json` 文件内容是否正确写入
3. 切换到更多页面，确认"链接处理"标签页显示新增记录
4. 切回主页，确认历史表格同步显示
5. 重复添加相同 URL，验证去重逻辑生效
6. 并发快速添加多个 URL，验证无数据丢失或文件损坏
