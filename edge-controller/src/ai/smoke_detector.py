#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
烟雾检测算法 - 边缘控制器版本
基于颜色、纹理和运动特征的轻量级烟雾检测
"""

import cv2
import numpy as np
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)

class SmokeDetector:
    """轻量级烟雾检测器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化烟雾检测器
        
        Args:
            config: 检测配置参数
        """
        self.config = config or {}
        
        # 检测参数
        self.confidence_threshold = self.config.get("confidence_threshold", 0.80)
        self.cooldown_period = self.config.get("cooldown_period", 15)
        
        # 烟雾颜色范围 (HSV)
        self.smoke_color_ranges = [
            # 白色烟雾
            ([0, 0, 200], [180, 30, 255]),
            # 灰色烟雾
            ([0, 0, 100], [180, 50, 200]),
            # 黑色烟雾
            ([0, 0, 0], [180, 255, 100])
        ]
        
        # 状态跟踪
        self.last_detection_time = 0
        self.smoke_regions = []
        
        # 背景减除器
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True,
            varThreshold=20
        )
        
        # 用于纹理分析的参数
        self.lbp_radius = 1
        self.lbp_n_points = 8
        
        logger.info("烟雾检测器初始化完成")
    
    def detect(self, frame: np.ndarray, timestamp: float, frame_number: int) -> Dict[str, Any]:
        """
        检测烟雾事件 - 标准接口
        
        Args:
            frame: 输入图像帧
            timestamp: 时间戳
            frame_number: 帧号
            
        Returns:
            检测结果，如果检测到烟雾返回事件信息，否则返回None
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
        检测烟雾（与火焰检测器接口兼容）
        
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
            # 烟雾检测
            smoke_result = self._detect_smoke(frame)
            if smoke_result:
                results.append(smoke_result)
                self.last_detection_time = current_time
                
        except Exception as e:
            logger.error(f"烟雾检测异常: {e}")
        
        return results
    
    def _detect_smoke(self, frame: np.ndarray) -> Dict[str, Any]:
        """检测烟雾"""
        try:
            # 转换颜色空间
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 创建烟雾颜色掩码
            smoke_mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
            
            for lower, upper in self.smoke_color_ranges:
                lower = np.array(lower, dtype=np.uint8)
                upper = np.array(upper, dtype=np.uint8)
                color_mask = cv2.inRange(hsv, lower, upper)
                smoke_mask = cv2.bitwise_or(smoke_mask, color_mask)
            
            # 运动检测
            fg_mask = self.background_subtractor.apply(frame)
            
            # 结合颜色和运动
            combined_mask = cv2.bitwise_and(smoke_mask, fg_mask)
            
            # 形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
            combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
            
            # 寻找轮廓
            contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            best_smoke = None
            max_confidence = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 200:  # 过滤小区域
                    continue
                
                # 分析烟雾特征
                confidence = self._analyze_smoke_features(contour, frame, hsv, gray)
                
                if confidence > self.confidence_threshold and confidence > max_confidence:
                    max_confidence = confidence
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 分析烟雾属性
                    density = self._estimate_smoke_density(gray[y:y+h, x:x+w])
                    color_type = self._analyze_smoke_color(hsv[y:y+h, x:x+w])
                    
                    best_smoke = {
                        "type": "smoke",
                        "subtype": "dense_smoke" if density == "dense" else "light_smoke",
                        "confidence": confidence,
                        "bbox": [x, y, w, h],
                        "smoke_density": density,
                        "color_analysis": color_type,
                        "area": area
                    }
            
            return best_smoke
            
        except Exception as e:
            logger.error(f"烟雾检测处理异常: {e}")
            return None
    
    def _analyze_smoke_features(self, contour: np.ndarray, frame: np.ndarray, 
                               hsv: np.ndarray, gray: np.ndarray) -> float:
        """分析烟雾特征"""
        try:
            # 获取轮廓属性
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)
            
            # 1. 形状特征（烟雾通常形状不规则且扩散）
            perimeter = cv2.arcLength(contour, True)
            compactness = (perimeter * perimeter) / max(area, 1)
            shape_score = min(compactness / 50.0, 1.0)  # 烟雾轮廓通常较复杂
            
            # 2. 面积特征（烟雾通常占据较大面积）
            frame_area = frame.shape[0] * frame.shape[1]
            area_ratio = area / frame_area
            area_score = min(area_ratio * 20, 1.0)
            
            # 3. 颜色特征
            roi_hsv = hsv[y:y+h, x:x+w]
            color_score = self._analyze_smoke_color_features(roi_hsv)
            
            # 4. 纹理特征（烟雾通常纹理较模糊）
            roi_gray = gray[y:y+h, x:x+w]
            texture_score = self._analyze_smoke_texture(roi_gray)
            
            # 5. 位置特征（烟雾通常向上扩散）
            position_score = 1.0 - (y / max(frame.shape[0], 1))  # 越高得分越高
            
            # 综合评分
            confidence = (
                shape_score * 0.2 +
                area_score * 0.2 +
                color_score * 0.3 +
                texture_score * 0.2 +
                position_score * 0.1
            )
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"烟雾特征分析异常: {e}")
            return 0.0
    
    def _analyze_smoke_color_features(self, hsv_roi: np.ndarray) -> float:
        """分析烟雾颜色特征"""
        try:
            if hsv_roi.size == 0:
                return 0.0
            
            total_pixels = hsv_roi.shape[0] * hsv_roi.shape[1]
            smoke_pixels = 0
            
            for lower, upper in self.smoke_color_ranges:
                lower = np.array(lower, dtype=np.uint8)
                upper = np.array(upper, dtype=np.uint8)
                mask = cv2.inRange(hsv_roi, lower, upper)
                smoke_pixels += np.count_nonzero(mask)
            
            color_ratio = smoke_pixels / max(total_pixels, 1)
            return min(color_ratio * 1.5, 1.0)
            
        except Exception as e:
            logger.error(f"烟雾颜色分析异常: {e}")
            return 0.0
    
    def _analyze_smoke_texture(self, gray_roi: np.ndarray) -> float:
        """分析烟雾纹理特征"""
        try:
            if gray_roi.size == 0:
                return 0.0
            
            # 计算局部二值模式 (LBP) 的简化版本
            # 烟雾通常具有较低的纹理复杂度
            
            # 计算梯度
            grad_x = cv2.Sobel(gray_roi, cv2.CV_64F, 1, 0, ksize=3)
            grad_y = cv2.Sobel(gray_roi, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
            
            # 烟雾的梯度通常较小（模糊）
            avg_gradient = np.mean(gradient_magnitude)
            texture_score = 1.0 - min(avg_gradient / 100.0, 1.0)
            
            return texture_score
            
        except Exception as e:
            logger.error(f"纹理分析异常: {e}")
            return 0.0
    
    def _estimate_smoke_density(self, gray_roi: np.ndarray) -> str:
        """估算烟雾密度"""
        try:
            if gray_roi.size == 0:
                return "unknown"
            
            # 基于平均亮度和方差估算密度
            avg_intensity = np.mean(gray_roi)
            intensity_var = np.var(gray_roi)
            
            # 密集烟雾通常亮度较低且变化较小
            if avg_intensity < 80 and intensity_var < 500:
                return "dense"
            elif avg_intensity < 150 and intensity_var < 1000:
                return "medium"
            else:
                return "light"
                
        except Exception as e:
            logger.error(f"密度估算异常: {e}")
            return "unknown"
    
    def _analyze_smoke_color(self, hsv_roi: np.ndarray) -> str:
        """分析烟雾颜色类型"""
        try:
            if hsv_roi.size == 0:
                return "unknown"
            
            # 计算平均HSV值
            avg_hsv = np.mean(hsv_roi, axis=(0, 1))
            avg_v = avg_hsv[2]  # 亮度
            avg_s = avg_hsv[1]  # 饱和度
            
            # 根据亮度和饱和度判断颜色
            if avg_v > 200 and avg_s < 30:
                return "white"
            elif avg_v < 100:
                return "black"
            else:
                return "gray"
                
        except Exception as e:
            logger.error(f"颜色分析异常: {e}")
            return "unknown"
    
    def get_stats(self) -> Dict[str, Any]:
        """获取检测器统计信息"""
        return {
            "detector_type": "smoke_detection",
            "confidence_threshold": self.confidence_threshold,
            "cooldown_period": self.cooldown_period,
            "color_ranges_count": len(self.smoke_color_ranges),
            "last_detection_time": self.last_detection_time
        }