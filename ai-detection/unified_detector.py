#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一检测服务
集成跌倒检测和火焰检测算法
"""

import cv2
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import json
from concurrent.futures import ThreadPoolExecutor
import time

from fall_detector import FallDetector
from fire_detector import FireSmokeDetector

logger = logging.getLogger(__name__)

class UnifiedDetector:
    """统一检测服务 - 集成跌倒检测和火焰检测"""
    
    def __init__(self, fire_model_path: Optional[str] = None):
        """
        初始化统一检测器
        
        Args:
            fire_model_path: 火焰检测YOLO模型路径
        """
        # 初始化各个检测器
        self.fall_detector = FallDetector()
        self.fire_detector = FireSmokeDetector(fire_model_path)
        
        # 检测统计
        self.detection_stats = {
            'total_frames': 0,
            'fall_alerts': 0,
            'fire_alerts': 0,
            'smoke_alerts': 0,
            'last_reset': datetime.now().isoformat()
        }
        
        # 告警阈值
        self.alert_thresholds = {
            'fall_confidence': 0.7,
            'fire_confidence': 0.6,
            'smoke_confidence': 0.5
        }
        
        # 连续检测计数器（减少误报）
        self.consecutive_counts = {
            'fall': 0,
            'fire': 0,
            'smoke': 0
        }
        
        # 告警触发阈值
        self.consecutive_thresholds = {
            'fall': 3,  # 连续3帧检测到跌倒才告警
            'fire': 2,  # 连续2帧检测到火焰才告警
            'smoke': 5  # 连续5帧检测到烟雾才告警
        }
        
        # 线程池用于并行处理
        self.executor = ThreadPoolExecutor(max_workers=2)
        
        logger.info("✅ 统一检测服务初始化完成")
    
    def process_frame(self, frame: np.ndarray, camera_id: str, 
                     enable_fall: bool = True, enable_fire: bool = True) -> Dict:
        """
        处理单帧图像，执行所有检测任务
        
        Args:
            frame: 输入图像帧
            camera_id: 摄像头ID
            enable_fall: 是否启用跌倒检测
            enable_fire: 是否启用火焰检测
            
        Returns:
            统一的检测结果
        """
        start_time = time.time()
        self.detection_stats['total_frames'] += 1
        
        results = {
            'camera_id': camera_id,
            'timestamp': datetime.now().isoformat(),
            'frame_size': frame.shape,
            'detections': [],
            'alerts': [],
            'processing_time': 0.0
        }
        
        # 并行执行检测任务
        futures = []
        
        if enable_fall:
            future_fall = self.executor.submit(self._detect_fall, frame)
            futures.append(('fall', future_fall))
        
        if enable_fire:
            future_fire = self.executor.submit(self._detect_fire_smoke, frame)
            futures.append(('fire', future_fire))
        
        # 收集检测结果
        for detection_type, future in futures:
            try:
                detection_result = future.result(timeout=5.0)  # 5秒超时
                if detection_result:
                    results['detections'].extend(detection_result)
            except Exception as e:
                logger.error(f"{detection_type}检测失败: {e}")
        
        # 分析检测结果并生成告警
        alerts = self._analyze_detections(results['detections'])
        results['alerts'] = alerts
        
        # 更新统计信息
        self._update_statistics(alerts)
        
        # 计算处理时间
        results['processing_time'] = time.time() - start_time
        
        return results
    
    def _detect_fall(self, frame: np.ndarray) -> List[Dict]:
        """执行跌倒检测"""
        try:
            fall_result = self.fall_detector.detect_fall(frame)
            detections = []
            
            if fall_result['is_fall']:
                detection = {
                    'type': 'fall',
                    'confidence': fall_result['confidence'],
                    'severity': fall_result['severity'],
                    'person_id': fall_result.get('person_id', 'unknown'),
                    'body_angle': fall_result.get('body_angle', 0),
                    'duration': fall_result.get('duration', 0),
                    'location': fall_result.get('location', [0, 0]),
                    'timestamp': datetime.now().isoformat()
                }
                detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"跌倒检测失败: {e}")
            return []
    
    def _detect_fire_smoke(self, frame: np.ndarray) -> List[Dict]:
        """执行火焰烟雾检测"""
        try:
            fire_detections = self.fire_detector.detect_fire_smoke(frame)
            
            # 添加时间戳
            for detection in fire_detections:
                if 'timestamp' not in detection:
                    detection['timestamp'] = datetime.now().isoformat()
            
            return fire_detections
            
        except Exception as e:
            logger.error(f"火焰检测失败: {e}")
            return []
    
    def _analyze_detections(self, detections: List[Dict]) -> List[Dict]:
        """分析检测结果并生成告警"""
        alerts = []
        
        # 重置计数器
        current_types = set()
        
        for detection in detections:
            detection_type = detection['type']
            confidence = detection['confidence']
            
            current_types.add(detection_type)
            
            # 检查是否满足告警阈值
            threshold_key = f"{detection_type}_confidence"
            if threshold_key in self.alert_thresholds:
                threshold = self.alert_thresholds[threshold_key]
                
                if confidence >= threshold:
                    # 增加连续检测计数
                    self.consecutive_counts[detection_type] += 1
                    
                    # 检查是否达到连续检测阈值
                    consecutive_threshold = self.consecutive_thresholds.get(detection_type, 1)
                    
                    if self.consecutive_counts[detection_type] >= consecutive_threshold:
                        alert = self._create_alert(detection)
                        alerts.append(alert)
                        
                        # 重置计数器
                        self.consecutive_counts[detection_type] = 0
        
        # 重置未检测到的类型的计数器
        for detection_type in self.consecutive_counts:
            if detection_type not in current_types:
                self.consecutive_counts[detection_type] = 0
        
        return alerts
    
    def _create_alert(self, detection: Dict) -> Dict:
        """创建告警对象"""
        detection_type = detection['type']
        
        # 根据类型设置告警级别
        severity_map = {
            'fall': 'HIGH',
            'fire': 'CRITICAL',
            'smoke': 'HIGH'
        }
        
        alert = {
            'id': f"{detection_type}_{int(time.time() * 1000)}",
            'type': detection_type,
            'severity': severity_map.get(detection_type, 'MEDIUM'),
            'confidence': detection['confidence'],
            'timestamp': detection['timestamp'],
            'message': self._get_alert_message(detection),
            'details': detection,
            'status': 'ACTIVE'
        }
        
        return alert
    
    def _get_alert_message(self, detection: Dict) -> str:
        """生成告警消息"""
        detection_type = detection['type']
        confidence = detection['confidence']
        
        messages = {
            'fall': f"检测到跌倒事件，置信度: {confidence:.2f}",
            'fire': f"检测到火焰，置信度: {confidence:.2f}",
            'smoke': f"检测到烟雾，置信度: {confidence:.2f}"
        }
        
        return messages.get(detection_type, f"检测到{detection_type}，置信度: {confidence:.2f}")
    
    def _update_statistics(self, alerts: List[Dict]):
        """更新检测统计信息"""
        for alert in alerts:
            alert_type = alert['type']
            if alert_type == 'fall':
                self.detection_stats['fall_alerts'] += 1
            elif alert_type == 'fire':
                self.detection_stats['fire_alerts'] += 1
            elif alert_type == 'smoke':
                self.detection_stats['smoke_alerts'] += 1
    
    def get_detection_statistics(self) -> Dict:
        """获取检测统计信息"""
        stats = self.detection_stats.copy()
        
        # 添加各检测器的统计信息
        stats['fall_detector'] = self.fall_detector.get_detection_statistics()
        stats['fire_detector'] = self.fire_detector.get_detection_statistics()
        
        # 计算检测率
        total_alerts = (stats['fall_alerts'] + stats['fire_alerts'] + stats['smoke_alerts'])
        stats['alert_rate'] = total_alerts / max(stats['total_frames'], 1)
        
        return stats
    
    def reset_statistics(self):
        """重置统计信息"""
        self.detection_stats = {
            'total_frames': 0,
            'fall_alerts': 0,
            'fire_alerts': 0,
            'smoke_alerts': 0,
            'last_reset': datetime.now().isoformat()
        }
        
        # 重置连续检测计数器
        for key in self.consecutive_counts:
            self.consecutive_counts[key] = 0
    
    def update_thresholds(self, new_thresholds: Dict):
        """更新告警阈值"""
        self.alert_thresholds.update(new_thresholds)
        logger.info(f"告警阈值已更新: {self.alert_thresholds}")
    
    def visualize_detections(self, frame: np.ndarray, detections: List[Dict], 
                           alerts: List[Dict]) -> np.ndarray:
        """可视化所有检测结果"""
        result_frame = frame.copy()
        
        # 绘制检测结果
        for detection in detections:
            detection_type = detection['type']
            
            if detection_type == 'fall':
                # 跌倒检测可视化
                result_frame = self.fall_detector.draw_pose_landmarks(
                    result_frame, detection.get('landmarks'))
                
                # 添加跌倒标识
                location = detection.get('location', [50, 50])
                cv2.putText(result_frame, f"FALL DETECTED!", 
                           (int(location[0]), int(location[1])),
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 3)
            
            elif detection_type in ['fire', 'smoke']:
                # 火焰/烟雾检测可视化
                if 'bbox' in detection:
                    x1, y1, x2, y2 = detection['bbox']
                    color = (0, 0, 255) if detection_type == 'fire' else (128, 128, 128)
                    
                    cv2.rectangle(result_frame, (x1, y1), (x2, y2), color, 2)
                    
                    label = f"{detection_type.upper()}: {detection['confidence']:.2f}"
                    cv2.putText(result_frame, label, (x1, y1-10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        # 添加告警信息
        if alerts:
            alert_y = 30
            for alert in alerts:
                alert_text = f"ALERT: {alert['message']}"
                cv2.putText(result_frame, alert_text, (10, alert_y),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                alert_y += 30
        
        # 添加状态信息
        status_text = f"Frames: {self.detection_stats['total_frames']}"
        cv2.putText(result_frame, status_text, (10, frame.shape[0] - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return result_frame
    
    def export_detection_log(self, filepath: str, start_time: Optional[datetime] = None):
        """导出检测日志"""
        log_data = {
            'export_time': datetime.now().isoformat(),
            'statistics': self.get_detection_statistics(),
            'thresholds': self.alert_thresholds,
            'consecutive_thresholds': self.consecutive_thresholds
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"检测日志已导出到: {filepath}")

if __name__ == "__main__":
    # 测试统一检测器
    detector = UnifiedDetector()
    
    # 创建测试图像
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 添加火焰模拟（红色区域）
    cv2.rectangle(test_frame, (100, 200), (200, 400), (0, 69, 255), -1)
    
    # 执行检测
    result = detector.process_frame(test_frame, "camera_test_01")
    
    print("=== 统一检测结果 ===")
    print(f"摄像头ID: {result['camera_id']}")
    print(f"处理时间: {result['processing_time']:.3f}秒")
    print(f"检测到 {len(result['detections'])} 个目标")
    print(f"生成 {len(result['alerts'])} 个告警")
    
    for detection in result['detections']:
        print(f"  - {detection['type']}: 置信度 {detection['confidence']:.3f}")
    
    for alert in result['alerts']:
        print(f"  🚨 {alert['severity']}: {alert['message']}")
    
    # 获取统计信息
    stats = detector.get_detection_statistics()
    print(f"\n统计信息: {json.dumps(stats, indent=2, ensure_ascii=False)}")