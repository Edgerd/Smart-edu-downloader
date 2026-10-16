// 下载管理页：任务列表 + 进度 + 控制
import 'dart:async';

import 'package:flutter/material.dart';

import '../core_ffi.dart';
import '../i18n.dart';

class DownloadPage extends StatefulWidget {
  const DownloadPage({super.key});

  @override
  State<DownloadPage> createState() => _DownloadPageState();
}

class _DownloadPageState extends State<DownloadPage>
    with AutomaticKeepAliveClientMixin {
  List<dynamic> _tasks = [];
  Timer? _timer;

  @override
  bool get wantKeepAlive => true;

  @override
  void initState() {
    super.initState();
    _refresh();
    _timer = Timer.periodic(const Duration(milliseconds: 500), (_) => _refresh());
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  Future<void> _refresh() async {
    final r = await Future(() => Core.call('get_tasks'));
    final list = (r['data'] as List?) ?? const [];
    if (mounted) setState(() => _tasks = list);
  }

  Future<void> _act(String method, String taskId) async {
    await Future(() => Core.call(method, {'task_id': taskId}));
    _refresh();
  }

  String _statusLabel(String status) {
    switch (status) {
      case 'completed':
        return I18n.t('download.completed');
      case 'failed':
        return I18n.t('download.failed');
      case 'downloading':
        return I18n.t('download.downloading');
      case 'paused':
        return I18n.t('download.paused');
      case 'cancelled':
        return I18n.t('download.cancelled');
      default:
        return I18n.t('download.pending');
    }
  }

  Color _statusColor(String status, ColorScheme cs) {
    switch (status) {
      case 'completed':
        return Colors.green;
      case 'failed':
        return cs.error;
      case 'downloading':
        return cs.primary;
      default:
        return cs.onSurfaceVariant;
    }
  }

  String _fmtSpeed(num bps) {
    if (bps <= 0) return '';
    const units = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    var v = bps.toDouble();
    var i = 0;
    while (v >= 1024 && i < units.length - 1) {
      v /= 1024;
      i++;
    }
    return '${v.toStringAsFixed(1)} ${units[i]}';
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
    super.build(context);
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      appBar: AppBar(
        title: Text(I18n.t('download.title')),
        actions: [
          IconButton(
            tooltip: I18n.t('download.clear_all'),
            onPressed: () async {
              await Future(() => Core.call('clear_all_tasks'));
              _refresh();
            },
            icon: const Icon(Icons.delete_sweep_rounded),
          ),
        ],
      ),
      body: _tasks.isEmpty
          ? Center(child: Text(I18n.t('download.empty')))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _tasks.length,
              itemBuilder: (context, i) {
                final t = _tasks[i] as Map;
                final status = t['status'] as String? ?? 'pending';
                final total = (t['total_size'] as num?)?.toDouble() ?? 0;
                final done = (t['downloaded_size'] as num?)?.toDouble() ?? 0;
                final progress = total > 0 ? (done / total).clamp(0.0, 1.0) : 0.0;
                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: Padding(
                    padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Expanded(
                              child: Text(
                                t['title'] ?? t['save_path'] ?? '',
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                                style: const TextStyle(fontWeight: FontWeight.w700),
                              ),
                            ),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 10, vertical: 4),
                              decoration: BoxDecoration(
                                color:
                                    _statusColor(status, cs).withValues(alpha: 0.12),
                                borderRadius: BorderRadius.circular(999),
                              ),
                              child: Text(
                                _statusLabel(status),
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  color: _statusColor(status, cs),
                                ),
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 10),
                        ClipRRect(
                          borderRadius: BorderRadius.circular(999),
                          child: LinearProgressIndicator(
                            value: status == 'completed' ? 1 : progress,
                            minHeight: 8,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '${_fmtSize(done)} / ${_fmtSize(total)}'
                          '${_fmtSpeed(t['speed'] ?? 0).isNotEmpty ? '  ·  ${_fmtSpeed(t['speed'])}' : ''}',
                          style: TextStyle(
                              fontSize: 12, color: cs.onSurfaceVariant),
                        ),
                        if (t['error'] != null &&
                            (t['error'] as String).isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 4),
                            child: Text(t['error'],
                                style:
                                    TextStyle(fontSize: 12, color: cs.error)),
                          ),
                        const SizedBox(height: 10),
                        Wrap(
                          spacing: 8,
                          children: [
                            if (status == 'downloading' || status == 'pending')
                              OutlinedButton.icon(
                                onPressed: () => _act('pause_task', t['task_id']),
                                icon: const Icon(Icons.pause_rounded, size: 18),
                                label: const Text('暂停'),
                              ),
                            if (status == 'paused' || status == 'failed' || status == 'cancelled')
                              OutlinedButton.icon(
                                onPressed: () => _act('retry_task', t['task_id']),
                                icon: const Icon(Icons.play_arrow_rounded, size: 18),
                                label: Text(I18n.t('action.retry')),
                              ),
                            if (status == 'downloading' || status == 'pending')
                              OutlinedButton.icon(
                                onPressed: () => _act('cancel_task', t['task_id']),
                                icon: const Icon(Icons.stop_rounded, size: 18),
                                label: Text(I18n.t('action.cancel')),
                              ),
                            IconButton(
                              tooltip: I18n.t('action.remove'),
                              onPressed: () => _act('remove_task', t['task_id']),
                              icon: const Icon(Icons.close_rounded, size: 20),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
    );
  }
}
