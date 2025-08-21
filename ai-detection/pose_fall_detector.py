#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实跌倒检测器 - 基于MediaPipe姿态检测
实现YOLO + PoseNet的跌倒检测算法
"""

import cv2
import mediapipe as mp
import numpy as np
import math
import time
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any

class MediaPipeFallDetector:
    """基于MediaPipe的真实跌倒检测器"""
    
    def __init__(self):
        """初始化检测器"""
        # 初始化MediaPipe姿态检测
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            smooth_landmarks=True,
            enable_segmentation=False,
            smooth_segmentation=True,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
        # 检测参数
        self.fall_angle_threshold = 60  # 身体角度阈值（度）
        self.movement_threshold = 0.15  # 运动幅度阈值
        self.fall_duration_min = 0.5   # 最小跌倒持续时间(秒)
        self.confidence_threshold = 0.7  # 置信度阈值
        
        # 关键点索引 (MediaPipe Pose)
        self.key_points = {
            'nose': 0,
            'left_shoulder': 11,
            'right_shoulder': 12,
            'left_hip': 23,
            'right_hip': 24,
            'left_knee': 25,
            'right_knee': 26,
            'left_ankle': 27,
            'right_ankle': 28
        }
        
        # 状态跟踪
        self.previous_landmarks = None
        self.previous_body_angle = None
        self.fall_start_time = None
        self.consecutive_fall_frames = 0
        self.person_history = []
        
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
        
        # 转换为RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # 姿态检测
        results = self.pose.process(rgb_frame)
        
        detection_result = {
            'frame_number': frame_number,
            'timestamp': timestamp,
            'person_detected': False,
            'is_fall': False,
            'confidence': 0.0,
            'body_angle': 0.0,
            'movement_magnitude': 0.0,
            'fall_duration': 0.0,
            'landmarks': None,
            'bbox': None,
            'analysis_timestamp': datetime.now().isoformat(),
            'processing_time': 0.0
        }
        
        if results.pose_landmarks:
            self.detection_stats['person_detected'] += 1
            detection_result['person_detected'] = True
            
            # 提取关键点
            landmarks = self._extract_landmarks(results.pose_landmarks)
            detection_result['landmarks'] = landmarks
            
            # 计算身体角度
            body_angle = self._calculate_body_angle(landmarks)
            detection_result['body_angle'] = body_angle
            
            # 计算运动幅度
            movement_magnitude = self._calculate_movement(landmarks)
            detection_result['movement_magnitude'] = movement_magnitude
            
            # 计算边界框
            bbox = self._calculate_bbox(landmarks, frame.shape)
            detection_result['bbox'] = bbox
            
            # 跌倒判断
            is_fall, confidence, fall_details = self._determine_fall(
                body_angle, movement_magnitude, timestamp
            )
            
            detection_result.update({
                'is_fall': is_fall,
                'confidence': confidence,
                **fall_details
            })
            
            if is_fall:
                self.detection_stats['fall_detected'] += 1
            
            # 更新历史记录
            self._update_history(landmarks, body_angle, timestamp)
        
        # 计算处理时间
        processing_time = time.time() - start_time
        detection_result['processing_time'] = round(processing_time, 4)
        self.detection_stats['processing_times'].append(processing_time)
        
        return detection_result
    
    def _extract_landmarks(self, pose_landmarks) -> Dict[str, Tuple[float, float, float]]:
        """提取关键点坐标"""
        landmarks = {}
        
        for name, index in self.key_points.items():
            if index < len(pose_landmarks.landmark):
                landmark = pose_landmarks.landmark[index]
                landmarks[name] = (landmark.x, landmark.y, landmark.visibility)
        
        return landmarks
    
    def _calculate_body_angle(self, landmarks: Dict) -> float:
        """计算身体倾斜角度"""
        try:
            # 使用肩膀和臀部的中点计算身体轴线
            if all(key in landmarks for key in ['left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']):
                # 肩膀中点
                shoulder_x = (landmarks['left_shoulder'][0] + landmarks['right_shoulder'][0]) / 2
                shoulder_y = (landmarks['left_shoulder'][1] + landmarks['right_shoulder'][1]) / 2
                
                # 臀部中点
                hip_x = (landmarks['left_hip'][0] + landmarks['right_hip'][0]) / 2
                hip_y = (landmarks['left_hip'][1] + landmarks['right_hip'][1]) / 2
                
                # 计算角度（相对于垂直方向）
                if abs(shoulder_y - hip_y) > 0.01:  # 避免除零
                    angle_rad = math.atan2(abs(shoulder_x - hip_x), abs(shoulder_y - hip_y))
                    angle_deg = math.degrees(angle_rad)
                    return angle_deg
                    
        except (KeyError, ZeroDivisionError, ValueError):
            pass
        
        return 0.0
    
    def _calculate_movement(self, landmarks: Dict) -> float:
        """计算运动幅度"""
        if self.previous_landmarks is None:
            self.previous_landmarks = landmarks
            return 0.0
        
        try:
            total_movement = 0.0
            count = 0
            
            # 计算主要关键点的移动距离
            key_points_for_movement = ['nose', 'left_shoulder', 'right_shoulder', 'left_hip', 'right_hip']
            
            for point_name in key_points_for_movement:
                if point_name in landmarks and point_name in self.previous_landmarks:
                    curr = landmarks[point_name]
                    prev = self.previous_landmarks[point_name]
                    
                    # 计算欧几里得距离
                    distance = math.sqrt(
                        (curr[0] - prev[0])**2 + (curr[1] - prev[1])**2
                    )
                    total_movement += distance
                    count += 1
            
            if count > 0:
                avg_movement = total_movement / count
                return avg_movement
                
        except (KeyError, ValueError):
            pass
        
        return 0.0
    
    def _calculate_bbox(self, landmarks: Dict, frame_shape: Tuple) -> List[int]:
        """计算人体边界框"""
        try:
            h, w = frame_shape[:2]
            
            x_coords = []
            y_coords = []
            
            for point_name, (x, y, visibility) in landmarks.items():
                if visibility > 0.5:  # 只使用可见的关键点
                    x_coords.append(x * w)
                    y_coords.append(y * h)
            
            if x_coords and y_coords:
                min_x = max(0, int(min(x_coords)) - 20)
                max_x = min(w, int(max(x_coords)) + 20)
                min_y = max(0, int(min(y_coords)) - 20)
                max_y = min(h, int(max(y_coords)) + 20)
                
                return [min_x, min_y, max_x, max_y]
                
        except (ValueError, TypeError):
            pass
        
        return [0, 0, 0, 0]
    
    def _determine_fall(self, body_angle: float, movement_magnitude: float, 
                       timestamp: float) -> Tuple[bool, float, Dict]:
        """判断是否发生跌倒"""
        fall_details = {
            'fall_duration': 0.0,
            'severity': 'NONE',
            'fall_direction': 'unknown',
            'body_position': 'upright'
        }
        
        # 跌倒判断条件
        angle_fall = body_angle > self.fall_angle_threshold
        movement_fall = movement_magnitude > self.movement_threshold
        
        # 综合判断
        fall_conditions = [
            angle_fall,
            movement_fall,
            len(self.person_history) > 3  # 需要一定的历史数据
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
                'severity': 'HIGH' if body_angle > 80 else 'MEDIUM',
                'fall_direction': self._determine_fall_direction(body_angle),
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
            self.consecutive_fall_frames >= 3 and
            self.fall_start_time is not None and
            (timestamp - self.fall_start_time) >= self.fall_duration_min
        )
        
        # 计算置信度
        confidence = 0.0
        if confirmed_fall:
            confidence = 0.6  # 基础置信度
            if body_angle > 80:
                confidence += 0.2
            if movement_magnitude > 0.2:
                confidence += 0.1
            if self.consecutive_fall_frames > 10:
                confidence += 0.1
            confidence = min(0.95, confidence)
        
        return confirmed_fall, confidence, fall_details
    
    def _determine_fall_direction(self, body_angle: float) -> str:
        """确定跌倒方向"""
        if self.previous_body_angle is not None:
            angle_change = body_angle - self.previous_body_angle
            if angle_change > 0:
                return 'forward'
            else:
                return 'backward'
        return 'side'
    
    def _update_history(self, landmarks: Dict, body_angle: float, timestamp: float):
        """更新历史记录"""
        self.previous_landmarks = landmarks.copy()
        self.previous_body_angle = body_angle
        
        # 添加到历史记录
        self.person_history.append({
            'timestamp': timestamp,
            'body_angle': body_angle,
            'landmarks': landmarks
        })
        
        # 保持历史记录长度
        max_history = 30
        if len(self.person_history) > max_history:
            self.person_history = self.person_history[-max_history:]
    
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
        self.person_history.clear()
        self.previous_landmarks = None
        self.previous_body_angle = None
    
    def update_parameters(self, **kwargs):
        """更新检测参数"""
        if 'fall_angle_threshold' in kwargs:
            self.fall_angle_threshold = kwargs['fall_angle_threshold']
        if 'movement_threshold' in kwargs:
            self.movement_threshold = kwargs['movement_threshold']
        if 'fall_duration_min' in kwargs:
            self.fall_duration_min = kwargs['fall_duration_min']
        if 'confidence_threshold' in kwargs:
            self.confidence_threshold = kwargs['confidence_threshold']
    
    def draw_pose_on_frame(self, frame: np.ndarray, landmarks: Dict, 
                          bbox: List[int] = None) -> np.ndarray:
        """在帧上绘制姿态关键点"""
        annotated_frame = frame.copy()
        h, w = frame.shape[:2]
        
        # 绘制边界框
        if bbox and len(bbox) == 4:
            cv2.rectangle(annotated_frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
        
        # 绘制关键点
        for point_name, (x, y, visibility) in landmarks.items():
            if visibility > 0.5:
                cv2.circle(annotated_frame, (int(x * w), int(y * h)), 5, (0, 0, 255), -1)
        
        # 绘制骨骼连接
        connections = [
            ('left_shoulder', 'right_shoulder'),
            ('left_shoulder', 'left_hip'),
            ('right_shoulder', 'right_hip'),
            ('left_hip', 'right_hip'),
            ('left_hip', 'left_knee'),
            ('right_hip', 'right_knee'),
            ('left_knee', 'left_ankle'),
            ('right_knee', 'right_ankle')
        ]
        
        for start_point, end_point in connections:
            if start_point in landmarks and end_point in landmarks:
                start = landmarks[start_point]
                end = landmarks[end_point]
                if start[2] > 0.5 and end[2] > 0.5:  # 两点都可见
                    cv2.line(annotated_frame, 
                            (int(start[0] * w), int(start[1] * h)),
                            (int(end[0] * w), int(end[1] * h)),
                            (255, 0, 0), 2)
        
        return annotated_frame
    
    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'pose'):
            self.pose.close()

class VideoFallProcessor:
    """视频跌倒检测处理器"""
    
    def __init__(self):
        """初始化处理器"""
        self.detector = MediaPipeFallDetector()
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
                        fall_event = {
                            'id': f'fall_{len(fall_events) + 1}',
                            'start_frame': frame_count,
                            'timestamp': timestamp,
                            'confidence': result['confidence'],
                            'body_angle': result['body_angle'],
                            'bbox': result['bbox'],
                            'severity': result.get('severity', 'UNKNOWN'),
                            'fall_direction': result.get('fall_direction', 'unknown')
                        }
                        fall_events.append(fall_event)
                        print(f"检测到跌倒事件 #{len(fall_events)} 在帧 {frame_count} (时间: {timestamp:.2f}s)")
                    
                    # 绘制检测结果（如果需要输出视频）
                    if out and result['person_detected'] and result['landmarks']:
                        annotated_frame = self.detector.draw_pose_on_frame(
                            frame, result['landmarks'], result['bbox']
                        )
                        
                        # 添加检测信息
                        info_text = f"Frame: {frame_count}, Fall: {result['is_fall']}"
                        if result['is_fall']:
                            info_text += f", Conf: {result['confidence']:.2f}"
                        
                        cv2.putText(annotated_frame, info_text, (10, 30), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        out.write(annotated_frame)
                    elif out:
                        out.write(frame)
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
        self.detector.cleanup()

if __name__ == "__main__":
    # 测试真实跌倒检测器
    print("🧪 测试MediaPipe跌倒检测器")
    
    # 创建测试图像
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    detector = MediaPipeFallDetector()
    
    # 测试检测
    result = detector.detect_fall_from_frame(test_frame, 0.0, 0)
    print(f"测试结果: {result}")
    
    # 输出统计信息
    stats = detector.get_detection_statistics()
    print(f"检测统计: {stats}")
    
    detector.cleanup()
    print("✅ 测试完成")