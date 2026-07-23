"""
资源库搜索引擎主模块
特性：
1. 单例模式确保全局唯一实例
2. 策略模式支持完美匹配/大致匹配切换
3. 工厂模式创建过滤器
4. 智能关键词修复（缩写展开、版本识别）
5. 通配符搜索（*、?）和模糊匹配（编辑距离 ≤ 2）
6. 搜索历史记录和热门关键词统计
7. 搜索统计（耗时、结果数）
8. 学科自动过滤（如搜索"语文"自动过滤其他学科）
9. 版本别名映射（新版/新教材 → 2022年版课程标准修订）
"""
import re
import time
import os
import json
import datetime
import threading
from typing import Any, List, Dict, Optional, Set, Tuple
from core.infrastructure.logger import log
from core.resource.search_index import SearchIndex
from core.resource.search_filter import FilterFactory, CompositeFilter
from core.resource.search_suggester import SearchSuggester

# 搜索模式常量（内部使用中文值，与语言无关）
SEARCH_MODE_APPROXIMATE = '大致匹配'
SEARCH_MODE_EXACT = '完美匹配'

# 模块级正则常量：避免在各方法中重复编译（CPython 虽会缓存，但提取为常量更清晰，
# 且消除 _strict_filter 循环体内对每条结果重复编译的反模式）。
_GRADE_EXACT_RE = re.compile(r'(\d+|[一二三四五六七八九十])年级')
_GRADE_KW_RE = re.compile(r'([一二三四五六七八九十\d]+)年级')
_HIGH_SCHOOL_RE = re.compile(r'(高一|高二|高三|高中[一二三])')
_GRADE_EXPLICIT_RE = re.compile(r'(\d+|[一二三四五六七八九十])\s*年级')
_GV_RE = re.compile(r'([一二三四五六七八九])\s*([上下])')

class SearchHistoryManager:
    """搜索历史管理器

    负责搜索历史的持久化存储、读取和统计。
    历史文件存储在系统临时目录/cache 下。
    """

    def __init__(self, history_file: Optional[str]=None) -> None:
        """初始化搜索历史管理器

        Args:
            history_file: 历史记录文件路径，默认使用 path_resolver 获取
        """
        if history_file is None:
            from core.infrastructure.path_resolver import get_search_history_file
            history_file = get_search_history_file()
        self._history_file: str = history_file
        self._history: List[Dict] = self._load_history()

    def _load_history(self) -> List[Dict]:
        """从文件加载搜索历史"""
        if os.path.exists(self._history_file):
            try:
                with open(self._history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('history', [])
            except Exception as e:
                log('WARNING', f'加载搜索历史失败: {e}')
        return []

    def _save_history(self) -> None:
        """保存搜索历史到文件"""
        try:
            cache_dir = os.path.dirname(self._history_file)
            if not os.path.exists(cache_dir):
                os.makedirs(cache_dir)
            with open(self._history_file, 'w', encoding='utf-8') as f:
                json.dump({'history': self._history}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log('WARNING', f'保存搜索历史失败: {e}')

    def add_search(self, keyword: str, result_count: int=0, search_time_ms: float=0.0) -> None:
        """添加搜索记录

        Args:
            keyword: 搜索关键词
            result_count: 搜索结果数量
            search_time_ms: 搜索耗时（毫秒）
        """
        if not keyword or not keyword.strip():
            return
        keyword = keyword.strip()
        for item in self._history:
            if item.get('keyword') == keyword:
                item['count'] = item.get('count', 1) + 1
                item['last_time'] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                if result_count >= 0:
                    item['last_result_count'] = result_count
                if search_time_ms > 0:
                    item['last_search_time_ms'] = search_time_ms
                self._save_history()
                return
        self._history.insert(0, {'keyword': keyword, 'count': 1, 'first_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'last_time': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'last_result_count': result_count, 'last_search_time_ms': search_time_ms})
        if len(self._history) > 100:
            self._history = self._history[:100]
        self._save_history()

    def get_history(self, limit: int=20) -> List[Dict]:
        """获取搜索历史

        Args:
            limit: 返回数量限制

        Returns:
            搜索历史列表
        """
        return self._history[:limit]

    def get_hot_keywords(self, limit: int=10) -> List[str]:
        """获取热门关键词（按搜索次数排序）

        Args:
            limit: 返回数量限制

        Returns:
            热门关键词列表
        """
        sorted_history = sorted(self._history, key=lambda x: x.get('count', 0), reverse=True)
        return [item['keyword'] for item in sorted_history[:limit]]

    def get_recent_keywords(self, limit: int=10) -> List[str]:
        """获取最近搜索关键词

        Args:
            limit: 返回数量限制

        Returns:
            最近搜索关键词列表
        """
        return [item['keyword'] for item in self._history[:limit]]

    def delete_history(self, keyword: str) -> bool:
        """删除指定搜索历史

        Args:
            keyword: 要删除的关键词

        Returns:
            是否删除成功
        """
        original_len = len(self._history)
        self._history = [item for item in self._history if item.get('keyword') != keyword]
        if len(self._history) < original_len:
            self._save_history()
            return True
        return False

    def clear_history(self) -> None:
        """清空搜索历史"""
        self._history = []
        self._save_history()

class SearchEngine:
    """资源库搜索引擎（单例模式）

    整合倒排索引、过滤器和建议生成器，提供完整的搜索功能。
    支持两种搜索模式：完美匹配和大致匹配。

    Attributes:
        SUBJECT_KEYWORDS: 学科关键词映射表
    """
    _instance: Optional['SearchEngine'] = None
    _instance_lock = threading.Lock()
    SUBJECT_KEYWORDS: Dict[str, List[str]] = {'语文': ['语文'], '数学': ['数学'], '英语': ['英语'], '科学': ['科学'], '道德与法治': ['道德与法治', '道法'], '音乐': ['音乐'], '美术': ['美术'], '体育': ['体育'], '体育与健康': ['体育与健康', '体育'], '信息技术': ['信息技术', '信息', '计算机'], '信息科技': ['信息科技', '信科'], '日语': ['日语', '日文'], '俄语': ['俄语', '俄文'], '物理': ['物理'], '化学': ['化学'], '生物': ['生物'], '历史': ['历史'], '地理': ['地理'], '政治': ['政治']}
    GRADE_MAP: Dict[str, str] = {'一': '一年级', '二': '二年级', '三': '三年级', '四': '四年级', '五': '五年级', '六': '六年级', '七': '七年级', '八': '八年级', '九': '九年级'}
    VOLUME_MAP: Dict[str, str] = {'上': '上册', '下': '下册'}
    STAGE_GRADE_MAP: Dict[str, List[str]] = {'小学': ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级'], '初中': ['七年级', '八年级', '九年级'], '高中': ['高一', '高二', '高三']}
    HIGH_SCHOOL_ALIASES: Dict[str, str] = {'高一': '高一', '高中一': '高一', '高二': '高二', '高中二': '高二', '高三': '高三', '高中三': '高三'}
    SUBJECT_ABBR_MAP: Dict[str, str] = {'数': '数学', '语': '语文', '英': '英语', '物': '物理', '化': '化学', '生': '生物', '政': '政治', '历': '历史', '地': '地理', '科': '科学', '音': '音乐', '美': '美术', '体': '体育', '信': '信息科技'}
    PUBLISHER_ALIASES: Dict[str, str] = {'统编版': '人教版', '统编': '人教版', '部编版': '人教版', '部编': '人教版', '人教版': '人教版', '新版': '2022年版课程标准修订', '新教材': '2022年版课程标准修订'}
    SUBJECT_ALIASES: Dict[str, List[str]] = {'政治': ['道德与法治', '道法'], '道德与法治': ['政治'], '道法': ['政治', '道德与法治']}
    FILLER_WORDS: Set[str] = {'的', '了', '吗', '呢', '啊', '呀', '哦', '嗯', '吧'}

    def __new__(cls) -> 'SearchEngine':
        """单例实现"""
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        """初始化搜索引擎及各子模块"""
        if self._initialized:
            return
        self._initialized = True
        self._history_manager = SearchHistoryManager()
        self._index = SearchIndex()
        self._suggester = SearchSuggester()
        self._suggester.set_history_manager(self._history_manager)
        self._flat_resources: List[Dict] = []
        self._id_to_resource: Dict[str, Dict] = {}
        self._search_mode: str = SEARCH_MODE_APPROXIMATE
        self._suggestions_enabled: bool = True
        self._max_results: int = 0
        self._smart_repair: bool = True
        self._known_publishers = self._init_known_publishers()
        log('INFO', 'SearchEngine 已初始化（单例）')

    def _init_known_publishers(self) -> List[str]:
        """初始化已知教材版本列表"""
        return [
            '冀教版', '人教版', '北师大版', '苏教版', '湘教版', '鲁教版', '沪科版', '浙教版', '华师大版', '沪教版',
            '教科版', '粤教版', '中图版', '地图版', '外研版', '译林版', '仁爱版', '科普版', '鲁科版', '川教版',
            '鄂教版', '粤沪版', '粤科技版', '青岛版', '沪粤版', '大象版', '西师大版', '语文版', '长春版', '河大版',
            '冀少版', '济南版', '沪科技版', '苏科版', '苏少版', '浙人版', '沪外版', '沪外教版', '湘少版', '湘美版',
            '湘科版', '湘文艺版', '沪教牛津版', '鲁美版', '鲁文艺版', '鲁外版', '粤教花城版', '粤教育版', '粤音版', '粤美版',
            '粤外版', '粤教科版', '鄂科版', '鄂美版', '鄂外版', '鄂音版', '鄂文艺版', '鄂教科版', '川科版', '川美版',
            '川外版', '川音版', '川文艺版', '川教科版', '辽教版', '辽科版', '辽美版', '辽外版', '辽音版', '辽文艺版',
            '辽教科版', '辽海版', '辽师大版', '闽教版', '闽科版', '闽美版', '闽外版', '闽音版', '闽文艺版', '闽教科版',
            '赣教版', '赣科版', '赣美版', '赣外版', '赣音版', '赣文艺版', '赣教科版', '人教A版', '人教B版', '北京版',
            '粤教粤科版', '冀人版', '科粤版', '商务星球版', '人音版', '湘艺版', '人美版', '湘美版', '华东师大版', '泰山版',
            '浙科版',
            # 补充资源中实际出现但原列表未覆盖的版本
            '大象社版', '武汉社版', '粤教科技版', '人教鄂教版', '沪科教版', '人教中图版', '沪科技粤教版', '科学社版',
            '科学粤教版', '鲁教湘教版', '中华中图版', '中图中华地图版', '华中师大版', '华文社版', '地质社版', '外研社版',
            '广西师大版', '接力社版', '教科外研社版', '晋人版', '晋教版', '未来社版', '桂教版', '桂美版', '沪书画版',
            '沪音版', '浙人美版', '清华大学版', '西南大学版', '西泠印社版', '豫科版', '辽宁师大版', '重庆大学版', '陕旅版',
        ]

    def set_flat_resources(self, resources: List[Dict]) -> None:
        """设置扁平化资源列表并构建索引

        Args:
            resources: 扁平化后的资源列表
        """
        # 资源对象未变化时跳过重建（ResourceProcessor 缓存同一对象），
        # 避免每次搜索/获取建议都全量重建倒排索引（主要性能瓶颈）。
        if resources is self._flat_resources:
            return
        self._flat_resources = resources
        self._id_to_resource = {str(r.get('id', '')): r for r in resources if r.get('id')}
        self._index.build_index(resources)
        self._suggester.set_resources(resources)
        log('INFO', f'搜索引擎已加载 {len(resources)} 个资源')

    def set_search_config(self, mode: str=SEARCH_MODE_APPROXIMATE, suggestions_enabled: bool=True, max_results: int=0, smart_repair: bool=True) -> None:
        """设置搜索配置

        Args:
            mode: 搜索模式（"完美匹配" 或 "大致匹配"）
            suggestions_enabled: 搜索建议开关
            max_results: 搜索结果最大数量（0 表示不限制）
            smart_repair: 智能关键词修复开关
        """
        self._search_mode = mode
        self._suggestions_enabled = suggestions_enabled
        self._max_results = max_results
        self._smart_repair = smart_repair
        log('DEBUG', f'搜索配置已更新: 模式={mode}, 最大结果={max_results}')

    def search(self, keyword: str) -> Tuple[List[Dict], Dict[str, Any]]:
        """执行完整搜索流程

        流程：关键词修复 → 关键词提取 → 索引查询 →
              评分排序 → 过滤 → 记录历史

        Args:
            keyword: 搜索关键词

        Returns:
            (搜索结果列表, 搜索统计信息字典)
            统计信息包含: keyword, result_count, search_time_ms, mode
        """
        start_time = time.time()
        stats: Dict[str, Any] = {'keyword': keyword, 'result_count': 0, 'search_time_ms': 0.0, 'mode': self._search_mode, 'correction': None}
        if not keyword or not keyword.strip():
            return ([], stats)
        keyword = keyword.strip()
        log('STEP', f"开始搜索: '{keyword}', 模式: {self._search_mode}")
        if self._smart_repair:
            repaired_keyword = self._repair_search_term(keyword)
        else:
            repaired_keyword = keyword
        keywords = self._extract_keywords(repaired_keyword)
        log('DEBUG', f'提取关键词: {keywords}')
        if not keywords:
            log('WARNING', '未提取到有效关键词')
            return ([], stats)
        has_wildcard = '*' in keyword or '?' in keyword
        if has_wildcard:
            results = self._wildcard_search(keyword)
        else:
            results = self._indexed_search(keywords)
        scored = self._score_results(keywords, results)
        scored.sort(key=lambda x: (x['score'], -self._get_resource_type_priority(x['resource'])), reverse=True)
        search_subject = self._detect_subject(keywords)
        if search_subject:
            scored = self._filter_by_subject(search_subject, scored)
        search_stage = self._detect_stage(keyword)
        if search_stage:
            scored = self._filter_by_stage(search_stage, scored)
        search_grade = self._detect_grade_explicit(keyword)
        if search_grade:
            scored = self._filter_by_grade(search_grade, scored)
        search_publisher = self._detect_publisher_explicit(keyword)
        if search_publisher:
            scored = self._filter_by_publisher(search_publisher, scored)
        if self._search_mode == SEARCH_MODE_EXACT:
            scored = self._strict_filter(keywords, scored)
        final_results = [item['resource'] for item in scored]
        if not final_results and self._search_mode == SEARCH_MODE_APPROXIMATE and (not has_wildcard):
            correction = self._find_correction(keyword)
            if correction and correction != keyword:
                stats['correction'] = correction
                log('INFO', f"搜索纠错: '{keyword}' → '{correction}'")
                final_results, _stats = self.search(correction)
                stats['result_count'] = len(final_results)
                stats['search_time_ms'] = (time.time() - start_time) * 1000
                return (final_results, stats)
        if self._max_results > 0 and len(final_results) > self._max_results:
            final_results = final_results[:self._max_results]
        stats['result_count'] = len(final_results)
        stats['search_time_ms'] = (time.time() - start_time) * 1000
        self._history_manager.add_search(keyword, len(final_results), stats['search_time_ms'])
        log('SUCCESS', f"搜索完成: {len(final_results)} 个结果, {stats['search_time_ms']:.1f}ms")
        return (final_results, stats)

    def get_suggestions(self, partial_keyword: str, limit: int=10) -> List[str]:
        """获取搜索建议

        Args:
            partial_keyword: 部分关键词
            limit: 返回数量限制

        Returns:
            搜索建议列表
        """
        if not self._suggestions_enabled:
            return []
        return self._suggester.get_suggestions(partial_keyword, limit)

    def get_semantic_expansions(self, keyword: str) -> List[str]:
        """获取语义扩展

        Args:
            keyword: 关键词

        Returns:
            语义扩展词列表
        """
        return self._suggester.get_semantic_expansions(keyword)

    def set_search_mode(self, mode: str) -> None:
        """设置搜索模式

        Args:
            mode: "完美匹配" 或 "大致匹配"
        """
        self._search_mode = mode
        log('INFO', f'搜索模式切换为: {mode}')

    def _repair_search_term(self, search_term: str) -> str:
        """修复搜索词：展开缩写、识别版本、重组为标准格式

        Args:
            search_term: 原始搜索词

        Returns:
            修复后的搜索词
        """
        if not search_term:
            return search_term
        term = search_term.strip()
        publisher = ''
        for alias, canonical in self.PUBLISHER_ALIASES.items():
            if alias in term:
                publisher = canonical
                term = term.replace(alias, '', 1)
                break
        if not publisher:
            for pub in sorted(self._known_publishers, key=len, reverse=True):
                if pub in term:
                    publisher = pub
                    term = term.replace(pub, '', 1)
                    break
        grade = ''
        volume = ''
        grade_volume_match = re.search(r'([一二三四五六七八九])([上下])', term)
        if grade_volume_match:
            grade_num = grade_volume_match.group(1)
            vol = grade_volume_match.group(2)
            grade = self.GRADE_MAP.get(grade_num, '')
            volume = self.VOLUME_MAP.get(vol, '')
            term = term.replace(grade_volume_match.group(0), '', 1)
        if not grade:
            for g in self.GRADE_MAP.values():
                if g in term:
                    grade = g
                    term = term.replace(g, '', 1)
                    break
        if not volume:
            for v in self.VOLUME_MAP.values():
                if v in term:
                    volume = v
                    term = term.replace(v, '', 1)
                    break
        subject = ''
        all_subjects = list(self.SUBJECT_KEYWORDS.keys())
        for subj in sorted(all_subjects, key=len, reverse=True):
            if subj in term:
                subject = subj
                term = term.replace(subj, '', 1)
                break
        if not subject:
            for abbr, full in sorted(self.SUBJECT_ABBR_MAP.items(), key=lambda x: -len(x[0])):
                if abbr in term:
                    subject = full
                    term = term.replace(abbr, '', 1)
                    break
        result_parts = []
        if publisher:
            result_parts.append(publisher)
        if subject:
            result_parts.append(subject)
        if grade:
            result_parts.append(grade)
        if volume:
            result_parts.append(volume)
        remaining = re.sub(r'\s+', ' ', term).strip()
        if remaining:
            result_parts.append(remaining)
        repaired = ' '.join(result_parts)
        if repaired != search_term:
            log('DEBUG', f"搜索词修复: '{search_term}' → '{repaired}'")
        return repaired if repaired else search_term

    def _extract_keywords(self, keyword: str) -> List[str]:
        """智能关键词提取

        Args:
            keyword: 搜索关键词

        Returns:
            去重后的关键词列表
        """
        raw_keywords = re.split(r'[\s，,；;]+', keyword.strip())
        raw_keywords = [k.strip().lower() for k in raw_keywords if k.strip()]
        keywords: List[str] = []
        for kw in raw_keywords:
            if kw in self.FILLER_WORDS:
                continue
            keywords.append(kw)
            gv_match = re.search(r'([一二三四五六七八九])([上下])', kw)
            if gv_match:
                grade_num = gv_match.group(1)
                vol = gv_match.group(2)
                if grade_num in self.GRADE_MAP:
                    keywords.append(self.GRADE_MAP[grade_num])
                if vol in self.VOLUME_MAP:
                    keywords.append(self.VOLUME_MAP[vol])
            if '下册' in kw:
                keywords.append('下')
            if '上册' in kw:
                keywords.append('上')
        for pub in self._known_publishers:
            if pub.lower() in keyword.lower():
                keywords.append(pub.lower())
        return self._optimize_keywords(keywords)

    @staticmethod
    def _optimize_keywords(keywords: List[str]) -> List[str]:
        """关键词优化：去除被包含的短词，去除过短词

        Args:
            keywords: 原始关键词列表

        Returns:
            优化后的关键词列表
        """
        if not keywords:
            return []
        sorted_kw = sorted(keywords, key=len, reverse=True)
        optimized: List[str] = []
        for kw in sorted_kw:
            if len(kw) < 2 and (not kw.isdigit()):
                continue
            is_subset = any((kw != existing and kw in existing for existing in optimized))
            if not is_subset:
                optimized.append(kw)
        return optimized

    def _indexed_search(self, keywords: List[str]) -> List[Dict]:
        """基于倒排索引的搜索

        Args:
            keywords: 关键词列表

        Returns:
            匹配的资源列表
        """
        if not self._flat_resources:
            return []
        all_matched_ids: Set[str] = set()
        for kw in keywords:
            matched = self._index.query(kw)
            all_matched_ids.update(matched)
        return [self._id_to_resource[rid] for rid in all_matched_ids if rid in self._id_to_resource]

    def _score_results(self, keywords: List[str], results: List[Dict]) -> List[Dict]:
        """对搜索结果进行评分

        评分规则：
        - 标题匹配: +100分
        - 学科匹配: +80分
        - 年级匹配: +60分
        - 版本匹配: +60分
        - 多字段匹配: +50分
        - 完美匹配加成: +200分

        Args:
            keywords: 关键词列表
            results: 搜索结果列表

        Returns:
            带分数的结果列表 [{'resource': ..., 'score': int}]
        """
        scored = []
        search_subject = self._detect_subject(keywords)
        search_grade = self._detect_grade(keywords)
        search_publisher = self._detect_publisher(keywords)
        for resource in results:
            title = resource.get('title', '').lower()
            subject = resource.get('subject', '').lower()
            grade = resource.get('grade', '').lower()
            publisher = resource.get('publisher', '').lower()
            full_text = f'{title} {subject} {grade} {publisher}'
            score = 0
            matched_fields = 0
            for kw in keywords:
                if not kw:
                    continue
                in_title = kw in title
                in_subject = kw in subject
                in_grade = kw in grade
                in_publisher = kw in publisher
                if in_title or in_subject or in_grade or in_publisher:
                    if in_title:
                        score += 100
                    if in_subject:
                        score += 80
                    if in_grade:
                        score += 60
                    if in_publisher:
                        score += 60
                    field_matches = sum([in_title, in_subject, in_grade, in_publisher])
                    if field_matches >= 2:
                        matched_fields += 1
            if matched_fields >= 2:
                score += 50
            if search_subject and any((skw in full_text for skw in self.SUBJECT_KEYWORDS.get(search_subject, []))):
                score += 200
            if search_grade and search_grade.lower() in full_text:
                score += 200
            if search_publisher:
                normalized_search_publisher = search_publisher.lower()
                for alias, canonical in self.PUBLISHER_ALIASES.items():
                    if alias in normalized_search_publisher:
                        normalized_search_publisher = canonical.lower()
                        break
                normalized_resource_publisher = publisher.lower()
                for alias, canonical in self.PUBLISHER_ALIASES.items():
                    if alias in normalized_resource_publisher:
                        normalized_resource_publisher = canonical.lower()
                        break
                if normalized_search_publisher == normalized_resource_publisher:
                    score += 200
            if any((kw in full_text for kw in ['新版', '新教材', '2022年版课程标准修订'])):
                score += 300
            if not search_publisher and '人教版' in publisher:
                score += 50
            if any((kw in full_text for kw in ['盲校', '聋校', '培智学校'])):
                score -= 100
            elif '五四制' in full_text:
                score -= 50
            scored.append({'resource': resource, 'score': score})
        return scored

    def _get_resource_type_priority(self, resource: Dict) -> int:
        """获取教材类型的优先级（用于二次排序）

        优先级顺序：普通教材 > 五四版教材 > 特殊教育教材

        Args:
            resource: 资源字典

        Returns:
            优先级值（0=普通教材，1=五四版，2=特殊教育）
        """
        title = resource.get('title', '')
        full_text = f"{title} {resource.get('subject', '')} {resource.get('grade', '')} {resource.get('publisher', '')}"
        if any((kw in full_text for kw in ['盲校', '聋校', '培智学校'])):
            return 2
        if '五四制' in full_text or '五四' in full_text:
            return 1
        return 0

    def _strict_filter(self, keywords: List[str], scored: List[Dict]) -> List[Dict]:
        """完美匹配模式下的严格过滤

        Args:
            keywords: 关键词列表
            scored: 带分数的结果列表

        Returns:
            过滤后的结果列表
        """
        search_subject = self._detect_subject(keywords)
        search_grade = self._detect_grade(keywords)
        search_publisher = self._detect_publisher(keywords)
        filtered = []
        for item in scored:
            resource = item['resource']
            title = resource.get('title', '').lower()
            subject = resource.get('subject', '').lower()
            grade = resource.get('grade', '').lower()
            publisher = resource.get('publisher', '').lower()
            full_text = f'{title} {subject} {grade} {publisher}'
            if search_subject:
                subject_matched = any((skw in full_text for skw in self.SUBJECT_KEYWORDS.get(search_subject, [])))
                if not subject_matched:
                    continue
            if search_grade:
                match = _GRADE_EXACT_RE.search(search_grade)
                if match:
                    if not re.search(f"{match.group(1)}{'年级'}", full_text):
                        continue
            if search_publisher and publisher:
                normalized_search_publisher = search_publisher.lower()
                for alias, canonical in self.PUBLISHER_ALIASES.items():
                    if alias in normalized_search_publisher:
                        normalized_search_publisher = canonical.lower()
                        break
                normalized_resource_publisher = publisher.lower()
                for alias, canonical in self.PUBLISHER_ALIASES.items():
                    if alias in normalized_resource_publisher:
                        normalized_resource_publisher = canonical.lower()
                        break
                if normalized_search_publisher != normalized_resource_publisher:
                    continue
            matched_count = sum((1 for kw in keywords if kw in full_text))
            coverage = matched_count / len(keywords) if keywords else 0
            if coverage < 0.5:
                continue
            filtered.append(item)
        log('DEBUG', f'完美模式过滤: {len(scored)} → {len(filtered)}')
        return filtered

    def _wildcard_search(self, keyword: str) -> List[Dict]:
        """通配符搜索（支持 * 和 ?）

        Args:
            keyword: 包含通配符的关键词

        Returns:
            匹配的资源列表
        """
        pattern = re.escape(keyword)
        pattern = pattern.replace('\\*', '.*').replace('\\?', '.')
        regex = re.compile(pattern, re.IGNORECASE)
        results = []
        for resource in self._flat_resources:
            full_text = f"{resource.get('title', '')} {resource.get('subject', '')} {resource.get('grade', '')} {resource.get('publisher', '')}"
            if regex.search(full_text):
                results.append(resource)
        log('DEBUG', f"通配符搜索 '{keyword}': {len(results)} 个结果")
        return results

    @staticmethod
    def _levenshtein_distance(s1: str, s2: str) -> int:
        """计算两个字符串的编辑距离（Levenshtein 距离）

        Args:
            s1: 字符串1
            s2: 字符串2

        Returns:
            编辑距离
        """
        if len(s1) < len(s2):
            return SearchEngine._levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        prev_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            curr_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = prev_row[j + 1] + 1
                deletions = curr_row[j] + 1
                substitutions = prev_row[j] + (c1 != c2)
                curr_row.append(min(insertions, deletions, substitutions))
            prev_row = curr_row
        return prev_row[-1]

    def _find_correction(self, keyword: str) -> Optional[str]:
        """查找搜索纠错建议

        从搜索历史中找编辑距离 ≤ 2 的相似关键词作为纠错建议。

        Args:
            keyword: 原始关键词

        Returns:
            纠错建议，无匹配时返回 None
        """
        if len(keyword) < 3:
            return None
        best_match = None
        best_distance = 999
        for item in self._history_manager.get_history(limit=50):
            hist_kw = item.get('keyword', '')
            if hist_kw == keyword:
                continue
            distance = self._levenshtein_distance(keyword, hist_kw)
            if distance <= 2 and distance < best_distance:
                best_distance = distance
                best_match = hist_kw
        return best_match

    def _detect_subject(self, keywords: List[str]) -> Optional[str]:
        """检测搜索的学科

        优先按完整关键词精确匹配，再按子串模糊匹配，
        避免"信息科技"被"信息技术"的"信息"子串误识别。
        """
        for kw in keywords:
            for subj, kw_list in self.SUBJECT_KEYWORDS.items():
                for subj_kw in kw_list:
                    if kw == subj_kw:
                        return subj
        for subj, kw_list in self.SUBJECT_KEYWORDS.items():
            for kw in keywords:
                for subj_kw in kw_list:
                    if subj_kw in kw:
                        return subj
        return None

    def _detect_grade(self, keywords: List[str]) -> Optional[str]:
        """检测搜索的年级"""
        grade_pattern = _GRADE_KW_RE
        for kw in keywords:
            match = grade_pattern.search(kw)
            if match:
                return kw
        return None

    def _detect_publisher(self, keywords: List[str]) -> Optional[str]:
        """检测搜索的教材版本"""
        for kw in keywords:
            for pub in self._known_publishers:
                if pub.lower() in kw:
                    return pub
        return None

    def _filter_by_subject(self, subject: str, scored: List[Dict]) -> List[Dict]:
        """按学科过滤搜索结果（支持学科别名映射）
        
        Args:
            subject: 学科名称
            scored: 带分数的结果列表
            
        Returns:
            过滤后的结果列表
        """
        allowed_subjects = {subject}
        if subject in self.SUBJECT_ALIASES:
            allowed_subjects.update(self.SUBJECT_ALIASES[subject])
        filtered = []
        for item in scored:
            resource = item['resource']
            resource_subject = resource.get('subject', '')
            if resource_subject in allowed_subjects:
                filtered.append(item)
        log('DEBUG', f"学科过滤 '{subject}' (含别名 {allowed_subjects}): {len(scored)} → {len(filtered)}")
        return filtered

    def _detect_grade_explicit(self, raw_keyword: str) -> Optional[str]:
        """检测用户是否明确提及年级（如"八年级"、"八下"、"8年级"、"高一"等）

        只有当用户输入中明确包含年级相关词汇时才返回，
        避免关键词提取后误判（如标题中包含"三"不代表三年级）。

        Args:
            raw_keyword: 原始搜索关键词（未分词）

        Returns:
            检测到的年级字符串，未检测到时返回 None
        """
        high_school_pattern = _HIGH_SCHOOL_RE
        match = high_school_pattern.search(raw_keyword)
        if match:
            grade_text = match.group(1)
            if grade_text in self.HIGH_SCHOOL_ALIASES:
                return self.HIGH_SCHOOL_ALIASES[grade_text]
            return grade_text
        grade_pattern = _GRADE_EXPLICIT_RE
        match = grade_pattern.search(raw_keyword)
        if match:
            return match.group(0)
        gv_pattern = _GV_RE
        match = gv_pattern.search(raw_keyword)
        if match:
            grade_num = match.group(1)
            vol = match.group(2)
            return f'{self.GRADE_MAP.get(grade_num, grade_num)}{self.VOLUME_MAP.get(vol, vol)}'
        return None

    def _filter_by_grade(self, grade: str, scored: List[Dict]) -> List[Dict]:
        """按年级硬过滤搜索结果

        当用户明确提及年级时，剔除其他年级的教材。
        支持年级数字标准化比较（如"八"和"8"等价）。
        支持高中年级（高一/高二/高三）。

        Args:
            grade: 年级字符串（如"八年级"、"八年级上册"、"高一"）
            scored: 带分数的结果列表

        Returns:
            过滤后的结果列表
        """
        if grade in ['高一', '高二', '高三']:
            filtered = []
            for item in scored:
                resource = item['resource']
                resource_grade = resource.get('grade', '')
                resource_title = resource.get('title', '')
                full_text = f'{resource_grade} {resource_title}'
                if grade in full_text:
                    filtered.append(item)
                elif any((stage_grade in full_text for stage_grades in self.STAGE_GRADE_MAP.values() for stage_grade in stage_grades if stage_grade not in ['高一', '高二', '高三'])):
                    continue
                elif not re.search(r'(年级|高一|高二|高三)', full_text):
                    filtered.append(item)
            log('DEBUG', f"高中年级过滤 '{grade}': {len(scored)} → {len(filtered)}")
            return filtered
        grade_num_match = re.search(r'(\d+|[一二三四五六七八九十])', grade)
        if not grade_num_match:
            return scored
        grade_digit = grade_num_match.group(1)
        chinese_to_arabic = {'一': '1', '二': '2', '三': '3', '四': '4', '五': '5', '六': '6', '七': '7', '八': '8', '九': '9', '十': '10'}
        search_grade_num = chinese_to_arabic.get(grade_digit, grade_digit)
        is_compulsory = search_grade_num in {str(i) for i in range(1, 10)}
        filtered = []
        for item in scored:
            resource = item['resource']
            resource_grade = resource.get('grade', '').lower()
            resource_title = resource.get('title', '').lower()
            full_text = f'{resource_grade} {resource_title}'
            if is_compulsory and ('高中' in full_text or '高一' in full_text or '高二' in full_text or ('高三' in full_text)):
                continue
            resource_grade_match = re.search(r'(\d+|[一二三四五六七八九十])\s*年级', full_text)
            if resource_grade_match:
                res_digit = resource_grade_match.group(1)
                res_grade_num = chinese_to_arabic.get(res_digit, res_digit)
                if res_grade_num == search_grade_num:
                    filtered.append(item)
            else:
                filtered.append(item)
        log('DEBUG', f"年级硬过滤 '{grade}' (年级数字={search_grade_num}): {len(scored)} → {len(filtered)}")
        return filtered

    def _detect_stage(self, raw_keyword: str) -> Optional[str]:
        """检测用户是否明确提及学段（如"小学"、"初中"、"高中"）

        Args:
            raw_keyword: 原始搜索关键词（未分词）

        Returns:
            检测到的学段名称，未检测到时返回 None
        """
        for stage in self.STAGE_GRADE_MAP.keys():
            if stage in raw_keyword:
                return stage
        return None

    def _filter_by_stage(self, stage: str, scored: List[Dict]) -> List[Dict]:
        """按学段过滤搜索结果

        当用户明确提及学段时，仅保留该学段的教材。

        Args:
            stage: 学段名称（如"小学"、"初中"、"高中"）
            scored: 带分数的结果列表

        Returns:
            过滤后的结果列表
        """
        allowed_grades = self.STAGE_GRADE_MAP.get(stage, [])
        if not allowed_grades:
            return scored
        filtered = []
        for item in scored:
            resource = item['resource']
            resource_grade = resource.get('grade', '')
            resource_title = resource.get('title', '')
            full_text = f'{resource_grade} {resource_title}'
            if any((grade in full_text for grade in allowed_grades)):
                filtered.append(item)
            elif not re.search(r'(年级|高一|高二|高三)', full_text):
                filtered.append(item)
        log('DEBUG', f"学段过滤 '{stage}' (允许年级: {allowed_grades}): {len(scored)} → {len(filtered)}")
        return filtered

    def _detect_publisher_explicit(self, raw_keyword: str) -> Optional[str]:
        """检测用户输入中是否明确提及教材版本

        支持别名映射（如"统编版"→"人教版"）。

        Args:
            raw_keyword: 原始搜索关键词

        Returns:
            标准化后的版本名称，未检测到时返回 None
        """
        for alias, canonical in sorted(self.PUBLISHER_ALIASES.items(), key=lambda x: -len(x[0])):
            if alias in raw_keyword:
                return canonical
        for pub in sorted(self._known_publishers, key=len, reverse=True):
            if pub in raw_keyword:
                return pub
        return None

    def _filter_by_publisher(self, publisher: str, scored: List[Dict]) -> List[Dict]:
        """按教材版本硬过滤搜索结果

        当用户明确指定版本时，剔除不匹配的版本。
        支持别名映射（如搜索"统编版"匹配资源中的"人教版"）。

        Args:
            publisher: 标准化后的目标版本名称
            scored: 带分数的结果列表

        Returns:
            过滤后的结果列表
        """
        target = publisher.lower()
        filtered = []
        for item in scored:
            resource = item['resource']
            resource_publisher = resource.get('publisher', '')
            if not resource_publisher:
                filtered.append(item)
                continue
            normalized = resource_publisher.lower()
            for alias, canonical in self.PUBLISHER_ALIASES.items():
                if alias in normalized:
                    normalized = canonical.lower()
                    break
            if normalized == target:
                filtered.append(item)
        log('DEBUG', f"版本硬过滤 '{publisher}': {len(scored)} → {len(filtered)}")
        return filtered

    @property
    def history(self) -> SearchHistoryManager:
        """获取搜索历史管理器"""
        return self._history_manager

    @property
    def known_publishers(self) -> List[str]:
        """获取已知教材版本列表"""
        return self._known_publishers.copy()

    @property
    def index(self) -> SearchIndex:
        """获取倒排索引"""
        return self._index

    @property
    def suggester(self) -> SearchSuggester:
        """获取搜索建议生成器"""
        return self._suggester
