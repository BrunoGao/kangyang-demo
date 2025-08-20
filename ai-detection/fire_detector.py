#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火焰/烟雾检测算法模块
基于YOLO和传统图像处理的火灾检测
"""

import cv2
import numpy as np
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import os

logger = logging.getLogger(__name__)

class FireSmokeDetector:
    """火焰和烟雾检测器"""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        初始化火焰检测器
        
        Args:
            model_path: YOLO模型路径，如果为None则使用传统方法
        """
        self.model_path = model_path
        self.use_yolo = model_path and os.path.exists(model_path)
        
        if self.use_yolo:
            try:
                # 尝试加载YOLO模型
                from ultralytics import YOLO
                self.model = YOLO(model_path)
                self.classes = {0: 'fire', 1: 'smoke'}
                logger.info(f"✅ YOLO火焰检测模型加载成功: {model_path}")
            except Exception as e:
                logger.warning(f"⚠️  YOLO模型加载失败，使用传统检测方法: {e}")
                self.use_yolo = False
        
        # 传统火焰检测参数
        self.fire_lower_hsv = np.array([0, 50, 50])    # 火焰HSV下限
        self.fire_upper_hsv = np.array([35, 255, 255]) # 火焰HSV上限
        self.smoke_threshold = 0.3  # 烟雾检测阈值
        
        # 检测历史记录
        self.detection_history = []
        self.max_history = 10
        
    def detect_fire_smoke(self, frame: np.ndarray) -> List[Dict]:
        """
        检测火焰和烟雾
        
        Args:
            frame: 输入图像帧
            
        Returns:
            检测结果列表
        """
        if self.use_yolo:
            return self._detect_with_yolo(frame)
        else:
            return self._detect_with_traditional(frame)
    
    def _detect_with_yolo(self, frame: np.ndarray) -> List[Dict]:
        """使用YOLO模型检测火焰和烟雾"""
        try:
            results = self.model(frame, conf=0.5, iou=0.4)
            detections = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        
                        if confidence > 0.5:  # 置信度阈值
                            detection = {
                                'type': self.classes.get(class_id, 'unknown'),
                                'confidence': confidence,
                                'bbox': [int(x1), int(y1), int(x2), int(y2)],
                                'area': (x2-x1) * (y2-y1),
                                'center': [(x1+x2)/2, (y1+y2)/2],
                                'timestamp': datetime.now().isoformat()
                            }
                            detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"YOLO检测失败: {e}")
            return []
    
    def _detect_with_traditional(self, frame: np.ndarray) -> List[Dict]:
        """使用传统图像处理方法检测火焰和烟雾"""
        detections = []
        
        try:
            # 火焰检测
            fire_detections = self._detect_fire_traditional(frame)
            detections.extend(fire_detections)
            
            # 烟雾检测
            smoke_detections = self._detect_smoke_traditional(frame)
            detections.extend(smoke_detections)
            
        except Exception as e:
            logger.error(f"传统检测方法失败: {e}")
        
        return detections
    
    def _detect_fire_traditional(self, frame: np.ndarray) -> List[Dict]:
        """传统火焰检测方法"""
        detections = []
        
        # 转换到HSV色彩空间
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 火焰颜色范围检测
        fire_mask = cv2.inRange(hsv, self.fire_lower_hsv, self.fire_upper_hsv)
        
        # 形态学操作去噪
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_OPEN, kernel)
        fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_CLOSE, kernel)
        
        # 查找轮廓
        contours, _ = cv2.findContours(fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 500:  # 最小区域阈值
                x, y, w, h = cv2.boundingRect(contour)
                
                # 计算火焰特征
                aspect_ratio = w / h if h > 0 else 0
                extent = area / (w * h) if w * h > 0 else 0
                
                # 火焰形状判断（通常较窄且不规则）
                if 0.2 < aspect_ratio < 2.0 and extent > 0.3:
                    confidence = min(0.8, area / 10000)  # 基于面积的置信度
                    
                    detection = {
                        'type': 'fire',
                        'confidence': confidence,
                        'bbox': [x, y, x+w, y+h],
                        'area': area,
                        'center': [x+w/2, y+h/2],
                        'timestamp': datetime.now().isoformat(),
                        'features': {
                            'aspect_ratio': aspect_ratio,
                            'extent': extent
                        }
                    }
                    detections.append(detection)
        
        return detections
    
    def _detect_smoke_traditional(self, frame: np.ndarray) -> List[Dict]:
        """传统烟雾检测方法"""
        detections = []
        
        # 转换为灰度图
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 高斯模糊
        blurred = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # 计算图像的标准差（烟雾会降低局部对比度）
        mean, std = cv2.meanStdDev(blurred)
        
        # 检测低对比度区域（可能是烟雾）
        if std[0][0] < 30:  # 标准差阈值
            h, w = gray.shape
            smoke_regions = self._find_smoke_regions(gray)
            
            for region in smoke_regions:
                x, y, width, height = region
                area = width * height
                
                if area > 1000:  # 最小烟雾区域
                    confidence = min(0.7, (30 - std[0][0]) / 30)
                    
                    detection = {
                        'type': 'smoke',
                        'confidence': confidence,
                        'bbox': [x, y, x+width, y+height],
                        'area': area,
                        'center': [x+width/2, y+height/2],
                        'timestamp': datetime.now().isoformat(),
                        'features': {
                            'std_dev': float(std[0][0]),
                            'mean_intensity': float(mean[0][0])
                        }
                    }
                    detections.append(detection)
        
        return detections
    
    def _find_smoke_regions(self, gray_frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """查找可能的烟雾区域"""
        regions = []
        
        # 边缘检测
        edges = cv2.Canny(gray_frame, 50, 150)
        
        # 查找轮廓
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 1000:  # 最小区域
                x, y, w, h = cv2.boundingRect(contour)
                regions.append((x, y, w, h))
        
        return regions
    
    def add_detection_to_history(self, detections: List[Dict]):
        """添加检测结果到历史记录"""
        self.detection_history.append({
            'timestamp': datetime.now().isoformat(),
            'count': len(detections),
            'types': [d['type'] for d in detections]
        })
        
        # 保持历史记录数量限制
        if len(self.detection_history) > self.max_history:
            self.detection_history = self.detection_history[-self.max_history:]
    
    def get_detection_statistics(self) -> Dict:
        """获取检测统计信息"""
        if not self.detection_history:
            return {
                'total_detections': 0,
                'fire_count': 0,
                'smoke_count': 0,
                'detection_rate': 0.0
            }
        
        total_detections = sum(h['count'] for h in self.detection_history)
        fire_count = sum(h['types'].count('fire') for h in self.detection_history)
        smoke_count = sum(h['types'].count('smoke') for h in self.detection_history)
        detection_rate = len([h for h in self.detection_history if h['count'] > 0]) / len(self.detection_history)
        
        return {
            'total_detections': total_detections,
            'fire_count': fire_count,
            'smoke_count': smoke_count,
            'detection_rate': detection_rate,
            'method': 'YOLO' if self.use_yolo else 'Traditional'
        }
    
    def visualize_detections(self, frame: np.ndarray, detections: List[Dict]) -> np.ndarray:
        """在图像上可视化检测结果"""
        result_frame = frame.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = detection['bbox']
            detection_type = detection['type']
            confidence = detection['confidence']
            
            # 根据类型选择颜色
            if detection_type == 'fire':
                color = (0, 0, 255)  # 红色
                label = f"火焰 {confidence:.2f}"
            elif detection_type == 'smoke':
                color = (128, 128, 128)  # 灰色
                label = f"烟雾 {confidence:.2f}"
            else:
                color = (0, 255, 0)  # 绿色
                label = f"{detection_type} {confidence:.2f}"
            
            # 绘制边界框
            cv2.rectangle(result_frame, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(result_frame, (x1, y1 - label_size[1] - 10), 
                         (x1 + label_size[0], y1), color, -1)
            cv2.putText(result_frame, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return result_frame

if __name__ == "__main__":
    # 测试火焰检测器
    detector = FireSmokeDetector()
    
    # 创建测试图像
    test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 模拟火焰区域（红色-橙色）
    cv2.rectangle(test_frame, (100, 200), (200, 400), (0, 69, 255), -1)  # 橙红色
    
    # 执行检测
    detections = detector.detect_fire_smoke(test_frame)
    print(f"检测到 {len(detections)} 个目标:")
    for det in detections:
        print(f"  - {det['type']}: 置信度 {det['confidence']:.3f}")
    
    # 获取统计信息
    detector.add_detection_to_history(detections)
    stats = detector.get_detection_statistics()
    print(f"检测统计: {stats}")