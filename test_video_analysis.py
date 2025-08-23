#!/usr/bin/env python3
"""
测试视频分析功能
演示康养AI检测系统的视频分析能力
"""

import cv2
import numpy as np
import json
from datetime import datetime
import os
import sys

def analyze_falldown_video():
    """分析falldown.mp4视频文件"""
    
    video_path = "/Users/brunogao/work/codes/kangyang/kangyang-demo/mp4/falldown.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ 视频文件不存在: {video_path}")
        return
    
    print(f"🎬 开始分析视频: {os.path.basename(video_path)}")
    
    # 打开视频文件
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("❌ 无法打开视频文件")
        return
    
    # 获取视频信息
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps if fps > 0 else 0
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📊 视频信息:")
    print(f"   - 时长: {duration:.2f} 秒")
    print(f"   - 帧率: {fps:.2f} FPS")
    print(f"   - 总帧数: {frame_count}")
    print(f"   - 分辨率: {width}x{height}")
    print(f"   - 文件大小: {os.path.getsize(video_path) / (1024*1024):.1f} MB")
    
    # 模拟AI检测过程
    print(f"\n🔍 开始AI检测分析...")
    
    detection_results = []
    frame_idx = 0
    processed_frames = 0
    
    # 每秒处理2帧以提高速度
    frame_skip = max(1, int(fps / 2)) if fps > 0 else 1
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # 跳帧处理
        if frame_idx % frame_skip != 0:
            frame_idx += 1
            continue
        
        timestamp = frame_idx / fps if fps > 0 else frame_idx
        
        # 模拟跌倒检测算法
        if simulate_fall_detection(frame, frame_idx):
            detection = {
                "algorithm": "fall_detection",
                "type": "fall",
                "confidence": 0.85 + np.random.random() * 0.15,  # 85-100% 置信度
                "timestamp": timestamp,
                "frame_index": frame_idx,
                "location": f"区域 A",
                "bbox": [0.3 + np.random.random() * 0.2, 
                        0.2 + np.random.random() * 0.2, 
                        0.6 + np.random.random() * 0.2,
                        0.5 + np.random.random() * 0.2],
                "severity": "high" if timestamp > 10 else "medium"
            }
            detection_results.append(detection)
            print(f"   ⚠️  检测到跌倒事件 @ {timestamp:.1f}s (置信度: {detection['confidence']:.3f})")
        
        processed_frames += 1
        frame_idx += 1
        
        # 限制处理帧数，避免过长时间
        if processed_frames >= 150:  # 最多处理150帧
            print(f"   ⏸️  达到处理帧数限制，停止分析")
            break
        
        # 显示进度
        if processed_frames % 30 == 0:
            progress = (processed_frames / 150) * 100
            print(f"   📈 分析进度: {progress:.1f}% ({processed_frames}/150 帧)")
    
    cap.release()
    
    # 生成分析报告
    report = generate_analysis_report(
        video_path, fps, frame_count, duration, width, height,
        processed_frames, frame_skip, detection_results
    )
    
    # 输出结果
    print(f"\n📋 分析报告:")
    print(f"   - 总检测事件: {len(detection_results)}")
    print(f"   - 处理帧数: {processed_frames}")
    print(f"   - 检测率: {len(detection_results) / processed_frames * 100:.1f}%")
    
    if detection_results:
        avg_confidence = sum(d['confidence'] for d in detection_results) / len(detection_results)
        max_confidence = max(d['confidence'] for d in detection_results)
        print(f"   - 平均置信度: {avg_confidence:.3f}")
        print(f"   - 最高置信度: {max_confidence:.3f}")
        
        print(f"\n🚨 检测事件详情:")
        for i, detection in enumerate(detection_results, 1):
            print(f"   {i}. {detection['timestamp']:.1f}s - {detection['type']} "
                  f"(置信度: {detection['confidence']:.3f}, 严重度: {detection['severity']})")
    
    # 保存报告文件
    report_file = "/Users/brunogao/work/codes/kangyang/kangyang-demo/falldown_analysis_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 分析完成! 报告已保存至: {report_file}")
    return report

def simulate_fall_detection(frame, frame_idx):
    """模拟跌倒检测算法"""
    # 简单的基于帧特征的模拟检测
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 计算图像的梯度和纹理特征
    grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    magnitude = np.sqrt(grad_x**2 + grad_y**2)
    
    # 根据帧索引和图像特征模拟检测结果
    # 在特定时间段内增加检测概率，模拟真实的跌倒场景
    base_prob = 0.02  # 基础检测概率 2%
    
    # 模拟在10-15秒和25-30秒时间段内有较高的跌倒概率
    time_factor = frame_idx / 30.0  # 假设30fps
    if 10 <= time_factor <= 15 or 25 <= time_factor <= 30:
        base_prob = 0.15  # 15% 概率
    
    # 结合图像特征
    texture_factor = np.mean(magnitude) / 255.0
    detection_prob = base_prob + texture_factor * 0.05
    
    return np.random.random() < detection_prob

def generate_analysis_report(video_path, fps, frame_count, duration, width, height,
                           processed_frames, frame_skip, detection_results):
    """生成详细的分析报告"""
    
    # 按算法分类统计
    algorithm_stats = {
        "fall_detection": {
            "total_detections": len([d for d in detection_results if d['algorithm'] == 'fall_detection']),
            "avg_confidence": sum(d['confidence'] for d in detection_results if d['algorithm'] == 'fall_detection') / len(detection_results) if detection_results else 0,
            "max_confidence": max(d['confidence'] for d in detection_results if d['algorithm'] == 'fall_detection') if detection_results else 0,
            "detection_frames": [d['frame_index'] for d in detection_results if d['algorithm'] == 'fall_detection']
        }
    }
    
    # 生成帧结果映射
    frame_results = {}
    for detection in detection_results:
        frame_key = str(detection['frame_index'])
        if frame_key not in frame_results:
            frame_results[frame_key] = []
        frame_results[frame_key].append(detection)
    
    report = {
        "video_info": {
            "filename": os.path.basename(video_path),
            "duration": duration,
            "fps": fps,
            "total_frames": frame_count,
            "resolution": f"{width}x{height}",
            "processed_frames": processed_frames,
            "frame_skip": frame_skip,
            "file_size_mb": os.path.getsize(video_path) / (1024*1024)
        },
        "algorithms_used": ["fall_detection"],
        "detection_summary": {
            "total_detections": len(detection_results),
            "frames_with_detections": len(frame_results),
            "detection_rate": len(frame_results) / processed_frames if processed_frames > 0 else 0,
            "analysis_coverage": processed_frames / frame_count if frame_count > 0 else 0
        },
        "detailed_results": detection_results,
        "algorithm_statistics": algorithm_stats,
        "frame_results": frame_results,
        "processing_info": {
            "processing_time": datetime.now().isoformat(),
            "system": "康养AI检测系统",
            "version": "1.0.0",
            "mode": "demo_analysis"
        },
        "performance_metrics": {
            "frames_per_second_processed": processed_frames / (duration / frame_skip) if duration > 0 else 0,
            "detection_density": len(detection_results) / duration if duration > 0 else 0,
            "confidence_distribution": {
                "high_confidence": len([d for d in detection_results if d['confidence'] > 0.9]),
                "medium_confidence": len([d for d in detection_results if 0.7 <= d['confidence'] <= 0.9]),
                "low_confidence": len([d for d in detection_results if d['confidence'] < 0.7])
            }
        }
    }
    
    return report

if __name__ == "__main__":
    print("🏥 康养AI检测系统 - 视频分析演示")
    print("=" * 50)
    
    try:
        report = analyze_falldown_video()
        
        if report:
            print(f"\n🎉 演示完成!")
            print(f"系统成功分析了falldown.mp4视频文件")
            print(f"模拟了真实的AI检测算法处理流程")
            print(f"生成了完整的检测报告和统计信息")
            
    except Exception as e:
        print(f"❌ 分析过程中发生错误: {e}")
        import traceback
        traceback.print_exc()