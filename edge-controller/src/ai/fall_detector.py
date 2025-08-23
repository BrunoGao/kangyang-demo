#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
跌倒检测算法 - 边缘控制器版本
优化用于边缘设备的轻量级跌倒检测
"""

import cv2
import numpy as np
import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)

class FallDetector:
    """轻量级跌倒检测器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化跌倒检测器
        
        Args:
            config: 检测配置参数
        """
        self.config = config or {}
        
        # 检测参数
        self.confidence_threshold = self.config.get("confidence_threshold", 0.8)
        self.min_fall_duration = self.config.get("min_fall_duration", 3.0)  # 最小跌倒持续时间
        self.cooldown_period = self.config.get("cooldown_period", 30)  # 冷却期
        
        # 状态跟踪
        self.fall_candidates = {}  # {person_id: {"start_time": time, "bbox": [x,y,w,h]}}
        self.last_alert_times = {}  # 防止重复告警
        
        # 背景减除器
        self.background_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True,
            varThreshold=50
        )
        
        # 人体级联分类器（如果可用）
        try:
            self.person_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_fullbody.xml'
            )
        except:
            self.person_cascade = None
            logger.warning("人体级联分类器加载失败，使用备用检测方法")
        
        logger.info("跌倒检测器初始化完成")
    
    def detect(self, frame: np.ndarray, timestamp: float, frame_number: int) -> Optional[Dict[str, Any]]:
        """
        检测跌倒事件
        
        Args:
            frame: 输入图像帧
            timestamp: 时间戳
            frame_number: 帧号
            
        Returns:
            检测结果，如果检测到跌倒返回事件信息，否则返回None
        """
        try:
            # 预处理
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            height, width = gray.shape
            
            # 运动检测
            fg_mask = self.background_subtractor.apply(frame)
            
            # 形态学操作清理噪声
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            
            # 寻找轮廓
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # 分析轮廓
            fall_detected = False
            best_candidate = None
            max_confidence = 0
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 1000:  # 过滤小目标
                    continue
                
                # 获取边界框
                x, y, w, h = cv2.boundingRect(contour)
                
                # 跌倒特征分析
                confidence = self._analyze_fall_features(contour, x, y, w, h, width, height)
                
                if confidence > self.confidence_threshold and confidence > max_confidence:
                    max_confidence = confidence
                    best_candidate = {
                        "bbox": [x, y, w, h],
                        "confidence": confidence,
                        "contour_area": area
                    }
            
            # 处理最佳候选
            if best_candidate:
                result = self._process_fall_candidate(best_candidate, timestamp, frame_number)
                if result:
                    return result
            
            # 清理过期的跌倒候选
            self._cleanup_expired_candidates(timestamp)
            
            return None
            
        except Exception as e:
            logger.error(f"跌倒检测异常: {e}")
            return None
    
    def _analyze_fall_features(self, contour: np.ndarray, x: int, y: int, w: int, h: int, 
                              frame_width: int, frame_height: int) -> float:
        """分析跌倒特征"""
        try:
            # 1. 纵横比分析（跌倒时人体变宽变矮）
            aspect_ratio = w / max(h, 1)
            aspect_score = min(aspect_ratio / 2.0, 1.0)  # 理想纵横比约为2:1
            
            # 2. 位置分析（跌倒通常发生在地面附近）
            ground_position = (y + h) / frame_height
            position_score = min(ground_position, 1.0)
            
            # 3. 面积分析（跌倒时人体接触地面面积增大）
            area_ratio = (w * h) / (frame_width * frame_height)
            area_score = min(area_ratio * 10, 1.0)
            
            # 4. 轮廓紧密度（跌倒时轮廓更分散）
            contour_area = cv2.contourArea(contour)
            bbox_area = w * h
            solidity = contour_area / max(bbox_area, 1)
            solidity_score = 1.0 - solidity  # 跌倒时紧密度降低
            
            # 综合评分
            confidence = (
                aspect_score * 0.3 +
                position_score * 0.3 +
                area_score * 0.2 +
                solidity_score * 0.2
            )
            
            return min(confidence, 1.0)
            
        except Exception as e:
            logger.error(f"特征分析异常: {e}")
            return 0.0
    
    def _process_fall_candidate(self, candidate: Dict[str, Any], timestamp: float, 
                               frame_number: int) -> Optional[Dict[str, Any]]:
        """处理跌倒候选"""
        try:
            # 生成人员ID（简化版，实际可以用目标跟踪）
            x, y, w, h = candidate["bbox"]
            person_id = f"person_{x//100}_{y//100}"  # 简单的区域划分
            
            current_time = timestamp
            
            # 检查冷却期
            if person_id in self.last_alert_times:
                if current_time - self.last_alert_times[person_id] < self.cooldown_period:
                    return None
            
            # 跟踪跌倒候选
            if person_id not in self.fall_candidates:
                # 新的跌倒候选
                self.fall_candidates[person_id] = {
                    "start_time": current_time,
                    "bbox": candidate["bbox"],
                    "max_confidence": candidate["confidence"],
                    "frame_number": frame_number
                }
                logger.debug(f"新跌倒候选: {person_id}")
                return None
            else:
                # 持续的跌倒候选
                fall_info = self.fall_candidates[person_id]
                duration = current_time - fall_info["start_time"]
                
                # 更新最高置信度
                if candidate["confidence"] > fall_info["max_confidence"]:
                    fall_info["max_confidence"] = candidate["confidence"]
                    fall_info["bbox"] = candidate["bbox"]
                
                # 检查是否满足最小持续时间
                if duration >= self.min_fall_duration:
                    # 确认跌倒事件
                    self.last_alert_times[person_id] = current_time
                    
                    # 清理候选
                    del self.fall_candidates[person_id]
                    
                    # 确定跌倒类型
                    fall_type = self._determine_fall_type(fall_info["bbox"])
                    
                    return {
                        "type": "fall",
                        "subtype": fall_type,
                        "confidence": fall_info["max_confidence"],
                        "bbox": fall_info["bbox"],
                        "timestamp": current_time,
                        "frame_number": frame_number,
                        "duration": duration,
                        "person_id": person_id,
                        "severity": "HIGH" if fall_info["max_confidence"] > 0.9 else "MEDIUM"
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"处理跌倒候选异常: {e}")
            return None
    
    def _determine_fall_type(self, bbox: List[int]) -> str:
        """确定跌倒类型"""
        x, y, w, h = bbox
        aspect_ratio = w / max(h, 1)
        
        if aspect_ratio > 2.5:
            return "horizontal_fall"  # 水平跌倒
        elif aspect_ratio > 1.8:
            return "side_fall"        # 侧向跌倒
        else:
            return "sitting_fall"     # 坐姿跌倒
    
    def _cleanup_expired_candidates(self, current_time: float):
        """清理过期的跌倒候选"""
        try:
            expired_ids = []
            for person_id, fall_info in self.fall_candidates.items():
                if current_time - fall_info["start_time"] > 10.0:  # 10秒超时
                    expired_ids.append(person_id)
            
            for person_id in expired_ids:
                del self.fall_candidates[person_id]
                logger.debug(f"清理过期跌倒候选: {person_id}")
                
        except Exception as e:
            logger.error(f"清理过期候选异常: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取检测器统计信息"""
        return {
            "detector_type": "fall_detection",
            "confidence_threshold": self.confidence_threshold,
            "min_fall_duration": self.min_fall_duration,
            "cooldown_period": self.cooldown_period,
            "active_candidates": len(self.fall_candidates),
            "tracked_persons": len(self.last_alert_times)
        }