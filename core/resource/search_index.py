"""
倒排索引搜索模块

提供基于倒排索引的高效资源检索功能：
1. 中文字符级 bigram（2-gram）分词 + 单字符词条
2. 倒排索引构建与维护（关键词 -> 资源ID集合）
3. O(1) 关键词查询
4. 增量更新与清空
"""
from typing import List, Dict, Set
from core.infrastructure.logger import log

class SearchIndex:
    """倒排索引搜索类

    使用字符级 bigram 对资源的标题、学科、年级、版本字段进行分词，
    构建倒排映射（关键词 -> 资源ID集合），支持 O(1) 查询。

    Attributes:
        _index: 倒排索引字典，{keyword: set(resource_ids)}
        _resource_tokens: 反向映射，{resource_id: set(tokens)}，
                          用于增量更新时快速定位旧词条
    """
    _INDEX_FIELDS = ('title', 'subject', 'grade', 'publisher')

    def __init__(self) -> None:
        """初始化倒排索引，创建空的索引字典和反向映射字典。"""
        self._index: Dict[str, Set[str]] = {}
        self._resource_tokens: Dict[str, Set[str]] = {}

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """对文本进行字符级 bigram 分词，同时保留单字符词条。

        对输入文本的每个连续 2 个字符生成一个 bigram 词条，
        同时将所有单个字符也作为独立词条加入结果集。

        Args:
            text: 待分词的文本字符串。

        Returns:
            去重后的词条列表，包含所有 bigram 和单字符。

        Example:
            >>> SearchIndex._tokenize("人教版")
            ['人教', '教版', '人', '教', '版']
        """
        if not text or not text.strip():
            return []
        cleaned = text.strip()
        tokens: List[str] = []
        if len(cleaned) >= 2:
            for i in range(len(cleaned) - 1):
                tokens.append(cleaned[i:i + 2])
        tokens.extend(list(cleaned))
        return list(dict.fromkeys(tokens))

    def build_index(self, resources: List[Dict]) -> None:
        """对资源列表构建倒排索引。

        遍历所有资源，对其标题、学科、年级、版本字段进行分词，
        为每个词条建立到资源 ID 集合的映射。调用前会先清空已有索引。

        Args:
            resources: 资源字典列表，每个字典需包含 id 字段，
                       以及 title、subject、grade、publisher 中至少一个字段。

        Raises:
            ValueError: 如果 resources 不是列表类型。

        Example:
            >>> idx = SearchIndex()
            >>> idx.build_index([
            ...     {"id": "1", "title": "人教版语文", "subject": "语文", "grade": "三年级"}
            ... ])
            >>> idx.query("语文")
            ['1']
        """
        if not isinstance(resources, list):
            raise ValueError(f"resources 必须为列表类型，实际类型: {type(resources)}")
        self.clear()
        for resource in resources:
            if not isinstance(resource, dict):
                log('WARNING', f'跳过非字典类型的资源: {type(resource)}')
                continue
            self._add_resource(resource)
        log('INFO', f'倒排索引构建完成，共 {len(self._index)} 个词条，{len(self._resource_tokens)} 个资源')

    def _add_resource(self, resource: Dict) -> None:
        """将单个资源的所有词条添加到倒排索引中。

        Args:
            resource: 包含 id 及索引字段的资源字典。
        """
        resource_id = resource.get('id')
        if not resource_id:
            log('WARNING', '跳过缺少 id 字段的资源')
            return
        rid = str(resource_id)
        field_values = []
        for field in self._INDEX_FIELDS:
            value = resource.get(field, '')
            if value and str(value).strip():
                field_values.append(str(value).strip())
        if not field_values:
            log('DEBUG', f'资源 {rid} 没有可索引的字段内容')
            return
        combined = ' '.join(field_values)
        tokens = self._tokenize(combined)
        if not tokens:
            return
        self._resource_tokens[rid] = set(tokens)
        for token in tokens:
            if token not in self._index:
                self._index[token] = set()
            self._index[token].add(rid)

    def _remove_resource(self, resource_id: str) -> None:
        """从倒排索引中移除指定资源的所有词条引用。

        通过反向映射定位该资源的所有词条，从对应集合中移除资源 ID，
        并清理空集合以节省内存。

        Args:
            resource_id: 要移除的资源 ID。
        """
        if not resource_id:
            return
        rid = str(resource_id)
        tokens = self._resource_tokens.pop(rid, None)
        if tokens is None:
            return
        for token in tokens:
            token_set = self._index.get(token)
            if token_set is not None:
                token_set.discard(rid)
                if not token_set:
                    del self._index[token]

    def query(self, keyword: str) -> List[str]:
        """查询匹配关键词的资源 ID 列表。

        对输入关键词进行与构建索引时一致的分词处理，
        对所有词条对应的资源 ID 集合取交集，返回匹配的资源 ID 列表。

        Args:
            keyword: 查询关键词，支持中文文本。

        Returns:
            匹配的资源 ID 字符串列表。如果无匹配或关键词为空，返回空列表。

        Example:
            >>> idx = SearchIndex()
            >>> idx.build_index([
            ...     {"id": "1", "title": "人教版语文三年级上册"},
            ...     {"id": "2", "title": "苏教版数学四年级下册"}
            ... ])
            >>> idx.query("语文")
            ['1']
            >>> idx.query("数学")
            ['2']
            >>> idx.query("英语")
            []
        """
        if not keyword or not keyword.strip():
            return []
        tokens = self._tokenize(keyword)
        if not tokens:
            return []
        result = self._index.get(tokens[0], set())
        for token in tokens[1:]:
            result = result & self._index.get(token, set())
            if not result:
                break
        return list(result)

    def update_index(self, resource: Dict) -> None:
        """增量更新单个资源索引。

        先移除该资源在索引中的旧词条引用，再基于最新资源数据重新添加。
        如果资源 ID 之前不存在于索引中，则直接添加。

        Args:
            resource: 包含 id 及索引字段的资源字典。

        Raises:
            ValueError: 如果 resource 不是字典类型。

        Example:
            >>> idx = SearchIndex()
            >>> idx.update_index({"id": "1", "title": "人教版语文"})
            >>> idx.query("语文")
            ['1']
            >>> idx.update_index({"id": "1", "title": "苏教版数学"})
            >>> idx.query("语文")
            []
            >>> idx.query("数学")
            ['1']
        """
        if not isinstance(resource, dict):
            raise ValueError(f"resource 必须为字典类型，实际类型: {type(resource)}")
        resource_id = resource.get('id')
        if not resource_id:
            log('WARNING', 'update_index: 资源缺少 id 字段，无法更新索引')
            return
        rid = str(resource_id)
        log('DEBUG', f'增量更新索引: 资源 {rid}')
        self._remove_resource(rid)
        self._add_resource(resource)

    def clear(self) -> None:
        """清空整个倒排索引，包括所有词条映射和反向映射。

        Example:
            >>> idx = SearchIndex()
            >>> idx.update_index({"id": "1", "title": "测试"})
            >>> idx.clear()
            >>> idx.query("测试")
            []
        """
        self._index.clear()
        self._resource_tokens.clear()
        log('DEBUG', '倒排索引已清空')

    @property
    def index_size(self) -> int:
        """获取当前索引中的词条总数。

        Returns:
            倒排索引中不同关键词的数量。
        """
        return len(self._index)

    @property
    def resource_count(self) -> int:
        """获取当前索引中的资源总数。

        Returns:
            已建立索引的不同资源数量。
        """
        return len(self._resource_tokens)
if __name__ == '__main__':
    from core.infrastructure.logger import get_logger, ConsoleHandler
    _logger = get_logger('SearchIndex')
    _logger.add_handler(ConsoleHandler())
    sample_resources = [{'id': 'res_001', 'title': '人教版语文三年级上册', 'subject': '语文', 'grade': '三年级', 'publisher': '人教版'}, {'id': 'res_002', 'title': '苏教版数学四年级下册', 'subject': '数学', 'grade': '四年级', 'publisher': '苏教版'}, {'id': 'res_003', 'title': '人教版语文五年级上册', 'subject': '语文', 'grade': '五年级', 'publisher': '人教版'}]
    print('=' * 60)
    print('SearchIndex 功能演示')
    print('=' * 60)
    print('\n[1] 构建索引...')
    idx = SearchIndex()
    idx.build_index(sample_resources)
    print(f"    索引词条数: {idx.index_size}")
    print(f"    资源数量:  {idx.resource_count}")
    print('\n[2] 查询测试...')
    print(f"    查询 '语文' -> {idx.query('语文')}")
    print(f"    查询 '数学' -> {idx.query('数学')}")
    print(f"    查询 '人教版' -> {idx.query('人教版')}")
    print(f"    查询 '英语' -> {idx.query('英语')}")
    print('\n[3] 增量更新...')
    idx.update_index({'id': 'res_001', 'title': '人教版英语三年级上册', 'subject': '英语', 'grade': '三年级', 'publisher': '人教版'})
    print(f"    更新后查询 '语文' -> {idx.query('语文')}")
    print(f"    更新后查询 '英语' -> {idx.query('英语')}")
    print('\n[4] 清空索引...')
    idx.clear()
    print(f"    索引词条数: {idx.index_size}")
    print(f"    资源数量:  {idx.resource_count}")
    print(f"    查询 '语文' -> {idx.query('语文')}")
    print('\n' + '=' * 60)
    print('演示完成')
    print('=' * 60)