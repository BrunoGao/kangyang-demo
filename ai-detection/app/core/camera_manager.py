#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多摄像头管理核心模块
支持22路摄像头的接入、管理和实时AI分析
"""

import asyncio
import cv2
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import threading
from dataclasses import dataclass
import json

from ..models.camera import (
    Camera, CameraStatus, CameraType, AlgorithmType,
    CameraConfig, CameraStream, CameraStats, SystemOverview
)
from .video_processor import FallDetector, FireDetector, SmokeDetector
from .wechat_notifier import get_wechat_notifier, AlertEvent

logger = logging.getLogger(__name__)

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

class CameraManager:
    """摄像头管理器 - 支持22路摄像头并发处理"""
    
    def __init__(self, max_cameras: int = 22):
        """
        初始化摄像头管理器
        
        Args:
            max_cameras: 最大支持摄像头数量
        """
        self.max_cameras = max_cameras
        self.cameras: Dict[str, Camera] = {}
        self.camera_configs: Dict[str, CameraConfig] = {}
        self.stream_processors: Dict[str, StreamProcessor] = {}
        self.camera_stats: Dict[str, CameraStats] = {}
        
        # 算法检测器池
        self.detector_pool = {
            AlgorithmType.FALL_DETECTION: FallDetector,
            AlgorithmType.FIRE_DETECTION: FireDetector,
            AlgorithmType.SMOKE_DETECTION: SmokeDetector
        }
        
        # 线程池执行器
        self.executor = ThreadPoolExecutor(max_workers=max_cameras * 2)
        
        # 系统状态
        self.system_start_time = datetime.now()
        self.total_detections = 0
        
        logger.info(f"摄像头管理器初始化完成，支持{max_cameras}路摄像头")
    
    async def add_camera(self, camera: Camera) -> bool:
        """
        添加摄像头
        
        Args:
            camera: 摄像头信息
            
        Returns:
            添加是否成功
        """
        try:
            if len(self.cameras) >= self.max_cameras:
                logger.error(f"已达到最大摄像头数量限制: {self.max_cameras}")
                return False
            
            if camera.id in self.cameras:
                logger.warning(f"摄像头已存在: {camera.id}")
                return False
            
            # 测试RTSP连接
            connection_ok = await self._test_rtsp_connection(camera.rtsp_url)
            if not connection_ok:
                logger.error(f"RTSP连接测试失败: {camera.rtsp_url}")
                camera.status = CameraStatus.ERROR
            else:
                camera.status = CameraStatus.ONLINE
            
            self.cameras[camera.id] = camera
            
            # 初始化统计信息
            self.camera_stats[camera.id] = CameraStats(
                camera_id=camera.id,
                total_detections=0,
                fall_detections=0,
                fire_detections=0,
                smoke_detections=0
            )
            
            logger.info(f"摄像头添加成功: {camera.id} - {camera.name}")
            return True
            
        except Exception as e:
            logger.error(f"添加摄像头失败: {str(e)}")
            return False
    
    async def remove_camera(self, camera_id: str) -> bool:
        """移除摄像头"""
        try:
            if camera_id not in self.cameras:
                return False
            
            # 停止视频流处理
            await self.stop_camera_stream(camera_id)
            
            # 清理数据
            del self.cameras[camera_id]
            if camera_id in self.camera_configs:
                del self.camera_configs[camera_id]
            if camera_id in self.camera_stats:
                del self.camera_stats[camera_id]
            
            logger.info(f"摄像头移除成功: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"移除摄像头失败: {str(e)}")
            return False
    
    async def configure_camera(self, camera_id: str, config: CameraConfig) -> bool:
        """配置摄像头算法参数"""
        try:
            if camera_id not in self.cameras:
                return False
            
            self.camera_configs[camera_id] = config
            
            # 更新摄像头的启用算法
            camera = self.cameras[camera_id]
            camera.enabled_algorithms = list(config.algorithm_configs.keys())
            camera.updated_at = datetime.now()
            
            logger.info(f"摄像头配置更新成功: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"配置摄像头失败: {str(e)}")
            return False
    
    async def start_camera_stream(self, camera_id: str) -> bool:
        """启动摄像头视频流处理"""
        try:
            if camera_id not in self.cameras:
                return False
            
            if camera_id in self.stream_processors and self.stream_processors[camera_id].is_running:
                logger.warning(f"摄像头流已在运行: {camera_id}")
                return True
            
            camera = self.cameras[camera_id]
            config = self.camera_configs.get(camera_id)
            
            if not config:
                logger.error(f"摄像头未配置: {camera_id}")
                return False
            
            # 创建算法检测器
            detectors = {}
            for algo_type in camera.enabled_algorithms:
                if algo_type in self.detector_pool:
                    detector_class = self.detector_pool[algo_type]
                    detectors[algo_type.value] = detector_class()
            
            # 创建流处理器
            processor = StreamProcessor(
                camera_id=camera_id,
                rtsp_url=camera.rtsp_url,
                detectors=detectors
            )
            
            # 启动处理线程
            processor.thread = threading.Thread(
                target=self._process_camera_stream,
                args=(processor, config),
                daemon=True
            )
            processor.is_running = True
            processor.thread.start()
            
            self.stream_processors[camera_id] = processor
            
            # 更新摄像头状态
            camera.status = CameraStatus.ONLINE
            
            logger.info(f"摄像头流启动成功: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"启动摄像头流失败: {str(e)}")
            return False
    
    async def stop_camera_stream(self, camera_id: str) -> bool:
        """停止摄像头视频流处理"""
        try:
            if camera_id not in self.stream_processors:
                return True
            
            processor = self.stream_processors[camera_id]
            processor.is_running = False
            
            if processor.thread and processor.thread.is_alive():
                processor.thread.join(timeout=5.0)
            
            del self.stream_processors[camera_id]
            
            # 更新摄像头状态
            if camera_id in self.cameras:
                self.cameras[camera_id].status = CameraStatus.OFFLINE
            
            logger.info(f"摄像头流停止成功: {camera_id}")
            return True
            
        except Exception as e:
            logger.error(f"停止摄像头流失败: {str(e)}")
            return False
    
    def _process_camera_stream(self, processor: StreamProcessor, config: CameraConfig):
        """处理摄像头视频流（在独立线程中运行）"""
        try:
            cap = cv2.VideoCapture(processor.rtsp_url)
            if not cap.isOpened():
                logger.error(f"无法打开视频流: {processor.camera_id}")
                return
            
            logger.info(f"开始处理视频流: {processor.camera_id}")
            
            while processor.is_running:
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"读取帧失败: {processor.camera_id}")
                    time.sleep(0.1)
                    continue
                
                processor.frame_count += 1
                processor.last_frame_time = datetime.now()
                
                # 每5帧处理一次（减少计算负担）
                if processor.frame_count % 5 == 0:
                    detections = self._detect_frame(frame, processor.detectors, processor.camera_id)
                    
                    if detections:
                        processor.detection_count += len(detections)
                        # 异步处理检测结果
                        asyncio.run_coroutine_threadsafe(
                            self._handle_detections(processor.camera_id, detections),
                            asyncio.get_event_loop()
                        )
                
                # 控制处理速度
                time.sleep(0.04)  # 约25FPS
            
        except Exception as e:
            logger.error(f"处理视频流异常: {processor.camera_id} - {str(e)}")
        finally:
            cap.release()
            logger.info(f"视频流处理结束: {processor.camera_id}")
    
    def _detect_frame(self, frame, detectors: Dict[str, Any], camera_id: str) -> List[Dict[str, Any]]:
        """检测单帧画面"""
        detections = []
        
        try:
            for algo_name, detector in detectors.items():
                if algo_name == AlgorithmType.FALL_DETECTION.value:
                    result = detector.detect(frame, time.time(), self.stream_processors[camera_id].frame_count)
                    if result:
                        detections.append(result)
                        
                elif algo_name == AlgorithmType.FIRE_DETECTION.value:
                    results = detector.detect_fire_smoke(frame)
                    for result in results:
                        if result['type'] == 'fire':
                            detection = {
                                'type': 'fire',
                                'subtype': 'flame',
                                'timestamp': time.time(),
                                'frame_number': self.stream_processors[camera_id].frame_count,
                                'confidence': result['confidence'],
                                'bbox': result['bbox'],
                                'severity': 'CRITICAL',
                                'algorithm': 'FireDetector'
                            }
                            detections.append(detection)
                            
                elif algo_name == AlgorithmType.SMOKE_DETECTION.value:
                    results = detector.detect_fire_smoke(frame)
                    for result in results:
                        if result['type'] == 'smoke':
                            detection = {
                                'type': 'smoke',
                                'subtype': 'dense_smoke',
                                'timestamp': time.time(),
                                'frame_number': self.stream_processors[camera_id].frame_count,
                                'confidence': result['confidence'],
                                'bbox': result['bbox'],
                                'severity': 'HIGH',
                                'algorithm': 'SmokeDetector'
                            }
                            detections.append(detection)
            
        except Exception as e:
            logger.error(f"帧检测失败: {camera_id} - {str(e)}")
        
        return detections
    
    async def _handle_detections(self, camera_id: str, detections: List[Dict[str, Any]]):
        """处理检测结果"""
        try:
            camera = self.cameras.get(camera_id)
            if not camera:
                return
            
            # 导入告警管理器（避免循环导入）
            from .alert_manager import alert_manager
            from ..models.alert import AlertType
            
            for detection in detections:
                # 更新统计信息
                stats = self.camera_stats[camera_id]
                stats.total_detections += 1
                stats.last_detection_time = datetime.now()
                
                if detection['type'] == 'fall':
                    stats.fall_detections += 1
                elif detection['type'] == 'fire':
                    stats.fire_detections += 1
                elif detection['type'] == 'smoke':
                    stats.smoke_detections += 1
                
                self.total_detections += 1
                
                # 创建系统告警
                alert_type_map = {
                    'fall': AlertType.FALL_DETECTION,
                    'fire': AlertType.FIRE_DETECTION,
                    'smoke': AlertType.SMOKE_DETECTION
                }
                
                alert_type = alert_type_map.get(detection['type'])
                if alert_type:
                    title = f"检测到{detection['type']}事件"
                    description = f"{camera.location} - {camera.name} 检测到{detection.get('subtype', detection['type'])}事件"
                    
                    # 创建告警（会自动发送微信通知）
                    await alert_manager.create_alert(
                        alert_type=alert_type,
                        title=title,
                        description=description,
                        camera_id=camera_id,
                        camera_name=camera.name,
                        location=camera.location,
                        confidence=detection['confidence'],
                        algorithm_name=detection.get('algorithm', 'Unknown'),
                        detection_data=detection
                    )
                
                logger.info(f"检测事件处理完成: {camera_id} - {detection['type']} - 置信度: {detection['confidence']:.3f}")
                
        except Exception as e:
            logger.error(f"处理检测结果失败: {str(e)}")
    
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
    
    async def get_system_overview(self) -> SystemOverview:
        """获取系统总览信息"""
        try:
            online_count = sum(1 for camera in self.cameras.values() if camera.status == CameraStatus.ONLINE)
            active_algorithms = sum(len(camera.enabled_algorithms) for camera in self.cameras.values())
            
            # 计算今日检测数
            today_detections = sum(
                stats.total_detections for stats in self.camera_stats.values()
            )
            
            # 系统负载 (简化计算)
            system_load = len(self.stream_processors) / self.max_cameras if self.max_cameras > 0 else 0
            
            # 边缘控制器状态 (模拟数据)
            edge_controllers = [
                {
                    'id': 'edge_controller_1',
                    'name': '边缘控制器#1',
                    'status': 'online',
                    'cpu_usage': 45.2,
                    'gpu_usage': 23.8,
                    'memory_usage': 62.1,
                    'camera_count': min(11, len(self.cameras))
                },
                {
                    'id': 'edge_controller_2', 
                    'name': '边缘控制器#2',
                    'status': 'online',
                    'cpu_usage': 38.7,
                    'gpu_usage': 19.3,
                    'memory_usage': 58.4,
                    'camera_count': max(0, len(self.cameras) - 11)
                }
            ]
            
            # 最近告警 (模拟数据)
            recent_alerts = []
            for camera_id, stats in list(self.camera_stats.items())[:5]:
                if stats.last_detection_time:
                    camera = self.cameras.get(camera_id)
                    recent_alerts.append({
                        'camera_id': camera_id,
                        'camera_name': camera.name if camera else 'Unknown',
                        'alert_type': 'fall_detection',
                        'time': stats.last_detection_time.isoformat(),
                        'severity': 'HIGH'
                    })
            
            return SystemOverview(
                total_cameras=len(self.cameras),
                online_cameras=online_count,
                active_algorithms=active_algorithms,
                total_detections_today=today_detections,
                system_load=system_load,
                edge_controllers=edge_controllers,
                recent_alerts=recent_alerts
            )
            
        except Exception as e:
            logger.error(f"获取系统总览失败: {str(e)}")
            raise
    
    async def get_camera_list(self) -> List[Camera]:
        """获取摄像头列表"""
        return list(self.cameras.values())
    
    async def get_camera_detail(self, camera_id: str) -> Optional[Camera]:
        """获取摄像头详情"""
        return self.cameras.get(camera_id)
    
    async def get_camera_stats(self, camera_id: str) -> Optional[CameraStats]:
        """获取摄像头统计信息"""
        return self.camera_stats.get(camera_id)
    
    async def batch_start_cameras(self, camera_ids: List[str]) -> Dict[str, bool]:
        """批量启动摄像头"""
        results = {}
        for camera_id in camera_ids:
            results[camera_id] = await self.start_camera_stream(camera_id)
        return results
    
    async def batch_stop_cameras(self, camera_ids: List[str]) -> Dict[str, bool]:
        """批量停止摄像头"""
        results = {}
        for camera_id in camera_ids:
            results[camera_id] = await self.stop_camera_stream(camera_id)
        return results
    
    async def shutdown(self):
        """关闭管理器"""
        logger.info("正在关闭摄像头管理器...")
        
        # 停止所有视频流
        for camera_id in list(self.stream_processors.keys()):
            await self.stop_camera_stream(camera_id)
        
        # 关闭线程池
        self.executor.shutdown(wait=True)
        
        logger.info("摄像头管理器已关闭")

# 全局管理器实例
camera_manager = CameraManager(max_cameras=22)