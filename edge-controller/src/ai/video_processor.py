#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频文件处理器 - 用于测试跌倒检测算法
支持MP4、AVI等视频文件的处理和检测
"""

import cv2
import numpy as np
import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
import os
from pathlib import Path

from .fall_detector import FallDetector
from .fire_detector import FireDetector  
from .smoke_detector import SmokeDetector

logger = logging.getLogger(__name__)

class VideoProcessor:
    """视频文件处理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化视频处理器
        
        Args:
            config: 处理配置参数
        """
        self.config = config or {}
        
        # 检测器初始化
        self.fall_detector = FallDetector(self.config.get("fall_detection", {}))
        self.fire_detector = FireDetector(self.config.get("fire_detection", {}))
        self.smoke_detector = SmokeDetector(self.config.get("smoke_detection", {}))
        
        # 处理参数
        self.fps_limit = self.config.get("fps_limit", 30)  # 处理帧率限制
        self.skip_frames = self.config.get("skip_frames", 0)  # 跳帧处理
        self.resize_width = self.config.get("resize_width", 640)  # 缩放宽度
        self.resize_height = self.config.get("resize_height", 480)  # 缩放高度
        
        # 统计信息
        self.stats = {
            "total_frames": 0,
            "processed_frames": 0,
            "detections": [],
            "processing_time": 0,
            "start_time": None,
            "end_time": None
        }
        
        logger.info("视频处理器初始化完成")
    
    def validate_video_file(self, video_path: str) -> Dict[str, Any]:
        """验证视频文件"""
        try:
            if not os.path.exists(video_path):
                return {"valid": False, "error": "视频文件不存在"}
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {"valid": False, "error": "无法打开视频文件"}
            
            # 获取视频信息
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            duration = total_frames / fps if fps > 0 else 0
            
            cap.release()
            
            return {
                "valid": True,
                "total_frames": total_frames,
                "fps": fps,
                "width": width,
                "height": height,
                "duration_seconds": duration,
                "file_size": os.path.getsize(video_path)
            }
            
        except Exception as e:
            logger.error(f"验证视频文件失败: {e}")
            return {"valid": False, "error": str(e)}
    
    async def process_video(self, video_path: str, 
                           algorithms: List[str] = None,
                           progress_callback: Callable = None) -> Dict[str, Any]:
        """
        处理视频文件，执行跌倒检测
        
        Args:
            video_path: 视频文件路径
            algorithms: 要启用的算法列表 ['fall_detection', 'fire_detection', 'smoke_detection']
            progress_callback: 进度回调函数
            
        Returns:
            处理结果
        """
        try:
            # 默认启用跌倒检测
            if algorithms is None:
                algorithms = ['fall_detection']
            
            # 验证视频文件
            validation = self.validate_video_file(video_path)
            if not validation["valid"]:
                return {"success": False, "error": validation["error"]}
            
            logger.info(f"开始处理视频: {video_path}")
            logger.info(f"视频信息: {validation}")
            
            # 重置统计信息
            self.stats = {
                "total_frames": validation["total_frames"],
                "processed_frames": 0,
                "detections": [],
                "processing_time": 0,
                "start_time": datetime.now(),
                "end_time": None,
                "video_info": validation
            }
            
            # 打开视频
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {"success": False, "error": "无法打开视频文件"}
            
            frame_number = 0
            detection_count = 0
            start_time = time.time()
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_number += 1
                current_time = time.time()
                
                # 跳帧处理
                if self.skip_frames > 0 and frame_number % (self.skip_frames + 1) != 0:
                    continue
                
                # 缩放处理
                if self.resize_width and self.resize_height:
                    frame = cv2.resize(frame, (self.resize_width, self.resize_height))
                
                # 执行检测
                detections = await self._run_detections(frame, current_time, frame_number, algorithms)
                
                if detections:
                    detection_count += len(detections)
                    self.stats["detections"].extend(detections)
                    
                    # 记录检测结果
                    for detection in detections:
                        logger.info(f"检测到{detection['type']}: 置信度={detection['confidence']:.2f}, 帧号={frame_number}")
                
                self.stats["processed_frames"] += 1
                
                # 进度回调
                if progress_callback:
                    progress = self.stats["processed_frames"] / validation["total_frames"]
                    await progress_callback(progress, frame_number, detections)
                
                # FPS限制
                if self.fps_limit > 0:
                    frame_time = 1.0 / self.fps_limit
                    elapsed = time.time() - current_time
                    if elapsed < frame_time:
                        await asyncio.sleep(frame_time - elapsed)
            
            cap.release()
            
            # 完成统计
            end_time = time.time()
            self.stats["end_time"] = datetime.now()
            self.stats["processing_time"] = end_time - start_time
            
            # 生成结果报告
            result = {
                "success": True,
                "video_path": video_path,
                "algorithms_used": algorithms,
                "processing_stats": {
                    "total_frames": validation["total_frames"],
                    "processed_frames": self.stats["processed_frames"],
                    "processing_time_seconds": self.stats["processing_time"],
                    "fps_processed": self.stats["processed_frames"] / self.stats["processing_time"],
                    "detection_count": detection_count
                },
                "detections": self.stats["detections"],
                "detection_summary": self._generate_detection_summary()
            }
            
            logger.info(f"视频处理完成: {result['processing_stats']}")
            return result
            
        except Exception as e:
            logger.error(f"处理视频异常: {e}")
            return {"success": False, "error": str(e)}
    
    async def _run_detections(self, frame: np.ndarray, timestamp: float, 
                            frame_number: int, algorithms: List[str]) -> List[Dict[str, Any]]:
        """运行检测算法"""
        detections = []
        
        try:
            # 跌倒检测
            if 'fall_detection' in algorithms:
                fall_result = self.fall_detector.detect(frame, timestamp, frame_number)
                if fall_result:
                    detections.append(fall_result)
            
            # 火焰检测
            if 'fire_detection' in algorithms:
                fire_result = self.fire_detector.detect(frame, timestamp, frame_number)
                if fire_result:
                    detections.append(fire_result)
            
            # 烟雾检测
            if 'smoke_detection' in algorithms:
                smoke_result = self.smoke_detector.detect(frame, timestamp, frame_number)
                if smoke_result:
                    detections.append(smoke_result)
            
        except Exception as e:
            logger.error(f"检测算法执行异常: {e}")
        
        return detections
    
    def _generate_detection_summary(self) -> Dict[str, Any]:
        """生成检测结果摘要"""
        try:
            detections = self.stats["detections"]
            
            # 按类型统计
            type_counts = {}
            confidence_by_type = {}
            
            for detection in detections:
                det_type = detection.get("type", "unknown")
                
                if det_type not in type_counts:
                    type_counts[det_type] = 0
                    confidence_by_type[det_type] = []
                
                type_counts[det_type] += 1
                confidence_by_type[det_type].append(detection.get("confidence", 0))
            
            # 计算统计信息
            summary = {
                "total_detections": len(detections),
                "detection_types": type_counts,
                "average_confidence_by_type": {},
                "max_confidence_by_type": {},
                "detection_timeline": []
            }
            
            # 置信度统计
            for det_type, confidences in confidence_by_type.items():
                if confidences:
                    summary["average_confidence_by_type"][det_type] = sum(confidences) / len(confidences)
                    summary["max_confidence_by_type"][det_type] = max(confidences)
            
            # 时间线（前10个检测）
            timeline = sorted(detections, key=lambda x: x.get("frame_number", 0))[:10]
            for detection in timeline:
                summary["detection_timeline"].append({
                    "frame_number": detection.get("frame_number"),
                    "timestamp": detection.get("timestamp"),
                    "type": detection.get("type"),
                    "confidence": detection.get("confidence"),
                    "subtype": detection.get("subtype")
                })
            
            return summary
            
        except Exception as e:
            logger.error(f"生成检测摘要异常: {e}")
            return {"error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取处理统计信息"""
        return self.stats.copy()