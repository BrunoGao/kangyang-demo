#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基于OpenCV的跌倒检测器
使用计算机视觉技术进行运动检测和形状分析
"""

import cv2
import numpy as np
import math
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any

class OpenCVFallDetector:
    """基于OpenCV的跌倒检测器"""
    
    def __init__(self):
        """初始化检测器"""
        # 检测参数
        self.motion_threshold = 30000  # 运动区域阈值
        self.aspect_ratio_threshold = 2.5  # 宽高比阈值（躺倒时宽>高）
        self.area_threshold = 5000  # 最小检测区域
        self.fall_duration_min = 1.0   # 最小跌倒持续时间(秒)
        
        # 背景减法器
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True, varThreshold=50, history=100
        )
        
        # 形态学操作核
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        
        # 状态跟踪
        self.previous_contours = []
        self.fall_start_time = None
        self.consecutive_fall_frames = 0
        self.person_positions = []
        
        # 统计信息
        self.detection_stats = {
            'total_frames': 0,
            'person_detected': 0,
            'fall_detected': 0,
            'false_positives': 0,
            'processing_times': []
        }
    
    def detect_fall_from_frame(self, frame: np.ndarray, timestamp: float, 
                              frame_number: int = 0) -> Dict[str, Any]:
        """
        从视频帧检测跌倒
        
        Args:
            frame: 输入视频帧
            timestamp: 时间戳
            frame_number: 帧编号
            
        Returns:
            检测结果字典
        """
        start_time = time.time()
        self.detection_stats['total_frames'] += 1
        
        detection_result = {
            'frame_number': frame_number,
            'timestamp': timestamp,
            'person_detected': False,
            'is_fall': False,
            'confidence': 0.0,
            'aspect_ratio': 0.0,
            'motion_area': 0.0,
            'fall_duration': 0.0,
            'bbox': None,
            'analysis_timestamp': datetime.now().isoformat(),
            'processing_time': 0.0
        }
        
        # 运动检测
        motion_mask = self.bg_subtractor.apply(frame)
        
        # 形态学操作去噪
        motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_OPEN, self.kernel)
        motion_mask = cv2.morphologyEx(motion_mask, cv2.MORPH_CLOSE, self.kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(motion_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # 过滤小轮廓
        significant_contours = [c for c in contours if cv2.contourArea(c) > self.area_threshold]
        
        if significant_contours:
            self.detection_stats['person_detected'] += 1
            detection_result['person_detected'] = True
            
            # 找到最大轮廓（假设是人体）
            largest_contour = max(significant_contours, key=cv2.contourArea)
            
            # 计算轮廓属性
            area = cv2.contourArea(largest_contour)
            detection_result['motion_area'] = area
            
            # 计算边界框和宽高比
            x, y, w, h = cv2.boundingRect(largest_contour)
            detection_result['bbox'] = [x, y, x + w, y + h]
            
            aspect_ratio = w / h if h > 0 else 0
            detection_result['aspect_ratio'] = aspect_ratio
            
            # 跌倒判断
            is_fall, confidence, fall_details = self._determine_fall(
                aspect_ratio, area, timestamp, (x, y, w, h)
            )
            
            detection_result.update({
                'is_fall': is_fall,
                'confidence': confidence,
                **fall_details
            })
            
            if is_fall:
                self.detection_stats['fall_detected'] += 1
            
            # 更新历史记录
            self._update_history((x + w//2, y + h//2), timestamp)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        detection_result['processing_time'] = round(processing_time, 4)
        self.detection_stats['processing_times'].append(processing_time)
        
        return detection_result
    
    def _determine_fall(self, aspect_ratio: float, area: float, timestamp: float,
                       bbox: Tuple[int, int, int, int]) -> Tuple[bool, float, Dict]:
        """判断是否发生跌倒"""
        fall_details = {
            'fall_duration': 0.0,
            'severity': 'NONE',
            'fall_direction': 'unknown',
            'body_position': 'upright'
        }
        
        # 跌倒判断条件
        horizontal_body = aspect_ratio > self.aspect_ratio_threshold  # 身体水平
        significant_motion = area > self.motion_threshold  # 显著运动
        
        # 位置变化检测
        position_change = self._analyze_position_change(bbox, timestamp)
        
        # 综合判断
        fall_conditions = [
            horizontal_body,
            significant_motion,
            position_change > 50,  # 位置显著变化
            len(self.person_positions) > 3  # 需要一定的历史数据
        ]
        
        is_potential_fall = sum(fall_conditions) >= 2
        
        if is_potential_fall:
            if self.fall_start_time is None:
                self.fall_start_time = timestamp
            self.consecutive_fall_frames += 1
            
            # 更新跌倒详细信息
            fall_duration = timestamp - (self.fall_start_time or timestamp)
            fall_details.update({
                'fall_duration': round(fall_duration, 2),
                'severity': 'HIGH' if aspect_ratio > 3.0 else 'MEDIUM',
                'fall_direction': self._determine_fall_direction(bbox),
                'body_position': 'falling' if fall_duration < 2.0 else 'down'
            })
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
            self.consecutive_fall_frames >= 5 and
            self.fall_start_time is not None and
            (timestamp - self.fall_start_time) >= self.fall_duration_min
        )
        
        # 计算置信度
        confidence = 0.0
        if confirmed_fall:
            confidence = 0.6  # 基础置信度
            if aspect_ratio > 3.0:
                confidence += 0.2
            if area > self.motion_threshold * 2:
                confidence += 0.1
            if self.consecutive_fall_frames > 10:
                confidence += 0.1
            confidence = min(0.95, confidence)
        
        return confirmed_fall, confidence, fall_details
    
    def _analyze_position_change(self, bbox: Tuple[int, int, int, int], 
                               timestamp: float) -> float:
        """分析位置变化"""
        x, y, w, h = bbox
        center_x, center_y = x + w//2, y + h//2
        
        if not self.person_positions:
            return 0.0
        
        # 计算与最近位置的距离
        last_pos = self.person_positions[-1]
        distance = math.sqrt((center_x - last_pos['x'])**2 + (center_y - last_pos['y'])**2)
        
        return distance
    
    def _determine_fall_direction(self, bbox: Tuple[int, int, int, int]) -> str:
        """确定跌倒方向"""
        x, y, w, h = bbox
        center_x = x + w//2
        
        if len(self.person_positions) >= 2:
            prev_center_x = self.person_positions[-1]['x']
            if center_x > prev_center_x + 20:
                return 'right'
            elif center_x < prev_center_x - 20:
                return 'left'
        
        return 'forward'
    
    def _update_history(self, position: Tuple[int, int], timestamp: float):
        """更新历史记录"""
        center_x, center_y = position
        
        # 添加到历史记录
        self.person_positions.append({
            'timestamp': timestamp,
            'x': center_x,
            'y': center_y
        })
        
        # 保持历史记录长度
        max_history = 30
        if len(self.person_positions) > max_history:
            self.person_positions = self.person_positions[-max_history:]
    
    def get_detection_statistics(self) -> Dict:
        """获取检测统计信息"""
        stats = self.detection_stats.copy()
        
        if stats['total_frames'] > 0:
            stats['person_detection_rate'] = stats['person_detected'] / stats['total_frames']
            stats['fall_detection_rate'] = stats['fall_detected'] / stats['total_frames']
            stats['false_positive_rate'] = stats['false_positives'] / max(1, stats['fall_detected'])
        else:
            stats['person_detection_rate'] = 0.0
            stats['fall_detection_rate'] = 0.0
            stats['false_positive_rate'] = 0.0
        
        if stats['processing_times']:
            stats['avg_processing_time'] = sum(stats['processing_times']) / len(stats['processing_times'])
            stats['max_processing_time'] = max(stats['processing_times'])
            stats['min_processing_time'] = min(stats['processing_times'])
        else:
            stats['avg_processing_time'] = 0.0
            stats['max_processing_time'] = 0.0
            stats['min_processing_time'] = 0.0
        
        return stats
    
    def reset_detection_state(self):
        """重置检测状态"""
        self.fall_start_time = None
        self.consecutive_fall_frames = 0
        self.person_positions.clear()
        self.previous_contours.clear()
        
        # 重置背景减法器
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True, varThreshold=50, history=100
        )
    
    def update_parameters(self, **kwargs):
        """更新检测参数"""
        if 'motion_threshold' in kwargs:
            self.motion_threshold = kwargs['motion_threshold']
        if 'aspect_ratio_threshold' in kwargs:
            self.aspect_ratio_threshold = kwargs['aspect_ratio_threshold']
        if 'area_threshold' in kwargs:
            self.area_threshold = kwargs['area_threshold']
        if 'fall_duration_min' in kwargs:
            self.fall_duration_min = kwargs['fall_duration_min']
    
    def draw_detection_on_frame(self, frame: np.ndarray, detection_result: Dict) -> np.ndarray:
        """在帧上绘制检测结果"""
        annotated_frame = frame.copy()
        
        # 绘制边界框
        if detection_result.get('bbox'):
            bbox = detection_result['bbox']
            color = (0, 0, 255) if detection_result['is_fall'] else (0, 255, 0)
            cv2.rectangle(annotated_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            
            # 添加标签
            label = f"Fall: {detection_result['is_fall']}"
            if detection_result['is_fall']:
                label += f" ({detection_result['confidence']:.2f})"
            
            cv2.putText(annotated_frame, label, (bbox[0], bbox[1] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return annotated_frame

class OpenCVVideoProcessor:
    """基于OpenCV的视频处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.detector = OpenCVFallDetector()
        self.processing_stats = {
            'total_videos': 0,
            'total_frames': 0,
            'total_falls': 0,
            'processing_time': 0.0
        }
    
    def process_video(self, video_path: str, output_path: str = None, 
                     detection_interval: int = 1) -> Dict:
        """
        处理视频进行跌倒检测
        
        Args:
            video_path: 输入视频路径
            output_path: 输出视频路径（可选）
            detection_interval: 检测间隔（帧）
            
        Returns:
            检测结果
        """
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")
        
        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        
        # 准备输出视频（如果需要）
        out = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        fall_events = []
        frame_results = []
        frame_count = 0
        start_time = time.time()
        
        print(f"开始处理视频: {video_path}")
        print(f"总帧数: {total_frames}, FPS: {fps}")
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                timestamp = frame_count / fps
                
                # 按间隔进行检测
                if frame_count % detection_interval == 0:
                    result = self.detector.detect_fall_from_frame(frame, timestamp, frame_count)
                    frame_results.append(result)
                    
                    # 记录跌倒事件
                    if result['is_fall']:
                        # 检查是否是新的跌倒事件
                        is_new_event = True
                        if fall_events:
                            last_event = fall_events[-1]
                            time_diff = timestamp - last_event['timestamp']
                            if time_diff < 5.0:  # 5秒内认为是同一事件
                                is_new_event = False
                                # 更新现有事件
                                last_event['end_timestamp'] = timestamp
                                last_event['end_frame'] = frame_count
                                last_event['confidence'] = max(last_event['confidence'], result['confidence'])
                        
                        if is_new_event:
                            fall_event = {
                                'id': f'fall_{len(fall_events) + 1}',
                                'start_frame': frame_count,
                                'end_frame': frame_count,
                                'timestamp': timestamp,
                                'end_timestamp': timestamp,
                                'confidence': result['confidence'],
                                'aspect_ratio': result['aspect_ratio'],
                                'bbox': result['bbox'],
                                'severity': result.get('severity', 'UNKNOWN'),
                                'fall_direction': result.get('fall_direction', 'unknown')
                            }
                            fall_events.append(fall_event)
                            print(f"检测到跌倒事件 #{len(fall_events)} 在帧 {frame_count} (时间: {timestamp:.2f}s)")
                    
                    # 绘制检测结果（如果需要输出视频）
                    if out:
                        annotated_frame = self.detector.draw_detection_on_frame(frame, result)
                        out.write(annotated_frame)
                elif out:
                    out.write(frame)
                
                frame_count += 1
                
                # 显示进度
                if frame_count % 100 == 0:
                    progress = (frame_count / total_frames) * 100
                    print(f"处理进度: {progress:.1f}% ({frame_count}/{total_frames})")
        
        finally:
            cap.release()
            if out:
                out.release()
        
        processing_time = time.time() - start_time
        
        # 更新统计信息
        self.processing_stats['total_videos'] += 1
        self.processing_stats['total_frames'] += frame_count
        self.processing_stats['total_falls'] += len(fall_events)
        self.processing_stats['processing_time'] += processing_time
        
        print(f"视频处理完成!")
        print(f"处理时间: {processing_time:.2f}秒")
        print(f"检测到 {len(fall_events)} 个跌倒事件")
        
        return {
            'video_info': {
                'path': video_path,
                'total_frames': total_frames,
                'fps': fps,
                'duration': total_frames / fps,
                'resolution': f'{width}x{height}'
            },
            'processing_info': {
                'processing_time': round(processing_time, 2),
                'processed_frames': frame_count,
                'detection_interval': detection_interval,
                'avg_fps': round(frame_count / processing_time, 2)
            },
            'detection_results': {
                'total_fall_events': len(fall_events),
                'fall_events': fall_events,
                'frame_results': frame_results
            },
            'statistics': self.detector.get_detection_statistics()
        }
    
    def cleanup(self):
        """清理资源"""
        pass

if __name__ == "__main__":
    # 测试OpenCV跌倒检测器
    print("🧪 测试OpenCV跌倒检测器")
    
    # 创建测试图像
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    detector = OpenCVFallDetector()
    
    # 测试检测
    result = detector.detect_fall_from_frame(test_frame, 0.0, 0)
    print(f"测试结果: {result}")
    
    # 输出统计信息
    stats = detector.get_detection_statistics()
    print(f"检测统计: {stats}")
    
    print("✅ 测试完成")