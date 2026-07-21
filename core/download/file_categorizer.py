"""文件分类保存模块"""
import os
from core.infrastructure.logger import log

# 分类规则内部常量（与语言无关）
CATEGORIZE_BY_SUBJECT = 'by_subject'
CATEGORIZE_BY_GRADE = 'by_grade'
CATEGORIZE_BY_VERSION = 'by_version'
CATEGORIZE_BY_SUBJECT_AND_GRADE = 'by_subject_and_grade'

# 兼容旧版设置中可能出现的中文翻译值
_LEGACY_CATEGORIZE_MAP = {
    '按科目': CATEGORIZE_BY_SUBJECT,
    '按年级': CATEGORIZE_BY_GRADE,
    '按版本': CATEGORIZE_BY_VERSION,
    '按科目和年级': CATEGORIZE_BY_SUBJECT_AND_GRADE,
}


def _normalize_categorize_rule(rule):
    """将分类规则统一转换为内部常量值。

    Args:
        rule: 原始分类规则值。

    Returns:
        str: 规范化后的分类规则常量。
    """
    if not rule:
        return CATEGORIZE_BY_SUBJECT
    rule = str(rule).strip().lower()
    if rule in (CATEGORIZE_BY_SUBJECT, CATEGORIZE_BY_GRADE, CATEGORIZE_BY_VERSION, CATEGORIZE_BY_SUBJECT_AND_GRADE):
        return rule
    return _LEGACY_CATEGORIZE_MAP.get(rule, CATEGORIZE_BY_SUBJECT)


class FileCategorizer:
    """文件分类器，根据不同的规则将文件分类保存"""

    @staticmethod
    def get_categorized_path(base_dir, rule, title=None, subject=None, grade=None, version=None):
        """根据分类规则获取文件保存路径"""
        try:
            normalized_rule = _normalize_categorize_rule(rule)
            if normalized_rule == CATEGORIZE_BY_SUBJECT:
                category = subject or FileCategorizer._extract_subject(title)
                category_dir = '其他科目' if not category else category
            elif normalized_rule == CATEGORIZE_BY_GRADE:
                category = grade or FileCategorizer._extract_grade(title)
                category_dir = '其他年级' if not category else category
            elif normalized_rule == CATEGORIZE_BY_VERSION:
                category = version or FileCategorizer._extract_version(title)
                category_dir = '其他版本' if not category else category
            elif normalized_rule == CATEGORIZE_BY_SUBJECT_AND_GRADE:
                subject_part = subject or FileCategorizer._extract_subject(title) or '其他科目'
                grade_part = grade or FileCategorizer._extract_grade(title) or '其他年级'
                category_dir = os.path.join(subject_part, grade_part)
            else:
                category_dir = '未分类'
            target_dir = os.path.join(base_dir, category_dir)
            os.makedirs(target_dir, exist_ok=True)
            log('INFO', f'文件分类: {category_dir}')
            return target_dir
        except Exception as e:
            log('ERROR', f'文件分类失败: {e}')
            return base_dir

    @staticmethod
    def _extract_subject(title):
        """从标题中提取科目信息"""
        if not title:
            return None
        subjects = ['语文', '数学', '英语', '物理', '化学', '生物', '历史', '地理', '政治', '美术', '音乐', '体育', '信息技术', '科学']
        for subject in subjects:
            if subject in title:
                return subject
        return None

    @staticmethod
    def _extract_grade(title):
        """从标题中提取年级信息"""
        if not title:
            return None
        grades = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级', '七年级', '八年级', '九年级', '高一', '高二', '高三', '一年级上册', '一年级下册', '二年级上册', '二年级下册', '三年级上册', '三年级下册', '四年级上册', '四年级下册', '五年级上册', '五年级下册', '六年级上册', '六年级下册']
        for grade in grades:
            if grade in title:
                return grade
        return None

    @staticmethod
    def _extract_version(title):
        """从标题中提取版本信息"""
        if not title:
            return None
        versions = ['人教版', '北师大版', '苏教版', '外研社版', '冀教版', '沪教版', '华师大版', '浙教版', '鲁教版', '教科版', '湘教版', '鄂教版']
        for version in versions:
            if version in title:
                return version
        return None