#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键启动测试环境脚本
整合所有测试功能，提供统一的启动入口
"""

import os
import sys
import time
import subprocess
import threading
from pathlib import Path
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_dependencies():
    """检查依赖环境"""
    logger.info("🔍 检查依赖环境...")
    
    required_packages = [
        'flask', 'requests', 'sqlite3'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"❌ 缺少依赖包: {', '.join(missing_packages)}")
        logger.info("请运行: pip install flask requests")
        return False
    
    logger.info("✅ 依赖环境检查通过")
    return True

def setup_test_environment():
    """设置测试环境"""
    logger.info("🛠️ 设置测试环境...")
    
    try:
        # 创建必要的目录
        directories = [
            'test_videos',
            'test_videos/fall_detection', 
            'test_videos/fire_detection',
            'test_videos/smoke_detection',
            'test_videos/normal_scenes',
            'test_videos/mixed_scenarios',
            'test_videos/synthetic_data',
            'test_videos/real_world_samples'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        # 初始化视频资源管理器
        try:
            from video_resource_manager import setup_test_video_environment
            setup_test_video_environment()
        except Exception as e:
            logger.warning(f"视频环境设置失败: {e}")
        
        logger.info("✅ 测试环境设置完成")
        return True
        
    except Exception as e:
        logger.error(f"❌ 测试环境设置失败: {e}")
        return False

def start_service(script_name, port, description):
    """启动服务"""
    def run_service():
        try:
            logger.info(f"🚀 启动 {description}...")
            subprocess.run([sys.executable, script_name], 
                         capture_output=False, text=True)
        except Exception as e:
            logger.error(f"❌ {description} 启动失败: {e}")
    
    if Path(script_name).exists():
        thread = threading.Thread(target=run_service)
        thread.daemon = True
        thread.start()
        return thread
    else:
        logger.warning(f"⚠️ 服务文件不存在: {script_name}")
        return None

def main():
    """主函数"""
    print("🧪 康养AI检测算法测试平台")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        sys.exit(1)
    
    # 设置环境
    if not setup_test_environment():
        sys.exit(1)
    
    print("\n🎯 可用测试服务:")
    print("1. 测试框架Web界面 (端口 5558)")
    print("2. 简化视频测试服务 (端口 5557)")
    print("3. 视频测试API服务 (端口 5556)")
    
    # 获取用户选择
    try:
        choice = input("\n请选择要启动的服务 (1-3) 或 'all' 启动全部: ").strip().lower()
    except KeyboardInterrupt:
        print("\n👋 用户取消启动")
        sys.exit(0)
    
    services = []
    
    if choice == 'all':
        services = [
            ('test_framework_web.py', 5558, '测试框架Web界面'),
            ('simple_video_test.py', 5557, '简化视频测试服务'),
            ('video_test_api.py', 5556, '视频测试API服务')
        ]
    elif choice == '1':
        services = [('test_framework_web.py', 5558, '测试框架Web界面')]
    elif choice == '2':
        services = [('simple_video_test.py', 5557, '简化视频测试服务')]
    elif choice == '3':
        services = [('video_test_api.py', 5556, '视频测试API服务')]
    else:
        print("❌ 无效选择")
        sys.exit(1)
    
    # 启动选中的服务
    threads = []
    for script, port, desc in services:
        thread = start_service(script, port, desc)
        if thread:
            threads.append((thread, script, port, desc))
    
    if not threads:
        print("❌ 没有可启动的服务")
        sys.exit(1)
    
    # 等待服务启动
    print("\n⏳ 等待服务启动...")
    time.sleep(3)
    
    # 显示访问信息
    print("\n✅ 服务启动完成!")
    print("📍 访问地址:")
    
    for _, script, port, desc in threads:
        print(f"  - {desc}: http://localhost:{port}")
    
    print("\n🎯 功能介绍:")
    print("  📊 测试框架Web界面: 完整的测试管理和报告")
    print("  ⚡ 简化视频测试: 快速算法验证")  
    print("  🔧 视频测试API: 程序化接口调用")
    
    print("\n📚 使用指南:")
    print("  1. 浏览器访问Web界面进行可视化测试")
    print("  2. 上传测试视频或使用预设场景")
    print("  3. 查看详细测试报告和性能分析")
    print("  4. 管理测试用例和历史记录")
    
    print("\n📋 测试建议:")
    print("  - 从简单场景开始测试")
    print("  - 逐步增加测试难度")
    print("  - 关注准确率和处理速度")
    print("  - 记录和分析失败案例")
    
    # 保持运行
    try:
        print("\n🔄 服务运行中... (按 Ctrl+C 退出)")
        while True:
            time.sleep(1)
            # 检查线程状态
            active_threads = [t for t, _, _, _ in threads if t.is_alive()]
            if len(active_threads) == 0:
                print("⚠️ 所有服务已停止")
                break
    
    except KeyboardInterrupt:
        print("\n👋 正在停止服务...")
    
    print("✅ 测试平台已关闭")

if __name__ == "__main__":
    main()