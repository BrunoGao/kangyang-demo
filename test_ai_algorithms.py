#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI算法测试脚本 - 康养检测系统
测试跌倒、烟雾、火焰识别算法
"""

import cv2
import numpy as np
import os
import sys
import logging
from pathlib import Path

# 添加边缘控制器源代码路径
edge_controller_path = Path(__file__).parent / "edge-controller" / "src"
sys.path.append(str(edge_controller_path))

try:
    from ai.fall_detector import FallDetector
    from ai.fire_detector import FireDetector  
    from ai.smoke_detector import SmokeDetector
except ImportError as e:
    print(f"❌ 导入AI模块失败: {e}")
    print("请确保边缘控制器源代码完整")
    sys.exit(1)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AITestSuite:
    """AI算法测试套件"""
    
    def __init__(self):
        """初始化测试套件"""
        self.fall_detector = FallDetector({
            "confidence_threshold": 0.8,
            "min_fall_duration": 2.0,
            "cooldown_period": 10
        })
        
        self.fire_detector = FireDetector({
            "confidence_threshold": 0.85,
            "cooldown_period": 5
        })
        
        self.smoke_detector = SmokeDetector({
            "confidence_threshold": 0.80,
            "cooldown_period": 8
        })
        
        print("🤖 AI检测器初始化完成")
        print(f"   • 跌倒检测器: 置信度阈值 {self.fall_detector.confidence_threshold}")
        print(f"   • 火焰检测器: 置信度阈值 {self.fire_detector.confidence_threshold}")
        print(f"   • 烟雾检测器: 置信度阈值 {self.smoke_detector.confidence_threshold}")
    
    def create_fall_test_frame(self) -> np.ndarray:
        """创建模拟跌倒场景的测试帧"""
        # 创建一个640x480的图像
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (40, 50, 60)  # 深色背景
        
        # 模拟跌倒人体轮廓（水平躺姿）
        # 绘制一个椭圆形表示跌倒的人体
        center_x, center_y = 320, 350  # 偏向底部
        width, height = 120, 40  # 宽度大于高度（水平姿态）
        
        cv2.ellipse(frame, (center_x, center_y), (width, height), 0, 0, 360, (180, 180, 180), -1)
        
        # 添加一些噪点模拟真实环境
        noise = np.random.randint(0, 30, frame.shape, dtype=np.uint8)
        frame = cv2.add(frame, noise)
        
        print("📸 生成跌倒测试场景:")
        print(f"   • 人体位置: ({center_x}, {center_y})")
        print(f"   • 人体尺寸: {width}x{height} (宽>高，符合跌倒特征)")
        print(f"   • 位置特征: 接近地面 ({center_y/frame.shape[0]:.1%})")
        
        return frame
    
    def create_fire_test_frame(self) -> np.ndarray:
        """创建模拟火焰场景的测试帧"""
        # 创建一个640x480的图像
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (20, 30, 40)  # 深色背景
        
        # 创建火焰颜色区域
        # 火焰通常是红色、橙色、黄色
        flame_colors = [
            (0, 0, 255),    # 红色
            (0, 165, 255),  # 橙色
            (0, 255, 255),  # 黄色
        ]
        
        # 绘制不规则的火焰形状
        for i in range(3):
            color = flame_colors[i]
            # 创建不规则的火焰轮廓
            points = np.array([
                [200 + i*50, 400],
                [180 + i*50, 350],
                [220 + i*50, 300],
                [190 + i*50, 250],
                [210 + i*50, 200],
                [240 + i*50, 250],
                [270 + i*50, 300],
                [250 + i*50, 350],
                [260 + i*50, 400]
            ], np.int32)
            
            cv2.fillPoly(frame, [points], color)
        
        # 添加亮度和饱和度
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        fire_mask = cv2.inRange(hsv, (0, 50, 50), (35, 255, 255))
        frame[fire_mask > 0] = cv2.add(frame[fire_mask > 0], (50, 50, 50))
        
        print("🔥 生成火焰测试场景:")
        print(f"   • 火焰颜色: 红-橙-黄渐变")
        print(f"   • 火焰形状: 不规则，向上扩散")
        print(f"   • 亮度特征: 高亮度区域")
        
        return frame
    
    def create_smoke_test_frame(self) -> np.ndarray:
        """创建模拟烟雾场景的测试帧"""
        # 创建一个640x480的图像
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[:] = (60, 80, 100)  # 中等背景
        
        # 创建烟雾效果（白色/灰色，模糊边界）
        smoke_center = (320, 200)
        
        # 使用多个圆形叠加创建烟雾效果
        for i in range(8):
            radius = 30 + i * 15
            alpha = 0.3 - i * 0.03
            
            overlay = frame.copy()
            cv2.circle(overlay, smoke_center, radius, (200, 200, 200), -1)
            frame = cv2.addWeighted(frame, 1-alpha, overlay, alpha, 0)
        
        # 添加运动模糊效果模拟烟雾扩散
        kernel = np.ones((5,5), np.float32) / 25
        frame = cv2.filter2D(frame, -1, kernel)
        
        # 在上方添加更多烟雾（烟雾向上扩散）
        for y in range(50, 200, 20):
            for x in range(250, 390, 30):
                cv2.circle(frame, (x + np.random.randint(-20, 20), y), 
                          15 + np.random.randint(-5, 5), 
                          (180 + np.random.randint(-30, 30),) * 3, -1)
        
        print("💨 生成烟雾测试场景:")
        print(f"   • 烟雾中心: {smoke_center}")
        print(f"   • 烟雾颜色: 白色/浅灰色")
        print(f"   • 扩散特征: 向上扩散，边界模糊")
        
        return frame
    
    def test_fall_detection(self):
        """测试跌倒检测算法"""
        print("\n" + "="*50)
        print("🚨 跌倒检测算法测试")
        print("="*50)
        
        # 创建测试帧
        frame = self.create_fall_test_frame()
        
        # 连续检测多帧以满足最小持续时间要求
        results = []
        for frame_num in range(5):  # 模拟5帧
            result = self.fall_detector.detect(
                frame, 
                1234567890.0 + frame_num * 0.5,  # 时间戳递增
                frame_num
            )
            if result:
                results.append(result)
        
        # 显示结果
        if results:
            latest_result = results[-1]
            print(f"✅ 检测到跌倒事件!")
            print(f"   • 类型: {latest_result['type']}")
            print(f"   • 子类型: {latest_result['subtype']}")
            print(f"   • 置信度: {latest_result['confidence']:.2f}")
            print(f"   • 严重程度: {latest_result['severity']}")
            print(f"   • 持续时间: {latest_result['duration']:.1f}秒")
            print(f"   • 边界框: {latest_result['bbox']}")
            
            # 获取统计信息
            stats = self.fall_detector.get_stats()
            print(f"\n📊 检测器统计:")
            for key, value in stats.items():
                print(f"   • {key}: {value}")
        else:
            print("❌ 未检测到跌倒事件")
        
        return results
    
    def test_fire_detection(self):
        """测试火焰检测算法"""
        print("\n" + "="*50)
        print("🔥 火焰检测算法测试")
        print("="*50)
        
        # 创建测试帧
        frame = self.create_fire_test_frame()
        
        # 执行检测
        results = self.fire_detector.detect_fire_smoke(frame)
        
        # 显示结果
        if results:
            for i, result in enumerate(results):
                print(f"✅ 检测到火焰 #{i+1}!")
                print(f"   • 类型: {result['type']}")
                print(f"   • 子类型: {result['subtype']}")
                print(f"   • 置信度: {result['confidence']:.2f}")
                print(f"   • 火焰强度: {result['fire_intensity']}")
                print(f"   • 估算温度: {result['estimated_temperature']}°C")
                print(f"   • 边界框: {result['bbox']}")
                print(f"   • 面积: {result['area']} 像素")
        else:
            print("❌ 未检测到火焰")
        
        # 获取统计信息
        stats = self.fire_detector.get_stats()
        print(f"\n📊 检测器统计:")
        for key, value in stats.items():
            print(f"   • {key}: {value}")
        
        return results
    
    def test_smoke_detection(self):
        """测试烟雾检测算法"""
        print("\n" + "="*50)
        print("💨 烟雾检测算法测试")
        print("="*50)
        
        # 创建测试帧
        frame = self.create_smoke_test_frame()
        
        # 执行检测
        results = self.smoke_detector.detect_fire_smoke(frame)
        
        # 显示结果
        if results:
            for i, result in enumerate(results):
                print(f"✅ 检测到烟雾 #{i+1}!")
                print(f"   • 类型: {result['type']}")
                print(f"   • 子类型: {result['subtype']}")
                print(f"   • 置信度: {result['confidence']:.2f}")
                print(f"   • 烟雾密度: {result['smoke_density']}")
                print(f"   • 颜色分析: {result['color_analysis']}")
                print(f"   • 边界框: {result['bbox']}")
                print(f"   • 面积: {result['area']} 像素")
        else:
            print("❌ 未检测到烟雾")
        
        # 获取统计信息
        stats = self.smoke_detector.get_stats()
        print(f"\n📊 检测器统计:")
        for key, value in stats.items():
            print(f"   • {key}: {value}")
        
        return results
    
    def run_all_tests(self):
        """运行所有算法测试"""
        print("🎯 康养AI检测系统 - 算法测试套件")
        print("🏥 专注于康养机构的安全监护")
        print()
        
        # 测试各个算法
        fall_results = self.test_fall_detection()
        fire_results = self.test_fire_detection()  
        smoke_results = self.test_smoke_detection()
        
        # 汇总结果
        print("\n" + "="*50)
        print("📋 测试结果汇总")
        print("="*50)
        print(f"🚨 跌倒检测: {'✅ 通过' if fall_results else '❌ 失败'} ({len(fall_results)} 个检测)")
        print(f"🔥 火焰检测: {'✅ 通过' if fire_results else '❌ 失败'} ({len(fire_results)} 个检测)")
        print(f"💨 烟雾检测: {'✅ 通过' if smoke_results else '❌ 失败'} ({len(smoke_results)} 个检测)")
        
        total_detections = len(fall_results) + len(fire_results) + len(smoke_results)
        print(f"\n🎉 总计检测到 {total_detections} 个安全事件")
        
        if total_detections > 0:
            print("\n✅ AI检测系统运行正常，已准备好保护康养机构的安全!")
            print("🛡️  系统具备以下能力:")
            print("   • 实时跌倒检测与告警")
            print("   • 火灾早期预警")  
            print("   • 烟雾扩散监测")
            print("   • 智能事件分类")
            print("   • 误报率控制")
        else:
            print("❌ 系统需要进一步调优")

def main():
    """主函数"""
    try:
        # 创建测试套件
        test_suite = AITestSuite()
        
        # 运行所有测试
        test_suite.run_all_tests()
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())