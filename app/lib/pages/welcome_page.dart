// 首次启动欢迎向导
import 'package:flutter/material.dart';

import '../core_ffi.dart';
import '../i18n.dart';

class WelcomePage extends StatefulWidget {
  final VoidCallback onDone;
  const WelcomePage({super.key, required this.onDone});

  @override
  State<WelcomePage> createState() => _WelcomePageState();
}

class _WelcomePageState extends State<WelcomePage> {
  final _ctrl = PageController();
  int _page = 0;
  final _tokenCtrl = TextEditingController();
  Color _seed = const Color(0xFF1277DD);
  bool _agree = false;

  Future<void> _next() async {
    if (_page < 2) {
      await _ctrl.nextPage(
          duration: const Duration(milliseconds: 400), curve: Curves.easeOutCubic);
    } else {
      if (_tokenCtrl.text.trim().isNotEmpty) {
        await Future(() =>
            Core.call('set_access_token', {'token': _tokenCtrl.text.trim()}));
      }
      await Future(() =>
          Core.call('set_setting', {'key': 'theme_seed_color', 'value': '#${_seed.toARGB32().toRadixString(16).substring(2).toUpperCase()}'}));
      widget.onDone();
    }
  }

  @override
  void dispose() {
    _ctrl.dispose();
    _tokenCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: PageView(
                controller: _ctrl,
                physics: const NeverScrollableScrollPhysics(),
                onPageChanged: (i) => setState(() => _page = i),
                children: [
                  // 1 欢迎
                  Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Container(
                          width: 120,
                          height: 120,
                          decoration: BoxDecoration(
                            color: cs.primaryContainer,
                            borderRadius: BorderRadius.circular(40),
                          ),
                          child: Icon(Icons.school_rounded,
                              size: 64, color: cs.primary),
                        ),
                        const SizedBox(height: 32),
                        Text(I18n.t('welcome.title'),
                            style: Theme.of(context)
                                .textTheme
                                .headlineMedium
                                ?.copyWith(fontWeight: FontWeight.w900)),
                        const SizedBox(height: 12),
                        Text(I18n.t('settings.about_desc'),
                            textAlign: TextAlign.center,
                            style: TextStyle(color: cs.onSurfaceVariant)),
                        const SizedBox(height: 24),
                        CheckboxListTile(
                          value: _agree,
                          onChanged: (v) => setState(() => _agree = v ?? false),
                          controlAffinity: ListTileControlAffinity.leading,
                          title: const Text('我已阅读并同意用户协议（仅供学习交流）'),
                        ),
                      ],
                    ),
                  ),
                  // 2 主题色
                  Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(I18n.t('settings.theme_color'),
                            style: Theme.of(context)
                                .textTheme
                                .headlineSmall
                                ?.copyWith(fontWeight: FontWeight.w800)),
                        const SizedBox(height: 24),
                        Wrap(
                          spacing: 16,
                          runSpacing: 16,
                          children: [
                            for (final c in const [
                              Color(0xFF1277DD),
                              Color(0xFF673AB7),
                              Color(0xFF00897B),
                              Color(0xFFE91E63),
                              Color(0xFFF57C00),
                              Color(0xFF3F51B5),
                            ])
                              InkWell(
                                onTap: () => setState(() => _seed = c),
                                customBorder: const CircleBorder(),
                                child: Container(
                                  width: 56,
                                  height: 56,
                                  decoration: BoxDecoration(
                                    color: c,
                                    shape: BoxShape.circle,
                                    border: _seed == c
                                        ? Border.all(
                                            color: cs.onSurface, width: 3)
                                        : null,
                                  ),
                                  child: _seed == c
                                      ? const Icon(Icons.check_rounded,
                                          color: Colors.white)
                                      : null,
                                ),
                              ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  // 3 Token
                  Padding(
                    padding: const EdgeInsets.all(32),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(I18n.t('welcome.token_page'),
                            style: Theme.of(context)
                                .textTheme
                                .headlineSmall
                                ?.copyWith(fontWeight: FontWeight.w800)),
                        const SizedBox(height: 12),
                        Text(I18n.t('welcome.token_desc'),
                            style: TextStyle(color: cs.onSurfaceVariant)),
                        const SizedBox(height: 24),
                        TextField(
                          controller: _tokenCtrl,
                          maxLines: 2,
                          decoration: InputDecoration(
                              hintText: I18n.t('settings.token_hint')),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(24),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      for (var i = 0; i < 3; i++)
                        Container(
                          width: i == _page ? 28 : 10,
                          height: 10,
                          margin: const EdgeInsets.only(right: 6),
                          decoration: BoxDecoration(
                            color: i == _page ? cs.primary : cs.surfaceContainerHighest,
                            borderRadius: BorderRadius.circular(999),
                          ),
                        ),
                    ],
                  ),
                  FilledButton.icon(
                    onPressed: (_page == 0 && !_agree) ? null : _next,
                    icon: Icon(_page < 2
                        ? Icons.arrow_forward_rounded
                        : Icons.check_rounded),
                    label: Text(_page < 2
                        ? I18n.t('welcome.next')
                        : I18n.t('welcome.done')),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
