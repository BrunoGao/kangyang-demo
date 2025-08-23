#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边缘控制器摄像头管理器
专注于RTSP视频流处理和AI检测，向管理平台推送事件
"""

import asyncio
import cv2
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor
import threading
from dataclasses import dataclass
import numpy as np

from .event_sender import EventSender, DetectionEvent
from stream.rtsp_handler import RTSPHandler
from ai.fall_detector import FallDetector
from ai.fire_detector import FireDetector 
from ai.smoke_detector import SmokeDetector

logger = logging.getLogger(__name__)

@dataclass 
class CameraInfo:
    """摄像头信息"""
    id: str
    name: str
    rtsp_url: str
    location: str
    zone_id: str = ""
    enabled_algorithms: List[str] = None
    status: str = "offline"  # offline, online, error
    
    def __post_init__(self):
        if self.enabled_algorithms is None:
            self.enabled_algorithms = ["fall_detection"]

@dataclass
class StreamProcessor:
    """视频流处理器"""
    camera_id: str
    rtsp_url: str
    detectors: Dict[str, Any]
    is_running: bool = False
    thread: Optional[threading.Thread] = None
    last_frame_time: Optional[datetime] = None
    frame_count: int = 0
    detection_count: int = 0
    fps: float = 0.0
    
class EdgeCameraManager:
    """边缘控制器摄像头管理器"""
    
    def __init__(self, max_cameras: int, config: Dict[str, Any], event_sender: EventSender):
        """
        初始化边缘摄像头管理器
        
        Args:
            max_cameras: 最大摄像头数量
            config: 配置信息
            event_sender: 事件发送器
        """
        self.max_cameras = max_cameras
        self.config = config
        self.event_sender = event_sender
        
        # 摄像头管理
        self.cameras: Dict[str, CameraInfo] = {}
        self.stream_processors: Dict[str, StreamProcessor] = {}
        self.camera_stats: Dict[str, Dict[str, Any]] = {}
        
        # 算法检测器
        self.detector_classes = {
            "fall_detection": FallDetector,
            "fire_detection": FireDetector, 
            "smoke_detection": SmokeDetector
        }
        
        # 线程池
        self.executor = ThreadPoolExecutor(max_workers=max_cameras * 2)
        
        # 统计信息
        self.start_time = datetime.now()
        self.total_detections = 0
        self.total_frames_processed = 0
        
        # RTSP处理器
        self.rtsp_handler = RTSPHandler(config.get("cameras", {}))
        
        logger.info(f"边缘摄像头管理器初始化完成，支持{max_cameras}路摄像头")
    
    async def initialize(self):
        """初始化管理器"""
        try:
            # 初始化RTSP处理器
            await self.rtsp_handler.initialize()
            
            # 加载摄像头配置（如果有的话）
            await self._load_camera_configs()
            
            logger.info("边缘摄像头管理器初始化完成")
            
        except Exception as e:
            logger.error(f"边缘摄像头管理器初始化失败: {e}")
            raise
    
    async def shutdown(self):
        """关闭管理器"""
        try:
            logger.info("正在关闭边缘摄像头管理器...")
            
            # 停止所有视频流
            for camera_id in list(self.stream_processors.keys()):
                await self.stop_camera_stream(camera_id)
            
            # 关闭线程池
            self.executor.shutdown(wait=True)
            
            # 关闭RTSP处理器
            await self.rtsp_handler.shutdown()
            
            logger.info("边缘摄像头管理器已关闭")
            
        except Exception as e:
            logger.error(f"关闭边缘摄像头管理器失败: {e}")
    
    async def add_camera(self, camera_info: CameraInfo) -> bool:
        """添加摄像头"""
        try:
            if len(self.cameras) >= self.max_cameras:
                logger.error(f"已达到最大摄像头数量限制: {self.max_cameras}")
                return False
            
            if camera_info.id in self.cameras:
                logger.warning(f"摄像头已存在: {camera_info.id}")
                return False
            
            # 测试RTSP连接
            connection_ok = await self._test_rtsp_connection(camera_info.rtsp_url)
            if connection_ok:
                camera_info.status = "online"
                logger.info(f"摄像头连接测试成功: {camera_info.id}")
            else:
                camera_info.status = "error"
                logger.warning(f"摄像头连接测试失败: {camera_info.id}")
            
            self.cameras[camera_info.id] = camera_info
            
            # 初始化统计
            self.camera_stats[camera_info.id] = {
                "total_detections": 0,
                "fall_detections": 0,
                "fire_detections": 0,
                "smoke_detections": 0,
                "fps": 0.0,
                "last_frame_time": None,
                "last_detection_time": None
            }
            
            logger.info(f"摄像头添加成功: {camera_info.id} - {camera_info.name}")
            return True
            
        except Exception as e:
            logger.error(f"添加摄像头失败: {e}")
            return False
    
    async def remove_camera(self, camera_id: str) -> bool:
        """移除摄像头"""
        try:
            if camera_id not in self.cameras:
                return False
            
            # 停止视频流
            await self.stop_camera_stream(camera_id)
            
            # 清理数据
            del self.cameras[camera_id]
            if camera_id in self.camera_stats:
                del self.camera_stats[camera_id]
            
            logger.info(f"摄像头移除成功: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"移除摄像头失败: {e}")
            return False
    
    async def start_camera_stream(self, camera_id: str) -> bool:
        """启动摄像头视频流处理"""
        try:
            if camera_id not in self.cameras:
                logger.error(f"摄像头不存在: {camera_id}")
                return False
            
            if camera_id in self.stream_processors and self.stream_processors[camera_id].is_running:
                logger.warning(f"摄像头流已在运行: {camera_id}")
                return True
            
            camera = self.cameras[camera_id]
            
            # 创建算法检测器
            detectors = {}
            detection_config = self.config.get("detection", {}).get("algorithms", {})
            
            for algo_name in camera.enabled_algorithms:
                if algo_name in self.detector_classes and algo_name in detection_config:
                    if detection_config[algo_name].get("enabled", True):
                        detector_class = self.detector_classes[algo_name]
                        detector = detector_class(detection_config[algo_name])
                        detectors[algo_name] = detector
                        logger.info(f"启用算法: {algo_name} for {camera_id}")
            
            if not detectors:
                logger.warning(f"没有启用的检测算法: {camera_id}")
                return False
            
            # 创建流处理器
            processor = StreamProcessor(
                camera_id=camera_id,
                rtsp_url=camera.rtsp_url,
                detectors=detectors
            )
            
            # 启动处理线程
            processor.thread = threading.Thread(
                target=self._process_camera_stream,
                args=(processor, camera),
                daemon=True
            )
            processor.is_running = True
            processor.thread.start()
            
            self.stream_processors[camera_id] = processor
            
            # 更新摄像头状态
            camera.status = "online"
            
            logger.info(f"摄像头流启动成功: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"启动摄像头流失败: {e}")
            return False
    
    async def stop_camera_stream(self, camera_id: str) -> bool:
        """停止摄像头视频流处理"""
        try:
            if camera_id not in self.stream_processors:
                return True
            
            processor = self.stream_processors[camera_id]
            processor.is_running = False
            
            # 等待线程结束
            if processor.thread and processor.thread.is_alive():
                processor.thread.join(timeout=5.0)
            
            del self.stream_processors[camera_id]
            
            # 更新摄像头状态
            if camera_id in self.cameras:
                self.cameras[camera_id].status = "offline"
            
            logger.info(f"摄像头流停止成功: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"停止摄像头流失败: {e}")
            return False
    
    def _process_camera_stream(self, processor: StreamProcessor, camera: CameraInfo):
        """处理摄像头视频流（在独立线程中运行）"""
        try:
            cap = cv2.VideoCapture(processor.rtsp_url)
            if not cap.isOpened():
                logger.error(f"无法打开视频流: {processor.camera_id}")
                return
            
            # 设置缓冲区大小
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # 获取目标帧率
            target_fps = self.config.get("cameras", {}).get("frame_rate", 8)
            frame_interval = 1.0 / target_fps
            
            logger.info(f"开始处理视频流: {processor.camera_id} @ {target_fps}FPS")
            
            last_time = time.time()
            fps_counter = 0
            fps_start_time = time.time()
            
            while processor.is_running:
                current_time = time.time()
                
                # 帧率控制
                if current_time - last_time < frame_interval:
                    time.sleep(0.001)
                    continue
                
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"读取帧失败: {processor.camera_id}")
                    time.sleep(0.1)
                    continue
                
                processor.frame_count += 1
                processor.last_frame_time = datetime.now()
                last_time = current_time
                
                # 更新FPS统计
                fps_counter += 1
                if fps_counter >= target_fps:
                    processor.fps = fps_counter / (current_time - fps_start_time)
                    fps_counter = 0
                    fps_start_time = current_time
                
                # AI检测
                detections = self._detect_frame(frame, processor.detectors, processor.camera_id)
                
                if detections:
                    processor.detection_count += len(detections)
                    self.total_detections += len(detections)
                    
                    # 异步发送检测事件
                    for detection in detections:
                        event = DetectionEvent(
                            id=str(uuid.uuid4()),
                            event_type=detection["type"],
                            event_subtype=detection.get("subtype", ""),
                            camera_id=processor.camera_id,
                            camera_name=camera.name,
                            location=camera.location,
                            timestamp=datetime.now().isoformat(),
                            confidence=detection["confidence"],
                            severity=detection.get("severity", "MEDIUM"),
                            bbox=detection.get("bbox"),
                            algorithm=detection.get("algorithm", ""),
                            additional_data=detection
                        )
                        
                        # 发送事件到管理平台
                        asyncio.run_coroutine_threadsafe(
                            self.event_sender.send_detection_event(event),
                            asyncio.get_event_loop()
                        )
                
                self.total_frames_processed += 1
                
                # 更新统计
                stats = self.camera_stats[processor.camera_id]
                stats["fps"] = processor.fps
                stats["last_frame_time"] = processor.last_frame_time
                if detections:
                    stats["last_detection_time"] = datetime.now()
            
        except Exception as e:
            logger.error(f"处理视频流异常: {processor.camera_id} - {e}")
        finally:
            cap.release()
            logger.info(f"视频流处理结束: {processor.camera_id}")
    
    def _detect_frame(self, frame: np.ndarray, detectors: Dict[str, Any], 
                     camera_id: str) -> List[Dict[str, Any]]:
        """检测单帧画面"""
        detections = []
        
        try:
            for algo_name, detector in detectors.items():
                try:
                    if algo_name == "fall_detection":
                        result = detector.detect(frame, time.time(), 
                                               self.stream_processors[camera_id].frame_count)
                        if result:
                            result["algorithm"] = "FallDetector"
                            detections.append(result)
                    
                    elif algo_name in ["fire_detection", "smoke_detection"]:
                        results = detector.detect_fire_smoke(frame)
                        for result in results:
                            if (algo_name == "fire_detection" and result["type"] == "fire") or \
                               (algo_name == "smoke_detection" and result["type"] == "smoke"):
                                detection = {
                                    "type": result["type"],
                                    "subtype": result.get("subtype", ""),
                                    "timestamp": time.time(),
                                    "frame_number": self.stream_processors[camera_id].frame_count,
                                    "confidence": result["confidence"],
                                    "bbox": result.get("bbox"),
                                    "severity": "CRITICAL" if result["type"] == "fire" else "HIGH",
                                    "algorithm": "FireSmokeDetector"
                                }
                                detections.append(detection)
                
                except Exception as e:
                    logger.error(f"算法检测失败 {algo_name}: {e}")
        
        except Exception as e:
            logger.error(f"帧检测失败: {camera_id} - {e}")
        
        return detections
    
    async def _test_rtsp_connection(self, rtsp_url: str) -> bool:
        """测试RTSP连接"""
        try:
            cap = cv2.VideoCapture(rtsp_url)
            if cap.isOpened():
                ret, _ = cap.read()
                cap.release()
                return ret
            return False
        except Exception:
            return False
    
    async def _load_camera_configs(self):
        """加载摄像头配置"""
        # 这里可以从配置文件或管理平台加载摄像头配置
        # 暂时留空，由API接口动态添加摄像头
        pass
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        try:
            active_cameras = len([p for p in self.stream_processors.values() if p.is_running])
            
            # 计算平均FPS
            avg_fps = 0.0
            if self.stream_processors:
                total_fps = sum(p.fps for p in self.stream_processors.values())
                avg_fps = total_fps / len(self.stream_processors)
            
            stats = {
                "controller_id": self.config.get("edge_controller", {}).get("id", "unknown"),
                "controller_name": self.config.get("edge_controller", {}).get("name", "Unknown"),
                "total_cameras": len(self.cameras),
                "active_cameras": active_cameras,
                "online_cameras": len([c for c in self.cameras.values() if c.status == "online"]),
                "total_detections": self.total_detections,
                "total_frames_processed": self.total_frames_processed,
                "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
                "average_fps": round(avg_fps, 2),
                "timestamp": datetime.now().isoformat()
            }
            
            # 更新事件发送器的控制器统计
            await self.event_sender.update_controller_stats(stats)
            
            return stats
            
        except Exception as e:
            logger.error(f"获取系统统计失败: {e}")
            return {}
    
    async def get_camera_list(self) -> List[Dict[str, Any]]:
        """获取摄像头列表"""
        cameras = []
        for camera_id, camera in self.cameras.items():
            camera_data = {
                "id": camera.id,
                "name": camera.name,
                "location": camera.location,
                "zone_id": camera.zone_id,
                "status": camera.status,
                "enabled_algorithms": camera.enabled_algorithms,
                "rtsp_url": camera.rtsp_url[:50] + "..." if len(camera.rtsp_url) > 50 else camera.rtsp_url
            }
            
            # 添加统计信息
            if camera_id in self.camera_stats:
                camera_data.update(self.camera_stats[camera_id])
            
            # 添加流处理信息
            if camera_id in self.stream_processors:
                processor = self.stream_processors[camera_id]
                camera_data.update({
                    "is_streaming": processor.is_running,
                    "frame_count": processor.frame_count,
                    "detection_count": processor.detection_count
                })
            
            cameras.append(camera_data)
        
        return cameras
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """获取性能统计信息"""
        try:
            stats = await self.get_system_stats()
            
            # 添加详细的性能指标
            performance_stats = {
                "timestamp": datetime.now().isoformat(),
                "system_metrics": {
                    "cpu_usage": stats.get("cpu_usage", 0),
                    "memory_usage": stats.get("memory_usage", 0),
                    "disk_usage": stats.get("disk_usage", 0),
                    "uptime_seconds": stats.get("uptime_seconds", 0)
                },
                "camera_metrics": {
                    "total_cameras": len(self.cameras),
                    "active_cameras": stats.get("active_cameras", 0),
                    "online_cameras": stats.get("online_cameras", 0),
                    "offline_cameras": len(self.cameras) - stats.get("online_cameras", 0)
                },
                "detection_metrics": {
                    "total_detections": stats.get("total_detections", 0),
                    "frames_processed": stats.get("total_frames_processed", 0),
                    "average_fps": stats.get("average_fps", 0.0),
                    "detection_rate": stats.get("detection_rate", 0.0)
                },
                "algorithm_stats": {}
            }
            
            # 收集每个算法的统计信息
            for detector_name in ["fall_detection", "fire_detection", "smoke_detection"]:
                performance_stats["algorithm_stats"][detector_name] = {
                    "detections": 0,
                    "false_positives": 0,
                    "accuracy": 0.95  # 模拟值
                }
            
            return performance_stats
            
        except Exception as e:
            logger.error(f"获取性能统计失败: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        try:
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": time.time() - (getattr(self, '_start_time', time.time())),
                "total_cameras": len(self.cameras),
                "active_cameras": len([c for c in self.cameras.values() if c.status == "online"]),
                "components": {
                    "camera_manager": "healthy",
                    "event_sender": "healthy" if self.event_sender else "unavailable",
                    "rtsp_handler": "healthy" if self.rtsp_handler else "unavailable"
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def update_algorithm_config(self, algorithm_name: str, config: Dict[str, Any]) -> bool:
        """更新算法配置"""
        try:
            # 这里可以实现算法配置的更新逻辑
            logger.info(f"更新算法配置: {algorithm_name} -> {config}")
            return True
        except Exception as e:
            logger.error(f"更新算法配置失败: {e}")
            return False
    
    async def reload_algorithm(self, algorithm_name: str) -> bool:
        """重载算法"""
        try:
            logger.info(f"重载算法: {algorithm_name}")
            # 这里可以实现算法重载逻辑
            return True
        except Exception as e:
            logger.error(f"重载算法失败: {e}")
            return False