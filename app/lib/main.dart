// Smart-edu-downloader 2.0 — Flutter + Rust
import 'dart:async';
import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:shared_preferences/shared_preferences.dart';

import 'core_ffi.dart';
import 'i18n.dart';
import 'pages/download_page.dart';
import 'pages/home_page.dart';
import 'pages/history_page.dart';
import 'pages/resource_page.dart';
import 'pages/settings_page.dart';
import 'pages/welcome_page.dart';
import 'theme.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  Core.init();
  final prefs = await SharedPreferences.getInstance();

  // 初始化 Rust core 数据目录
  final supportDir = Platform.isWindows
      ? Directory('${Platform.environment['APPDATA']}\\Smart-edu-downloader-2.0')
      : Platform.isMacOS
          ? Directory(
              '${Platform.environment['HOME']}/Library/Application Support/Smart-edu-downloader-2.0')
          : Directory(
              '${Platform.environment['HOME']}/.local/share/Smart-edu-downloader-2.0');
  await supportDir.create(recursive: true);
  Core.call('init', {'data_dir': supportDir.path});

  final settings = Core.call('get_settings');
  final data = (settings['data'] as Map?)?.cast<String, dynamic>() ?? {};

  // 启动次数统计
  final launchCount = (data['launch_count'] as num?)?.toInt() ?? 0;
  if (launchCount == 0) {
    Core.call('set_setting', {'key': 'first_run', 'value': true});
  }
  Core.call('set_setting', {'key': 'launch_count', 'value': launchCount + 1});

  final firstRun = prefs.getBool('first_run_done') != true &&
      (data['first_run'] as bool? ?? true);
  I18n.setLocale(data['language'] as String? ?? 'zh_CN');
  final themeMode = data['theme_mode'] as String? ?? 'system';
  final seed = AppTheme.seedFrom(data['theme_seed_color'] as String? ?? '#1277DD');

  runApp(SedApp(
    firstRun: firstRun,
    themeMode: _mode(themeMode),
    seed: seed,
  ));
}

ThemeMode _mode(String s) {
  switch (s) {
    case 'light':
      return ThemeMode.light;
    case 'dark':
      return ThemeMode.dark;
    default:
      return ThemeMode.system;
  }
}

class SedApp extends StatefulWidget {
  final bool firstRun;
  final ThemeMode themeMode;
  final Color seed;
  const SedApp(
      {super.key,
      required this.firstRun,
      required this.themeMode,
      required this.seed});

  static void reload(BuildContext context) =>
      context.findAncestorStateOfType<_SedAppState>()!.reload();

  @override
  State<SedApp> createState() => _SedAppState();
}

class _SedAppState extends State<SedApp> {
  late bool _firstRun;
  late ThemeMode _themeMode;
  late Color _seed;

  @override
  void initState() {
    super.initState();
    _firstRun = widget.firstRun;
    _themeMode = widget.themeMode;
    _seed = widget.seed;
  }

  void reload() {
    final settings = Core.call('get_settings');
    final data = (settings['data'] as Map?)?.cast<String, dynamic>() ?? {};
    setState(() {
      I18n.setLocale(data['language'] as String? ?? 'zh_CN');
      _themeMode = _mode(data['theme_mode'] as String? ?? 'system');
      _seed =
          AppTheme.seedFrom(data['theme_seed_color'] as String? ?? '#1277DD');
    });
  }

  void finishWelcome() {
    Core.call('set_setting', {'key': 'first_run', 'value': false});
    SharedPreferences.getInstance().then((p) => p.setBool('first_run_done', true));
    setState(() => _firstRun = false);
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: I18n.appName,
      debugShowCheckedModeBanner: false,
      theme: AppTheme.light(_seed),
      darkTheme: AppTheme.dark(_seed),
      themeMode: _themeMode,
      home: _firstRun
          ? WelcomePage(onDone: finishWelcome)
          : const _Shell(),
    );
  }
}

class _Shell extends StatefulWidget {
  const _Shell();

  @override
  State<_Shell> createState() => _ShellState();
}

class _ShellState extends State<_Shell> {
  int _index = 0;
  Timer? _clipboardTimer;
  final bool _clipboardAlerting = false;

  final _pages = const [
    HomePage(),
    ResourcePage(),
    DownloadPage(),
    HistoryPage(),
    SettingsPage(),
  ];

  @override
  void initState() {
    super.initState();
    _startClipboardMonitor();
  }

  @override
  void dispose() {
    _clipboardTimer?.cancel();
    super.dispose();
  }

  void _startClipboardMonitor() {
    _clipboardTimer = Timer.periodic(const Duration(seconds: 2), (_) async {
      if (!_clipboardAlerting) {
        try {
          final text = await Clipboard.getData(Clipboard.kTextPlain);
          final s = text?.text ?? '';
          if (s.contains('smartedu.cn') &&
              (s.contains('contentId') || s.contains('tchMaterial'))) {
            ClipboardEvents.announce(s);
          }
        } catch (_) {}
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(index: _index, children: _pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: [
          NavigationDestination(
              icon: const Icon(Icons.home_outlined),
              selectedIcon: const Icon(Icons.home_rounded),
              label: I18n.home),
          NavigationDestination(
              icon: const Icon(Icons.auto_stories_outlined),
              selectedIcon: const Icon(Icons.auto_stories_rounded),
              label: I18n.resource),
          NavigationDestination(
              icon: const Icon(Icons.download_outlined),
              selectedIcon: const Icon(Icons.download_rounded),
              label: I18n.downloads),
          NavigationDestination(
              icon: const Icon(Icons.history_outlined),
              selectedIcon: const Icon(Icons.history_rounded),
              label: I18n.history),
          NavigationDestination(
              icon: const Icon(Icons.settings_outlined),
              selectedIcon: const Icon(Icons.settings_rounded),
              label: I18n.settings),
        ],
      ),
    );
  }
}

/// 剪贴板事件广播（首页监听）
class ClipboardEvents {
  static final ValueNotifier<String?> detected = ValueNotifier(null);
  static void announce(String url) {
    if (detected.value != url) detected.value = url;
  }

  static void consume() => detected.value = null;
}
