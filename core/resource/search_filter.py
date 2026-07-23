"""
搜索结果过滤器模块

提供可组合的搜索结果过滤器，用于在搜索完成后对结果进行多维度筛选。
支持：
1. 学科过滤（SubjectFilter）
2. 年级过滤（GradeFilter）
3. 版本过滤（PublisherFilter）
4. 组合过滤（CompositeFilter，AND 逻辑）
5. 工厂类便捷创建（FilterFactory）
"""
from core.i18n import _
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from core.infrastructure.logger import log

class SearchFilter(ABC):
    """搜索结果过滤器抽象基类

    所有具体过滤器必须实现 filter 方法，对传入的搜索结果列表进行筛选，
    返回通过筛选的结果列表。过滤器之间互不感知，可独立使用或组合使用。
    """

    @abstractmethod
    def filter(self, results: List[Dict]) -> List[Dict]:
        """对搜索结果进行过滤

        Args:
            results: 搜索结果列表，每个元素为包含资源信息的字典，
                     至少包含 subject、grade、publisher 等字段。

        Returns:
            过滤后的结果列表，顺序与输入保持一致。
        """
        raise NotImplementedError

class SubjectFilter(SearchFilter):
    """学科过滤器

    根据指定的学科名称对搜索结果进行过滤，仅保留 subject 字段匹配的结果。
    匹配规则为不区分大小写的包含匹配。

    Attributes:
        subject: 目标学科名称。
    """

    def __init__(self, subject: str):
        """初始化学科过滤器

        Args:
            subject: 目标学科名称，如 "语文"、"数学"、"英语" 等。
        """
        self.subject = subject
        log('DEBUG', f"学科过滤器已创建: subject='{subject}'")

    def filter(self, results: List[Dict]) -> List[Dict]:
        """按学科过滤搜索结果

        Args:
            results: 搜索结果列表。

        Returns:
            仅包含匹配学科的结果列表。
        """
        if not self.subject:
            log('WARNING', '学科过滤器: 目标学科为空，返回全部结果')
            return results
        filtered = [item for item in results if self._match_subject(item.get('subject', ''))]
        log('DEBUG', f"学科过滤: {len(results)} -> {len(filtered)} (subject='{self.subject}')")
        return filtered

    def _match_subject(self, resource_subject: str) -> bool:
        """检查资源学科是否与目标学科匹配

        Args:
            resource_subject: 资源中的学科字段值。

        Returns:
            是否匹配。
        """
        return self.subject.lower() in resource_subject.lower()

class GradeFilter(SearchFilter):
    """年级过滤器

    根据指定的年级名称对搜索结果进行过滤，仅保留 grade 字段匹配的结果。
    匹配规则为不区分大小写的包含匹配。

    Attributes:
        grade: 目标年级名称。
    """

    def __init__(self, grade: str):
        """初始化年级过滤器

        Args:
            grade: 目标年级名称，如 "一年级"、"七年级" 等。
        """
        self.grade = grade
        log('DEBUG', f"年级过滤器已创建: grade='{grade}'")

    def filter(self, results: List[Dict]) -> List[Dict]:
        """按年级过滤搜索结果

        Args:
            results: 搜索结果列表。

        Returns:
            仅包含匹配年级的结果列表。
        """
        if not self.grade:
            log('WARNING', '年级过滤器: 目标年级为空，返回全部结果')
            return results
        filtered = [item for item in results if self._match_grade(item.get('grade', ''))]
        log('DEBUG', f"年级过滤: {len(results)} -> {len(filtered)} (grade='{self.grade}')")
        return filtered

    def _match_grade(self, resource_grade: str) -> bool:
        """检查资源年级是否与目标年级匹配

        Args:
            resource_grade: 资源中的年级字段值。

        Returns:
            是否匹配。
        """
        return self.grade.lower() in resource_grade.lower()

class PublisherFilter(SearchFilter):
    """出版社过滤器

    根据指定的出版社名称对搜索结果进行过滤，仅保留 publisher 字段匹配的结果。
    匹配规则为不区分大小写的包含匹配。

    Attributes:
        publisher: 目标出版社名称。
    """

    def __init__(self, publisher: str):
        """初始化出版社过滤器

        Args:
            publisher: 目标出版社名称，如 "人教版"、"北师大版" 等。
        """
        self.publisher = publisher
        log('DEBUG', f"版本过滤器已创建: publisher='{publisher}'")

    def filter(self, results: List[Dict]) -> List[Dict]:
        """按出版社过滤搜索结果

        Args:
            results: 搜索结果列表。

        Returns:
            仅包含匹配出版社的结果列表。
        """
        if not self.publisher:
            log('WARNING', '版本过滤器: 目标出版社为空，返回全部结果')
            return results
        filtered = [item for item in results if self._match_publisher(item.get('publisher', ''))]
        log('DEBUG', f"版本过滤: {len(results)} -> {len(filtered)} (publisher='{self.publisher}')")
        return filtered

    def _match_publisher(self, resource_publisher: str) -> bool:
        """检查资源出版社是否与目标出版社匹配

        Args:
            resource_publisher: 资源中的出版社字段值。

        Returns:
            是否匹配。
        """
        return self.publisher.lower() in resource_publisher.lower()

class CompositeFilter(SearchFilter):
    """组合过滤器

    将多个过滤器以 AND 逻辑组合，依次应用每个子过滤器。
    仅保留通过所有子过滤器筛选的结果。

    Attributes:
        _filters: 内部持有的子过滤器列表。
    """

    def __init__(self, filters: Optional[List[SearchFilter]]=None):
        """初始化组合过滤器

        Args:
            filters: 子过滤器列表，可选。默认为空列表。
        """
        self._filters: List[SearchFilter] = list(filters) if filters else []
        log('DEBUG', f'组合过滤器已创建: 包含 {len(self._filters)} 个子过滤器')

    def add_filter(self, filter_instance: SearchFilter) -> None:
        """添加一个子过滤器

        Args:
            filter_instance: 要添加的过滤器实例。
        """
        self._filters.append(filter_instance)
        log('DEBUG', f'组合过滤器: 添加子过滤器 {type(filter_instance).__name__}，当前共 {len(self._filters)} 个')

    def remove_filter(self, filter_instance: SearchFilter) -> None:
        """移除一个子过滤器

        Args:
            filter_instance: 要移除的过滤器实例。
        """
        if filter_instance in self._filters:
            self._filters.remove(filter_instance)
            log('DEBUG', f'组合过滤器: 移除子过滤器 {type(filter_instance).__name__}，当前共 {len(self._filters)} 个')

    def clear(self) -> None:
        """清空所有子过滤器"""
        self._filters.clear()
        log('DEBUG', '组合过滤器: 已清空所有子过滤器')

    def filter(self, results: List[Dict]) -> List[Dict]:
        """依次应用所有子过滤器，返回交集结果

        Args:
            results: 搜索结果列表。

        Returns:
            通过所有子过滤器筛选的结果列表。
        """
        if not self._filters:
            log('DEBUG', '组合过滤器: 无子过滤器，返回全部结果')
            return results
        current = results
        for f in self._filters:
            current = f.filter(current)
            if not current:
                log('DEBUG', f'组合过滤器: 经 {type(f).__name__} 过滤后结果为空，提前终止')
                break
        return current

    @property
    def filter_count(self) -> int:
        """获取当前子过滤器数量"""
        return len(self._filters)

class FilterFactory:
    """过滤器工厂类

    提供便捷的静态方法，用于创建各种类型的过滤器实例。
    所有方法均为静态方法，无需实例化即可使用。

    Example:
        >>> subject_filter = FilterFactory.create_subject_filter("语文")
        >>> grade_filter = FilterFactory.create_grade_filter("七年级")
        >>> publisher_filter = FilterFactory.create_publisher_filter("人教版")
    """

    @staticmethod
    def create_subject_filter(subject: str) -> SubjectFilter:
        """创建学科过滤器

        Args:
            subject: 目标学科名称。

        Returns:
            SubjectFilter 实例。
        """
        log('DEBUG', f"FilterFactory: 创建学科过滤器 (subject='{subject}')")
        return SubjectFilter(subject)

    @staticmethod
    def create_grade_filter(grade: str) -> GradeFilter:
        """创建年级过滤器

        Args:
            grade: 目标年级名称。

        Returns:
            GradeFilter 实例。
        """
        log('DEBUG', f"FilterFactory: 创建年级过滤器 (grade='{grade}')")
        return GradeFilter(grade)

    @staticmethod
    def create_publisher_filter(publisher: str) -> PublisherFilter:
        """创建出版社过滤器

        Args:
            publisher: 目标出版社名称。

        Returns:
            PublisherFilter 实例。
        """
        log('DEBUG', f"FilterFactory: 创建版本过滤器 (publisher='{publisher}')")
        return PublisherFilter(publisher)

    @staticmethod
    def create_composite_filter(subject: Optional[str]=None, grade: Optional[str]=None, publisher: Optional[str]=None) -> CompositeFilter:
        """根据参数创建组合过滤器

        仅当参数非空时才添加对应的子过滤器。

        Args:
            subject: 目标学科名称，可选。
            grade: 目标年级名称，可选。
            publisher: 目标出版社名称，可选。

        Returns:
            CompositeFilter 实例，包含所有非空参数对应的子过滤器。
        """
        composite = CompositeFilter()
        if subject:
            composite.add_filter(SubjectFilter(subject))
        if grade:
            composite.add_filter(GradeFilter(grade))
        if publisher:
            composite.add_filter(PublisherFilter(publisher))
        log('DEBUG', f'FilterFactory: 创建组合过滤器，包含 {composite.filter_count} 个子过滤器')
        return composite
if __name__ == '__main__':
    '模块自测代码'
    sample_results: List[Dict] = [{'title': '语文一年级上册', 'subject': '语文', 'grade': '一年级', 'publisher': '人教版'}, {'title': '数学一年级上册', 'subject': '数学', 'grade': '一年级', 'publisher': '人教版'}, {'title': '语文七年级上册', 'subject': '语文', 'grade': '七年级', 'publisher': '人教版'}, {'title': '数学七年级上册', 'subject': '数学', 'grade': '七年级', 'publisher': '北师大版'}, {'title': '英语七年级上册', 'subject': '英语', 'grade': '七年级', 'publisher': '人教版'}, {'title': '语文一年级下册', 'subject': '语文', 'grade': '一年级', 'publisher': '苏教版'}]
    print('=== 学科过滤: 语文 ===')
    sf = FilterFactory.create_subject_filter('语文')
    for item in sf.filter(sample_results):
        print(f"  {item['title']}")
    print('\n=== 年级过滤: 七年级 ===')
    gf = FilterFactory.create_grade_filter('七年级')
    for item in gf.filter(sample_results):
        print(f"  {item['title']}")
    print('\n=== 版本过滤: 人教版 ===')
    pf = FilterFactory.create_publisher_filter('人教版')
    for item in pf.filter(sample_results):
        print(f"  {item['title']}")
    print('\n=== 组合过滤: 语文 + 七年级 + 人教版 ===')
    cf = FilterFactory.create_composite_filter(subject='语文', grade='七年级', publisher='人教版')
    for item in cf.filter(sample_results):
        print(f"  {item['title']}")
    print('\n=== 手动组合: 数学 + 一年级 ===')
    manual = CompositeFilter()
    manual.add_filter(SubjectFilter('数学'))
    manual.add_filter(GradeFilter('一年级'))
    for item in manual.filter(sample_results):
        print(f"  {item['title']}")
    print('\n=== 空过滤器 ===')
    empty = CompositeFilter()
    for item in empty.filter(sample_results):
        print(f"  {item['title']}")