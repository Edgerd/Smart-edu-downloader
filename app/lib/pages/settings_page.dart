// 设置页
import 'package:flutter/material.dart';

import '../core_ffi.dart';
import '../i18n.dart';
import '../theme.dart';
import '../main.dart' show SedApp;

class SettingsPage extends StatefulWidget {
  const SettingsPage({super.key});

  @override
  State<SettingsPage> createState() => _SettingsPageState();
}

class _SettingsPageState extends State<SettingsPage> {
  Map<String, dynamic> _s = {};

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final r = await Future(() => Core.call('get_settings'));
    if (mounted) {
      setState(() => _s = ((r['data'] as Map?) ?? {}).cast<String, dynamic>());
    }
  }

  Future<void> _set(String key, dynamic value) async {
    await Future(() => Core.call('set_setting', {'key': key, 'value': value}));
    await _load();
    if (mounted) SedApp.reload(context);
  }

  Future<void> _setToken(String token) async {
    await Future(() => Core.call('set_access_token', {'token': token}));
    await _load();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(I18n.t('settings.title'))),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _group(context, I18n.t('settings.token'), [
            Padding(
              padding: const EdgeInsets.all(16),
              child: TextField(
                obscureText: true,
                controller: TextEditingController(
                    text: (_s['access_token'] as String? ?? '').startsWith('xor:')
                        ? ''
                        : _s['access_token'] as String? ?? ''),
                onSubmitted: _setToken,
                decoration: InputDecoration(
                  hintText: I18n.t('settings.token_hint'),
                  suffixIcon: TextButton(
                    onPressed: () {
                      final ctrl = TextEditingController();
                      showDialog(
                        context: context,
                        builder: (ctx) => AlertDialog(
                          title: Text(I18n.t('settings.token')),
                          content: TextField(
                            controller: ctrl,
                            maxLines: 3,
                            decoration: InputDecoration(
                                hintText: I18n.t('settings.token_hint')),
                          ),
                          actions: [
                            TextButton(
                                onPressed: () => Navigator.pop(ctx),
                                child: Text(I18n.t('action.cancel'))),
                            FilledButton(
                                onPressed: () {
                                  _setToken(ctrl.text.trim());
                                  Navigator.pop(ctx);
                                },
                                child: Text(I18n.t('action.save'))),
                          ],
                        ),
                      );
                    },
                    child: Text(I18n.t('action.save')),
                  ),
                ),
              ),
            ),
          ]),
          _group(context, I18n.t('settings.download_dir'), [
            _pathTile(context, I18n.t('settings.download_dir'), 'download_dir'),
            _numTile(context, I18n.t('settings.max_concurrent'),
                'max_concurrent_downloads', 1, 20),
            _numTile(context, I18n.t('settings.threads'), 'download_threads', 1, 32),
            _numTile(
                context, I18n.t('settings.speed_limit'), 'speed_limit', 0, 100000),
            _switchTile(context, I18n.t('settings.categorize'), 'auto_categorize'),
            _choiceTile(
              context,
              I18n.t('settings.naming_rule'),
              'file_naming_rule',
              {
                'default': I18n.t('settings.naming.default'),
                'timestamp': I18n.t('settings.naming.timestamp'),
                'textbook_name_timestamp':
                    I18n.t('settings.naming.textbook_name_timestamp'),
              },
            ),
          ]),
          _group(context, I18n.t('settings.search_mode'), [
            _choiceTile(
              context,
              I18n.t('settings.search_mode'),
              'search_mode',
              {
                'approximate': I18n.t('settings.search.approximate'),
                'exact': I18n.t('settings.search.exact'),
                'fuzzy': I18n.t('settings.search.fuzzy'),
              },
            ),
          ]),
          _group(context, I18n.t('settings.theme_color'), [
            Padding(
              padding: const EdgeInsets.all(16),
              child: Wrap(
                spacing: 12,
                children: [
                  for (final c in const [
                    ('#1277DD', '经典蓝'),
                    ('#673AB7', '深紫'),
                    ('#00897B', '青绿'),
                    ('#E91E63', '品红'),
                    ('#F57C00', '活力橙'),
                    ('#3F51B5', '靛蓝'),
                  ])
                    _ColorDot(
                      color: AppTheme.seedFrom(c.$1),
                      selected:
                          (_s['theme_seed_color'] as String? ?? '').toUpperCase() ==
                              c.$1.toUpperCase(),
                      onTap: () => _set('theme_seed_color', c.$1),
                    ),
                ],
              ),
            ),
            _choiceTile(
              context,
              I18n.t('settings.theme_mode'),
              'theme_mode',
              {'system': I18n.t('common.system'), 'light': I18n.t('common.light'), 'dark': I18n.t('common.dark')},
            ),
          ]),
          _group(context, I18n.t('settings.language'), [
            _choiceTile(
              context,
              I18n.t('settings.language'),
              'language',
              {'zh_CN': '简体中文', 'zh_TW': '繁體中文', 'en_US': 'English', 'ja_JP': '日本語'},
            ),
          ]),
          _group(context, I18n.t('settings.ssl_verify'), [
            _switchTile(context, I18n.t('settings.ssl_verify'), 'ssl_verify',
                subtitle: I18n.t('settings.ssl_verify_desc')),
          ]),
          _group(context, I18n.t('settings.proxy'), [
            _switchTile(context, I18n.t('settings.proxy_enabled'), 'proxy_enabled'),
            _textTile(context, I18n.t('settings.proxy_host'), 'proxy_host'),
            _textTile(context, I18n.t('settings.proxy_port'), 'proxy_port'),
          ]),
          _group(context, I18n.t('settings.about'), [
            ListTile(
              leading: const Icon(Icons.info_rounded),
              title: Text(I18n.t('settings.about')),
              subtitle: Text(I18n.t('settings.about_desc')),
            ),
            ListTile(
              leading: const Icon(Icons.cleaning_services_rounded),
              title: Text(I18n.t('settings.clear_cache')),
              onTap: () async {
                await Future(() => Core.call('clear_cache'));
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('OK')));
                }
              },
            ),
            ListTile(
              leading: const Icon(Icons.history_rounded),
              title: Text(I18n.t('settings.clear_history')),
              onTap: () async {
                await Future(() => Core.call('clear_history'));
                if (context.mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('OK')));
                }
              },
            ),
          ]),
          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _group(BuildContext context, String title, List<Widget> children) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.only(left: 8, bottom: 8),
            child: Text(title,
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                    fontWeight: FontWeight.w800,
                    color: Theme.of(context).colorScheme.primary)),
          ),
          Card(child: Column(children: children)),
        ],
      ),
    );
  }

  Widget _switchTile(BuildContext context, String title, String key,
      {String? subtitle}) {
    return SwitchListTile(
      value: _s[key] as bool? ?? false,
      onChanged: (v) => _set(key, v),
      title: Text(title),
      subtitle: subtitle != null ? Text(subtitle) : null,
    );
  }

  Widget _numTile(BuildContext context, String title, String key, int min, int max) {
    final v = (_s[key] as num?)?.toInt() ?? min;
    return ListTile(
      title: Text(title),
      trailing: SizedBox(
        width: 120,
        child: TextFormField(
          key: ValueKey('$key-$v'),
          initialValue: '$v',
          keyboardType: TextInputType.number,
          textAlign: TextAlign.end,
          onFieldSubmitted: (s) {
            final n = int.tryParse(s) ?? min;
            _set(key, n.clamp(min, max));
          },
          decoration:
              const InputDecoration(isDense: true, border: InputBorder.none),
        ),
      ),
    );
  }

  Widget _textTile(BuildContext context, String title, String key) {
    return ListTile(
      title: Text(title),
      trailing: SizedBox(
        width: 160,
        child: TextFormField(
          key: ValueKey('$key-${_s[key] ?? ''}'),
          initialValue: _s[key] as String? ?? '',
          textAlign: TextAlign.end,
          onFieldSubmitted: (s) => _set(key, s),
          decoration:
              const InputDecoration(isDense: true, border: InputBorder.none),
        ),
      ),
    );
  }

  Widget _pathTile(BuildContext context, String title, String key) {
    return ListTile(
      title: Text(title),
      subtitle: Text(_s[key] as String? ?? ''),
      trailing: const Icon(Icons.folder_open_rounded),
      onTap: () {
        final ctrl = TextEditingController(text: _s[key] as String? ?? '');
        showDialog(
          context: context,
          builder: (ctx) => AlertDialog(
            title: Text(title),
            content: TextField(controller: ctrl),
            actions: [
              TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: Text(I18n.t('action.cancel'))),
              FilledButton(
                  onPressed: () {
                    _set(key, ctrl.text.trim());
                    Navigator.pop(ctx);
                  },
                  child: Text(I18n.t('action.save'))),
            ],
          ),
        );
      },
    );
  }

  Widget _choiceTile(BuildContext context, String title, String key,
      Map<String, String> options) {
    final current = _s[key] as String? ?? options.keys.first;
    return ListTile(
      title: Text(title),
      trailing: DropdownButton<String>(
        value: options.containsKey(current) ? current : options.keys.first,
        underline: const SizedBox(),
        items: [
          for (final e in options.entries)
            DropdownMenuItem(value: e.key, child: Text(e.value)),
        ],
        onChanged: (v) {
          if (v != null) _set(key, v);
        },
      ),
    );
  }
}

class _ColorDot extends StatelessWidget {
  final Color color;
  final bool selected;
  final VoidCallback onTap;
  const _ColorDot(
      {required this.color, required this.selected, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      customBorder: const CircleBorder(),
      child: Container(
        width: 44,
        height: 44,
        decoration: BoxDecoration(
          color: color,
          shape: BoxShape.circle,
          border: selected
              ? Border.all(
                  color: Theme.of(context).colorScheme.onSurface, width: 3)
              : null,
        ),
        child: selected
            ? const Icon(Icons.check_rounded, color: Colors.white)
            : null,
      ),
    );
  }
}
