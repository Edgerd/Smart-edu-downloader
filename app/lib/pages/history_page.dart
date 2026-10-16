// 下载历史页
import 'package:flutter/material.dart';

import '../core_ffi.dart';
import '../i18n.dart';

class HistoryPage extends StatefulWidget {
  const HistoryPage({super.key});

  @override
  State<HistoryPage> createState() => _HistoryPageState();
}

class _HistoryPageState extends State<HistoryPage> {
  List<dynamic> _records = [];

  @override
  void initState() {
    super.initState();
    _refresh();
  }

  Future<void> _refresh() async {
    final r = await Future(() => Core.call('get_history'));
    if (mounted) setState(() => _records = (r['data'] as List?) ?? const []);
  }

  String _fmtSize(num bytes) {
    const units = ['B', 'KB', 'MB', 'GB'];
    var v = bytes.toDouble();
    var i = 0;
    while (v >= 1024 && i < units.length - 1) {
      v /= 1024;
      i++;
    }
    return '${v.toStringAsFixed(1)} ${units[i]}';
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(I18n.t('history.title')),
        actions: [
          IconButton(
            tooltip: I18n.t('settings.clear_history'),
            onPressed: () async {
              await Future(() => Core.call('clear_history'));
              _refresh();
            },
            icon: const Icon(Icons.delete_sweep_rounded),
          ),
        ],
      ),
      body: _records.isEmpty
          ? Center(child: Text(I18n.t('history.empty')))
          : RefreshIndicator(
              onRefresh: _refresh,
              child: ListView.builder(
                padding: const EdgeInsets.all(16),
                itemCount: _records.length,
                itemBuilder: (context, i) {
                  final r = _records[i] as Map;
                  return Card(
                    margin: const EdgeInsets.only(bottom: 10),
                    child: ListTile(
                      leading: CircleAvatar(
                        backgroundColor:
                            Theme.of(context).colorScheme.primaryContainer,
                        child: const Icon(Icons.picture_as_pdf_rounded),
                      ),
                      title: Text(r['title'] ?? '',
                          maxLines: 1, overflow: TextOverflow.ellipsis),
                      subtitle: Text(
                          '${r['filename'] ?? ''} · ${_fmtSize((r['file_size'] as num?) ?? 0)}'),
                      trailing: IconButton(
                        icon: const Icon(Icons.close_rounded),
                        onPressed: () async {
                          await Future(() =>
                              Core.call('remove_history', {'resource_id': r['resource_id']}));
                          _refresh();
                        },
                      ),
                    ),
                  );
                },
              ),
            ),
    );
  }
}
