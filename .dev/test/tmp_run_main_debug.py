"""临时启动调试脚本"""
import sys
import traceback

sys.path.insert(0, '.')

try:
    import main
    main.main()
except Exception as e:
    with open('.dev/test/startup_error_debug.log', 'w', encoding='utf-8') as f:
        f.write(f"Exception: {e}\n")
        traceback.print_exc(file=f)
    print(f"Exception: {e}")
    traceback.print_exc()
    sys.exit(1)
