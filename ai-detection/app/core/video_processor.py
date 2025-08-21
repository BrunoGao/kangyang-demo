#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
真实视频处理器
支持上传视频的实时分析和检测
"""

import cv2
import numpy as np
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, AsyncGenerator
import tempfile
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class RealVideoProcessor:
    """真实视频处理器"""
    
    def __init__(self):
        """初始化视频处理器"""
        self.supported_formats = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']
        self.max_file_size = 500 * 1024 * 1024  # 500MB
        
        logger.info("真实视频处理器初始化完成")
    
    async def process_video_file(self, video_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理视频文件并进行检测分析
        
        Args:
            video_path: 视频文件路径
            config: 检测配置
            
        Returns:
            分析结果
        """
        try:
            # 验证文件
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"视频文件不存在: {video_path}")
            
            # 获取视频信息
            video_info = await self._get_video_info(video_path)
            
            # 执行检测分析
            detection_results = await self._analyze_video(video_path, config, video_info)
            
            return {
                'success': True,
                'video_info': video_info,
                'detection_results': detection_results,
                'config': config,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"视频处理失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _get_video_info(self, video_path: str) -> Dict[str, Any]:
        """获取视频基本信息"""
        cap = cv2.VideoCapture(video_path)
        
        try:
            if not cap.isOpened():
                raise ValueError("无法打开视频文件")
            
            # 获取视频属性
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = frame_count / fps if fps > 0 else 0
            
            # 获取文件大小
            file_size = os.path.getsize(video_path)
            
            video_info = {
                'filename': os.path.basename(video_path),
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'resolution': f"{width}x{height}",
                'duration_seconds': round(duration, 2),
                'fps': round(fps, 2),
                'total_frames': frame_count,
                'codec': 'Unknown'  # 可以通过其他方式获取
            }
            
            logger.info(f"视频信息: {video_info}")
            return video_info
            
        finally:
            cap.release()
    
    async def _analyze_video(self, video_path: str, config: Dict[str, Any], video_info: Dict[str, Any]) -> Dict[str, Any]:
        """分析视频内容"""
        detection_types = config.get('detection_types', ['fall'])
        confidence_threshold = config.get('confidence_threshold', 0.8)
        detection_mode = config.get('detection_mode', 'standard')
        
        # 初始化检测器
        detectors = {}
        if 'fall' in detection_types:
            detectors['fall'] = FallDetector(confidence_threshold)
        if 'fire' in detection_types:
            detectors['fire'] = FireDetector(confidence_threshold)
        if 'smoke' in detection_types:
            detectors['smoke'] = SmokeDetector(confidence_threshold)
        
        # 分析视频帧
        detections = []
        frame_analysis = []
        
        cap = cv2.VideoCapture(video_path)
        try:
            if not cap.isOpened():
                raise ValueError("无法打开视频文件进行分析")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # 确定采样间隔
            sample_interval = self._get_sample_interval(detection_mode, fps)
            
            frame_number = 0
            processed_frames = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 按间隔采样
                if frame_number % sample_interval == 0:
                    timestamp = frame_number / fps
                    
                    # 对当前帧进行检测
                    frame_detections = await self._detect_frame(frame, detectors, timestamp, frame_number)
                    
                    if frame_detections:
                        detections.extend(frame_detections)
                    
                    # 记录帧分析信息
                    frame_analysis.append({
                        'frame_number': frame_number,
                        'timestamp': timestamp,
                        'detections': len(frame_detections)
                    })
                    
                    processed_frames += 1
                
                frame_number += 1
                
                # 每处理100帧输出一次进度
                if frame_number % 100 == 0:
                    progress = (frame_number / frame_count) * 100
                    logger.info(f"处理进度: {progress:.1f}% ({frame_number}/{frame_count})")
            
            # 合并相近的检测事件
            merged_detections = self._merge_detections(detections)
            
            return {
                'detections': merged_detections,
                'frame_analysis': frame_analysis,
                'processed_frames': processed_frames,
                'total_frames': frame_count,
                'sample_interval': sample_interval,
                'detection_summary': {
                    'fall_events': len([d for d in merged_detections if d['type'] == 'fall']),
                    'fire_events': len([d for d in merged_detections if d['type'] == 'fire']),
                    'smoke_events': len([d for d in merged_detections if d['type'] == 'smoke']),
                    'total_events': len(merged_detections)
                }
            }
            
        finally:
            cap.release()
    
    def _get_sample_interval(self, detection_mode: str, fps: float) -> int:
        """根据检测模式获取采样间隔"""
        if detection_mode == 'high_accuracy':
            return 1  # 每帧检测 - 完整分析
        elif detection_mode == 'real_time':
            return max(1, int(fps / 10))  # 10fps采样
        elif detection_mode == 'elderly_optimized':
            return max(1, int(fps / 15))  # 15fps采样
        elif detection_mode == 'full_analysis':
            return 1  # 完整帧分析 - 新增模式
        else:  # standard
            return max(1, int(fps / 5))  # 5fps采样
    
    async def _detect_frame(self, frame: np.ndarray, detectors: Dict, timestamp: float, frame_number: int) -> List[Dict[str, Any]]:
        """检测单个帧"""
        detections = []
        
        try:
            # 跌倒检测
            if 'fall' in detectors:
                fall_result = await detectors['fall'].detect(frame, timestamp, frame_number)
                if fall_result:
                    detections.append(fall_result)
            
            # 火焰检测
            if 'fire' in detectors:
                fire_result = await detectors['fire'].detect(frame, timestamp, frame_number)
                if fire_result:
                    detections.append(fire_result)
            
            # 烟雾检测
            if 'smoke' in detectors:
                smoke_result = await detectors['smoke'].detect(frame, timestamp, frame_number)
                if smoke_result:
                    detections.append(smoke_result)
                    
        except Exception as e:
            logger.error(f"帧检测失败 (frame {frame_number}): {str(e)}")
        
        return detections
    
    def _merge_detections(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """合并相近的检测事件"""
        if not detections:
            return []
        
        # 按类型和时间排序
        detections.sort(key=lambda x: (x['type'], x['timestamp']))
        
        merged = []
        current_event = None
        
        for detection in detections:
            if current_event is None:
                current_event = detection.copy()
                current_event['start_time'] = detection['timestamp']
                current_event['end_time'] = detection['timestamp']
                current_event['duration'] = 0
                current_event['frame_detections'] = [detection]
            else:
                # 如果是同类型事件且时间间隔小于3秒，合并
                if (detection['type'] == current_event['type'] and 
                    detection['timestamp'] - current_event['end_time'] < 3.0):
                    current_event['end_time'] = detection['timestamp']
                    current_event['duration'] = current_event['end_time'] - current_event['start_time']
                    current_event['frame_detections'].append(detection)
                    # 更新置信度为最高值
                    current_event['confidence'] = max(current_event['confidence'], detection['confidence'])
                else:
                    # 结束当前事件，开始新事件
                    current_event['duration'] = current_event['end_time'] - current_event['start_time']
                    merged.append(current_event)
                    
                    current_event = detection.copy()
                    current_event['start_time'] = detection['timestamp']
                    current_event['end_time'] = detection['timestamp']
                    current_event['duration'] = 0
                    current_event['frame_detections'] = [detection]
        
        # 添加最后一个事件
        if current_event:
            current_event['duration'] = current_event['end_time'] - current_event['start_time']
            merged.append(current_event)
        
        # 为合并的事件生成ID
        for i, event in enumerate(merged):
            event['id'] = f"{event['type']}_{i+1}"
            event['detection_count'] = len(event['frame_detections'])
        
        return merged


class FallDetector:
    """跌倒检测器"""
    
    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2()
        
    async def detect(self, frame: np.ndarray, timestamp: float, frame_number: int) -> Optional[Dict[str, Any]]:
        """检测跌倒事件"""
        try:
            # 简化的跌倒检测算法
            # 1. 背景减法检测运动
            fg_mask = self.bg_subtractor.apply(frame)
            
            # 2. 形态学操作清理噪声
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel)
            
            # 3. 查找轮廓
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 500:  # 最小面积阈值
                    # 计算边界框
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 跌倒检测逻辑：宽度比高度大很多
                    aspect_ratio = w / h if h > 0 else 0
                    
                    if aspect_ratio > 1.5:  # 可能的跌倒
                        confidence = min(0.95, 0.6 + (aspect_ratio - 1.5) * 0.2)
                        
                        if confidence >= self.confidence_threshold:
                            return {
                                'type': 'fall',
                                'subtype': 'horizontal_fall',
                                'timestamp': timestamp,
                                'frame_number': frame_number,
                                'confidence': round(confidence, 3),
                                'bbox': [x, y, x + w, y + h],
                                'severity': 'HIGH' if confidence > 0.85 else 'MEDIUM',
                                'algorithm': 'OpenCV_MotionDetection'
                            }
            
        except Exception as e:
            logger.error(f"跌倒检测失败: {str(e)}")
        
        return None


class FireDetector:
    """火焰检测器"""
    
    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        
    async def detect(self, frame: np.ndarray, timestamp: float, frame_number: int) -> Optional[Dict[str, Any]]:
        """检测火焰"""
        try:
            # 转换到HSV色彩空间
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # 定义火焰颜色范围 (橙红色)
            lower_fire = np.array([0, 50, 50])
            upper_fire = np.array([35, 255, 255])
            
            # 创建掩码
            fire_mask = cv2.inRange(hsv, lower_fire, upper_fire)
            
            # 形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_CLOSE, kernel)
            
            # 查找轮廓
            contours, _ = cv2.findContours(fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 200:  # 最小火焰面积
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 基于颜色区域大小计算置信度
                    confidence = min(0.95, 0.5 + (area / 1000) * 0.3)
                    
                    if confidence >= self.confidence_threshold:
                        return {
                            'type': 'fire',
                            'subtype': 'flame',
                            'timestamp': timestamp,
                            'frame_number': frame_number,
                            'confidence': round(confidence, 3),
                            'bbox': [x, y, x + w, y + h],
                            'severity': 'CRITICAL',
                            'fire_area': int(area),
                            'algorithm': 'OpenCV_ColorDetection'
                        }
                        
        except Exception as e:
            logger.error(f"火焰检测失败: {str(e)}")
        
        return None


class SmokeDetector:
    """烟雾检测器"""
    
    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
        
    async def detect(self, frame: np.ndarray, timestamp: float, frame_number: int) -> Optional[Dict[str, Any]]:
        """检测烟雾"""
        try:
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 检测烟雾特征 (模糊区域)
            blur = cv2.GaussianBlur(gray, (15, 15), 0)
            diff = cv2.absdiff(gray, blur)
            
            # 阈值处理
            _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
            
            # 查找轮廓
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area > 1000:  # 烟雾区域较大
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # 基于模糊区域大小计算置信度
                    confidence = min(0.90, 0.4 + (area / 2000) * 0.4)
                    
                    if confidence >= self.confidence_threshold:
                        return {
                            'type': 'smoke',
                            'subtype': 'dense_smoke',
                            'timestamp': timestamp,
                            'frame_number': frame_number,
                            'confidence': round(confidence, 3),
                            'bbox': [x, y, x + w, y + h],
                            'severity': 'HIGH',
                            'smoke_area': int(area),
                            'algorithm': 'OpenCV_BlurDetection'
                        }
                        
        except Exception as e:
            logger.error(f"烟雾检测失败: {str(e)}")
        
        return None


# 创建全局视频处理器实例
video_processor = RealVideoProcessor()