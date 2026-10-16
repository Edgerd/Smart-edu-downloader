// 首页：URL 解析 + 下载
import 'package:flutter/material.dart';

import '../core_ffi.dart';
import '../i18n.dart';
import '../main.dart' show ClipboardEvents;

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  final _urlCtrl = TextEditingController();
  Map<String, dynamic>? _result; // parse_url 返回
  bool _loading = false;
  bool _withBookmarks = true;

  @override
  void initState() {
    super.initState();
    ClipboardEvents.detected.addListener(_onClipboard);
  }

  @override
  void dispose() {
    ClipboardEvents.detected.removeListener(_onClipboard);
    _urlCtrl.dispose();
    super.dispose();
  }

  void _onClipboard() {
    final url = ClipboardEvents.detected.value;
    if (url != null && mounted && _urlCtrl.text.trim().isEmpty) {
      _urlCtrl.text = url;
      ClipboardEvents.consume();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(I18n.t('home.clipboard_found')),
        action: SnackBarAction(label: I18n.t('action.ok'), onPressed: () {}),
      ));
    }
  }

  Future<void> _parse() async {
    final url = _urlCtrl.text.trim();
    if (url.isEmpty || _loading) return;
    setState(() => _loading = true);
    // FFI 调用在简单后台线程执行
    final r = await Future(() =>
        Core.call('parse_url', {'url': url, 'bookmarks': _withBookmarks}));
    if (!mounted) return;
    setState(() {
      _loading = false;
      _result = r;
    });
  }

  Future<void> _download() async {
    final res = _result;
    if (res == null) return;
    final url = res['resource_url'] as String?;
    if (url == null || url.isEmpty) {
      _snack(res['error'] as String? ?? I18n.t('home.parse_fail'));
      return;
    }
    final chapters = res['chapters'];
    final r = await Future(() => Core.call('add_task', {
          'url': url,
          'title': res['title'],
          'chapters': chapters ?? [],
        }));
    if (!mounted) return;
    if (Core.ok(r)) {
      _snack('${I18n.t('action.download')} #${r['data']}');
      setState(() {
        _result = null;
        _urlCtrl.clear();
      });
    } else {
      _snack(r['error'] as String? ?? 'error');
    }
  }

  void _snack(String msg) {
    ScaffoldMessenger.of(context)
        .showSnackBar(SnackBar(content: Text(msg)));
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    final err = _result?['error'] as String?;
    final resourceUrl = _result?['resource_url'] as String?;
    final cover = _result?['cover_url'] as String?;
    final title = _result?['title'] as String?;
    final chapters = (_result?['chapters'] as List?) ?? const [];

    return Scaffold(
      appBar: AppBar(title: Text(I18n.t('home.title'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: _urlCtrl,
                  decoration: InputDecoration(
                    hintText: I18n.t('home.url_hint'),
                    prefixIcon: const Icon(Icons.link_rounded),
                  ),
                  onSubmitted: (_) => _parse(),
                ),
              ),
              const SizedBox(width: 12),
              FilledButton.icon(
                onPressed: _loading ? null : _parse,
                icon: _loading
                    ? const SizedBox(
                        width: 18,
                        height: 18,
                        child: CircularProgressIndicator(strokeWidth: 2))
                    : const Icon(Icons.travel_explore_rounded),
                label: Text(I18n.t('home.parse')),
              ),
            ],
          ),
          const SizedBox(height: 8),
          CheckboxListTile(
            value: _withBookmarks,
            onChanged: (v) => setState(() => _withBookmarks = v ?? true),
            title: Text(I18n.t('home.chapters')),
            controlAffinity: ListTileControlAffinity.leading,
          ),
          const SizedBox(height: 12),
          if (err != null || (resourceUrl == null && _result != null))
            Card(
              color: cs.errorContainer,
              child: ListTile(
                leading: Icon(Icons.error_rounded, color: cs.onErrorContainer),
                title: Text(err ?? I18n.t('home.parse_fail'),
                    style: TextStyle(color: cs.onErrorContainer)),
              ),
            ),
          if (resourceUrl != null) ...[
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(14),
                          child: cover != null && cover.isNotEmpty
                              ? Image.network(cover,
                                  width: 96,
                                  height: 128,
                                  fit: BoxFit.cover,
                                  errorBuilder: (_, __, ___) =>
                                      const SizedBox(width: 96, height: 128))
                              : Container(
                                  width: 96,
                                  height: 128,
                                  color: cs.surfaceContainerHighest,
                                  child: const Icon(Icons.menu_book_rounded)),
                        ),
                        const SizedBox(width: 16),
                        Expanded(
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(title ?? '',
                                  style: Theme.of(context)
                                      .textTheme
                                      .titleLarge
                                      ?.copyWith(fontWeight: FontWeight.w800)),
                              const SizedBox(height: 8),
                              Text(resourceUrl,
                                  maxLines: 3,
                                  overflow: TextOverflow.ellipsis,
                                  style: Theme.of(context)
                                      .textTheme
                                      .bodySmall
                                      ?.copyWith(color: cs.onSurfaceVariant)),
                            ],
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    Align(
                      alignment: Alignment.centerRight,
                      child: FilledButton.icon(
                        onPressed: _download,
                        icon: const Icon(Icons.download_rounded),
                        label: Text(I18n.t('action.download')),
                      ),
                    ),
                  ],
                ),
              ),
            ),
            if (chapters.isNotEmpty) ...[
              const SizedBox(height: 12),
              Text(I18n.t('home.chapters'),
                  style: Theme.of(context)
                      .textTheme
                      .titleMedium
                      ?.copyWith(fontWeight: FontWeight.w700)),
              const SizedBox(height: 6),
              Card(
                child: Column(
                  children: [
                    for (final ch in chapters.take(50))
                      ListTile(
                        dense: true,
                        leading: Icon(Icons.bookmark_rounded,
                            size: 18, color: cs.primary),
                        title: Text(ch['title'] ?? ''),
                        trailing: ch['page_index'] != null
                            ? Text('P${ch['page_index']}')
                            : null,
                      ),
                  ],
                ),
              ),
            ],
          ],
        ],
      ),
    );
  }
}
