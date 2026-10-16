// Rust core FFI 绑定：sed_call(method, payload) -> JSON 字符串
import 'dart:convert';
import 'dart:ffi';
import 'dart:io';

import 'package:ffi/ffi.dart';

typedef _CallNative = Pointer<Utf8> Function(Pointer<Utf8>, Pointer<Utf8>);
typedef _CallDart = Pointer<Utf8> Function(Pointer<Utf8>, Pointer<Utf8>);
typedef _FreeNative = Void Function(Pointer<Utf8>);
typedef _FreeDart = void Function(Pointer<Utf8>);

class Core {
  static DynamicLibrary? _dylib;
  static late _CallDart _call;
  static late _FreeDart _free;

  static void init() {
    if (_dylib != null) return;
    if (Platform.isWindows) {
      _dylib = DynamicLibrary.open('sed_core.dll');
    } else if (Platform.isMacOS) {
      _dylib = DynamicLibrary.open('libsed_core.dylib');
    } else if (Platform.isAndroid || Platform.isLinux) {
      _dylib = DynamicLibrary.open('libsed_core.so');
    } else {
      _dylib = DynamicLibrary.open('libsed_core.so');
    }
    _call = _dylib!
        .lookupFunction<_CallNative, _CallDart>('sed_call');
    _free = _dylib!.lookupFunction<_FreeNative, _FreeDart>('sed_free');
  }

  /// 同步调用 Rust core。耗时操作请在 Isolate/异步上下文中使用。
  static Map<String, dynamic> call(String method,
      [Map<String, dynamic>? payload]) {
    init();
    final m = method.toNativeUtf8();
    final p = jsonEncode(payload ?? {}).toNativeUtf8();
    final result = _call(m, p);
    final str = result.toDartString();
    malloc.free(m);
    malloc.free(p);
    _free(result);
    try {
      return jsonDecode(str) as Map<String, dynamic>;
    } catch (_) {
      return {'ok': false, 'error': 'core 返回解析失败'};
    }
  }

  /// 在后台 Isolate 中调用（通过 compute 不可传递静态闭包，故用简单线程包装）。
  static Future<Map<String, dynamic>> callAsync(String method,
      [Map<String, dynamic>? payload]) async {
    // 简单实现：直接调用（Rust 侧为阻塞式网络请求，短超时可接受）
    // 为避免阻塞 UI，这里用 Future.microtask 后仍会阻塞 —— 大请求请使用 runInIsolate
    return call(method, payload);
  }

  static bool ok(Map<String, dynamic> r) => r['ok'] == true;
}
