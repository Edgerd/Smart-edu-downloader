# -*- coding: utf-8 -*-
"""项目静态扫描工具：检测常见 bug 与代码异味。

仅用于只读扫描，不修改任何源文件。
"""

import ast
import os
import re
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
IGNORE_DIRS = {'.venv', '.git', '__pycache__', '.pytest_cache', 'dist', 'build'}
IGNORE_PATHS = {'.dev/test', 'gui/examples'}
IGNORE_FILES = {'scan_bugs.py'}

CHINESE_RE = re.compile(r'[\u4e00-\u9fff]')
THEME_COLORS = {'#1A82E2', '#1a82e2', '#2078DA', '#2078da'}

# 允许使用默认主题色的场景关键词
_THEME_FALLBACK_KEYWORDS = {
    'load_accent_color', 'load_theme_color', 'get_settings_manager',
    'settings.get', 'default_settings', 'except', 'return',
    '"theme_color"', '"accent_color"',
}

# 允许保留中文的业务/数据模块路径片段
_CHINESE_WHITELIST_PATHS = {
    'search_engine.py', 'search_suggester.py', 'search_filter.py',
    'search_index.py', 'resource_processor.py', 'file_categorizer.py',
    'textbook_info.py', 'resource_fetcher.py', 'resource_library.py',
}

# 主题色检测中完全忽略的文件
_THEME_IGNORE_FILES = {'icon_manager.py', 'vertical_tab_widget.py'}

# print 检测中完全忽略的文件（日志/测试输出等合理场景）
_PRINT_IGNORE_FILES = {'logger.py'}


def _should_ignore_path(rel_path: str) -> bool:
    """根据相对路径判断是否需要忽略。"""
    for ignore in IGNORE_PATHS:
        if ignore in rel_path.replace('\\', '/'):
            return True
    return False


def iter_py_files():
    """遍历项目中的 Python 源文件。"""
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for name in files:
            if name.endswith('.py') and name not in IGNORE_FILES:
                path = Path(root) / name
                rel = path.relative_to(PROJECT_ROOT).as_posix()
                if _should_ignore_path(rel):
                    continue
                yield path


def get_docstring_lines(tree: ast.AST, lines: list[str]) -> set[int]:
    """返回 docstring 所占的行号集合。"""
    docstring_lines = set()
    for node in ast.walk(tree):
        doc = None
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            doc = ast.get_docstring(node)
        if doc and node.body:
            body_node = node.body[0]
            start = getattr(body_node, 'lineno', 1)
            end = getattr(body_node, 'end_lineno', start)
            for i in range(start, end + 1):
                docstring_lines.add(i)
    return docstring_lines


def check_hardcoded_theme_color(file_path: Path, source: str, lines: list[str]) -> list[str]:
    """检测非默认参数/注释/docstring 位置的硬编码主题色。"""
    issues = []
    rel = file_path.relative_to(PROJECT_ROOT).as_posix()
    if file_path.name in _THEME_IGNORE_FILES:
        return issues
    try:
        tree = ast.parse(source)
        docstring_lines = get_docstring_lines(tree, lines)
    except SyntaxError:
        docstring_lines = set()
    prev_line = ""
    for idx, line in enumerate(lines, start=1):
        if not any(c in line for c in THEME_COLORS):
            prev_line = line
            continue
        if idx in docstring_lines:
            prev_line = line
            continue
        stripped = line.strip()
        if stripped.startswith('#'):
            prev_line = line
            continue
        # 函数默认参数、配置读取、异常回退等场景允许使用默认主题色
        if any(kw in line for kw in _THEME_FALLBACK_KEYWORDS):
            prev_line = line
            continue
        # 多行函数签名中的默认参数
        if 'def ' in prev_line and 'accent_color' in line and '=' in line:
            prev_line = line
            continue
        if 'def ' in line and '=' in line and 'accent_color' in line:
            prev_line = line
            continue
        if 'theme_color' in line and '= ' in line:
            prev_line = line
            continue
        prev_line = line
        issues.append(f"{rel}:{idx}: 疑似硬编码主题色: {stripped[:80]}")
    return issues


def check_bare_except(file_path: Path, lines: list[str]) -> list[str]:
    """检测裸异常捕获。"""
    issues = []
    for idx, line in enumerate(lines, start=1):
        if re.match(r'^\s*except\s*:', line):
            issues.append(f"{file_path.relative_to(PROJECT_ROOT)}:{idx}: 裸异常捕获")
    return issues


def check_chinese_hardcode(file_path: Path, source: str, tree: ast.AST, lines: list[str]) -> list[str]:
    """检测不在 docstring 且不在 _() 中的中文字符串。"""
    issues = []
    rel = file_path.relative_to(PROJECT_ROOT).as_posix()
    if 'i18n' in rel:
        return issues
    # 搜索/资源等业务数据模块允许保留中文关键词
    if any(whitelisted in rel for whitelisted in _CHINESE_WHITELIST_PATHS):
        return issues

    docstring_lines = get_docstring_lines(tree, lines)

    class ChineseStringVisitor(ast.NodeVisitor):
        def visit_Str(self, node):
            self._check(node)

        def visit_Constant(self, node):
            if isinstance(node.value, str):
                self._check(node)

        def _check(self, node):
            if not CHINESE_RE.search(node.value):
                return
            # 跳过 docstring
            if node.lineno in docstring_lines:
                return
            # 跳过被 _(...) 或 _(..., key=...) 包裹的字符串
            parent = getattr(node, 'parent', None)
            if isinstance(parent, ast.Call):
                func = parent.func
                if isinstance(func, ast.Name) and func.id == '_':
                    return
            issues.append(f"{rel}:{node.lineno}: 疑似中文硬编码: {node.value[:40]}")


    # 为每个节点设置父节点引用
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            setattr(child, 'parent', parent)

    ChineseStringVisitor().visit(tree)
    return issues


def check_deprecated_api(file_path: Path, lines: list[str]) -> list[str]:
    """检测已弃用的 Qt API。"""
    issues = []
    for idx, line in enumerate(lines, start=1):
        if 'exec_()' in line:
            issues.append(f"{file_path.relative_to(PROJECT_ROOT)}:{idx}: 使用已弃用的 exec_()")
    return issues


def check_print_statements(file_path: Path, lines: list[str]) -> list[str]:
    """检测非 __main__ 块中的 print 语句。"""
    issues = []
    rel = file_path.relative_to(PROJECT_ROOT).as_posix()
    # 启动脚本在日志系统初始化前允许使用 print
    if rel == 'main.py' or file_path.name in _PRINT_IGNORE_FILES:
        return issues
    in_main = False
    main_depth = 0
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith('if __name__'):
            in_main = True
            main_depth = line[:len(line) - len(line.lstrip())].count('    ')
            continue
        if in_main:
            indent = line[:len(line) - len(line.lstrip())].count('    ') if stripped else main_depth + 1
            if indent <= main_depth and stripped and not stripped.startswith('#'):
                in_main = False
        if re.match(r'^\s*print\s*[( ]', line) and not in_main:
            issues.append(f"{rel}:{idx}: 非 __main__ 块中的 print")
    return issues


def check_resource_leaks(file_path: Path, lines: list[str]) -> list[str]:
    """检测可能的资源泄漏模式。"""
    issues = []
    for idx, line in enumerate(lines, start=1):
        if 'requests.Session()' in line and 'http_client' not in str(file_path):
            issues.append(f"{file_path.relative_to(PROJECT_ROOT)}:{idx}: 直接创建 requests.Session()")
    return issues


def main():
    """主入口。"""
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    all_issues = []
    for py_file in iter_py_files():
        try:
            with py_file.open('r', encoding='utf-8-sig') as f:
                source = f.read()
                lines = source.splitlines()
            tree = ast.parse(source)
        except SyntaxError as e:
            print(f"语法错误 {py_file}: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"无法读取 {py_file}: {e}", file=sys.stderr)
            continue

        all_issues.extend(check_hardcoded_theme_color(py_file, source, lines))
        all_issues.extend(check_bare_except(py_file, lines))
        all_issues.extend(check_chinese_hardcode(py_file, source, tree, lines))
        all_issues.extend(check_deprecated_api(py_file, lines))
        all_issues.extend(check_print_statements(py_file, lines))
        all_issues.extend(check_resource_leaks(py_file, lines))

    output_path = PROJECT_ROOT / '.dev' / 'test' / 'scan_output.txt'
    with output_path.open('w', encoding='utf-8') as out:
        if not all_issues:
            out.write("未检测到明显问题。\n")
            print("未检测到明显问题。")
            return

        out.write(f"共检测到 {len(all_issues)} 处问题：\n\n")
        for issue in all_issues:
            out.write(issue + "\n")

    print(f"扫描完成，共检测到 {len(all_issues)} 处问题，结果已保存到 {output_path}")


if __name__ == '__main__':
    main()
