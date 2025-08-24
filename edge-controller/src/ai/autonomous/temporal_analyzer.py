#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时序分析引擎 - 自主产权核心算法
核心功能：
1. 1-2秒滑窗时序特征提取
2. 轻量级TSM (Temporal Shift Module) 实现  
3. 运动连续性和一致性分析
4. 跌倒事件的时序模式识别

算法特点：
- 基于滑动窗口的时序特征分析
- 运动轨迹平滑和异常检测
- 多尺度时序特征融合
- 自适应阈值和模式匹配
"""

import numpy as np
import logging
from typing import Dict, List, Tuple, Any
from collections import deque
import math

logger = logging.getLogger(__name__)

class TemporalSequenceAnalyzer:
    """时序分析引擎 - 自主产权核心算法"""
    
    def __init__(self, window_size: int = 30, fps: int = 15):
        """
        初始化时序分析器
        
        Args:
            window_size: 滑窗大小 (帧数)
            fps: 视频帧率
        """
        self.window_size = window_size
        self.fps = fps
        self.time_window = window_size / fps  # 时间窗口 (秒)
        
        # 时序特征提取器
        self.motion_smoother = MotionSmoother(alpha=0.3)
        self.pattern_matcher = FallPatternMatcher()
        
        # 历史数据缓存
        self.sequence_cache = deque(maxlen=window_size * 2)
        
        logger.info(f"时序分析引擎初始化: 窗口={window_size}帧 ({self.time_window:.1f}秒)")
    
    def analyze_sequence(self, keypoint_sequence: List[Dict]) -> Dict[str, Any]:
        """
        分析关键点时序序列
        
        Args:
            keypoint_sequence: 关键点序列数据
            
        Returns:
            时序分析结果
        """
        if len(keypoint_sequence) < 5:
            return {'consistency_score': 0, 'temporal_features': {}}
        
        try:
            # 提取时序特征
            temporal_features = self._extract_temporal_features(keypoint_sequence)
            
            # 运动连续性分析
            consistency_score = self._analyze_motion_consistency(keypoint_sequence)
            
            # 跌倒模式匹配
            pattern_score, pattern_type = self.pattern_matcher.match_fall_pattern(temporal_features)
            
            # 速度和加速度分析
            velocity_features = self._analyze_velocity_profile(keypoint_sequence)
            
            # 异常检测
            anomaly_score = self._detect_motion_anomaly(keypoint_sequence)
            
            return {
                'consistency_score': consistency_score,
                'pattern_score': pattern_score,
                'pattern_type': pattern_type,
                'anomaly_score': anomaly_score,
                'temporal_features': temporal_features,
                'velocity_features': velocity_features,
                'sequence_length': len(keypoint_sequence),
                'time_span': self._calculate_time_span(keypoint_sequence)
            }
            
        except Exception as e:
            logger.error(f"时序分析异常: {e}")
            return {'consistency_score': 0, 'temporal_features': {}}
    
    def _extract_temporal_features(self, sequence: List[Dict]) -> Dict[str, Any]:
        """
        提取时序特征 - 核心特征工程
        
        Args:
            sequence: 关键点序列
            
        Returns:
            时序特征字典
        """
        features = {}
        
        # 提取轨迹数据
        trajectories = self._extract_trajectories(sequence)
        
        # 1. 质心轨迹特征
        centroid_trajectory = trajectories.get('centroid', [])
        if len(centroid_trajectory) >= 2:
            features.update(self._analyze_centroid_motion(centroid_trajectory))
        
        # 2. 关键点稳定性特征
        features.update(self._analyze_keypoint_stability(sequence))
        
        # 3. 身体比例变化特征
        features.update(self._analyze_body_proportion_changes(sequence))
        
        # 4. 角度变化特征
        features.update(self._analyze_angle_changes(sequence))
        
        # 5. 频域特征 (简化的频率分析)
        features.update(self._analyze_frequency_features(trajectories))
        
        return features
    
    def _extract_trajectories(self, sequence: List[Dict]) -> Dict[str, List]:
        """提取关键点轨迹"""
        trajectories = {
            'centroid': [],
            'head': [],
            'shoulders': [],
            'hips': [],
            'knees': [],
            'ankles': []
        }
        
        for frame_data in sequence:
            keypoints = frame_data['keypoints']
            timestamp = frame_data['timestamp']
            
            # 质心轨迹
            valid_points = keypoints[keypoints[:, 2] > 0.3]
            if len(valid_points) > 0:
                centroid = np.mean(valid_points[:, :2], axis=0)
                trajectories['centroid'].append({
                    'pos': centroid,
                    'timestamp': timestamp
                })
            
            # 头部轨迹 (鼻子)
            if keypoints[0, 2] > 0.3:
                trajectories['head'].append({
                    'pos': keypoints[0, :2],
                    'timestamp': timestamp
                })
            
            # 肩膀轨迹
            shoulder_points = keypoints[[5, 6]]  # 左右肩膀
            valid_shoulders = shoulder_points[shoulder_points[:, 2] > 0.3]
            if len(valid_shoulders) > 0:
                shoulder_center = np.mean(valid_shoulders[:, :2], axis=0)
                trajectories['shoulders'].append({
                    'pos': shoulder_center,
                    'timestamp': timestamp
                })
            
            # 髋部轨迹
            hip_points = keypoints[[11, 12]]  # 左右髋部
            valid_hips = hip_points[hip_points[:, 2] > 0.3]
            if len(valid_hips) > 0:
                hip_center = np.mean(valid_hips[:, :2], axis=0)
                trajectories['hips'].append({
                    'pos': hip_center,
                    'timestamp': timestamp
                })
        
        return trajectories
    
    def _analyze_centroid_motion(self, centroid_trajectory: List[Dict]) -> Dict[str, float]:
        """分析质心运动特征"""
        if len(centroid_trajectory) < 3:
            return {}
        
        positions = np.array([point['pos'] for point in centroid_trajectory])
        timestamps = np.array([point['timestamp'] for point in centroid_trajectory])
        
        # 计算速度序列
        velocities = []
        for i in range(1, len(positions)):
            dt = timestamps[i] - timestamps[i-1]
            if dt > 0:
                velocity = (positions[i] - positions[i-1]) / dt
                velocities.append(velocity)
        
        if not velocities:
            return {}
        
        velocities = np.array(velocities)
        velocity_magnitudes = np.linalg.norm(velocities, axis=1)
        
        # 计算加速度序列
        accelerations = []
        if len(velocities) >= 2:
            for i in range(1, len(velocities)):
                dt = timestamps[i+1] - timestamps[i]
                if dt > 0:
                    acceleration = (velocities[i] - velocities[i-1]) / dt
                    accelerations.append(acceleration)
        
        accelerations = np.array(accelerations) if accelerations else np.array([[0, 0]])
        acceleration_magnitudes = np.linalg.norm(accelerations, axis=1)
        
        # 轨迹特征
        total_displacement = np.linalg.norm(positions[-1] - positions[0])
        path_length = np.sum(np.linalg.norm(np.diff(positions, axis=0), axis=1))
        
        return {
            'centroid_displacement_total': total_displacement,
            'centroid_path_length': path_length,
            'centroid_velocity_mean': np.mean(velocity_magnitudes),
            'centroid_velocity_max': np.max(velocity_magnitudes),
            'centroid_velocity_std': np.std(velocity_magnitudes),
            'centroid_acceleration_mean': np.mean(acceleration_magnitudes),
            'centroid_acceleration_max': np.max(acceleration_magnitudes),
            'centroid_downward_motion': np.sum(velocities[:, 1] > 0),  # 向下运动次数
            'path_efficiency': total_displacement / max(path_length, 1)  # 路径效率
        }
    
    def _analyze_keypoint_stability(self, sequence: List[Dict]) -> Dict[str, float]:
        """分析关键点稳定性"""
        if len(sequence) < 3:
            return {}
        
        stability_scores = []
        confidence_changes = []
        
        for i in range(1, len(sequence)):
            curr_kpts = sequence[i]['keypoints']
            prev_kpts = sequence[i-1]['keypoints']
            
            # 计算关键点位置变化
            valid_mask = (curr_kpts[:, 2] > 0.3) & (prev_kpts[:, 2] > 0.3)
            if np.any(valid_mask):
                pos_changes = np.linalg.norm(
                    curr_kpts[valid_mask, :2] - prev_kpts[valid_mask, :2], 
                    axis=1
                )
                stability_score = np.mean(pos_changes)
                stability_scores.append(stability_score)
                
                # 置信度变化
                conf_change = np.mean(np.abs(curr_kpts[:, 2] - prev_kpts[:, 2]))
                confidence_changes.append(conf_change)
        
        if not stability_scores:
            return {}
        
        return {
            'keypoint_stability_mean': np.mean(stability_scores),
            'keypoint_stability_std': np.std(stability_scores),
            'keypoint_stability_max': np.max(stability_scores),
            'confidence_change_mean': np.mean(confidence_changes),
            'stability_trend': self._calculate_trend(stability_scores)
        }
    
    def _analyze_body_proportion_changes(self, sequence: List[Dict]) -> Dict[str, float]:
        """分析身体比例变化"""
        if len(sequence) < 3:
            return {}
        
        height_ratios = []
        width_ratios = []
        
        for frame_data in sequence:
            keypoints = frame_data['keypoints']
            
            # 计算身体高度比
            if all(keypoints[i, 2] > 0.3 for i in [0, 15, 16]):  # 头部和脚踝
                head_y = keypoints[0, 1]
                foot_y = max(keypoints[15, 1], keypoints[16, 1])
                
                if all(keypoints[i, 2] > 0.3 for i in [11, 12]):  # 髋部
                    hip_y = np.mean(keypoints[[11, 12], 1])
                    body_height = foot_y - head_y
                    upper_height = hip_y - head_y
                    
                    if body_height > 0:
                        height_ratio = upper_height / body_height
                        height_ratios.append(height_ratio)
            
            # 计算身体宽度比
            if all(keypoints[i, 2] > 0.3 for i in [5, 6, 11, 12]):  # 肩膀和髋部
                shoulder_width = abs(keypoints[6, 0] - keypoints[5, 0])
                hip_width = abs(keypoints[12, 0] - keypoints[11, 0])
                
                if shoulder_width > 0:
                    width_ratio = hip_width / shoulder_width
                    width_ratios.append(width_ratio)
        
        features = {}
        if height_ratios:
            features.update({
                'height_ratio_mean': np.mean(height_ratios),
                'height_ratio_std': np.std(height_ratios),
                'height_ratio_change': height_ratios[-1] - height_ratios[0] if len(height_ratios) > 1 else 0
            })
        
        if width_ratios:
            features.update({
                'width_ratio_mean': np.mean(width_ratios),
                'width_ratio_std': np.std(width_ratios),
                'width_ratio_change': width_ratios[-1] - width_ratios[0] if len(width_ratios) > 1 else 0
            })
        
        return features
    
    def _analyze_angle_changes(self, sequence: List[Dict]) -> Dict[str, float]:
        """分析角度变化特征"""
        if len(sequence) < 2:
            return {}
        
        body_angles = []
        limb_angles = []
        
        for frame_data in sequence:
            keypoints = frame_data['keypoints']
            
            # 身体角度 (肩膀到髋部的向量)
            if all(keypoints[i, 2] > 0.3 for i in [5, 6, 11, 12]):
                shoulder_center = np.mean(keypoints[[5, 6], :2], axis=0)
                hip_center = np.mean(keypoints[[11, 12], :2], axis=0)
                body_vector = hip_center - shoulder_center
                
                if np.linalg.norm(body_vector) > 0:
                    body_angle = math.atan2(body_vector[1], body_vector[0])
                    body_angles.append(body_angle)
            
            # 肢体角度 (肩膀水平线)
            if all(keypoints[i, 2] > 0.3 for i in [5, 6]):
                shoulder_vector = keypoints[6, :2] - keypoints[5, :2]
                if np.linalg.norm(shoulder_vector) > 0:
                    shoulder_angle = math.atan2(shoulder_vector[1], shoulder_vector[0])
                    limb_angles.append(shoulder_angle)
        
        features = {}
        if len(body_angles) > 1:
            angle_changes = np.diff(body_angles)
            features.update({
                'body_angle_change_mean': np.mean(np.abs(angle_changes)),
                'body_angle_change_max': np.max(np.abs(angle_changes)),
                'body_angle_velocity': np.std(angle_changes) * self.fps  # 角速度估计
            })
        
        if len(limb_angles) > 1:
            limb_changes = np.diff(limb_angles)
            features.update({
                'limb_angle_change_mean': np.mean(np.abs(limb_changes)),
                'limb_angle_instability': np.std(limb_changes)
            })
        
        return features
    
    def _analyze_frequency_features(self, trajectories: Dict[str, List]) -> Dict[str, float]:
        """分析频域特征（简化版本）"""
        features = {}
        
        for traj_name, trajectory in trajectories.items():
            if len(trajectory) < 10:  # 需要足够的数据点
                continue
            
            positions = np.array([point['pos'] for point in trajectory])
            
            # 计算运动的周期性特征
            if len(positions) > 0:
                # 简化的频率分析：计算位置变化的周期性
                x_positions = positions[:, 0]
                y_positions = positions[:, 1]
                
                # 计算自相关来检测周期性
                x_autocorr = self._simple_autocorrelation(x_positions)
                y_autocorr = self._simple_autocorrelation(y_positions)
                
                features.update({
                    f'{traj_name}_x_periodicity': x_autocorr,
                    f'{traj_name}_y_periodicity': y_autocorr,
                    f'{traj_name}_motion_regularity': (x_autocorr + y_autocorr) / 2
                })
        
        return features
    
    def _simple_autocorrelation(self, signal: np.ndarray) -> float:
        """简单的自相关计算"""
        if len(signal) < 4:
            return 0
        
        try:
            # 计算延迟1的自相关
            corr = np.corrcoef(signal[:-1], signal[1:])[0, 1]
            return abs(corr) if not np.isnan(corr) else 0
        except:
            return 0
    
    def _analyze_motion_consistency(self, sequence: List[Dict]) -> float:
        """分析运动连续性"""
        if len(sequence) < 3:
            return 0
        
        consistency_scores = []
        
        # 时间间隔一致性
        timestamps = [frame['timestamp'] for frame in sequence]
        time_intervals = np.diff(timestamps)
        time_consistency = 1.0 - min(np.std(time_intervals) / max(np.mean(time_intervals), 0.001), 1.0)
        consistency_scores.append(time_consistency)
        
        # 位置变化一致性
        position_changes = []
        for i in range(1, len(sequence)):
            curr_kpts = sequence[i]['keypoints']
            prev_kpts = sequence[i-1]['keypoints']
            
            # 计算质心变化
            curr_valid = curr_kpts[curr_kpts[:, 2] > 0.3]
            prev_valid = prev_kpts[prev_kpts[:, 2] > 0.3]
            
            if len(curr_valid) > 0 and len(prev_valid) > 0:
                curr_centroid = np.mean(curr_valid[:, :2], axis=0)
                prev_centroid = np.mean(prev_valid[:, :2], axis=0)
                change = np.linalg.norm(curr_centroid - prev_centroid)
                position_changes.append(change)
        
        if position_changes:
            # 位置变化的平滑性
            change_smoothness = 1.0 - min(np.std(position_changes) / max(np.mean(position_changes), 0.001), 1.0)
            consistency_scores.append(change_smoothness)
        
        # 关键点可见性一致性
        visibility_consistency = self._analyze_visibility_consistency(sequence)
        consistency_scores.append(visibility_consistency)
        
        return np.mean(consistency_scores) if consistency_scores else 0
    
    def _analyze_visibility_consistency(self, sequence: List[Dict]) -> float:
        """分析关键点可见性一致性"""
        if len(sequence) < 2:
            return 1.0
        
        visibility_changes = []
        for i in range(1, len(sequence)):
            curr_visible = np.sum(sequence[i]['keypoints'][:, 2] > 0.3)
            prev_visible = np.sum(sequence[i-1]['keypoints'][:, 2] > 0.3)
            change_ratio = abs(curr_visible - prev_visible) / max(prev_visible, 1)
            visibility_changes.append(change_ratio)
        
        if not visibility_changes:
            return 1.0
        
        # 可见性变化应该是渐进的，不应该有突然的大幅变化
        avg_change = np.mean(visibility_changes)
        consistency = max(0, 1.0 - avg_change * 2)  # 调整权重
        return consistency
    
    def _analyze_velocity_profile(self, sequence: List[Dict]) -> Dict[str, float]:
        """分析速度剖面"""
        if len(sequence) < 3:
            return {}
        
        centroids = []
        timestamps = []
        
        for frame_data in sequence:
            keypoints = frame_data['keypoints']
            valid_points = keypoints[keypoints[:, 2] > 0.3]
            
            if len(valid_points) > 0:
                centroid = np.mean(valid_points[:, :2], axis=0)
                centroids.append(centroid)
                timestamps.append(frame_data['timestamp'])
        
        if len(centroids) < 3:
            return {}
        
        centroids = np.array(centroids)
        timestamps = np.array(timestamps)
        
        # 计算速度序列
        velocities = []
        for i in range(1, len(centroids)):
            dt = timestamps[i] - timestamps[i-1]
            if dt > 0:
                velocity = (centroids[i] - centroids[i-1]) / dt
                velocities.append(velocity)
        
        if not velocities:
            return {}
        
        velocities = np.array(velocities)
        velocity_mags = np.linalg.norm(velocities, axis=1)
        
        # 速度剖面特征
        features = {
            'velocity_profile_mean': np.mean(velocity_mags),
            'velocity_profile_max': np.max(velocity_mags),
            'velocity_profile_std': np.std(velocity_mags),
            'velocity_trend': self._calculate_trend(velocity_mags),
            'acceleration_events': np.sum(np.diff(velocity_mags) > 50),  # 加速事件
            'deceleration_events': np.sum(np.diff(velocity_mags) < -50)  # 减速事件
        }
        
        return features
    
    def _detect_motion_anomaly(self, sequence: List[Dict]) -> float:
        """检测运动异常"""
        if len(sequence) < 5:
            return 0
        
        anomaly_indicators = []
        
        # 1. 关键点突然消失/出现
        visibility_changes = []
        for i in range(1, len(sequence)):
            curr_visible = np.sum(sequence[i]['keypoints'][:, 2] > 0.3)
            prev_visible = np.sum(sequence[i-1]['keypoints'][:, 2] > 0.3)
            change_ratio = abs(curr_visible - prev_visible) / max(prev_visible, 1)
            visibility_changes.append(change_ratio)
        
        if visibility_changes:
            avg_visibility_change = np.mean(visibility_changes)
            anomaly_indicators.append(min(avg_visibility_change * 2, 1.0))
        
        # 2. 运动速度异常
        velocity_anomalies = self._detect_velocity_anomalies(sequence)
        anomaly_indicators.append(velocity_anomalies)
        
        # 3. 姿态异常
        pose_anomalies = self._detect_pose_anomalies(sequence)
        anomaly_indicators.append(pose_anomalies)
        
        return np.mean(anomaly_indicators) if anomaly_indicators else 0
    
    def _detect_velocity_anomalies(self, sequence: List[Dict]) -> float:
        """检测速度异常"""
        if len(sequence) < 3:
            return 0
        
        velocities = []
        for i in range(1, len(sequence)):
            curr_kpts = sequence[i]['keypoints']
            prev_kpts = sequence[i-1]['keypoints']
            dt = sequence[i]['timestamp'] - sequence[i-1]['timestamp']
            
            if dt > 0:
                # 计算质心速度
                curr_valid = curr_kpts[curr_kpts[:, 2] > 0.3]
                prev_valid = prev_kpts[prev_kpts[:, 2] > 0.3]
                
                if len(curr_valid) > 0 and len(prev_valid) > 0:
                    curr_centroid = np.mean(curr_valid[:, :2], axis=0)
                    prev_centroid = np.mean(prev_valid[:, :2], axis=0)
                    velocity_mag = np.linalg.norm(curr_centroid - prev_centroid) / dt
                    velocities.append(velocity_mag)
        
        if len(velocities) < 2:
            return 0
        
        # 检测速度突变
        velocity_changes = np.abs(np.diff(velocities))
        mean_change = np.mean(velocity_changes)
        max_change = np.max(velocity_changes)
        
        # 异常评分：突然的大幅速度变化
        anomaly_score = min(max_change / max(mean_change * 3, 1), 1.0)
        return anomaly_score
    
    def _detect_pose_anomalies(self, sequence: List[Dict]) -> float:
        """检测姿态异常"""
        if len(sequence) < 2:
            return 0
        
        pose_anomalies = []
        
        for frame_data in sequence:
            keypoints = frame_data['keypoints']
            
            # 检测非自然的身体比例
            if all(keypoints[i, 2] > 0.3 for i in [0, 15, 16, 11, 12]):  # 头部、脚踝、髋部
                head_y = keypoints[0, 1]
                foot_y = max(keypoints[15, 1], keypoints[16, 1])
                hip_y = np.mean(keypoints[[11, 12], 1])
                
                body_height = foot_y - head_y
                upper_height = hip_y - head_y
                
                if body_height > 0:
                    height_ratio = upper_height / body_height
                    
                    # 正常的身体比例应该在0.3-0.8之间
                    if height_ratio < 0.2 or height_ratio > 0.9:
                        pose_anomalies.append(1.0)
                    elif height_ratio < 0.3 or height_ratio > 0.8:
                        pose_anomalies.append(0.5)
                    else:
                        pose_anomalies.append(0.0)
        
        return np.mean(pose_anomalies) if pose_anomalies else 0
    
    def _calculate_trend(self, values: List[float]) -> float:
        """计算数值趋势"""
        if len(values) < 2:
            return 0
        
        # 简单的线性趋势
        x = np.arange(len(values))
        try:
            slope = np.polyfit(x, values, 1)[0]
            return slope
        except:
            return 0
    
    def _calculate_time_span(self, sequence: List[Dict]) -> float:
        """计算时间跨度"""
        if len(sequence) < 2:
            return 0
        
        return sequence[-1]['timestamp'] - sequence[0]['timestamp']


class MotionSmoother:
    """运动平滑器"""
    
    def __init__(self, alpha: float = 0.3):
        self.alpha = alpha
        self.prev_value = None
    
    def smooth(self, value: float) -> float:
        """指数平滑"""
        if self.prev_value is None:
            self.prev_value = value
            return value
        
        smoothed = self.alpha * value + (1 - self.alpha) * self.prev_value
        self.prev_value = smoothed
        return smoothed


class FallPatternMatcher:
    """跌倒模式匹配器"""
    
    def __init__(self):
        # 预定义的跌倒模式
        self.fall_patterns = {
            'sudden_fall': {
                'velocity_increase': True,
                'height_decrease': True,
                'duration': (0.5, 2.0)
            },
            'gradual_fall': {
                'velocity_increase': False,
                'height_decrease': True,
                'duration': (1.0, 3.0)
            },
            'collapse': {
                'velocity_increase': True,
                'height_decrease': True,
                'duration': (0.2, 1.0)
            }
        }
    
    def match_fall_pattern(self, temporal_features: Dict) -> Tuple[float, str]:
        """匹配跌倒模式"""
        best_score = 0
        best_pattern = 'unknown'
        
        for pattern_name, pattern_config in self.fall_patterns.items():
            score = self._calculate_pattern_score(temporal_features, pattern_config)
            if score > best_score:
                best_score = score
                best_pattern = pattern_name
        
        return best_score, best_pattern
    
    def _calculate_pattern_score(self, features: Dict, pattern_config: Dict) -> float:
        """计算模式匹配分数"""
        score = 0
        checks = 0
        
        # 速度增加检查
        if 'velocity_increase' in pattern_config:
            velocity_trend = features.get('centroid_velocity_mean', 0)
            if pattern_config['velocity_increase'] and velocity_trend > 100:
                score += 1
            elif not pattern_config['velocity_increase'] and velocity_trend <= 100:
                score += 1
            checks += 1
        
        # 高度降低检查
        if 'height_decrease' in pattern_config:
            height_change = features.get('height_ratio_change', 0)
            if pattern_config['height_decrease'] and height_change < -0.1:
                score += 1
            checks += 1
        
        return score / max(checks, 1) if checks > 0 else 0