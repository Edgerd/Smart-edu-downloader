// 资源库：搜索 + 筛选 + 封面网格
import 'package:flutter/material.dart';

import '../core_ffi.dart';
import '../i18n.dart';

class ResourcePage extends StatefulWidget {
  const ResourcePage({super.key});

  @override
  State<ResourcePage> createState() => _ResourcePageState();
}

class _ResourcePageState extends State<ResourcePage> {
  final _searchCtrl = TextEditingController();
  List<dynamic> _results = [];
  List<dynamic> _all = []; // 全量扁平列表用于浏览
  bool _loading = false;
  String? _error;
  String? _subjectFilter;

  @override
  void initState() {
    super.initState();
    _loadAll();
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }

  Future<void> _loadAll({bool force = false}) async {
    setState(() {
      _loading = true;
      _error = null;
    });
    final r = await Future(
        () => Core.call('fetch_resource_list', {'force_refresh': force}));
    if (!mounted) return;
    if (Core.ok(r)) {
      final flat = await Future(() => Core.call('get_flat_resources'));
      final list = (flat['data'] as List?) ?? const [];
      setState(() {
        _loading = false;
        _all = list;
        _results = _filtered(list);
      });
    } else {
      setState(() {
        _loading = false;
        _error = r['error'] as String? ?? I18n.t('resource.load_fail');
      });
    }
  }

  Future<void> _search(String kw) async {
    if (kw.trim().isEmpty) {
      setState(() => _results = _filtered(_all));
      return;
    }
    setState(() => _loading = true);
    final r = await Future(() => Core.call('search', {'keyword': kw}));
    if (!mounted) return;
    setState(() {
      _loading = false;
      _results = _filtered((r['data'] as List?) ?? const []);
    });
  }

  List<dynamic> _filtered(List<dynamic> src) {
    if (_subjectFilter == null) return src;
    return src
        .where((e) => (e['subject'] as String? ?? '') == _subjectFilter)
        .toList();
  }

  Iterable<String> get _subjects {
    final set = <String>{};
    for (final e in _all) {
      final s = e['subject'] as String? ?? '';
      if (s.isNotEmpty) set.add(s);
    }
    return set.toList()..sort();
  }

  Future<void> _openDetail(Map e) async {
    final url = e['url'] as String? ?? '';
    final r = await Future(
        () => Core.call('parse_url', {'url': url, 'bookmarks': false}));
    if (!mounted) return;
    final res = r;
    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      builder: (ctx) => Padding(
        padding: const EdgeInsets.fromLTRB(20, 0, 20, 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: (e['cover_url'] as String?)?.isNotEmpty == true
                      ? Image.network(e['cover_url'],
                          width: 72, height: 96, fit: BoxFit.cover)
                      : Container(
                          width: 72,
                          height: 96,
                          color: Theme.of(context)
                              .colorScheme
                              .surfaceContainerHighest,
                          child: const Icon(Icons.menu_book_rounded)),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Text(e['title'] ?? '',
                      style: Theme.of(context)
                          .textTheme
                          .titleMedium
                          ?.copyWith(fontWeight: FontWeight.w800)),
                ),
              ],
            ),
            const SizedBox(height: 16),
            if (res['error'] != null)
              Text(res['error'], style: const TextStyle(color: Colors.red)),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton.icon(
                onPressed: (res['resource_url'] as String?)?.isEmpty ?? true
                    ? null
                    : () async {
                        final ar = await Future(() => Core.call('add_task', {
                              'url': res['resource_url'],
                              'title': e['title'],
                              'chapters': [],
                            }));
                        if (ctx.mounted) {
                          Navigator.pop(ctx);
                        }
                        if (mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(SnackBar(
                              content: Text(Core.ok(ar)
                                  ? '${I18n.t('action.download')} OK'
                                  : ar['error'] ?? 'error')));
                        }
                      },
                icon: const Icon(Icons.download_rounded),
                label: Text(I18n.t('action.download')),
              ),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(I18n.t('resource.title')),
        actions: [
          IconButton(
              onPressed: () => _loadAll(force: true),
              icon: const Icon(Icons.refresh_rounded)),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
            child: TextField(
              controller: _searchCtrl,
              onSubmitted: _search,
              decoration: InputDecoration(
                hintText: I18n.t('resource.search_hint'),
                prefixIcon: const Icon(Icons.search_rounded),
                suffixIcon: IconButton(
                    icon: const Icon(Icons.arrow_forward_rounded),
                    onPressed: () => _search(_searchCtrl.text)),
              ),
            ),
          ),
          SizedBox(
            height: 44,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              children: [
                ChoiceChip(
                  label: const Text('全部'),
                  selected: _subjectFilter == null,
                  onSelected: (_) => setState(() {
                    _subjectFilter = null;
                    _results = _all;
                  }),
                ),
                for (final s in _subjects)
                  Padding(
                    padding: const EdgeInsets.only(left: 8),
                    child: ChoiceChip(
                      label: Text(s),
                      selected: _subjectFilter == s,
                      onSelected: (_) => setState(() {
                        _subjectFilter = s;
                        _results = _filtered(_all);
                      }),
                    ),
                  ),
              ],
            ),
          ),
          Expanded(
            child: _loading
                ? Center(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const CircularProgressIndicator(),
                        const SizedBox(height: 12),
                        Text(I18n.t('resource.loading')),
                      ],
                    ),
                  )
                : _error != null
                    ? Center(child: Text(_error!))
                    : _results.isEmpty
                        ? Center(child: Text(I18n.t('resource.empty')))
                        : GridView.builder(
                            padding: const EdgeInsets.all(16),
                            gridDelegate:
                                const SliverGridDelegateWithMaxCrossAxisExtent(
                              maxCrossAxisExtent: 180,
                              mainAxisSpacing: 12,
                              crossAxisSpacing: 12,
                              childAspectRatio: 0.62,
                            ),
                            itemCount: _results.length,
                            itemBuilder: (context, i) {
                              final e = _results[i] as Map;
                              return _BookCard(
                                item: e,
                                onTap: () => _openDetail(e),
                              );
                            },
                          ),
          ),
        ],
      ),
    );
  }
}

class _BookCard extends StatelessWidget {
  final Map item;
  final VoidCallback onTap;
  const _BookCard({required this.item, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final cover = item['cover_url'] as String?;
    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              child: cover != null && cover.isNotEmpty
                  ? Image.network(cover, fit: BoxFit.cover,
                      errorBuilder: (_, __, ___) => Container(
                          color: cs.surfaceContainerHighest,
                          child: const Icon(Icons.menu_book_rounded)))
                  : Container(
                      color: cs.surfaceContainerHighest,
                      child: const Icon(Icons.menu_book_rounded)),
            ),
            Padding(
              padding: const EdgeInsets.all(8),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(item['title'] ?? '',
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                  if ((item['publisher'] as String? ?? '').isNotEmpty)
                    Text(item['publisher'],
                        style: TextStyle(
                            fontSize: 11, color: cs.onSurfaceVariant)),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
