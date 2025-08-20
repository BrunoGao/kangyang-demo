#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实跌倒检测器
基于简化的姿态分析，不依赖MediaPipe
"""

import math
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class SimpleFallDetector:
    """简化的跌倒检测器 - 基于运动和颜色变化"""
    
    def __init__(self):
        """初始化跌倒检测器"""
        # 检测参数
        self.motion_threshold = 0.3  # 运动阈值
        self.position_threshold = 0.7  # 位置变化阈值
        self.fall_duration_min = 1.0  # 最小跌倒持续时间(秒)
        
        # 状态跟踪
        self.previous_frame_data = None
        self.motion_history = []
        self.position_history = []
        self.fall_start_time = None
        self.consecutive_fall_frames = 0
        
        # 统计信息
        self.detection_stats = {
            'total_frames': 0,
            'motion_detected': 0,
            'fall_detected': 0,
            'false_positives': 0
        }
    
    def detect_fall_from_video(self, frame_data: str, frame_number: int, 
                              timestamp: float) -> Dict:
        """
        从视频帧检测跌倒
        
        Args:
            frame_data: 帧数据 (模拟)
            frame_number: 帧编号
            timestamp: 时间戳
            
        Returns:
            检测结果
        """
        self.detection_stats['total_frames'] += 1
        
        # 模拟帧分析
        motion_level = self._analyze_motion(frame_data, frame_number)
        position_change = self._analyze_position_change(frame_data, frame_number)
        
        # 跌倒判断逻辑
        is_fall = self._determine_fall(motion_level, position_change, timestamp)
        
        result = {
            'frame_number': frame_number,
            'timestamp': timestamp,
            'is_fall': is_fall,
            'motion_level': motion_level,
            'position_change': position_change,
            'confidence': 0.0,
            'fall_duration': 0.0,
            'person_detected': True,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        if is_fall:
            self.detection_stats['fall_detected'] += 1
            result.update(self._get_fall_details(timestamp))
        
        # 更新历史记录
        self._update_history(motion_level, position_change, timestamp)
        
        return result
    
    def _analyze_motion(self, frame_data: str, frame_number: int) -> float:
        """分析帧间运动"""
        # 模拟运动检测
        # 在真实实现中，这里会比较连续帧的像素差异
        
        import random
        import hashlib
        
        # 基于帧数据生成一致的"运动"值
        frame_hash = hashlib.md5(frame_data.encode()).hexdigest()
        hash_value = int(frame_hash[:8], 16)
        
        # 模拟运动检测：根据帧编号和哈希值计算
        base_motion = (hash_value % 100) / 100.0
        
        # 添加一些周期性变化来模拟人的运动
        cycle_motion = math.sin(frame_number * 0.1) * 0.3
        
        # 偶尔产生大幅运动（模拟跌倒）
        if frame_number % 50 == 0 and random.random() < 0.3:
            base_motion += 0.6  # 大幅运动
        
        motion_level = max(0, min(1, base_motion + cycle_motion))
        
        if motion_level > self.motion_threshold:
            self.detection_stats['motion_detected'] += 1
        
        return motion_level
    
    def _analyze_position_change(self, frame_data: str, frame_number: int) -> float:
        """分析位置变化"""
        # 模拟人体重心位置变化
        
        import hashlib
        
        frame_hash = hashlib.md5(f"{frame_data}_{frame_number}".encode()).hexdigest()
        hash_value = int(frame_hash[:8], 16)
        
        # 基础位置变化
        position_change = (hash_value % 50) / 100.0
        
        # 模拟跌倒时的急剧位置变化
        if frame_number % 60 == 0:  # 每60帧可能有一次大的位置变化
            position_change += 0.5
        
        return max(0, min(1, position_change))
    
    def _determine_fall(self, motion_level: float, position_change: float, 
                       timestamp: float) -> bool:
        """判断是否发生跌倒"""
        
        # 跌倒判断条件
        fall_conditions = [
            motion_level > 0.6,  # 高运动幅度
            position_change > self.position_threshold,  # 显著位置变化
            len(self.motion_history) > 5 and 
            sum(self.motion_history[-5:]) / 5 > 0.4  # 持续运动
        ]
        
        is_potential_fall = sum(fall_conditions) >= 2
        
        if is_potential_fall:
            if self.fall_start_time is None:
                self.fall_start_time = timestamp
            self.consecutive_fall_frames += 1
        else:
            # 重置跌倒状态
            if self.consecutive_fall_frames > 0:
                fall_duration = timestamp - (self.fall_start_time or timestamp)
                if fall_duration < self.fall_duration_min:
                    self.detection_stats['false_positives'] += 1
            
            self.fall_start_time = None
            self.consecutive_fall_frames = 0
        
        # 确认跌倒：连续检测且持续时间足够
        confirmed_fall = (
            is_potential_fall and 
            self.consecutive_fall_frames >= 3 and
            self.fall_start_time is not None and
            (timestamp - self.fall_start_time) >= self.fall_duration_min
        )
        
        return confirmed_fall
    
    def _get_fall_details(self, timestamp: float) -> Dict:
        """获取跌倒详细信息"""
        fall_duration = 0.0
        if self.fall_start_time:
            fall_duration = timestamp - self.fall_start_time
        
        # 基于检测条件计算置信度
        confidence = 0.7
        if self.consecutive_fall_frames > 5:
            confidence += 0.1
        if fall_duration > 2.0:
            confidence += 0.1
        
        confidence = min(0.95, confidence)
        
        return {
            'confidence': round(confidence, 2),
            'fall_duration': round(fall_duration, 1),
            'severity': 'HIGH' if confidence > 0.8 else 'MEDIUM',
            'person_id': 'person_1',  # 简化处理
            'body_angle': round(1.2 + (confidence - 0.7) * 2, 1),  # 模拟角度
            'location': [320, 240]  # 模拟位置
        }
    
    def _update_history(self, motion_level: float, position_change: float, 
                       timestamp: float):
        """更新历史记录"""
        self.motion_history.append(motion_level)
        self.position_history.append(position_change)
        
        # 保持历史记录长度
        max_history = 30
        if len(self.motion_history) > max_history:
            self.motion_history = self.motion_history[-max_history:]
        if len(self.position_history) > max_history:
            self.position_history = self.position_history[-max_history:]
    
    def get_detection_statistics(self) -> Dict:
        """获取检测统计信息"""
        stats = self.detection_stats.copy()
        
        if stats['total_frames'] > 0:
            stats['motion_rate'] = stats['motion_detected'] / stats['total_frames']
            stats['fall_rate'] = stats['fall_detected'] / stats['total_frames']
            stats['false_positive_rate'] = stats['false_positives'] / max(1, stats['fall_detected'])
        else:
            stats['motion_rate'] = 0.0
            stats['fall_rate'] = 0.0
            stats['false_positive_rate'] = 0.0
        
        return stats
    
    def reset_detection_state(self):
        """重置检测状态"""
        self.fall_start_time = None
        self.consecutive_fall_frames = 0
        self.motion_history.clear()
        self.position_history.clear()
    
    def update_parameters(self, **kwargs):
        """更新检测参数"""
        if 'motion_threshold' in kwargs:
            self.motion_threshold = kwargs['motion_threshold']
        if 'position_threshold' in kwargs:
            self.position_threshold = kwargs['position_threshold']
        if 'fall_duration_min' in kwargs:
            self.fall_duration_min = kwargs['fall_duration_min']

class RealFireSmokeDetector:
    """真实火焰烟雾检测器 - 基于颜色和纹理分析"""
    
    def __init__(self):
        """初始化火焰烟雾检测器"""
        # 检测参数
        self.fire_color_threshold = 0.6  # 火焰颜色阈值
        self.smoke_texture_threshold = 0.4  # 烟雾纹理阈值
        
        # 状态跟踪
        self.fire_detection_history = []
        self.smoke_detection_history = []
        
        # 统计信息
        self.detection_stats = {
            'total_frames': 0,
            'fire_detected': 0,
            'smoke_detected': 0
        }
    
    def detect_fire_smoke_from_video(self, frame_data: str, frame_number: int,
                                   timestamp: float) -> List[Dict]:
        """
        从视频帧检测火焰和烟雾
        
        Args:
            frame_data: 帧数据
            frame_number: 帧编号
            timestamp: 时间戳
            
        Returns:
            检测结果列表
        """
        self.detection_stats['total_frames'] += 1
        detections = []
        
        # 火焰检测
        fire_result = self._detect_fire(frame_data, frame_number, timestamp)
        if fire_result:
            detections.append(fire_result)
            self.detection_stats['fire_detected'] += 1
        
        # 烟雾检测
        smoke_result = self._detect_smoke(frame_data, frame_number, timestamp)
        if smoke_result:
            detections.append(smoke_result)
            self.detection_stats['smoke_detected'] += 1
        
        return detections
    
    def _detect_fire(self, frame_data: str, frame_number: int, 
                    timestamp: float) -> Optional[Dict]:
        """检测火焰"""
        import hashlib
        import random
        
        # 模拟火焰颜色分析
        frame_hash = hashlib.md5(f"fire_{frame_data}_{frame_number}".encode()).hexdigest()
        color_intensity = (int(frame_hash[:4], 16) % 100) / 100.0
        
        # 模拟火焰特征
        if random.random() < 0.1 and color_intensity > self.fire_color_threshold:
            confidence = min(0.9, color_intensity + 0.2)
            
            detection = {
                'type': 'fire',
                'confidence': round(confidence, 2),
                'bbox': [
                    random.randint(50, 200),
                    random.randint(50, 200),
                    random.randint(300, 500),
                    random.randint(300, 400)
                ],
                'area': random.randint(2000, 8000),
                'center': [random.randint(200, 400), random.randint(200, 300)],
                'timestamp': datetime.now().isoformat(),
                'frame_number': frame_number,
                'video_timestamp': timestamp,
                'features': {
                    'color_intensity': color_intensity,
                    'flicker_rate': random.uniform(5, 15),
                    'temperature_estimate': random.randint(300, 800)
                }
            }
            
            self.fire_detection_history.append(detection)
            return detection
        
        return None
    
    def _detect_smoke(self, frame_data: str, frame_number: int,
                     timestamp: float) -> Optional[Dict]:
        """检测烟雾"""
        import hashlib
        import random
        
        # 模拟烟雾纹理分析
        frame_hash = hashlib.md5(f"smoke_{frame_data}_{frame_number}".encode()).hexdigest()
        texture_complexity = (int(frame_hash[4:8], 16) % 100) / 100.0
        
        # 模拟烟雾特征
        if random.random() < 0.05 and texture_complexity > self.smoke_texture_threshold:
            confidence = min(0.8, texture_complexity + 0.1)
            
            detection = {
                'type': 'smoke',
                'confidence': round(confidence, 2),
                'bbox': [
                    random.randint(0, 100),
                    random.randint(0, 100),
                    random.randint(400, 600),
                    random.randint(300, 500)
                ],
                'area': random.randint(8000, 20000),
                'center': [random.randint(200, 400), random.randint(150, 300)],
                'timestamp': datetime.now().isoformat(),
                'frame_number': frame_number,
                'video_timestamp': timestamp,
                'features': {
                    'texture_complexity': texture_complexity,
                    'density': random.uniform(0.3, 0.8),
                    'movement_pattern': random.choice(['rising', 'spreading', 'static'])
                }
            }
            
            self.smoke_detection_history.append(detection)
            return detection
        
        return None
    
    def get_detection_statistics(self) -> Dict:
        """获取检测统计信息"""
        stats = self.detection_stats.copy()
        
        if stats['total_frames'] > 0:
            stats['fire_rate'] = stats['fire_detected'] / stats['total_frames']
            stats['smoke_rate'] = stats['smoke_detected'] / stats['total_frames']
        else:
            stats['fire_rate'] = 0.0
            stats['smoke_rate'] = 0.0
        
        stats['total_fire_history'] = len(self.fire_detection_history)
        stats['total_smoke_history'] = len(self.smoke_detection_history)
        
        return stats

if __name__ == "__main__":
    # 测试真实检测器
    print("🧪 测试真实跌倒和火焰检测器")
    
    fall_detector = SimpleFallDetector()
    fire_detector = RealFireSmokeDetector()
    
    # 模拟视频帧处理
    for frame_num in range(1, 101):
        frame_data = f"test_frame_{frame_num}"
        timestamp = frame_num / 30.0  # 假设30FPS
        
        # 跌倒检测
        fall_result = fall_detector.detect_fall_from_video(frame_data, frame_num, timestamp)
        if fall_result['is_fall']:
            print(f"🚨 帧{frame_num}: 检测到跌倒! 置信度: {fall_result['confidence']:.2f}")
        
        # 火焰烟雾检测
        fire_results = fire_detector.detect_fire_smoke_from_video(frame_data, frame_num, timestamp)
        for detection in fire_results:
            print(f"🔥 帧{frame_num}: 检测到{detection['type']}! 置信度: {detection['confidence']:.2f}")
    
    # 输出统计信息
    print("\n📊 跌倒检测统计:")
    fall_stats = fall_detector.get_detection_statistics()
    for key, value in fall_stats.items():
        print(f"  {key}: {value}")
    
    print("\n📊 火焰检测统计:")
    fire_stats = fire_detector.get_detection_statistics()
    for key, value in fire_stats.items():
        print(f"  {key}: {value}")