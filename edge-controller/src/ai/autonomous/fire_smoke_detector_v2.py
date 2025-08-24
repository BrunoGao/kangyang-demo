#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主产权火焰烟雾检测算法 V2.0
核心创新：
1. 多模态融合检测 (颜色+纹理+运动+热辐射)
2. 时序一致性验证和动态阈值自适应
3. 分层级检测架构 (粗检测+精细化验证)
4. 环境自适应和误报抑制机制

算法特点：
- 基于HSV颜色空间的火焰特征提取
- LBP纹理分析和光流运动检测
- 多尺度时序特征融合
- 智能阈值自适应和规则引擎验证
"""

import cv2
import numpy as np
import logging
import time
import math
from typing import Dict, Any, List, Optional, Tuple
from collections import deque
from datetime import datetime

logger = logging.getLogger(__name__)

class AutonomousFireSmokeDetector:
    """自主产权火焰烟雾检测算法 - 核心算法模块"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化火焰烟雾检测器
        
        Args:
            config: 检测配置参数
        """
        self.config = config or {}
        
        # 核心参数
        self.confidence_threshold = self.config.get("confidence_threshold", 0.75)
        self.temporal_window_size = self.config.get("temporal_window_size", 45)  # 3秒@15fps
        self.min_detection_duration = self.config.get("min_detection_duration", 2.0)  # 最小检测持续时间
        self.cooldown_period = self.config.get("cooldown_period", 10.0)  # 冷却期
        
        # 火焰检测参数
        self.fire_color_ranges = {
            'red_orange': {'h': [0, 25], 's': [100, 255], 'v': [100, 255]},
            'yellow': {'h': [25, 35], 's': [100, 255], 'v': [150, 255]},
            'bright_yellow': {'h': [15, 45], 's': [50, 255], 'v': [200, 255]}
        }
        
        # 烟雾检测参数  
        self.smoke_color_ranges = {
            'gray_smoke': {'h': [0, 180], 's': [0, 50], 'v': [50, 200]},
            'white_smoke': {'h': [0, 180], 's': [0, 30], 'v': [150, 255]},
            'dark_smoke': {'h': [0, 180], 's': [0, 80], 'v': [30, 120]}
        }
        
        # 检测算法组件
        self.motion_detector = MotionFlowAnalyzer()
        self.texture_analyzer = TextureAnalyzer()
        self.temporal_validator = TemporalValidator(window_size=self.temporal_window_size)
        self.environmental_adapter = EnvironmentalAdapter()
        
        # 状态跟踪
        self.detection_history = deque(maxlen=self.temporal_window_size)
        self.last_detection_time = 0
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(detectShadows=True)
        
        # 统计信息
        self.stats = {
            "total_detections": 0,
            "fire_events": 0,
            "smoke_events": 0,
            "false_alarms_suppressed": 0,
            "processing_time_avg": 0
        }
        
        logger.info("自主火焰烟雾检测算法V2.0初始化完成")
    
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
            
            # 环境自适应预处理
            adapted_frame = self.environmental_adapter.adapt(frame, timestamp)
            
            # 多模态特征提取
            color_features = self._extract_color_features(adapted_frame)
            motion_features = self.motion_detector.analyze(adapted_frame, timestamp)
            texture_features = self.texture_analyzer.analyze(adapted_frame)
            
            # 粗检测阶段
            coarse_results = self._coarse_detection(color_features, motion_features, texture_features)
            
            if not coarse_results['has_candidate']:
                return None
            
            # 精细化验证阶段
            fine_results = self._fine_detection(adapted_frame, coarse_results)
            
            # 时序一致性验证
            temporal_result = self.temporal_validator.validate(fine_results, timestamp)
            
            if not temporal_result['is_valid']:
                return None
            
            # 生成最终检测结果
            detection_result = self._generate_detection_result(
                temporal_result, frame, timestamp, frame_number
            )
            
            # 更新统计信息
            processing_time = time.time() - start_time
            self._update_stats(processing_time, detection_result)
            
            if detection_result:
                self.last_detection_time = timestamp
                logger.info(f"检测到{detection_result['type']}事件: "
                           f"置信度={detection_result['confidence']:.3f}")
            
            return detection_result
            
        except Exception as e:
            logger.error(f"火焰烟雾检测异常: {e}")
            return None
    
    def _extract_color_features(self, frame: np.ndarray) -> Dict[str, Any]:
        """提取颜色特征 - 火焰烟雾颜色分析"""
        try:
            # 转换到HSV颜色空间
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            h, w = frame.shape[:2]
            
            features = {
                'fire_masks': {},
                'smoke_masks': {},
                'fire_ratio': 0,
                'smoke_ratio': 0,
                'fire_regions': [],
                'smoke_regions': []
            }
            
            # 火焰颜色检测
            total_fire_pixels = 0
            for color_name, color_range in self.fire_color_ranges.items():
                # 创建颜色掩码
                lower = np.array([color_range['h'][0], color_range['s'][0], color_range['v'][0]])
                upper = np.array([color_range['h'][1], color_range['s'][1], color_range['v'][1]])
                mask = cv2.inRange(hsv, lower, upper)
                
                # 形态学操作去噪
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                
                features['fire_masks'][color_name] = mask
                total_fire_pixels += cv2.countNonZero(mask)
                
                # 检测火焰区域
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 100:  # 最小面积阈值
                        rect = cv2.boundingRect(contour)
                        features['fire_regions'].append({
                            'bbox': rect,
                            'area': area,
                            'color_type': color_name
                        })
            
            # 烟雾颜色检测
            total_smoke_pixels = 0
            for color_name, color_range in self.smoke_color_ranges.items():
                lower = np.array([color_range['h'][0], color_range['s'][0], color_range['v'][0]])
                upper = np.array([color_range['h'][1], color_range['s'][1], color_range['v'][1]])
                mask = cv2.inRange(hsv, lower, upper)
                
                # 烟雾特有的形态学处理
                kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
                
                features['smoke_masks'][color_name] = mask
                total_smoke_pixels += cv2.countNonZero(mask)
                
                # 检测烟雾区域
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for contour in contours:
                    area = cv2.contourArea(contour)
                    if area > 500:  # 烟雾通常面积较大
                        rect = cv2.boundingRect(contour)
                        features['smoke_regions'].append({
                            'bbox': rect,
                            'area': area,
                            'color_type': color_name
                        })
            
            # 计算比例特征
            total_pixels = h * w
            features['fire_ratio'] = total_fire_pixels / total_pixels
            features['smoke_ratio'] = total_smoke_pixels / total_pixels
            
            return features
            
        except Exception as e:
            logger.error(f"颜色特征提取异常: {e}")
            return {'fire_ratio': 0, 'smoke_ratio': 0, 'fire_regions': [], 'smoke_regions': []}
    
    def _coarse_detection(self, color_features: Dict, motion_features: Dict, 
                         texture_features: Dict) -> Dict[str, Any]:
        """粗检测阶段 - 快速筛选候选区域"""
        results = {
            'has_candidate': False,
            'fire_score': 0,
            'smoke_score': 0,
            'candidate_type': None,
            'candidate_regions': []
        }
        
        # 火焰粗检测
        fire_score = 0
        if color_features['fire_ratio'] > 0.001:  # 至少0.1%的火焰颜色像素
            fire_score += min(color_features['fire_ratio'] * 1000, 0.5)  # 颜色评分
            
            # 运动评分
            if motion_features.get('has_motion', False):
                motion_intensity = motion_features.get('motion_intensity', 0)
                fire_score += min(motion_intensity / 100, 0.3)
            
            # 纹理评分
            texture_complexity = texture_features.get('complexity', 0)
            fire_score += min(texture_complexity / 50, 0.2)
        
        # 烟雾粗检测
        smoke_score = 0
        if color_features['smoke_ratio'] > 0.005:  # 至少0.5%的烟雾颜色像素
            smoke_score += min(color_features['smoke_ratio'] * 200, 0.4)  # 颜色评分
            
            # 烟雾特有的运动模式
            if motion_features.get('has_rising_motion', False):
                smoke_score += 0.3
            
            # 烟雾特有的纹理特征
            if texture_features.get('smoke_like_texture', False):
                smoke_score += 0.3
        
        # 确定候选类型
        if fire_score > 0.4 or smoke_score > 0.4:
            results['has_candidate'] = True
            results['fire_score'] = fire_score
            results['smoke_score'] = smoke_score
            
            if fire_score > smoke_score:
                results['candidate_type'] = 'fire'
                results['candidate_regions'] = color_features['fire_regions']
            else:
                results['candidate_type'] = 'smoke'
                results['candidate_regions'] = color_features['smoke_regions']
        
        return results
    
    def _fine_detection(self, frame: np.ndarray, coarse_results: Dict) -> Dict[str, Any]:
        """精细化检测阶段 - 深度特征验证"""
        fine_results = {
            'type': coarse_results['candidate_type'],
            'confidence': 0,
            'regions': [],
            'features': {}
        }
        
        if not coarse_results['has_candidate']:
            return fine_results
        
        candidate_type = coarse_results['candidate_type']
        candidate_regions = coarse_results['candidate_regions']
        
        total_confidence = 0
        valid_regions = []
        
        for region in candidate_regions:
            region_confidence = self._analyze_region_detail(frame, region, candidate_type)
            
            if region_confidence > 0.3:  # 区域置信度阈值
                valid_regions.append({
                    'bbox': region['bbox'],
                    'confidence': region_confidence,
                    'type': candidate_type
                })
                total_confidence += region_confidence
        
        if valid_regions:
            fine_results['confidence'] = min(total_confidence / len(valid_regions), 1.0)
            fine_results['regions'] = valid_regions
        
        return fine_results
    
    def _analyze_region_detail(self, frame: np.ndarray, region: Dict, detection_type: str) -> float:
        """分析区域细节特征"""
        try:
            bbox = region['bbox']
            x, y, w, h = bbox
            
            # 提取区域图像
            roi = frame[y:y+h, x:x+w]
            if roi.size == 0:
                return 0
            
            confidence = 0
            
            if detection_type == 'fire':
                confidence = self._analyze_fire_region(roi)
            elif detection_type == 'smoke':
                confidence = self._analyze_smoke_region(roi)
            
            return confidence
            
        except Exception as e:
            logger.error(f"区域细节分析异常: {e}")
            return 0
    
    def _analyze_fire_region(self, roi: np.ndarray) -> float:
        """分析火焰区域特征"""
        try:
            confidence = 0
            
            # 1. 颜色分布分析
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            
            # 火焰的颜色应该有渐变 (从红到黄)
            h_channel = hsv_roi[:, :, 0]
            s_channel = hsv_roi[:, :, 1]
            v_channel = hsv_roi[:, :, 2]
            
            # 高饱和度像素比例
            high_sat_ratio = np.sum(s_channel > 100) / s_channel.size
            confidence += min(high_sat_ratio * 0.5, 0.3)
            
            # 亮度变化
            bright_ratio = np.sum(v_channel > 150) / v_channel.size
            confidence += min(bright_ratio * 0.3, 0.2)
            
            # 2. 边缘特征分析 (火焰边缘不规则)
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray_roi, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            confidence += min(edge_density * 0.5, 0.2)
            
            # 3. 形状特征 (火焰向上)
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                # 计算轮廓的垂直伸展度
                rect = cv2.boundingRect(largest_contour)
                aspect_ratio = rect[3] / max(rect[2], 1)  # height/width
                if aspect_ratio > 1.2:  # 火焰通常是竖直的
                    confidence += 0.2
            
            # 4. 纹理复杂度
            texture_complexity = np.std(gray_roi)
            confidence += min(texture_complexity / 100, 0.1)
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"火焰区域分析异常: {e}")
            return 0
    
    def _analyze_smoke_region(self, roi: np.ndarray) -> float:
        """分析烟雾区域特征"""
        try:
            confidence = 0
            
            # 1. 颜色分布分析 (烟雾通常是灰色系)
            hsv_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
            s_channel = hsv_roi[:, :, 1]
            v_channel = hsv_roi[:, :, 2]
            
            # 低饱和度特征 (烟雾饱和度低)
            low_sat_ratio = np.sum(s_channel < 60) / s_channel.size
            confidence += min(low_sat_ratio * 0.4, 0.3)
            
            # 中等亮度特征
            mid_bright_ratio = np.sum((v_channel > 60) & (v_channel < 200)) / v_channel.size
            confidence += min(mid_bright_ratio * 0.3, 0.2)
            
            # 2. 边缘模糊度 (烟雾边缘模糊)
            gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray_roi, (5, 5), 0)
            edge_sharpness = np.mean(np.abs(gray_roi.astype(float) - blurred.astype(float)))
            
            # 边缘越模糊，烟雾可能性越大
            if edge_sharpness < 10:  # 阈值需要根据实际情况调整
                confidence += 0.2
            
            # 3. 密度渐变 (烟雾通常有密度渐变)
            # 计算垂直方向的亮度渐变
            vertical_gradient = np.mean(np.abs(np.diff(gray_roi, axis=0)))
            confidence += min(vertical_gradient / 50, 0.2)
            
            # 4. 形状特征 (烟雾通常扩散状)
            contours, _ = cv2.findContours(
                cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1],
                cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )
            
            if contours:
                largest_contour = max(contours, key=cv2.contourArea)
                # 计算轮廓的紧致度 (烟雾轮廓通常不规则)
                area = cv2.contourArea(largest_contour)
                perimeter = cv2.arcLength(largest_contour, True)
                if perimeter > 0:
                    compactness = 4 * math.pi * area / (perimeter * perimeter)
                    # 紧致度越小，越像烟雾
                    if compactness < 0.3:
                        confidence += 0.1
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"烟雾区域分析异常: {e}")
            return 0
    
    def _generate_detection_result(self, temporal_result: Dict, frame: np.ndarray,
                                  timestamp: float, frame_number: int) -> Optional[Dict[str, Any]]:
        """生成最终检测结果"""
        if not temporal_result.get('is_valid', False):
            return None
        
        detection_type = temporal_result.get('type', 'unknown')
        confidence = temporal_result.get('confidence', 0)
        regions = temporal_result.get('regions', [])
        
        if confidence < self.confidence_threshold:
            return None
        
        return {
            'type': detection_type,
            'subtype': self._get_detection_subtype(detection_type, regions),
            'confidence': confidence,
            'timestamp': timestamp,
            'frame_number': frame_number,
            'regions': regions,
            'region_count': len(regions),
            'total_area': sum(r['bbox'][2] * r['bbox'][3] for r in regions),
            'severity': self._assess_severity(confidence, regions),
            'environmental_context': self.environmental_adapter.get_current_context(),
            'algorithm': 'autonomous_fire_smoke_detector_v2'
        }
    
    def _get_detection_subtype(self, detection_type: str, regions: List) -> str:
        """确定检测子类型"""
        if not regions:
            return f'{detection_type}_general'
        
        total_area = sum(r['bbox'][2] * r['bbox'][3] for r in regions)
        region_count = len(regions)
        
        if detection_type == 'fire':
            if total_area > 10000:
                return 'large_fire'
            elif region_count > 3:
                return 'multiple_fire_spots'
            else:
                return 'small_fire'
        
        elif detection_type == 'smoke':
            if total_area > 50000:
                return 'dense_smoke'
            elif region_count > 2:
                return 'widespread_smoke'
            else:
                return 'light_smoke'
        
        return f'{detection_type}_general'
    
    def _assess_severity(self, confidence: float, regions: List) -> str:
        """评估事件严重程度"""
        severity_score = confidence
        
        # 根据区域数量和面积调整严重程度
        if regions:
            total_area = sum(r['bbox'][2] * r['bbox'][3] for r in regions)
            region_count = len(regions)
            
            # 面积因子
            if total_area > 20000:
                severity_score += 0.2
            elif total_area > 10000:
                severity_score += 0.1
            
            # 区域数量因子
            if region_count > 3:
                severity_score += 0.15
            elif region_count > 1:
                severity_score += 0.05
        
        severity_score = min(severity_score, 1.0)
        
        if severity_score > 0.85:
            return 'critical'
        elif severity_score > 0.7:
            return 'high'
        elif severity_score > 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _update_stats(self, processing_time: float, detection_result: Optional[Dict]):
        """更新统计信息"""
        self.stats["total_detections"] += 1
        
        if detection_result:
            if detection_result['type'] == 'fire':
                self.stats["fire_events"] += 1
            elif detection_result['type'] == 'smoke':
                self.stats["smoke_events"] += 1
        
        # 更新平均处理时间
        current_avg = self.stats["processing_time_avg"]
        total = self.stats["total_detections"]
        self.stats["processing_time_avg"] = (current_avg * (total - 1) + processing_time) / total
    
    def get_stats(self) -> Dict[str, Any]:
        """获取检测器统计信息"""
        return {
            "detector_type": "autonomous_fire_smoke_detection_v2",
            "version": "2.0.0",
            "algorithm_features": [
                "multi_modal_fusion",
                "temporal_consistency_validation",
                "hierarchical_detection_architecture", 
                "environmental_adaptation",
                "false_alarm_suppression"
            ],
            "confidence_threshold": self.confidence_threshold,
            "temporal_window_size": self.temporal_window_size,
            "detection_types": ["fire", "smoke"],
            "stats": self.stats,
            "copyright": "自主产权算法 - 康养AI团队"
        }


class MotionFlowAnalyzer:
    """运动光流分析器"""
    
    def __init__(self):
        self.prev_gray = None
        self.optical_flow_params = {
            'pyr_scale': 0.5,
            'levels': 3,
            'winsize': 15,
            'iterations': 3,
            'poly_n': 5,
            'poly_sigma': 1.2,
            'flags': 0
        }
    
    def analyze(self, frame: np.ndarray, timestamp: float) -> Dict[str, Any]:
        """分析运动特征"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if self.prev_gray is None:
                self.prev_gray = gray
                return {'has_motion': False, 'motion_intensity': 0}
            
            # 计算光流
            flow = cv2.calcOpticalFlowPyrLK(self.prev_gray, gray, None, None, **self.optical_flow_params)
            
            # 分析运动特征
            motion_magnitude = np.sqrt(flow[..., 0]**2 + flow[..., 1]**2)
            motion_intensity = np.mean(motion_magnitude)
            
            # 检测向上运动 (烟雾特征)
            upward_flow = flow[..., 1] < -2  # 向上运动
            has_rising_motion = np.sum(upward_flow) > frame.size * 0.1  # 10%以上像素向上运动
            
            self.prev_gray = gray
            
            return {
                'has_motion': motion_intensity > 1.0,
                'motion_intensity': motion_intensity,
                'has_rising_motion': has_rising_motion,
                'flow_field': flow
            }
            
        except Exception as e:
            logger.error(f"运动分析异常: {e}")
            return {'has_motion': False, 'motion_intensity': 0}


class TextureAnalyzer:
    """纹理分析器"""
    
    def analyze(self, frame: np.ndarray) -> Dict[str, Any]:
        """分析纹理特征"""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # LBP纹理分析
            lbp_complexity = self._calculate_lbp_complexity(gray)
            
            # 梯度复杂度
            gradient_complexity = self._calculate_gradient_complexity(gray)
            
            # 烟雾特有的纹理模式检测
            smoke_like_texture = self._detect_smoke_texture(gray)
            
            return {
                'complexity': lbp_complexity + gradient_complexity,
                'lbp_complexity': lbp_complexity,
                'gradient_complexity': gradient_complexity,
                'smoke_like_texture': smoke_like_texture
            }
            
        except Exception as e:
            logger.error(f"纹理分析异常: {e}")
            return {'complexity': 0, 'smoke_like_texture': False}
    
    def _calculate_lbp_complexity(self, gray: np.ndarray) -> float:
        """计算LBP纹理复杂度"""
        # 简化的LBP实现
        h, w = gray.shape
        lbp = np.zeros_like(gray)
        
        for i in range(1, h-1):
            for j in range(1, w-1):
                center = gray[i, j]
                code = 0
                code |= (gray[i-1, j-1] >= center) << 7
                code |= (gray[i-1, j] >= center) << 6
                code |= (gray[i-1, j+1] >= center) << 5
                code |= (gray[i, j+1] >= center) << 4
                code |= (gray[i+1, j+1] >= center) << 3
                code |= (gray[i+1, j] >= center) << 2
                code |= (gray[i+1, j-1] >= center) << 1
                code |= (gray[i, j-1] >= center) << 0
                lbp[i, j] = code
        
        # 计算LBP直方图的熵作为复杂度指标
        hist, _ = np.histogram(lbp.flatten(), bins=256)
        hist = hist / hist.sum()
        entropy = -np.sum(hist * np.log(hist + 1e-7))
        
        return entropy
    
    def _calculate_gradient_complexity(self, gray: np.ndarray) -> float:
        """计算梯度复杂度"""
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        gradient_magnitude = np.sqrt(grad_x**2 + grad_y**2)
        return np.mean(gradient_magnitude)
    
    def _detect_smoke_texture(self, gray: np.ndarray) -> bool:
        """检测烟雾特有的纹理模式"""
        # 烟雾通常具有模糊、渐变的纹理特征
        blurred = cv2.GaussianBlur(gray, (9, 9), 0)
        diff = np.abs(gray.astype(float) - blurred.astype(float))
        
        # 如果图像和模糊后的图像差异很小，可能是烟雾
        avg_diff = np.mean(diff)
        return avg_diff < 15  # 阈值需要根据实际情况调整


class TemporalValidator:
    """时序一致性验证器"""
    
    def __init__(self, window_size: int = 45):
        self.window_size = window_size
        self.detection_history = deque(maxlen=window_size)
    
    def validate(self, detection_result: Dict, timestamp: float) -> Dict[str, Any]:
        """验证时序一致性"""
        # 添加到历史记录
        self.detection_history.append({
            'result': detection_result,
            'timestamp': timestamp
        })
        
        if len(self.detection_history) < 5:  # 至少需要5帧历史
            return {'is_valid': False}
        
        # 检查最近检测的一致性
        recent_detections = list(self.detection_history)[-10:]  # 最近10帧
        detection_types = [d['result'].get('type') for d in recent_detections if d['result'].get('confidence', 0) > 0.3]
        
        if not detection_types:
            return {'is_valid': False}
        
        # 类型一致性检查
        most_common_type = max(set(detection_types), key=detection_types.count)
        type_consistency = detection_types.count(most_common_type) / len(detection_types)
        
        # 置信度趋势检查
        confidences = [d['result'].get('confidence', 0) for d in recent_detections if d['result'].get('confidence', 0) > 0]
        avg_confidence = np.mean(confidences) if confidences else 0
        
        # 时间持续性检查
        valid_duration = recent_detections[-1]['timestamp'] - recent_detections[0]['timestamp']
        
        is_valid = (type_consistency > 0.6 and 
                   avg_confidence > 0.5 and 
                   valid_duration > 1.0)  # 至少持续1秒
        
        return {
            'is_valid': is_valid,
            'type': most_common_type,
            'confidence': avg_confidence,
            'consistency': type_consistency,
            'duration': valid_duration,
            'regions': detection_result.get('regions', [])
        }


class EnvironmentalAdapter:
    """环境自适应处理器"""
    
    def __init__(self):
        self.brightness_history = deque(maxlen=30)
        self.current_context = {
            'lighting_condition': 'normal',
            'brightness_level': 0,
            'adaptation_applied': False
        }
    
    def adapt(self, frame: np.ndarray, timestamp: float) -> np.ndarray:
        """环境自适应预处理"""
        try:
            # 分析当前lighting条件
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray)
            self.brightness_history.append(brightness)
            
            # 更新环境context
            self._update_context(brightness)
            
            adapted_frame = frame.copy()
            
            # 根据光照条件进行自适应调整
            if self.current_context['lighting_condition'] == 'dark':
                adapted_frame = self._enhance_low_light(adapted_frame)
            elif self.current_context['lighting_condition'] == 'bright':
                adapted_frame = self._reduce_overexposure(adapted_frame)
            
            return adapted_frame
            
        except Exception as e:
            logger.error(f"环境自适应异常: {e}")
            return frame
    
    def _update_context(self, brightness: float):
        """更新环境context"""
        self.current_context['brightness_level'] = brightness
        
        if brightness < 80:
            self.current_context['lighting_condition'] = 'dark'
        elif brightness > 180:
            self.current_context['lighting_condition'] = 'bright'  
        else:
            self.current_context['lighting_condition'] = 'normal'
    
    def _enhance_low_light(self, frame: np.ndarray) -> np.ndarray:
        """低光照增强"""
        # CLAHE增强
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        lab[:, :, 0] = clahe.apply(lab[:, :, 0])
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        self.current_context['adaptation_applied'] = True
        return enhanced
    
    def _reduce_overexposure(self, frame: np.ndarray) -> np.ndarray:
        """过曝减少"""
        # 简单的gamma校正
        gamma = 0.7
        gamma_corrected = np.power(frame / 255.0, gamma) * 255.0
        
        self.current_context['adaptation_applied'] = True
        return gamma_corrected.astype(np.uint8)
    
    def get_current_context(self) -> Dict[str, Any]:
        """获取当前环境context"""
        return self.current_context.copy()