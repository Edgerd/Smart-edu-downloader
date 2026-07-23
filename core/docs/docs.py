# -*- coding: utf-8 -*-
"""文档模块"""
from core.i18n import _

import os


def get_readme_html():
    """获取说明文档HTML内容"""
    return _("core.docs.readme_html_content")


def create_readme_doc():
    """创建说明文档到文件系统"""
    doc_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), _("core.docs.readme_html"))
    content = get_readme_html()

    with open(doc_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return doc_path


def get_readme_path():
    """获取说明文档路径"""
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), _("core.docs.readme_html"))