#!/bin/bash
set -e

# 函数：启动主应用
start_app() {
    echo "🚀 启动AI检测主应用..."
    exec python app.py
}

# 函数：启动测试框架
start_test() {
    echo "🧪 启动AI测试框架..."
    exec python test_framework.py --mode=continuous
}

# 函数：启动测试Web界面
start_test_web() {
    echo "🌐 启动测试Web界面..."
    exec python test_framework_web.py
}

# 函数：启动测试平台
start_test_platform() {
    echo "🎯 启动完整测试平台..."
    exec python start_test_platform.py
}

# 函数：运行快速测试
run_quick_test() {
    echo "⚡ 运行快速验证测试..."
    python test_framework.py --mode=quick --output=/app/test_results/quick_test.json
    echo "✅ 快速测试完成，结果保存在 /app/test_results/"
    exit 0
}

# 根据参数决定启动模式
case "${1:-app}" in
    app)
        start_app
        ;;
    test)
        start_test
        ;;
    test-web)
        start_test_web
        ;;
    test-platform)
        start_test_platform
        ;;
    quick-test)
        run_quick_test
        ;;
    *)
        echo "❌ 未知的启动模式: $1"
        echo "📋 可用模式: app, test, test-web, test-platform, quick-test"
        exit 1
        ;;
esac