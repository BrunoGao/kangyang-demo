#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火焰检测算法 - 边缘控制器版本
基于颜色和运动特征的轻量级火焰检测
"""

import cv2
import numpy as np
import logging
import time
from typing import Dict, Any, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)

class FireDetector:
    """轻量级火焰检测器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化火焰检测器
        
        Args:
            config: 检测配置参数
        """
        self.config = config or {}
        
        # 检测参数
        self.confidence_threshold = self.config.get("confidence_threshold", 0.85)
        self.cooldown_period = self.config.get("cooldown_period", 10)
        
        # 火焰颜色范围 (HSV)
        self.fire_color_ranges = [
            # 红色火焰
            ([0, 50, 50], [10, 255, 255]),
            ([170, 50, 50], [180, 255, 255]),
            # 橙色火焰
            ([10, 50, 50], [25, 255, 255]),
            # 黄色火焰
            ([25, 50, 50], [35, 255, 255])
        ]
        
        # 状态跟踪
        self.last_detection_time = 0
        self.fire_regions = []
        
        # 背景减除器用于运动检测
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True,
            varThreshold=30
        )
        
        logger.info("火焰检测器初始化完成")
    
    def detect(self, frame: np.ndarray, timestamp: float, frame_number: int) -> Dict[str, Any]:
        """
        检测火焰事件 - 标准接口
        
        Args:
            frame: 输入图像帧
            timestamp: 时间戳
            frame_number: 帧号
            
        Returns:
            检测结果，如果检测到火焰返回事件信息，否则返回None
        """
        results = self.detect_fire_smoke(frame)
        if results:
            result = results[0]  # 取第一个结果
            result["timestamp"] = timestamp
            result["frame_number"] = frame_number
            return result
        return None
    
    def detect_fire_smoke(self, frame: np.ndarray) -> List[Dict[str, Any]]:
        """
        检测火焰和烟雾
        
        Args:
            frame: 输入图像帧
            
        Returns:
            检测结果列表
        """
        results = []
        current_time = time.time()
        
        # 检查冷却期
        if current_time - self.last_detection_time < self.cooldown_period:
            return results
        
        try:
            # 火焰检测
            fire_result = self._detect_fire(frame)
            if fire_result:
                results.append(fire_result)
                self.last_detection_time = current_time
                
        except Exception as e:
            logger.error(f"火焰检测异常: {e}")
        
        return results
    
    def _detect_fire(self, frame: np.ndarray) -> Dict[str, Any]:
        """检测火焰"""
        try:
            # 转换颜色空间
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # 创建火焰颜色掩码
            fire_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            
            for lower, upper in self.fire_color_ranges:
                lower = np.array(lower, dtype=np.uint8)
                upper = np.array(upper, dtype=np.uint8)
                color_mask = cv2.inRange(hsv, lower, upper)
                fire_mask = cv2.bitwise_or(fire_mask, color_mask)
            
            # 运动检测
            fg_mask = self.background_subtractor.apply(frame)
            
            # 结合颜色和运动
            combined_mask = cv2.bitwise_and(fire_mask, fg_mask)
            
            # 形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
            
            # 寻找轮廓
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            best_fire = None
            max_confidence = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 100:  # 过滤小区域
                    continue
                
                # 分析火焰特征
                confidence = self._analyze_fire_features(contour, frame, hsv)
                
                if confidence > self.confidence_threshold and confidence > max_confidence:
                    max_confidence = confidence
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 估算火焰强度
                    intensity = self._estimate_fire_intensity(frame[y:y+h, x:x+w])
                    
                    best_fire = {
                        "type": "fire",
                        "subtype": "flame",
                        "confidence": confidence,
                        "bbox": [x, y, w, h],
                        "fire_intensity": intensity,
                        "area": area,
                        "estimated_temperature": min(200 + intensity * 600, 1000)
                    }
            
            return best_fire
            
        except Exception as e:
            logger.error(f"火焰检测处理异常: {e}")
            return None
    
    def _analyze_fire_features(self, contour: np.ndarray, frame: np.ndarray, hsv: np.ndarray) -> float:
        """分析火焰特征"""
        try:
            # 获取轮廓属性
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)
            
            # 1. 形状特征（火焰通常不规则）
            hull = cv2.convexHull(contour)
            hull_area = cv2.contourArea(hull)
            solidity = area / max(hull_area, 1)
            shape_score = 1.0 - solidity  # 火焰形状不规则
            
            # 2. 纵横比特征（火焰通常较高）
            aspect_ratio = h / max(w, 1)
            aspect_score = min(aspect_ratio / 2.0, 1.0)
            
            # 3. 颜色特征分析
            roi_hsv = hsv[y:y+h, x:x+w]
            color_score = self._analyze_fire_colors(roi_hsv)
            
            # 4. 亮度特征（火焰通常较亮）
            roi_gray = cv2.cvtColor(frame[y:y+h, x:x+w], cv2.COLOR_BGR2GRAY)
            brightness = np.mean(roi_gray) / 255.0
            brightness_score = min(brightness * 1.5, 1.0)
            
            # 综合评分
            confidence = (
                shape_score * 0.2 +
                aspect_score * 0.2 +
                color_score * 0.4 +
                brightness_score * 0.2
            )
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"火焰特征分析异常: {e}")
            return 0.0
    
    def _analyze_fire_colors(self, hsv_roi: np.ndarray) -> float:
        """分析火焰颜色特征"""
        try:
            if hsv_roi.size == 0:
                return 0.0
            
            total_pixels = hsv_roi.shape[0] * hsv_roi.shape[1]
            fire_pixels = 0
            
            for lower, upper in self.fire_color_ranges:
                lower = np.array(lower, dtype=np.uint8)
                upper = np.array(upper, dtype=np.uint8)
                mask = cv2.inRange(hsv_roi, lower, upper)
                fire_pixels += np.count_nonzero(mask)
            
            color_ratio = fire_pixels / max(total_pixels, 1)
            return min(color_ratio * 2.0, 1.0)
            
        except Exception as e:
            logger.error(f"颜色分析异常: {e}")
            return 0.0
    
    def _estimate_fire_intensity(self, fire_region: np.ndarray) -> str:
        """估算火焰强度"""
        try:
            if fire_region.size == 0:
                return "low"
            
            # 基于亮度和饱和度估算强度
            hsv = cv2.cvtColor(fire_region, cv2.COLOR_BGR2HSV)
            
            # 平均亮度
            avg_brightness = np.mean(hsv[:, :, 2])
            
            # 平均饱和度
            avg_saturation = np.mean(hsv[:, :, 1])
            
            # 综合评估
            intensity_score = (avg_brightness + avg_saturation) / 2
            
            if intensity_score > 200:
                return "high"
            elif intensity_score > 120:
                return "medium"
            else:
                return "low"
                
        except Exception as e:
            logger.error(f"强度估算异常: {e}")
            return "unknown"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取检测器统计信息"""
        return {
            "detector_type": "fire_detection",
            "confidence_threshold": self.confidence_threshold,
            "cooldown_period": self.cooldown_period,
            "color_ranges_count": len(self.fire_color_ranges),
            "last_detection_time": self.last_detection_time
        }