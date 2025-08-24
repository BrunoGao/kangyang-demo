#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主产权跌倒检测算法 V2.0
核心创新：
1. 轻量级关键点提取 + 时序分析引擎
2. 多阶段跌倒状态识别 (起因/过程/落地/静止)
3. 几何特征 + 运动特征融合
4. 自适应阈值和误报抑制

算法特点：
- 基于17个关键点的轻量化人体姿态估计
- 1-2秒滑窗时序分析，支持延迟评估
- 高度比、质心位移、角速度等几何特征
- 连续性验证和速度衰减一致性检查
"""

import cv2
import numpy as np
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
from datetime import datetime
import math

from .temporal_analyzer import TemporalSequenceAnalyzer
from .keypoint_extractor import LightweightPoseNet

logger = logging.getLogger(__name__)

class AutonomousFallDetector:
    """自主产权跌倒检测算法 - 核心算法模块"""
    
    # 17个关键点定义 (COCO格式优化版)
    KEYPOINT_NAMES = [
        'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
        'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
        'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
    ]
    
    # 关键连接关系
    SKELETON_CONNECTIONS = [
        (5, 6), (5, 7), (6, 8), (7, 9), (8, 10),  # 上肢
        (11, 12), (11, 13), (12, 14), (13, 15), (14, 16),  # 下肢  
        (5, 11), (6, 12)  # 躯干连接
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化自主跌倒检测器
        
        Args:
            config: 检测配置参数
        """
        self.config = config or {}
        
        # 核心参数
        self.confidence_threshold = self.config.get("confidence_threshold", 0.85)
        self.temporal_window_size = self.config.get("temporal_window_size", 30)  # 1-2秒@15fps
        self.min_fall_duration = self.config.get("min_fall_duration", 0.5)  # 最小跌倒持续时间
        self.cooldown_period = self.config.get("cooldown_period", 5.0)  # 冷却期
        
        # 几何特征阈值
        self.height_ratio_threshold = self.config.get("height_ratio_threshold", 0.6)
        self.velocity_threshold = self.config.get("velocity_threshold", 150)  # 像素/秒
        self.stability_threshold = self.config.get("stability_threshold", 0.3)
        
        # 核心组件初始化
        self.pose_extractor = LightweightPoseNet()
        self.temporal_analyzer = TemporalSequenceAnalyzer(
            window_size=self.temporal_window_size,
            fps=15
        )
        
        # 状态追踪
        self.keypoint_history = deque(maxlen=self.temporal_window_size)
        self.last_detection_time = 0
        self.person_tracker = PersonTracker()
        
        # 统计信息
        self.stats = {
            "total_detections": 0,
            "fall_events": 0,
            "false_alarms_suppressed": 0,
            "processing_time_avg": 0
        }
        
        logger.info("自主跌倒检测算法V2.0初始化完成")
    
    def detect(self, frame: np.ndarray, timestamp: float, frame_number: int) -> Optional[Dict[str, Any]]:
        """
        标准检测接口
        
        Args:
            frame: 输入图像帧
            timestamp: 时间戳  
            frame_number: 帧号
            
        Returns:
            检测结果或None
        """
        start_time = time.time()
        
        try:
            # 冷却期检查
            if timestamp - self.last_detection_time < self.cooldown_period:
                return None
            
            # 关键点提取
            keypoints = self.pose_extractor.extract(frame)
            if keypoints is None or len(keypoints) == 0:
                return None
            
            # 人员追踪和筛选
            valid_persons = self.person_tracker.track_and_filter(keypoints, frame)
            if not valid_persons:
                return None
            
            # 时序分析
            detection_result = None
            for person_id, person_keypoints in valid_persons.items():
                result = self._analyze_fall_sequence(
                    person_keypoints, 
                    timestamp, 
                    frame_number, 
                    person_id
                )
                
                if result and result['confidence'] > self.confidence_threshold:
                    detection_result = result
                    break
            
            # 更新统计信息
            processing_time = time.time() - start_time
            self._update_stats(processing_time, detection_result is not None)
            
            if detection_result:
                self.last_detection_time = timestamp
                logger.info(f"检测到跌倒事件: 置信度={detection_result['confidence']:.3f}, "
                           f"阶段={detection_result['fall_stage']}")
            
            return detection_result
            
        except Exception as e:
            logger.error(f"跌倒检测异常: {e}")
            return None
    
    def _analyze_fall_sequence(self, keypoints: np.ndarray, timestamp: float, 
                              frame_number: int, person_id: int) -> Optional[Dict[str, Any]]:
        """
        分析跌倒序列 - 核心算法逻辑
        
        Args:
            keypoints: 关键点坐标 (17, 3) [x, y, confidence]
            timestamp: 时间戳
            frame_number: 帧号
            person_id: 人员ID
            
        Returns:
            跌倒分析结果
        """
        # 添加到历史序列
        self.keypoint_history.append({
            'keypoints': keypoints,
            'timestamp': timestamp,
            'frame_number': frame_number,
            'person_id': person_id
        })
        
        # 序列长度不足时返回
        if len(self.keypoint_history) < 10:  # 至少需要0.67秒的数据
            return None
        
        # 提取几何和运动特征
        geometric_features = self._extract_geometric_features(keypoints)
        motion_features = self._extract_motion_features()
        
        # 时序特征分析
        temporal_features = self.temporal_analyzer.analyze_sequence(
            list(self.keypoint_history)
        )
        
        # 跌倒状态分类
        fall_prob, fall_stage = self._classify_fall_state(
            geometric_features, 
            motion_features, 
            temporal_features
        )
        
        # 置信度阈值判断
        if fall_prob < self.confidence_threshold:
            return None
        
        # 连续性验证
        if not self._verify_fall_consistency(temporal_features, fall_stage):
            self.stats["false_alarms_suppressed"] += 1
            return None
        
        # 生成检测结果
        return {
            'type': 'fall',
            'subtype': self._get_fall_subtype(geometric_features, motion_features),
            'confidence': fall_prob,
            'fall_stage': fall_stage,
            'timestamp': timestamp,
            'frame_number': frame_number,
            'person_id': person_id,
            'bbox': self._get_person_bbox(keypoints),
            'geometric_features': geometric_features,
            'motion_features': motion_features,
            'temporal_features': temporal_features,
            'algorithm': 'autonomous_fall_detector_v2'
        }
    
    def _extract_geometric_features(self, keypoints: np.ndarray) -> Dict[str, float]:
        """
        提取几何特征 - 自主算法核心
        
        Args:
            keypoints: 关键点坐标
            
        Returns:
            几何特征字典
        """
        try:
            # 关键点有效性检查
            valid_points = keypoints[keypoints[:, 2] > 0.3]  # 置信度阈值
            if len(valid_points) < 5:
                return {}
            
            # 1. 身体高度比分析
            head_y = min(keypoints[[0, 1, 2], 1])  # 头部最高点
            foot_y = max(keypoints[[15, 16], 1])   # 脚部最低点
            hip_y = np.mean(keypoints[[11, 12], 1])  # 臀部平均高度
            
            body_height = foot_y - head_y
            upper_height = hip_y - head_y
            height_ratio = upper_height / max(body_height, 1) if body_height > 0 else 0
            
            # 2. 重心位移分析
            shoulder_center = np.mean(keypoints[[5, 6], :2], axis=0)
            hip_center = np.mean(keypoints[[11, 12], :2], axis=0)
            centroid = np.mean([shoulder_center, hip_center], axis=0)
            
            # 3. 身体角度分析
            shoulder_vector = keypoints[6, :2] - keypoints[5, :2]  # 肩膀向量
            hip_vector = keypoints[12, :2] - keypoints[11, :2]     # 髋部向量
            
            shoulder_angle = math.atan2(shoulder_vector[1], shoulder_vector[0])
            hip_angle = math.atan2(hip_vector[1], hip_vector[0])
            body_tilt = abs(shoulder_angle - hip_angle)
            
            # 4. 肢体分布分析
            limb_spread = self._calculate_limb_spread(keypoints)
            
            # 5. 稳定性指标
            stability_score = self._calculate_stability_score(keypoints)
            
            return {
                'height_ratio': height_ratio,
                'body_height': body_height,
                'centroid_x': centroid[0],
                'centroid_y': centroid[1],
                'body_tilt': body_tilt,
                'shoulder_angle': shoulder_angle,
                'hip_angle': hip_angle,
                'limb_spread': limb_spread,
                'stability_score': stability_score,
                'head_y': head_y,
                'foot_y': foot_y,
                'hip_y': hip_y
            }
            
        except Exception as e:
            logger.error(f"几何特征提取异常: {e}")
            return {}
    
    def _extract_motion_features(self) -> Dict[str, float]:
        """
        提取运动特征 - 基于时序数据
        
        Returns:
            运动特征字典
        """
        if len(self.keypoint_history) < 3:
            return {}
        
        try:
            # 获取最近3帧的数据
            recent_frames = list(self.keypoint_history)[-3:]
            
            # 质心运动分析
            centroids = []
            timestamps = []
            for frame_data in recent_frames:
                kpts = frame_data['keypoints']
                shoulder_center = np.mean(kpts[[5, 6], :2], axis=0)
                hip_center = np.mean(kpts[[11, 12], :2], axis=0)
                centroid = np.mean([shoulder_center, hip_center], axis=0)
                centroids.append(centroid)
                timestamps.append(frame_data['timestamp'])
            
            centroids = np.array(centroids)
            
            # 计算速度和加速度
            if len(centroids) >= 2:
                dt = timestamps[1] - timestamps[0]
                velocity = (centroids[1] - centroids[0]) / dt if dt > 0 else np.array([0, 0])
                velocity_magnitude = np.linalg.norm(velocity)
                
                if len(centroids) >= 3:
                    dt2 = timestamps[2] - timestamps[1]
                    velocity2 = (centroids[2] - centroids[1]) / dt2 if dt2 > 0 else np.array([0, 0])
                    acceleration = (velocity2 - velocity) / ((dt + dt2) / 2) if (dt + dt2) > 0 else np.array([0, 0])
                    acceleration_magnitude = np.linalg.norm(acceleration)
                else:
                    acceleration = np.array([0, 0])
                    acceleration_magnitude = 0
            else:
                velocity = np.array([0, 0])
                velocity_magnitude = 0
                acceleration = np.array([0, 0])
                acceleration_magnitude = 0
            
            # 角速度分析
            angular_velocity = self._calculate_angular_velocity(recent_frames)
            
            # 运动稳定性
            motion_stability = self._calculate_motion_stability(recent_frames)
            
            return {
                'velocity_x': velocity[0],
                'velocity_y': velocity[1],
                'velocity_magnitude': velocity_magnitude,
                'acceleration_x': acceleration[0],
                'acceleration_y': acceleration[1], 
                'acceleration_magnitude': acceleration_magnitude,
                'angular_velocity': angular_velocity,
                'motion_stability': motion_stability,
                'downward_motion': max(0, velocity[1])  # 向下运动分量
            }
            
        except Exception as e:
            logger.error(f"运动特征提取异常: {e}")
            return {}
    
    def _classify_fall_state(self, geometric_features: Dict, motion_features: Dict, 
                           temporal_features: Dict) -> Tuple[float, str]:
        """
        跌倒状态分类 - 核心分类器
        
        Returns:
            (置信度, 跌倒阶段)
        """
        if not geometric_features or not motion_features:
            return 0.0, 'normal'
        
        # 特征权重配置
        weights = {
            'height_ratio': 0.25,
            'velocity': 0.20,
            'acceleration': 0.15,
            'body_tilt': 0.15,
            'stability': 0.15,
            'temporal': 0.10
        }
        
        scores = {}
        
        # 1. 高度比评分
        height_ratio = geometric_features.get('height_ratio', 1.0)
        if height_ratio < self.height_ratio_threshold:
            scores['height_ratio'] = (self.height_ratio_threshold - height_ratio) / self.height_ratio_threshold
        else:
            scores['height_ratio'] = 0
        
        # 2. 速度评分
        velocity_mag = motion_features.get('velocity_magnitude', 0)
        downward_motion = motion_features.get('downward_motion', 0)
        if velocity_mag > self.velocity_threshold:
            scores['velocity'] = min(velocity_mag / (self.velocity_threshold * 2), 1.0)
        else:
            scores['velocity'] = 0
        
        # 增加向下运动奖励
        scores['velocity'] += min(downward_motion / 200, 0.3)
        
        # 3. 加速度评分
        accel_mag = motion_features.get('acceleration_magnitude', 0)
        scores['acceleration'] = min(accel_mag / 500, 1.0)
        
        # 4. 身体倾斜评分
        body_tilt = geometric_features.get('body_tilt', 0)
        scores['body_tilt'] = min(body_tilt / (math.pi / 4), 1.0)  # 45度为满分
        
        # 5. 稳定性评分 (不稳定性越高，分数越高)
        stability = geometric_features.get('stability_score', 1.0)
        scores['stability'] = max(0, 1.0 - stability)
        
        # 6. 时序特征评分
        temporal_consistency = temporal_features.get('consistency_score', 0)
        scores['temporal'] = temporal_consistency
        
        # 加权计算总置信度
        total_confidence = sum(scores[key] * weights[key] for key in scores)
        total_confidence = min(total_confidence, 1.0)
        
        # 确定跌倒阶段
        fall_stage = self._determine_fall_stage(geometric_features, motion_features, total_confidence)
        
        return total_confidence, fall_stage
    
    def _determine_fall_stage(self, geometric_features: Dict, motion_features: Dict, confidence: float) -> str:
        """确定跌倒阶段"""
        if confidence < 0.5:
            return 'normal'
        
        height_ratio = geometric_features.get('height_ratio', 1.0)
        velocity_y = motion_features.get('velocity_y', 0)
        velocity_mag = motion_features.get('velocity_magnitude', 0)
        
        if velocity_mag > self.velocity_threshold * 1.5 and velocity_y > 0:
            return 'falling'  # 跌倒过程中
        elif height_ratio < 0.4 and velocity_mag < 50:
            return 'fallen'   # 已跌倒静止
        elif height_ratio < 0.6 and velocity_y > 0:
            return 'losing_balance'  # 失去平衡
        else:
            return 'unstable'  # 不稳定状态
    
    def _verify_fall_consistency(self, temporal_features: Dict, fall_stage: str) -> bool:
        """
        跌倒一致性验证 - 误报抑制
        
        Args:
            temporal_features: 时序特征
            fall_stage: 跌倒阶段
            
        Returns:
            是否通过一致性验证
        """
        # 时序一致性检查
        consistency = temporal_features.get('consistency_score', 0)
        if consistency < 0.3:
            return False
        
        # 阶段合理性检查
        if fall_stage in ['fallen', 'falling']:
            # 检查是否有足够的运动历史
            if len(self.keypoint_history) < 5:
                return False
            
            # 检查速度变化的合理性
            recent_velocities = []
            for i in range(max(0, len(self.keypoint_history) - 5), len(self.keypoint_history)):
                frame_data = list(self.keypoint_history)[i]
                # 计算该帧的瞬时速度（简化）
                if i > 0:
                    prev_frame = list(self.keypoint_history)[i-1]
                    dt = frame_data['timestamp'] - prev_frame['timestamp']
                    if dt > 0:
                        # 简化的速度计算
                        vel = np.linalg.norm(
                            np.mean(frame_data['keypoints'][:, :2], axis=0) - 
                            np.mean(prev_frame['keypoints'][:, :2], axis=0)
                        ) / dt
                        recent_velocities.append(vel)
            
            # 速度应该有一个下降趋势（从运动到静止）
            if len(recent_velocities) >= 3:
                velocity_trend = np.polyfit(range(len(recent_velocities)), recent_velocities, 1)[0]
                if fall_stage == 'fallen' and velocity_trend > 0:  # 应该减速
                    return False
        
        return True
    
    def _get_fall_subtype(self, geometric_features: Dict, motion_features: Dict) -> str:
        """确定跌倒子类型"""
        body_tilt = geometric_features.get('body_tilt', 0)
        height_ratio = geometric_features.get('height_ratio', 1.0)
        velocity_x = abs(motion_features.get('velocity_x', 0))
        velocity_y = motion_features.get('velocity_y', 0)
        
        if height_ratio > 0.7 and velocity_y > 0:
            return 'sitting_fall'    # 坐着跌倒
        elif body_tilt > math.pi / 6 and velocity_x > velocity_y:
            return 'side_fall'       # 侧向跌倒  
        elif height_ratio < 0.3:
            return 'horizontal_fall' # 水平跌倒
        else:
            return 'general_fall'    # 一般跌倒
    
    def _calculate_limb_spread(self, keypoints: np.ndarray) -> float:
        """计算肢体分布范围"""
        valid_points = keypoints[keypoints[:, 2] > 0.3]
        if len(valid_points) < 4:
            return 0
        
        x_range = np.max(valid_points[:, 0]) - np.min(valid_points[:, 0])
        y_range = np.max(valid_points[:, 1]) - np.min(valid_points[:, 1])
        return math.sqrt(x_range ** 2 + y_range ** 2)
    
    def _calculate_stability_score(self, keypoints: np.ndarray) -> float:
        """计算姿态稳定性得分"""
        try:
            # 基于关键点置信度和对称性
            left_shoulder = keypoints[5]
            right_shoulder = keypoints[6]
            left_hip = keypoints[11]  
            right_hip = keypoints[12]
            
            if all(pt[2] > 0.3 for pt in [left_shoulder, right_shoulder, left_hip, right_hip]):
                # 肩膀水平度
                shoulder_level = abs(left_shoulder[1] - right_shoulder[1])
                # 髋部水平度  
                hip_level = abs(left_hip[1] - right_hip[1])
                
                # 稳定性 = 1 - 归一化的不平衡度
                instability = (shoulder_level + hip_level) / 100  # 归一化
                stability = max(0, 1 - instability)
                return stability
            else:
                return 0.5  # 默认中等稳定性
        except:
            return 0.5
    
    def _calculate_angular_velocity(self, recent_frames: List) -> float:
        """计算角速度"""
        if len(recent_frames) < 2:
            return 0
        
        try:
            angles = []
            timestamps = []
            for frame_data in recent_frames:
                kpts = frame_data['keypoints']
                shoulder_vector = kpts[6, :2] - kpts[5, :2]
                angle = math.atan2(shoulder_vector[1], shoulder_vector[0])
                angles.append(angle)
                timestamps.append(frame_data['timestamp'])
            
            if len(angles) >= 2:
                dt = timestamps[1] - timestamps[0]
                if dt > 0:
                    angular_vel = abs(angles[1] - angles[0]) / dt
                    return angular_vel
            return 0
        except:
            return 0
    
    def _calculate_motion_stability(self, recent_frames: List) -> float:
        """计算运动稳定性"""
        if len(recent_frames) < 3:
            return 1.0
        
        try:
            positions = []
            for frame_data in recent_frames:
                kpts = frame_data['keypoints']
                centroid = np.mean(kpts[kpts[:, 2] > 0.3][:, :2], axis=0)
                positions.append(centroid)
            
            positions = np.array(positions)
            if len(positions) >= 2:
                movements = np.diff(positions, axis=0)
                movement_var = np.var(np.linalg.norm(movements, axis=1))
                stability = 1.0 / (1.0 + movement_var / 100)  # 归一化
                return stability
            return 1.0
        except:
            return 1.0
    
    def _get_person_bbox(self, keypoints: np.ndarray) -> List[int]:
        """获取人员边界框"""
        valid_points = keypoints[keypoints[:, 2] > 0.3]
        if len(valid_points) == 0:
            return [0, 0, 100, 100]
        
        x_min, y_min = np.min(valid_points[:, :2], axis=0)
        x_max, y_max = np.max(valid_points[:, :2], axis=0)
        
        # 扩展边界框
        padding = 20
        return [
            int(max(0, x_min - padding)),
            int(max(0, y_min - padding)), 
            int(x_max - x_min + 2 * padding),
            int(y_max - y_min + 2 * padding)
        ]
    
    def _update_stats(self, processing_time: float, detected: bool):
        """更新统计信息"""
        self.stats["total_detections"] += 1
        if detected:
            self.stats["fall_events"] += 1
        
        # 更新平均处理时间
        current_avg = self.stats["processing_time_avg"]
        total = self.stats["total_detections"]
        self.stats["processing_time_avg"] = (current_avg * (total - 1) + processing_time) / total
    
    def get_stats(self) -> Dict[str, Any]:
        """获取检测器统计信息"""
        return {
            "detector_type": "autonomous_fall_detection_v2",
            "version": "2.0.0",
            "algorithm_features": [
                "lightweight_pose_estimation",
                "temporal_sequence_analysis", 
                "multi_stage_fall_classification",
                "geometric_motion_fusion",
                "false_alarm_suppression"
            ],
            "confidence_threshold": self.confidence_threshold,
            "temporal_window_size": self.temporal_window_size,
            "stats": self.stats,
            "keypoint_format": "17_points_coco_optimized",
            "copyright": "自主产权算法 - 康养AI团队"
        }


class PersonTracker:
    """简化的人员追踪器"""
    
    def __init__(self):
        self.tracked_persons = {}
        self.next_id = 1
    
    def track_and_filter(self, keypoints_list: List[np.ndarray], frame: np.ndarray) -> Dict[int, np.ndarray]:
        """追踪和筛选有效人员"""
        valid_persons = {}
        
        for i, keypoints in enumerate(keypoints_list):
            # 简单的有效性检查
            valid_points = keypoints[keypoints[:, 2] > 0.3]
            if len(valid_points) >= 5:  # 至少5个有效关键点
                person_id = self._get_or_assign_id(keypoints)
                valid_persons[person_id] = keypoints
        
        return valid_persons
    
    def _get_or_assign_id(self, keypoints: np.ndarray) -> int:
        """获取或分配人员ID"""
        # 简化实现：直接分配新ID
        person_id = self.next_id
        self.next_id += 1
        return person_id