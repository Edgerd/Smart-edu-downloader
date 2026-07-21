# Smart-edu-downloader 项目说明

## 项目概述

国家中小学生教育云平台课本下载器 

## 作者信息

- 作者: Edgerd
- B站主页: <https://space.bilibili.com/3537111380658360>

## 项目结构

```
Smart-edu-downloader/
├── core/                      # 核心模块
│   ├── __init__.py
│   ├── downloader.py         # 下载器模块（多线程、断点续传）
│   ├── exceptions.py          # 自定义异常
│   ├── textbook_info.py       # 教材信息提取
│   ├── url_modifier.py        # URL处理
│   └── version.py             # 版本信息
├── gui/                       # GUI界面
│   ├── __init__.py
│   ├── main_window.py         # 主窗口（融合PCLL和SED风格）
│   └── pages/                 # 页面模块
│       ├── __init__.py
│       ├── about_dialog.py    # 关于对话框
│       ├── download_page.py   # 下载管理页面
│       ├── home_page.py       # 主页
│       ├── more_page.py       # 更多功能页面
│       └── setting_page.py    # 设置页面
├── resources/                 # 资源文件
├── __init__.py
├── main.py                    # 主入口文件
└── requirements.txt           # 依赖列表
```

## 核心功能

1. **下载功能**：多线程断点续传下载
2. **URL处理**：自动验证和修复URL
3. **教材信息**：自动提取教材标题和封面
4. **收藏夹**：收藏常用URL
5. **历史记录**：记录操作历史

## 界面设计（PCLL风格）

- 现代化UI设计
- 圆角窗口效果
- 平滑页面切换动画
- 渐变色标题栏
- 响应式布局

## 依赖项

- PyQt5 >= 5.15.10
- requests >= 2.31.0
- beautifulsoup4 >= 4.12.0
- PyMuPDF >= 1.23.0
- psutil >= 5.9.0

## 安装和运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行程序
python main.py
```

## 版本历史

- v5.0: 融合PCLL和SED技术方案，PyQt5现代化界面
- v3.x: 早期版本

