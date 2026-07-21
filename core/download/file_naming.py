# -*- coding: utf-8 -*-
"""文件命名规则模块"""
import time
from core.infrastructure.logger import log

# 文件命名规则常量（语言无关，持久化存储）
FILE_NAMING_DEFAULT = 'default'
FILE_NAMING_TEXTBOOK_NAME = 'textbook_name'
FILE_NAMING_TIMESTAMP = 'timestamp'
FILE_NAMING_TEXTBOOK_NAME_TIMESTAMP = 'textbook_name_timestamp'


class FileNameGenerator:
    """文件名生成器，支持多种命名规则"""

    @staticmethod
    def generate_filename(rule, title=None, chapters=None, url=None, include_chapter=False, include_timestamp=False):
        """根据规则生成文件名"""
        try:
            if rule == FILE_NAMING_TEXTBOOK_NAME:
                filename = FileNameGenerator._generate_by_title(title)
            elif rule == FILE_NAMING_TIMESTAMP:
                filename = FileNameGenerator._generate_by_timestamp()
            elif rule == FILE_NAMING_TEXTBOOK_NAME_TIMESTAMP:
                filename = FileNameGenerator._generate_by_title_and_timestamp(title)
            else:
                # default 规则
                filename = FileNameGenerator._generate_default(url, title)

            # 如果包含章节信息，添加章节前缀
            if include_chapter and chapters:
                chapter_prefix = FileNameGenerator._get_chapter_prefix(chapters)
                if chapter_prefix:
                    name_parts = filename.rsplit('.', 1)
                    filename = f"{name_parts[0]}_{chapter_prefix}.{name_parts[1] if len(name_parts) > 1 else 'pdf'}"

            # 如果包含时间戳且规则不包含
            if include_timestamp and rule not in [FILE_NAMING_TIMESTAMP, FILE_NAMING_TEXTBOOK_NAME_TIMESTAMP]:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                name_parts = filename.rsplit('.', 1)
                filename = f"{name_parts[0]}_{timestamp}.{name_parts[1] if len(name_parts) > 1 else 'pdf'}"

            return filename
            
        except Exception as e:
            log("ERROR", f"生成文件名失败: {e}")
            # 返回默认文件名
            return f"download_{int(time.time())}.pdf"
    
    @staticmethod
    def _generate_by_title(title):
        """根据教材名称生成文件名"""
        if title:
            safe_title = FileNameGenerator._sanitize_filename(title)
            return f"{safe_title}.pdf"
        return f"download_{int(time.time())}.pdf"
    
    @staticmethod
    def _generate_by_timestamp():
        """根据时间戳生成文件名"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        return f"download_{timestamp}.pdf"
    
    @staticmethod
    def _generate_by_title_and_timestamp(title):
        """根据教材名称和时间戳生成文件名"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        if title:
            safe_title = FileNameGenerator._sanitize_filename(title)
            return f"{safe_title}_{timestamp}.pdf"
        return f"download_{timestamp}.pdf"
    
    @staticmethod
    def _generate_default(url, title):
        """默认命名规则"""
        if title:
            safe_title = FileNameGenerator._sanitize_filename(title)
            return f"{safe_title}.pdf"
        return f"download_{int(time.time())}.pdf"
    
    @staticmethod
    def _sanitize_filename(filename):
        """清理文件名中的非法字符"""
        # 替换Windows和Linux文件名中的非法字符
        illegal_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
        for char in illegal_chars:
            filename = filename.replace(char, '_')
        
        # 限制文件名长度
        if len(filename) > 100:
            filename = filename[:100]
        
        return filename.strip()
    
    @staticmethod
    def _get_chapter_prefix(chapters):
        """获取章节前缀"""
        if not chapters or not isinstance(chapters, list):
            return ""
        
        # 获取第一个章节的名称
        first_chapter = chapters[0] if chapters else None
        if first_chapter and isinstance(first_chapter, dict):
            chapter_title = first_chapter.get("title", "")
            if chapter_title:
                # 清理章节名称
                return FileNameGenerator._sanitize_filename(chapter_title)[:50]
        
        return ""
