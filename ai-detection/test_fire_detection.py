#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试火焰检测功能 (不依赖OpenCV)
"""

import json
import time
from datetime import datetime

# 模拟火焰检测器类 (不使用OpenCV)
class MockFireDetector:
    def __init__(self):
        self.detection_history = []
        self.classes = {0: 'fire', 1: 'smoke'}
    
    def detect_fire_smoke(self, frame_data):
        """模拟火焰检测"""
        import random
        
        detections = []
        
        # 模拟火焰检测
        if random.random() < 0.3:  # 30%概率检测到火焰
            fire_detection = {
                'type': 'fire',
                'confidence': round(random.uniform(0.6, 0.9), 2),
                'bbox': [100, 150, 250, 300],
                'area': 22500,
                'center': [175, 225],
                'timestamp': datetime.now().isoformat()
            }
            detections.append(fire_detection)
        
        # 模拟烟雾检测
        if random.random() < 0.2:  # 20%概率检测到烟雾
            smoke_detection = {
                'type': 'smoke',
                'confidence': round(random.uniform(0.5, 0.8), 2),
                'bbox': [50, 50, 400, 250],
                'area': 70000,
                'center': [225, 150],
                'timestamp': datetime.now().isoformat()
            }
            detections.append(smoke_detection)
        
        return detections

def test_fire_detection():
    """测试火焰检测功能"""
    print("🔥 测试火焰检测算法...")
    
    detector = MockFireDetector()
    
    # 模拟处理10帧图像
    total_detections = 0
    fire_count = 0
    smoke_count = 0
    
    for frame_num in range(10):
        print(f"\n--- 处理第 {frame_num + 1} 帧 ---")
        
        # 模拟图像数据
        mock_frame = f"frame_{frame_num}"
        
        # 执行检测
        detections = detector.detect_fire_smoke(mock_frame)
        total_detections += len(detections)
        
        if detections:
            print(f"✅ 检测到 {len(detections)} 个目标:")
            for detection in detections:
                print(f"  - {detection['type']}: 置信度 {detection['confidence']}")
                print(f"    位置: {detection['bbox']}")
                print(f"    面积: {detection['area']}")
                
                if detection['type'] == 'fire':
                    fire_count += 1
                elif detection['type'] == 'smoke':
                    smoke_count += 1
        else:
            print("❌ 未检测到火焰或烟雾")
        
        time.sleep(0.1)  # 模拟处理时间
    
    # 输出统计结果
    print(f"\n📊 检测统计:")
    print(f"  总帧数: 10")
    print(f"  总检测数: {total_detections}")
    print(f"  火焰检测: {fire_count}")
    print(f"  烟雾检测: {smoke_count}")
    print(f"  检测率: {total_detections/10:.1%}")

def test_unified_detection_api():
    """测试统一检测API"""
    print("\n🔧 测试统一检测API...")
    
    import requests
    
    try:
        # 测试健康检查
        health_response = requests.get("http://localhost:5555/api/health")
        print(f"✅ 健康检查: {health_response.status_code}")
        health_data = health_response.json()
        print(f"  支持功能: {health_data.get('features', [])}")
        
        # 测试统计API
        stats_response = requests.get("http://localhost:5555/api/statistics")
        stats_data = stats_response.json()
        print(f"✅ 统计数据: 今日告警 {stats_data.get('today_alerts', 0)}")
        print(f"  - 跌倒: {stats_data.get('today_fall_alerts', 0)}")
        print(f"  - 火焰: {stats_data.get('today_fire_alerts', 0)}")
        print(f"  - 烟雾: {stats_data.get('today_smoke_alerts', 0)}")
        
        # 测试火焰专项统计
        fire_stats_response = requests.get("http://localhost:5555/api/fire_statistics")
        fire_stats = fire_stats_response.json()
        print(f"✅ 火焰检测统计:")
        print(f"  启用状态: {fire_stats.get('fire_detection_enabled', False)}")
        print(f"  模型类型: {fire_stats.get('fire_model_type', 'Unknown')}")
        print(f"  误报率: {fire_stats.get('false_positive_rate', 0):.1%}")
        
        # 测试图像处理API
        test_data = {
            "image": "test_image_base64_data",
            "camera_id": "test_camera",
            "enable_fall": True,
            "enable_fire": True
        }
        
        for i in range(3):
            process_response = requests.post(
                "http://localhost:5555/api/process_frame",
                json=test_data
            )
            
            if process_response.status_code == 200:
                result = process_response.json()
                detections = result.get('detections', [])
                alerts = result.get('alerts', [])
                
                print(f"\n🎯 第 {i+1} 次检测:")
                print(f"  检测数量: {len(detections)}")
                print(f"  告警数量: {len(alerts)}")
                print(f"  处理时间: {result.get('processing_time', 0):.3f}秒")
                
                for detection in detections:
                    print(f"    - {detection['type']}: {detection['confidence']:.2f}")
                
                for alert in alerts:
                    print(f"    🚨 {alert['severity']}: {alert['message']}")
            
            time.sleep(1)
        
    except Exception as e:
        print(f"❌ API测试失败: {e}")

if __name__ == "__main__":
    print("🧪 开始火焰检测功能测试\n")
    
    # 测试算法逻辑
    test_fire_detection()
    
    # 测试API接口
    test_unified_detection_api()
    
    print("\n✅ 火焰检测功能测试完成!")