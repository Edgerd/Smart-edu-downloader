# 智慧中小学课本下载工具

[![Stars](https://img.shields.io/github/stars/Edgerd/Smart-edu-downloader?style=flat&logo=data:image/svg%2bxml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZlcnNpb249IjEiIHdpZHRoPSIxNiIgaGVpZ2h0PSIxNiI+PHBhdGggZD0iTTggLjI1YS43NS43NSAwIDAgMSAuNjczLjQxOGwxLjg4MiAzLjgxNSA0LjIxLjYxMmEuNzUuNzUgMCAwIDEgLjQxNiAxLjI3OWwtMy4wNDYgMi45Ny43MTkgNC4xOTJhLjc1MS43NTEgMCAwIDEtMS4wODguNzkxTDggMTIuMzQ3bC0zLjc2NiAxLjk4YS43NS43NSAwIDAgMS0xLjA4OC0uNzlsLjcyLTQuMTk0TC44MTggNi4zNzRhLjc1Ljc1IDAgMCAxIC40MTYtMS4yOGw0LjIxLS42MTFMNy4zMjcuNjY4QS43NS43NSAwIDAgMSA4IC4yNVoiIGZpbGw9IiNlYWM1NGYiLz48L3N2Zz4=&logoSize=auto&label=Stars&labelColor=444444&color=eac54f)](https://github.com/Edgerd/Smart-edu-downloader)
[![Issues](https://img.shields.io/github/issues/Edgerd/Smart-edu-downloader?style=flat&label=Issues&labelColor=444444&color=1F883D)](https://github.com/Edgerd/Smart-edu-downloader/issues)
[![动态](https://img.shields.io/badge/动态-BiliBili-00A4DB?style=flat&labelColor=444444&logoSize=auto)](https://space.bilibili.com/3537111380658360/dynamic)
[![赞助](https://img.shields.io/badge/赞助-爱发电-946ce6?style=flat&labelColor=444444&logoSize=auto)](https://ifdian.net/a/edgerd)

一个基于 PyQt5 开发的教育资源下载工具，提供简洁的图形界面，支持智能搜索、资源浏览、批量下载和个性化设置。

> 当前版本：`5.6.17 Beta 2`  
> 作者：[Edgerd](https://space.bilibili.com/3537111380658360)

## 📖 主要功能

- 智能解析或检索教育平台 URL 自动解析课本链接，也可输入中文关键词搜索教材资源。
- 可按学科、年级、版本等维度筛选和浏览课本资源。
- 支持多线程下载、下载历史记录、文件自动分类命名。
- 教材封面预览，异步加载教材封面，本地缓存 7 天自动清理。
- 自动检测剪贴板中的教育平台链接，前台唤醒并自动填充。
- 支持浅色主题、自定义主题色，内置多语言切换。
- 首次启动时提供欢迎向导，帮助完成基础设置。

## 运行环境

- **操作系统**：Windows 10 / Windows 11
- **Python**：3.10 及以上（推荐 3.13）
- **依赖库**：PyQt5、requests、beautifulsoup4、PyMuPDF、qfluentwidgets

## 快速开始

### 一、下载程序

#### 1. 下载文件
打开右侧 Releases 下载程序文件

#### 2. 解压程序
使用压缩软件解压程序

#### 3. 开始使用
启动程序 按新手引导使用

### 二、自行打包

#### 1. 克隆仓库

```bash
git clone https://github.com/Edgerd/Smart-edu-downloader.git
cd Smart-edu-downloader
```

#### 2. 创建虚拟环境（推荐）

```bash
python -m venv .venv
.venv\Scripts\activate
```

#### 3. 安装依赖

```bash
pip install -r requirements.txt
```

#### 4. 运行程序

```bash
python main.py
```

## 项目结构

```
Smart-edu-downloader/
├── core/                   # 核心功能模块
│   ├── cache/              # 缓存管理、剪贴板监控、搜索历史
│   ├── config/             # 配置与主题管理
│   ├── docs/               # 文档处理
│   ├── download/           # 下载器、下载历史、文件分类
│   ├── i18n/               # 国际化翻译
│   ├── infrastructure/     # 日志、崩溃处理、路径解析、启动初始化
│   ├── network/            # HTTP 客户端、Token 加密
│   ├── resource/           # 资源库、搜索、解析、封面
│   ├── settings/           # 设置相关管理
│   ├── ui/                 # UI 通用工具
│   └── url/                # URL 处理
├── gui/                    # 图形界面
│   ├── components/         # 可复用组件
│   ├── managers/           # 页面、动画、设置管理
│   ├── pages/              # 各个页面（首页、资源库、下载、设置等）
│   ├── widgets/            # 自定义控件
│   └── welcome/            # 新手引导向导
├── resources/              # 资源文件
│   ├── fonts/              # 字体
│   ├── i18n/               # 语言包
│   ├── icons/              # 图标
│   └── images/             # 图片
├── main.py                 # 程序入口
├── version.py              # 版本号
└── .dev/                   # 开发文档与测试工具
```

## 许可证

本项目仅供学习交流使用，请勿用于商业用途。

## 反馈与支持

如有问题或建议，欢迎通过 B 站私信或 GitHub Issues 反馈。
