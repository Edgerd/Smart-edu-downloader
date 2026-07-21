# 统一缓存路径检查清单

* [x] core/infrastructure/path\_resolver.py 已创建并导出所有路径函数

* [x] SettingsManager 使用 runtime/settings/settings.json 路径

* [x] 旧根目录 settings.json 能自动迁移到 runtime/settings/

* [x] more\_page.py 搜索历史路径通过 path\_resolver 获取

* [x] download\_history.py 下载历史路径在 runtime/cache/ 下

* [x] setting\_page.py 不再使用裸文件名 settings\_file

* [x] log\_file\_handler.py 使用 path\_resolver 获取日志路径

* [x] url\_modifier.py 使用 path\_resolver 获取 URL 历史路径

* [x] downloader.py 使用 path\_resolver 获取下载任务路径

* [x] resource\_library.py 使用 path\_resolver 获取缓存路径

* [x] search\_engine.py 使用 path\_resolver 获取搜索历史路径

* [x] cache\_manager.py 使用 path\_resolver 获取缓存和临时目录路径

* [x] core/settings.json 已迁移并删除

* [x] core/runtime/ 目录已迁移并删除

* [x] clipboard\_monitor.py 日志函数已统一为 log

* [x] cover\_cache.py 封面缓存路径通过 path\_resolver 获取

* [x] main.py 启动时调用 migrate\_all\_old\_data()

* [x] 程序能正常启动，无路径相关错误

* [x] 所有缓存文件均位于 runtime/ 目录下