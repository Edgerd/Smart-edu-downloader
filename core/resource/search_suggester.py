"""
搜索建议与语义扩展模块

提供搜索建议、热门关键词、语义扩展等功能：
1. 基于资源标题和搜索历史的智能搜索建议
2. 热门关键词统计
3. 学段/学科语义扩展（如"初中"→"七年级、八年级、九年级"）
"""
from typing import List, Dict, Optional, Set
from core.infrastructure.logger import log

class SearchSuggester:
    """搜索建议生成器

    负责根据用户输入的部分关键词生成搜索建议，提供热门关键词，
    以及基于语义规则的关键词扩展。

    Attributes:
        _resources: 资源列表，每个元素为包含 title 等字段的字典。
        _history_manager: 搜索历史管理器引用（SearchHistoryManager 实例）。
    """
    _SEMANTIC_EXPANSIONS: Dict[str, List[str]] = {'初中': ['七年级', '八年级', '九年级'], '小学': ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级'], '高中': ['高一', '高二', '高三', '必修一', '必修二', '必修三', '选修一', '选修二'], '中学': ['七年级', '八年级', '九年级', '高一', '高二', '高三'], '理综': ['物理', '化学', '生物'], '文综': ['政治', '历史', '地理'], '科学': ['物理', '化学', '生物', '地理'], '信息技术': ['计算机', '编程', '信息'], '信息科技': ['计算机', '编程', '信息'], '道德与法治': ['道法', '政治', '思想品德'], '道法': ['道德与法治', '政治'], '物理': ['力学', '电学', '光学', '热学', '声学', '原子物理'], '化学': ['有机化学', '无机化学', '化学反应', '元素'], '生物': ['遗传学', '生态学', '细胞', '分子生物学'], '数学': ['代数', '几何', '函数', '概率', '统计'], '语文': ['阅读理解', '写作', '文言文', '古诗文', '现代文'], '英语': ['听力', '口语', '阅读', '写作', '语法', '词汇'], '历史': ['中国古代史', '中国近代史', '世界史', '文明史'], '地理': ['自然地理', '人文地理', '区域地理', '地图'], '政治': ['经济学', '哲学', '政治制度', '法律'], '音乐': ['乐理', '声乐', '器乐', '音乐欣赏'], '美术': ['绘画', '雕塑', '设计', '美术鉴赏'], '体育': ['田径', '球类', '体操', '武术', '游泳'], '七年级': ['初一', '七上', '七下'], '八年级': ['初二', '八上', '八下'], '九年级': ['初三', '九上', '九下'], '一年级': ['一上', '一下'], '二年级': ['二上', '二下'], '三年级': ['三上', '三下'], '四年级': ['四上', '四下'], '五年级': ['五上', '五下'], '六年级': ['六上', '六下']}

    def __init__(self):
        """初始化搜索建议生成器"""
        self._resources: List[Dict] = []
        self._history_manager = None
        log('DEBUG', 'SearchSuggester 已初始化', module='SearchSuggester')

    def set_resources(self, resources: List[Dict]) -> None:
        """设置资源列表，用于从资源标题中提取搜索建议。

        Args:
            resources: 资源字典列表，每个字典应包含 'title' 键。

        Example:
            >>> suggester = SearchSuggester()
            >>> suggester.set_resources([
            ...     {"title": "七年级数学上册人教版"},
            ...     {"title": "八年级物理下册"},
            ... ])
        """
        if not isinstance(resources, list):
            log('WARNING', 'set_resources 收到非列表类型参数，已忽略', module='SearchSuggester')
            return
        self._resources = resources
        log('INFO', f'已设置 {len(resources)} 个资源用于搜索建议', module='SearchSuggester')

    def set_history_manager(self, history_manager) -> None:
        """设置搜索历史管理器引用，用于从历史记录中提取搜索建议。

        Args:
            history_manager: SearchHistoryManager 实例，
                需实现 get_history(limit) 和 get_hot_keywords(limit) 方法。

        Example:
            >>> from core.resource.search_engine import SearchHistoryManager
            >>> suggester = SearchSuggester()
            >>> suggester.set_history_manager(SearchHistoryManager())
        """
        self._history_manager = history_manager
        log('INFO', '已设置搜索历史管理器引用', module='SearchSuggester')

    def get_suggestions(self, partial_keyword: str, limit: int=10) -> List[str]:
        """获取搜索建议。

        从资源标题和搜索历史中匹配包含 partial_keyword 的建议，
        合并去重后按相关度排序。搜索历史中的建议具有更高权重，优先显示。

        Args:
            partial_keyword: 用户输入的部分关键词（至少 1 个字符）。
            limit: 返回的建议数量上限，默认 10。

        Returns:
            去重排序后的搜索建议列表（优先展示历史记录中的匹配项）。

        Example:
            >>> suggester = SearchSuggester()
            >>> suggester.set_resources([
            ...     {"title": "七年级数学上册人教版"},
            ...     {"title": "七年级语文下册"},
            ... ])
            >>> suggester.get_suggestions("七年")
            ['七年级数学上册人教版', '七年级语文下册']
        """
        if not partial_keyword or len(partial_keyword.strip()) < 1:
            return []
        keyword = partial_keyword.strip().lower()
        scored: Dict[str, int] = {}
        self._collect_from_titles(keyword, scored)
        if self._history_manager is not None:
            self._collect_from_history(keyword, scored)
        if not scored:
            return []
        sorted_items = sorted(scored.items(), key=lambda x: (-x[1], x[0]))
        result = [item[0] for item in sorted_items[:limit]]
        log('DEBUG', f"为 '{partial_keyword}' 生成 {len(result)} 条建议", module='SearchSuggester')
        return result

    def _collect_from_titles(self, keyword: str, scored: Dict[str, int]) -> None:
        """从资源标题中收集匹配建议，基础权重为 50。

        Args:
            keyword: 小写化的部分关键词。
            scored: 建议→分数的映射字典，原地修改。
        """
        seen_suggestions: Set[str] = set()
        for resource in self._resources:
            title = resource.get('title', '')
            if not title:
                continue
            title_lower = title.lower()
            if keyword not in title_lower:
                continue
            suggestion = self._extract_context(title, keyword, max_len=40)
            if suggestion and suggestion not in seen_suggestions:
                seen_suggestions.add(suggestion)
                base_score = 100 if suggestion.lower().startswith(keyword) else 50
                scored[suggestion] = max(scored.get(suggestion, 0), base_score)

    @staticmethod
    def _extract_context(title: str, keyword: str, max_len: int=40) -> str:
        """从标题中提取包含关键词的上下文片段。

        Args:
            title: 原始标题。
            keyword: 小写化关键词。
            max_len: 最大返回长度。

        Returns:
            截取的上下文片段。
        """
        title_lower = title.lower()
        idx = title_lower.find(keyword)
        if idx == -1:
            return title[:max_len]
        start = max(0, idx - 5)
        end = min(len(title), idx + len(keyword) + 15)
        suggestion = title[start:end].strip()
        return suggestion[:max_len] if len(suggestion) > max_len else suggestion

    def _collect_from_history(self, keyword: str, scored: Dict[str, int]) -> None:
        """从搜索历史中收集匹配建议，权重更高（200 起步），以覆盖标题建议。

        Args:
            keyword: 小写化的部分关键词。
            scored: 建议→分数的映射字典，原地修改。
        """
        try:
            history = self._history_manager.get_history(limit=50)
        except Exception as e:
            log('WARNING', f'获取搜索历史失败: {e}', module='SearchSuggester')
            return
        for item in history:
            hist_kw = item.get('keyword', '')
            if not hist_kw:
                continue
            hist_lower = hist_kw.lower()
            if keyword not in hist_lower:
                continue
            base_score = 300 if hist_lower.startswith(keyword) else 200
            count_bonus = min(item.get('count', 1) * 10, 100)
            final_score = base_score + count_bonus
            scored[hist_kw] = max(scored.get(hist_kw, 0), final_score)

    def get_hot_keywords(self, limit: int=10) -> List[str]:
        """获取热门关键词。

        优先从搜索历史管理器获取按搜索频率排序的热门关键词，
        如果历史管理器不可用，则从资源标题中提取高频词作为替代。

        Args:
            limit: 返回数量上限，默认 10。

        Returns:
            热门关键词列表。

        Example:
            >>> suggester = SearchSuggester()
            >>> suggester.get_hot_keywords(5)
            []
        """
        if self._history_manager is not None:
            try:
                hot = self._history_manager.get_hot_keywords(limit=limit)
                if hot:
                    log('DEBUG', f'从历史记录获取 {len(hot)} 个热门关键词', module='SearchSuggester')
                    return hot
            except Exception as e:
                log('WARNING', f'获取热门关键词失败: {e}', module='SearchSuggester')
        fallback = self._extract_hot_from_titles(limit)
        log('DEBUG', f'从标题提取 {len(fallback)} 个热门关键词（回退方案）', module='SearchSuggester')
        return fallback

    def _extract_hot_from_titles(self, limit: int) -> List[str]:
        """从资源标题中提取出现频率最高的关键词作为回退热门关键词。

        Args:
            limit: 返回数量上限。

        Returns:
            高频关键词列表。
        """
        if not self._resources:
            return []
        word_counter: Dict[str, int] = {}
        for resource in self._resources:
            title = resource.get('title', '')
            if not title:
                continue
            segments = self._segment_title(title)
            for seg in segments:
                word_counter[seg] = word_counter.get(seg, 0) + 1
        sorted_words = sorted(word_counter.items(), key=lambda x: -x[1])
        return [word for word, _ in sorted_words[:limit]]

    @staticmethod
    def _segment_title(title: str) -> List[str]:
        """将标题切分为有意义的短词片段。

        识别年级词（如"七年级"）、学科词（如"数学"）、
        版本词（如"人教版"）等作为独立片段。

        Args:
            title: 资源标题。

        Returns:
            片段列表。
        """
        segments: List[str] = []
        n = len(title)
        for length in range(2, 7):
            for i in range(n - length + 1):
                seg = title[i:i + length]
                if seg.strip() and (not seg.isdigit()):
                    segments.append(seg)
        return segments

    def get_semantic_expansions(self, keyword: str) -> List[str]:
        """获取关键词的语义扩展。

        根据预定义的语义映射表，将关键词扩展为关联词列表。
        例如：
        - "初中" → ["七年级", "八年级", "九年级"]
        - "小学" → ["一年级", "二年级", "三年级", "四年级", "五年级", "六年级"]
        - "理综" → ["物理", "化学", "生物"]

        支持双向查找：如果 keyword 本身是某个映射的值，
        也会返回其对应的键作为扩展（如 "七年级" → ["初一", "七上", "七下"]）。

        Args:
            keyword: 待扩展的关键词。

        Returns:
            语义扩展词列表（不包含原词），如果无匹配则返回空列表。

        Example:
            >>> suggester = SearchSuggester()
            >>> suggester.get_semantic_expansions("初中")
            ['七年级', '八年级', '九年级']
            >>> suggester.get_semantic_expansions("七年级")
            ['初一', '七上', '七下']
            >>> suggester.get_semantic_expansions("不存在")
            []
        """
        if not keyword or not keyword.strip():
            return []
        keyword = keyword.strip()
        expansions: List[str] = []
        if keyword in self._SEMANTIC_EXPANSIONS:
            expansions.extend(self._SEMANTIC_EXPANSIONS[keyword])
        for key, values in self._SEMANTIC_EXPANSIONS.items():
            for val in values:
                if val == keyword and key != keyword:
                    expansions.append(key)
        result = list(dict.fromkeys(expansions))
        log('DEBUG', f"语义扩展 '{keyword}' → {result}", module='SearchSuggester')
        return result
if __name__ == '__main__':
    '模块自测：验证 SearchSuggester 的基本功能。'
    print('=' * 60)
    print('SearchSuggester 模块自测')
    print('=' * 60)
    suggester = SearchSuggester()
    print('\n[测试 1] 资源标题建议')
    test_resources = [{'title': '七年级数学上册人教版'}, {'title': '七年级语文下册部编版'}, {'title': '八年级物理上册人教版'}, {'title': '九年级化学下册人教版'}, {'title': '一年级语文上册'}]
    suggester.set_resources(test_resources)
    suggestions = suggester.get_suggestions('七年')
    print(f"{"  输入'七年' → 建议: "}{suggestions}")
    suggestions = suggester.get_suggestions('八')
    print(f"{"  输入'八' → 建议: "}{suggestions}")
    print('\n[测试 2] 边界情况')
    print(f"{'  空字符串: '}{suggester.get_suggestions('')}")
    print(f"{'  不匹配: '}{suggester.get_suggestions('xyz')}")
    print('\n[测试 3] 语义扩展')
    test_cases = ['初中', '小学', '高中', '理综', '文综', '七年级', '数学', '物理']
    for tc in test_cases:
        expansions = suggester.get_semantic_expansions(tc)
        print(f"  '{tc}' → {expansions}")
    print('\n[测试 4] 热门关键词（回退方案）')
    hot = suggester.get_hot_keywords(5)
    print(f"{'  热门关键词: '}{hot}")
    print('\n[测试 5] 搜索历史集成')
    from core.resource.search_engine import SearchHistoryManager
    hm = SearchHistoryManager()
    hm.add_search('七年级数学')
    hm.add_search('七年级数学')
    hm.add_search('八年级物理')
    hm.add_search('九年级化学')
    suggester.set_history_manager(hm)
    suggestions = suggester.get_suggestions('七年')
    print(f"{"  输入'七年'（含历史）→ 建议: "}{suggestions}")
    hot = suggester.get_hot_keywords(5)
    print(f"{'  热门关键词（含历史）: '}{hot}")
    print('\n' + '=' * 60)
    print('自测完成')
    print('=' * 60)